from __future__ import annotations

from gamelog import write_log
from screen import Screen, ScreenNames
from tcod.console import Console
from gamemap import GameMap
from tcod.path import hillclimb2d
from geom import Point, Direction
from typing import TYPE_CHECKING
from swatch import HP_EMPTY, HP_FILLED

from tcod.ecs import Entity

import components as comps
import queries as q
import updates as u
import combat as cbt
import ui

if TYPE_CHECKING:
    from engine import Engine


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, engine: Engine):
        super().__init__(ScreenNames.MAIN, engine)
        self.camera = ui.Camera(ui.MAP_W, ui.MAP_H)

    @property
    def cur_map(self) -> GameMap:
        return q.cur_map(self.world)

    @property
    def player(self) -> Entity:
        return q.player(self.world)

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

    def on_update(self):
        player = self.player

        while True:
            self.update_dmap()
            self.update_energy()
            self.get_npc_moves()
            self.check_moves()
            self.check_collisions()
            self.resolve_bumps()
            self.check_on_hits()
            self.check_deaths()
            self.end_turn()
            self.update_fov()

            if player.components[comps.Actor].energy >= 100:
                break

        pos = player.components[comps.Location]
        self.camera.center = pos

    def check_collisions(self):
        for e, target in self.world.Q[Entity, comps.CollidesWith]:
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
        for e in self.world.Q.all_of(
            components=[comps.Location, comps.TryMove],
            relations=[(comps.MapId, cur_map.id)],
        ):
            dest = e.components[comps.TryMove]

            if cur_map.walkable(dest.x, dest.y):
                blockers = list(q.blockers_at(self.world, dest))
                if len(blockers) > 0:
                    e.components[comps.CollidesWith] = blockers[0]
                else:
                    e.components[comps.Location] = dest
                    e.components[comps.Actor].energy -= 100
                    write_log(self.world, "action", f"{q.name(e)} moved")

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
        sent_comp = self.world[None].components[comps.Actor]
        sent_comp.energy += sent_comp.speed

    def resolve_bumps(self):
        for attacker, defender in self.world.Q[Entity, comps.BumpAttacking]:
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
                raw_dmg = cbt.roll_dmg(attacker)
                defender.components[comps.Combatant].damage(raw_dmg)
                u.add_msg_about(
                    attacker,
                    f"<entity> hits {def_name} for {raw_dmg} damage!",
                )
                write_log(
                    self.world,
                    "combat",
                    f"{atk_name} bumps {def_name} for {raw_dmg} raw",
                )
                attacker.components[comps.CheckOnHits] = defender
            else:
                u.add_msg_about(attacker, f"<entity> misses {def_name}!")

            attacker.components[comps.Actor].energy -= 100
            attacker.components.pop(comps.BumpAttacking)

    def check_deaths(self):
        query = self.world.Q.all_of(components=[comps.Combatant]).none_of(
            tags=["player", "dead"]
        )
        for e, stats in query[Entity, comps.Combatant]:
            if stats.dead:
                u.add_msg_about(e, "<entity> has fallen!")
                u.kill(e)

    def check_on_hits(self):
        for attacker, defender, on_hit in self.world.Q[
            Entity, comps.CheckOnHits, comps.OnHit
        ]:
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

    def end_turn(self):
        query = q.current_actors(self.world)
        sentinel = self.world[None].components[comps.Actor]
        if sentinel.energy == 100:
            for e in query:
                u.tick_effects(e, 1)
            sentinel.energy = 0
            self.world[None].components[comps.GameTurn] += 1
            write_log(self.world, "end turn", "Turn ends")

    def on_up(self):
        pos = self.player.components[comps.Location]
        self.player.components[comps.TryMove] = pos + Direction.UP
        self.engine.should_update = True

    def on_down(self):
        pos = self.player.components[comps.Location]
        self.player.components[comps.TryMove] = pos + Direction.DOWN
        self.engine.should_update = True

    def on_left(self):
        pos = self.player.components[comps.Location]
        self.player.components[comps.TryMove] = pos + Direction.LEFT
        self.engine.should_update = True

    def on_right(self):
        pos = self.player.components[comps.Location]
        self.player.components[comps.TryMove] = pos + Direction.RIGHT
        self.engine.should_update = True

    def on_wait(self):
        pos = self.player.components[comps.Location]
        self.player.components[comps.TryMove] = pos
        self.engine.should_update = True

    def on_cancel(self):
        self.engine.running = False
        self.engine.should_update = False

    def update_fov(self):
        player_loc = self.player.components[comps.Location]
        self.cur_map.update_fov(player_loc.x, player_loc.y, 8)

    def draw_stats(self, con: Console):
        stats = self.player.components[comps.Combatant]
        name = self.player.components[comps.Name]
        map_name = self.cur_map.name
        loc = self.player.components[comps.Location]

        con.print(ui.MAP_W, 0, f"{name}")
        con.print(ui.MAP_W, 1, f"{map_name} - {loc}")
        con.print(ui.MAP_W, 2, f"HP: {stats.hp_str}")
        ui.draw_bar(
            ui.MAP_W, 3, stats.cur_hp, stats.max_hp, 10, HP_FILLED, HP_EMPTY, con
        )
        con.print(ui.MAP_W, 4, f"ATP: {stats.atp}")
        con.print(ui.MAP_W, 5, f"DFP: {stats.dfp}")
        con.print(ui.MAP_W, 6, f"DMG: {stats.dmg_str}")

    def draw_fx(self, con: Console):
        effects = self.player.components[comps.EffectsList]
        x = ui.MSG_W
        y = ui.MAP_H
        con.draw_frame(ui.MSG_W, ui.MAP_H, ui.SCR_W - ui.MSG_W, ui.MSG_H, "Effects")
        for i, eff in enumerate(effects[-8:]):
            con.print(x + 1, y + i + 1, f"{eff}")
