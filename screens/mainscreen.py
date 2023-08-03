from __future__ import annotations

from gamelog import write_log
from screen import Screen, ScreenNames
from tcod.console import Console
from gamemap import GameMap
from tcod.path import hillclimb2d
from geom import Point, Direction
from typing import TYPE_CHECKING
from swatch import HP_EMPTY, HP_FILLED, TARGET

from tcod.ecs import Entity

import components as comps
import queries as q
import updates as u
import combat as cbt
import ui

if TYPE_CHECKING:
    from engine import Engine


class GameStates:
    MAIN = "main"
    SAVE = "save"
    ITEM = "item"


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, engine: Engine):
        super().__init__(ScreenNames.MAIN, engine)
        self.camera = ui.Camera(ui.MAP_W, ui.MAP_H)
        self.look_target: Point = None
        self.select_target: Entity = None
        self.mode = GameStates.MAIN
        self.save_menu = ui.YesNoMenu(self.engine.root, "Save Game?")
        self.item_menu: ui.MenuWithValues = None
        self.item_help = ui.TextBox(
            self.engine.root,
            30,
            5,
            "[ENTER] to use/equip, [SPACE] to drop, [ESC] to cancel",
            title="Item Help",
        )

    @property
    def cur_map(self) -> GameMap:
        return q.cur_map(self.world)

    def on_enter(self):
        self.mode = GameStates.MAIN

    def on_draw(self, con: Console):
        w = self.world
        cur_map = self.cur_map
        ui.draw_map(cur_map, self.camera, con)
        # ui.draw_dmap(cur_map, self.camera, con)
        for e in q.drawable_entities(w):
            p = e.components[comps.Location]
            render = e.components[comps.Renderable]
            if cur_map.visible[p.x, p.y] or not cur_map.dark:
                ui.draw_on_map(
                    p.x,
                    p.y,
                    render.glyph,
                    self.camera,
                    con,
                    cur_map,
                    render.color,
                )
        ui.draw_msgs(w, con)
        self.draw_stats(con)
        self.draw_fx(con)
        self.draw_look(con)
        if self.mode == GameStates.SAVE:
            self.save_menu.draw()
        if self.mode == GameStates.ITEM:
            self.item_menu.draw()
            self.item_help.draw()

    def on_update(self):
        player = self.player
        while True:
            self.update_dmap()
            self.get_npc_moves()
            self.check_moves()
            self.check_collisions()
            self.resolve_bumps()
            self.check_on_hits()
            self.check_item_users()
            self.check_deaths()
            self.update_energy()
            self.check_target()
            self.end_turn()
            self.update_fov()

            should_break = player.components[comps.Actor].energy >= 0 or q.is_dead(
                self.player
            )

            if should_break:
                break

        pos = player.components[comps.Location]
        self.camera.center = pos
        if q.is_dead(self.player):
            self.engine.shutdown()
            self.engine.switch_screen(ScreenNames.GAME_OVER)

    def check_collisions(self):
        for e, target in q.collisions(self.world):
            e_actor_comp = e.components[comps.Actor]

            if target == e:
                e_actor_comp.energy -= 100
                e.components.pop(comps.CollidesWith)
                continue

            if q.is_hostile(e, target):
                e.components[comps.BumpAttacking] = target

            e.components.pop(comps.CollidesWith)

    def check_moves(self):
        cur_map = self.cur_map
        for e in q.trying_to_move(self.world):
            dest = e.components[comps.TryMove]

            if cur_map.walkable(dest.x, dest.y):
                blockers = list(q.blockers_at(self.world, dest))
                if len(blockers) > 0:
                    e.components[comps.CollidesWith] = blockers[0]
                else:
                    e.components[comps.Location] = dest
                    e.components[comps.Actor].energy -= 100
                    arm = q.get_armor(e)
                    if arm:
                        e.components[comps.Actor].energy -= arm.components[
                            comps.Equipment
                        ].encumbrance
                    write_log(self.world, "action", f"{q.name(e)} moved")

                    if e.components.get(comps.InventoryMax) is not None:
                        items = q.items_at(self.world, e.components[comps.Location])
                        for item in items:
                            u.pick_up_item(item, e)

            e.components.pop(comps.TryMove)

    def get_npc_moves(self):
        cur_map = self.cur_map
        for e in filter(lambda e: q.is_enemy(e), q.turn_actors(self.world)):
            write_log(self.world, "action", f"{q.name(e)} acts")
            e_pos = e.components[comps.Location]
            path = hillclimb2d(cur_map.dist, (e_pos.x, e_pos.y), True, False)

            if len(path) > 1:
                try_x, try_y = path[1]
                e.components[comps.TryMove] = Point(try_x, try_y)

    def update_dmap(self):
        pos = self.player.components[comps.Location]
        self.cur_map.update_dmap(pos)

    def update_energy(self):
        for e in q.current_actors(self.world):
            act_comp = e.components[comps.Actor]
            act_comp.energy += act_comp.speed
            write_log(
                self.world,
                "energy",
                f"{q.name(e)} gains {act_comp.speed} energy, has {act_comp.energy}",
            )

    def resolve_bumps(self):
        for attacker, defender in q.bumpers(self.world):
            atk_name = q.name(attacker)
            def_name = q.name(defender)

            u.add_msg_about(attacker, f"<entity> attacks {def_name}!")
            result = cbt.bump_attack(attacker, defender)
            write_log(
                self.world,
                "combat",
                f"{atk_name} bumping {def_name}: hit={result.hit}, margin={result.margin}",  # noqa: E501
            )
            if result.hit:
                dmg_l, dmg_h = q.dmg(attacker)
                raw_dmg = cbt.gauss_roll(dmg_l, dmg_h)
                def_redu = q.get_stat(defender, "reduction")
                final_dmg = max(0, raw_dmg - def_redu)
                defender.components[comps.Combatant].damage(final_dmg)
                arm = q.get_armor(defender)
                if arm:
                    arm.components[comps.Equipment].durability -= 1
                u.add_msg_about(
                    attacker,
                    f"<entity> hits {def_name} for {final_dmg} damage!",
                )
                write_log(
                    self.world,
                    "combat",
                    f"{atk_name} bumps {def_name} for {raw_dmg} raw, {final_dmg} after armor reduction",  # noqa: E501
                )
                wpn = q.get_weapon(attacker)
                if wpn:
                    wpn.components[comps.CheckOnHits] = defender
                else:
                    attacker.components[comps.CheckOnHits] = defender
            else:
                u.add_msg_about(attacker, f"<entity> misses {def_name}!")

            attacker.components[comps.Actor].energy -= 100
            attacker.components.pop(comps.BumpAttacking)

    def check_deaths(self):
        query = q.living(self.world)
        for e, stats in query[Entity, comps.Combatant]:
            if stats.dead:
                u.add_msg_about(e, "<entity> has fallen!")
                u.kill(e)

    def check_on_hits(self):
        for attacker, defender, on_hit in q.on_hits(self.world):
            atk_name = q.name(attacker)
            def_name = q.name(defender)
            write_log(
                self.world,
                "combat",
                f"Checking on-hits for {atk_name} against {def_name}",
            )
            if cbt.pct_chance(on_hit.chance):
                u.apply_effect(defender, on_hit.eff)
                write_log(
                    self.world,
                    "combat",
                    f"On-hit {on_hit.eff.name} successfully applied by {atk_name} to {def_name}",  # noqa: E501
                )
            attacker.components.pop(comps.CheckOnHits)

    def check_item_users(self):
        for e, use_info in q.trying_to_use_item(self.world):
            item = use_info.item
            item_comp = item.components[comps.Item]
            target = use_info.target
            user_name = q.name(e)
            target_name = q.name(target)
            item_name = q.name(item)
            wl_mod = e.components[comps.Combatant].wl_mod
            match item_comp.item_delivery:
                case "throw":
                    if q.is_visible(e) and q.is_visible(target):
                        u.add_msg_about(
                            e, f"<entity> throws {item_name} at {target_name}!"
                        )
                    u.apply_item(item, target)
                case "drink":
                    if q.is_visible(e):
                        u.add_msg_about(e, f"<entity> drinks {item_name}.")
                    u.apply_item(item, e)
                case "read":
                    dur = item_comp.eff_duration + wl_mod // 2
                    pot = item_comp.eff_potency + wl_mod
                    if q.is_visible(e):
                        if e is target:
                            u.add_msg_about(e, f"<entity> reads {item_name}!")
                        else:
                            u.add_msg_about(
                                e,
                                f"<entity> reads {item_name}, pointing at {target_name}!",  # noqa: E501
                            )
                    u.apply_item(item, target, duration=dur, potency=pot)
            item.clear()
            e.components[comps.Actor].energy -= 100
            write_log(
                self.world, "item", f"{user_name} uses {item_name} on {target_name}"
            )
            e.components.pop(comps.UseItemOn)

    def end_turn(self):
        query = q.current_actors(self.world)
        sentinel = self.world[None].components[comps.GameTicks]
        if sentinel == 5:
            for e in query:
                u.tick_effects(e, 1)
            self.world[None].components[comps.GameTicks] = 0
            self.world[None].components[comps.GameTurn] += 1
            write_log(self.world, "end turn", "Turn ends")
        else:
            self.world[None].components[comps.GameTicks] += 1

    def check_target(self):
        if self.select_target and (
            not q.is_visible(self.select_target) or q.is_dead(self.select_target)
        ):
            self.select_target = None

    def on_up(self):
        match self.mode:
            case GameStates.MAIN:
                pos = self.player.components[comps.Location]
                self.player.components[comps.TryMove] = pos + Direction.UP
                self.engine.should_update = True
            case GameStates.SAVE:
                self.save_menu.move_up()
            case GameStates.ITEM:
                self.item_menu.move_up()

    def on_down(self):
        match self.mode:
            case GameStates.MAIN:
                pos = self.player.components[comps.Location]
                self.player.components[comps.TryMove] = pos + Direction.DOWN
                self.engine.should_update = True
            case GameStates.SAVE:
                self.save_menu.move_down()
            case GameStates.ITEM:
                self.item_menu.move_down()

    def on_left(self):
        if self.mode == GameStates.MAIN:
            pos = self.player.components[comps.Location]
            self.player.components[comps.TryMove] = pos + Direction.LEFT
            self.engine.should_update = True

    def on_right(self):
        if self.mode == GameStates.MAIN:
            pos = self.player.components[comps.Location]
            self.player.components[comps.TryMove] = pos + Direction.RIGHT
            self.engine.should_update = True

    def on_wait(self):
        match self.mode:
            case GameStates.MAIN:
                pos = self.player.components[comps.Location]
                self.player.components[comps.TryMove] = pos
                self.engine.should_update = True
            case GameStates.ITEM:
                item_to_drop: Entity = self.item_menu.selected_val
                u.drop_item(item_to_drop, self.player)
                u.add_msg_about(self.player, f"<entity> drops {q.name(item_to_drop)}")
                inv = q.inventory(self.player)
                if inv:
                    self._setup_item_menu()
                else:
                    self.mode = GameStates.MAIN

    def on_cancel(self):
        match self.mode:
            case GameStates.MAIN:
                self.mode = GameStates.SAVE
            case GameStates.SAVE | GameStates.ITEM:
                self.mode = GameStates.MAIN

    def on_mouse_move(self, x: int, y: int):
        if self.mode == GameStates.MAIN:
            if self.camera.in_view(x, y):
                self.look_target = self.camera.to_map_coords(x, y, self.cur_map)
            else:
                self.look_target = None

    def on_confirm(self):
        match self.mode:
            case GameStates.SAVE:
                if self.save_menu.confirmed:
                    self.engine.shutdown()
                    self.engine.switch_screen(ScreenNames.TITLE)
                    return

                self.mode = GameStates.MAIN
            case GameStates.ITEM:
                item_to_use: Entity = self.item_menu.selected_val
                if q.is_equipment(item_to_use):
                    if q.is_equipped_to(item_to_use, self.player):
                        u.unequip_item(item_to_use, self.player)
                    else:
                        u.equip_item(item_to_use, self.player)
                else:
                    item_comp = item_to_use.components[comps.Item]
                    if item_comp.item_delivery == "drink":
                        target = self.player
                    else:
                        target = self.select_target

                    if not target:
                        u.add_msg(self.world, "(No target for selected item.)", TARGET)
                        self.mode = GameStates.MAIN
                        return

                    self.player.components[comps.UseItemOn] = comps.UseItemOn(
                        target, item_to_use
                    )

                self.mode = GameStates.MAIN
                self.engine.should_update = True
            case GameStates.MAIN:
                loc = q.location(self.player)
                map_conns = q.map_connections(self.world, self.cur_map.id)
                tile = self.cur_map.tiles[loc.x, loc.y]
                went_stairs = False
                if tile == self.cur_map.stairs_down_tile:
                    new_m, new_loc = map_conns["down"]
                    u.change_map(self.player, new_m, new_loc)
                    went_stairs = True
                elif tile == self.cur_map.stairs_up_tile:
                    new_m, new_loc = map_conns["up"]
                    u.change_map(self.player, new_m, new_loc)
                    went_stairs = True

                if went_stairs:
                    self.player.components[comps.Actor].energy -= 100
                    self.engine.should_update = True

    def _setup_item_menu(self):
        inv = q.inventory(self.player)
        opts_dict = {
            f"{i+1} - {q.name(e)}{' (e)' if e in list(q.get_equipped(self.player)) else ''}": e  # noqa: E501
            for i, e in enumerate(inv)
        }
        self.item_menu = ui.MenuWithValues(
            self.engine.root, opts_dict, title="Inventory"
        )
        self.item_help.y = self.item_menu.y - 5

    def on_inventory(self):
        inv = q.inventory(self.player)
        if inv:
            self._setup_item_menu()
            self.mode = GameStates.ITEM
        else:
            u.add_msg(self.world, "(Nothing in the pack.)", TARGET)

    def on_mouse_click(self, x: int, y: int):
        if self.mode == GameStates.MAIN:
            blocker_list = list(q.blockers_at(self.world, self.look_target))
            if blocker_list:
                blocker = blocker_list[0]
                if q.is_visible(blocker):
                    self.select_target = blocker

    def update_fov(self):
        player_loc = self.player.components[comps.Location]
        self.cur_map.update_fov(player_loc.x, player_loc.y, 8)

    def draw_stats(self, con: Console):
        stats = self.player.components[comps.Combatant]
        name = self.player.components[comps.Name]
        map_name = self.cur_map.name
        loc = self.player.components[comps.Location]
        hp_txt = f"HP: {stats.hp_str}"
        target_name = (
            self.select_target.components[comps.Name] if self.select_target else "None"
        )
        wpn = q.get_weapon(self.player)
        arm = q.get_armor(self.player)
        trink = q.get_trinket(self.player)
        wpn_txt = q.name(wpn) if wpn else "None"
        arm_text = q.name(arm) if arm else "None"
        trink_text = q.name(trink) if trink else "None"

        atp = q.get_stat(self.player, "atp")
        dfp = q.get_stat(self.player, "dfp")
        redu = q.get_stat(self.player, "reduction")
        dmg_l, dmg_h = q.dmg(self.player)

        con.print(ui.MAP_W, 0, f"{name}")
        con.print(ui.MAP_W, 1, f"{map_name} - {loc}")
        con.print(ui.MAP_W, 2, hp_txt)
        self.draw_hp_bar(ui.MAP_W + len(hp_txt), 2, 8, self.player, con)
        con.print(ui.MAP_W, 3, f"ST: {stats.st} AG: {stats.ag} WL: {stats.wl}")
        con.print(ui.MAP_W, 4, f"ATP: {atp} DFP: {dfp}")
        con.print(ui.MAP_W, 5, f"DMG: {dmg_l}-{dmg_h} RED: {redu}")
        con.print(ui.MAP_W, 6, f"Weapon: {wpn_txt}")
        con.print(ui.MAP_W, 7, f"Armor: {arm_text}")
        con.print(ui.MAP_W, 8, f"Trinket:  {trink_text}")
        con.print(ui.MAP_W, 9, f"Target: {target_name}")

    def draw_fx(self, con: Console):
        effects = list(
            filter(
                lambda eff: not eff.expired, self.player.components[comps.EffectsList]
            )
        )
        x = ui.MSG_W
        y = ui.MAP_H
        con.draw_frame(ui.MSG_W, ui.MAP_H, ui.SCR_W - ui.MSG_W, ui.MSG_H, "Effects")
        for i, eff in enumerate(effects[-8:]):
            con.print(x + 1, y + i + 1, f"{eff}")

    def draw_hp_bar(self, x: int, y: int, w: int, e: Entity, con: Console):
        vitals = e.components.get(comps.Combatant)
        if not vitals:
            return

        ui.draw_bar(x, y, vitals.cur_hp, vitals.max_hp, w, HP_FILLED, HP_EMPTY, con)

    def draw_look(self, con: Console):
        lt = self.look_target
        if lt:
            ui.draw_on_map(lt.x, lt.y, "X", self.camera, con, self.cur_map, TARGET)

            es = list(q.entities_at(self.world, lt))
            if es and self.cur_map.visible[lt.x, lt.y]:
                con.print(ui.MAP_W, 10, "Things here:")
                for i, e in enumerate(es):
                    name = e.components[comps.Name]
                    dead = q.is_dead(e)
                    if dead:
                        name = f"{name} (dead)"
                    y = 11 + i
                    con.print(
                        ui.MAP_W,
                        y,
                        name,
                        e.components[comps.Renderable].color,
                    )
                    if not dead:
                        self.draw_hp_bar(ui.MAP_W + len(name) + 1, y, 5, e, con)
