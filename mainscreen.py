from screen import Screen
from tcod.console import Console
from gamemap import GameMap
from tcod.event import KeySym
from tcod.map import compute_fov
from tcod.path import hillclimb2d
from tcod.constants import FOV_DIAMOND
from geom import Point, Direction
from typing import Optional
from action import Action
from swatch import HP_EMPTY, HP_FILLED
from ui import (
    MSG_H,
    MSG_W,
    SCR_W,
    Camera,
    draw_bar,
    draw_map,
    draw_msgs,
    draw_on_map,
    MAP_W,
    MAP_H,
)
from tcod.ecs import World, Entity

import components as comps
import queries as q
import updates as u
import combat as cbt


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, world: World):
        super().__init__("main", world)
        self.camera = Camera(MAP_W, MAP_H)

    @property
    def cur_map(self) -> GameMap:
        return q.cur_map(self.world)

    @property
    def player(self) -> Entity:
        return q.player(self.world)

    def on_draw(self, con: Console):
        w = self.world
        cur_map = self.cur_map
        draw_map(cur_map, self.camera, con)
        # draw_dmap(cur_map, self.camera, con)
        for e in q.drawable_entities(w):
            p = e.components[comps.Location].pos
            render = e.components[comps.Renderable]
            if cur_map.visible[p.x, p.y] or not cur_map.dark:
                draw_on_map(
                    p.x,
                    p.y,
                    render.glyph,
                    self.camera,
                    con,
                    cur_map,
                    render.color,
                )
        draw_msgs(w, con)
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

        pos = player.components[comps.Location].pos
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
            dest = e.components[comps.TryMove].pos

            if cur_map.walkable(dest.x, dest.y):
                blockers = list(q.blockers_at(self.world, dest))
                if len(blockers) > 0:
                    e.components[comps.CollidesWith] = blockers[0]
                else:
                    e.components[comps.Location].pos = dest
                    e.components[comps.Actor].energy -= 50

            e.components.pop(comps.TryMove)

    def get_npc_moves(self):
        cur_map = self.cur_map
        for e in filter(lambda e: q.is_enemy(e), q.turn_actors(self.world)):
            e_pos = e.components[comps.Location].pos
            path = hillclimb2d(cur_map.dist, (e_pos.x, e_pos.y), True, False)

            if len(path) > 1:
                try_x, try_y = path[1]
                e.components[comps.TryMove] = comps.TryMove(Point(try_x, try_y))

    def update_dmap(self):
        pos = self.player.components[comps.Location].pos
        self.cur_map.update_dmap(pos)

    def update_energy(self):
        for e in q.current_actors(self.world):
            act_comp = e.components[comps.Actor]
            act_comp.energy += act_comp.speed
        sent_comp = self.world[None].components[comps.Actor]
        sent_comp.energy += sent_comp.speed

    def resolve_bumps(self):
        for attacker, defender in self.world.Q[Entity, comps.BumpAttacking]:
            def_name = defender.components[comps.Name]

            u.add_msg_about(attacker, f"<entity> attacks {def_name}!")
            result = cbt.bump_attack(attacker, defender)
            if result.hit:
                raw_dmg = cbt.roll_dmg(attacker)
                defender.components[comps.Combatant].damage(raw_dmg)
                u.add_msg_about(
                    attacker,
                    f"<entity> hits {def_name} for {raw_dmg} damage!",
                )
                attacker.components[comps.CheckOnHits] = defender
            else:
                u.add_msg_about(attacker, f"<entity> misses {def_name}!")

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
            if cbt.pct_chance(on_hit.chance):
                u.apply_effect(defender, on_hit.eff)
            attacker.components.pop(comps.CheckOnHits)

    def end_turn(self):
        query = q.current_actors(self.world)
        sentinel = self.world[None].components[comps.Actor]
        if sentinel.energy == 100:
            for e in query:
                u.tick_effects(e, 1)
            sentinel.energy = 0

    def on_key(self, key: KeySym) -> Optional[Action]:
        dp = Direction.NONE
        running = True
        update = True

        match key:
            case KeySym.w:
                dp = Direction.UP
            case KeySym.a:
                dp = Direction.LEFT
            case KeySym.s:
                dp = Direction.DOWN
            case KeySym.d:
                dp = Direction.RIGHT
            case KeySym.SPACE:
                dp = Direction.NONE
            case KeySym.ESCAPE:
                running = False
                update = False
            case _:
                update = False

        if running:
            player = self.player
            pos = player.components[comps.Location]
            if update:
                new_point = pos.pos + dp
                player.components[comps.TryMove] = comps.TryMove(new_point)

        return Action(running, None, update)

    def update_fov(self):
        cur_map = self.cur_map
        player_loc = self.player.components[comps.Location]

        cur_map.visible = compute_fov(
            cur_map.tiles["transparent"],
            (player_loc.pos.x, player_loc.pos.y),
            radius=8,
            algorithm=FOV_DIAMOND,
        )

        cur_map.explored |= cur_map.visible

    def draw_stats(self, con: Console):
        stats = self.player.components[comps.Combatant]
        name = self.player.components[comps.Name]
        map_name = self.cur_map.name
        loc = self.player.components[comps.Location]

        con.print(MAP_W, 0, f"{name}")
        con.print(MAP_W, 1, f"{map_name} - {loc}")
        con.print(MAP_W, 2, f"HP: {stats.hp_str}")
        draw_bar(MAP_W, 3, stats.cur_hp, stats.max_hp, 10, HP_FILLED, HP_EMPTY, con)
        con.print(MAP_W, 4, f"ATP: {stats.atp}")
        con.print(MAP_W, 5, f"DFP: {stats.dfp}")
        con.print(MAP_W, 6, f"DMG: {stats.dmg_str}")

    def draw_fx(self, con: Console):
        effects = self.player.components[comps.EffectsList]
        x = MSG_W
        y = MAP_H
        con.draw_frame(MSG_W, MAP_H, SCR_W - MSG_W, MSG_H, "Effects")
        for i, eff in enumerate(effects[-8:]):
            con.print(x + 1, y + i + 1, f"{eff}")
