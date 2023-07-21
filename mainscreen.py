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
from ui import Camera, draw_map, draw_msgs, draw_on_map, MAP_W, MAP_H
from tcod.ecs import World, Entity

import components as comps
import queries as q


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
        loc = q.player(w).components[comps.Location]
        con.print(MAP_W, 0, f"Pos: {loc}")

    def on_update(self):
        player = self.player

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
        for e in self.world.Q.all_of(relations=[(comps.CollidesWith, ...)]):
            target = e.relation_tag[comps.CollidesWith]
            e_actor_comp = e.components[comps.Actor]

            if target == e:
                e_actor_comp.energy -= 100
                e.relation_tag.pop(comps.CollidesWith)
                continue

            target_name = target.components[comps.Name]
            e_name = e.components[comps.Name]

            q.add_msg(self.world, f"{e_name} kicks {target_name}!")
            e_actor_comp.energy -= 50
            e.relation_tag.pop(comps.CollidesWith)

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
                    e.relation_tag[comps.CollidesWith] = blockers[0]
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
