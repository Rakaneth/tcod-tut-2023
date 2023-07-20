from screen import Screen
from tcod.console import Console
from gamestate import GameState
from tcod.event import KeySym
from tcod.map import compute_fov
from geom import Point, Direction
from typing import Optional
from action import Action
from ui import Camera, draw_map, draw_msgs, draw_on_map, MAP_W, MAP_H
from components import MapId

import components as comps


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, gs: GameState):
        super().__init__("main", gs)
        self.camera = Camera(MAP_W, MAP_H)

    def on_draw(self, con: Console):
        draw_map(self.gs.cur_map, self.camera, con)
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
    
    def on_update(self):
        self.check_moves()
        self.check_collisions()
        self.update_fov()
        player = self.gs.player
        pos = player.components[comps.Location].pos
        self.camera.center = pos
    
    def check_collisions(self):
        bad = (255, 0, 0)
        good = (0, 255, 0)
        color = (255, 255, 255)

        for e in self.gs.world.Q.all_of(
            relations=[(comps.CollidesWith, ...)]
        ):
            target = e.relation_tag[comps.CollidesWith]
            name = target.components[comps.Name]
            
            if self.gs.is_enemy(target):
                color = bad
                self.gs.add_msg(f"{name} is a BAD GUY! Kick them harder!")
            elif self.gs.is_friendly(target):
                color = good
                self.gs.add_msg(f"{name} is a GOOD GUY! Why'd you kick them?")
            else:
                self.gs.add_msg(f"{name} is neutral. Don't anger them!")

            target.components[comps.Renderable].color = color
            e.relation_tag.pop(comps.CollidesWith)
    
    def check_moves(self):
        for e in self.gs.world.Q.all_of(
            components=[comps.Location, comps.TryMove],
            relations=[(MapId, self.gs.cur_map.id)]
        ):
            dest = e.components[comps.TryMove].pos

            if self.gs.cur_map.walkable(dest.x, dest.y):
                blockers = list(self.gs.get_entities_at(dest))
                if len(blockers) > 0:
                    e.relation_tag[comps.CollidesWith] = blockers[0]
                else:
                    e.components[comps.Location].pos = dest
                
            e.components.pop(comps.TryMove)
                
                
    def on_key(self, key: KeySym) -> Optional[Action]:
        dp = Point(0, 0)
        running = True

        match key:
            case KeySym.w:
                dp = Direction.UP
            case KeySym.a:
                dp = Direction.LEFT
            case KeySym.s:
                dp = Direction.DOWN
            case KeySym.d:
                dp = Direction.RIGHT
            case KeySym.ESCAPE:
                running = False

        if running:
            player = self.gs.player
            pos = player.components[comps.Location]
            new_point = pos.pos + dp
            player.components[comps.TryMove] = comps.TryMove(new_point)

        return Action(running, None)

    def update_fov(self):
        cur_map = self.gs.cur_map
        player_loc = self.gs.player.components[comps.Location]

        cur_map.visible = compute_fov(
            cur_map.tiles["transparent"],
            (player_loc.pos.x, player_loc.pos.y),
            radius=8,
        )

        cur_map.explored |= cur_map.visible
