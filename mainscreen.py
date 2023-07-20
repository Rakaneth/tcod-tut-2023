from screen import Screen
from tcod.console import Console
from gamestate import GameState
from tcod.event import KeySym
from tcod.map import compute_fov
from tcod.path import hillclimb2d
from tcod.constants import FOV_DIAMOND
from geom import Point, Direction
from typing import Optional
from action import Action
from ui import Camera, draw_map, draw_msgs, draw_on_map, MAP_W, MAP_H

import components as comps


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, gs: GameState):
        super().__init__("main", gs)
        self.camera = Camera(MAP_W, MAP_H)

    def on_draw(self, con: Console):
        draw_map(self.gs.cur_map, self.camera, con)
        # draw_dmap(self.gs.cur_map, self.camera, con)
        for e in self.gs.drawable_entities():
            p = e.components[comps.Location].pos
            render = e.components[comps.Renderable]
            if self.gs.cur_map.visible[p.x, p.y] or not self.gs.cur_map.dark:
                draw_on_map(
                    p.x,
                    p.y,
                    render.glyph,
                    self.camera,
                    con,
                    self.gs.cur_map,
                    render.color,
                )
        draw_msgs(self.gs, con)
        loc = self.gs.player.components[comps.Location]
        con.print(MAP_W, 0, f"Pos: {loc}")

    def on_update(self):
        player = self.gs.player

        while True:
            self.update_dmap()
            self.update_energy()
            self.get_npc_moves()
            self.check_moves()
            self.check_collisions()
            self.update_fov()

            if player.components[comps.Actor].energy >= 100:
                break

        pos = player.components[comps.Location].pos
        self.camera.center = pos

    def check_collisions(self):
        for e in self.gs.world.Q.all_of(relations=[(comps.CollidesWith, ...)]):
            target = e.relation_tag[comps.CollidesWith]
            e_actor_comp = e.components[comps.Actor]

            if target == e:
                e_actor_comp.energy -= 100
                e.relation_tag.pop(comps.CollidesWith)
                continue

            target_name = target.components[comps.Name]
            e_name = e.components[comps.Name]

            self.gs.add_msg(f"{e_name} kicks {target_name}!")
            e_actor_comp.energy -= 50
            e.relation_tags.pop(comps.CollidesWith)

    def check_moves(self):
        for e in self.gs.world.Q.all_of(
            components=[comps.Location, comps.TryMove],
            relations=[(comps.MapId, self.gs.cur_map.id)],
        ):
            dest = e.components[comps.TryMove].pos

            if self.gs.cur_map.walkable(dest.x, dest.y):
                blockers = list(self.gs.get_blockers_at(dest))
                if len(blockers) > 0:
                    e.relation_tag[comps.CollidesWith] = blockers[0]
                else:
                    e.components[comps.Location].pos = dest
                    e.components[comps.Actor].energy -= 50

            e.components.pop(comps.TryMove)

    def get_npc_moves(self):
        cur_map = self.gs.cur_map
        for e in filter(lambda e: self.gs.is_enemy(e), self.gs.get_turn_actors()):
            e_pos = e.components[comps.Location].pos
            path = hillclimb2d(cur_map.dist, (e_pos.x, e_pos.y), True, False)

            if len(path) > 1:
                try_x, try_y = path[1]
                e.components[comps.TryMove] = comps.TryMove(Point(try_x, try_y))

    def update_dmap(self):
        pos = self.gs.player.components[comps.Location].pos
        self.gs.cur_map.update_dmap(pos)

    def update_energy(self):
        for e in self.gs.get_current_actors():
            act_comp = e.components[comps.Actor]
            act_comp.energy += act_comp.speed

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
            player = self.gs.player
            pos = player.components[comps.Location]
            if update:
                new_point = pos.pos + dp
                player.components[comps.TryMove] = comps.TryMove(new_point)

        return Action(running, None, update)

    def update_fov(self):
        cur_map = self.gs.cur_map
        player_loc = self.gs.player.components[comps.Location]

        cur_map.visible = compute_fov(
            cur_map.tiles["transparent"],
            (player_loc.pos.x, player_loc.pos.y),
            radius=8,
            algorithm=FOV_DIAMOND,
        )

        cur_map.explored |= cur_map.visible
