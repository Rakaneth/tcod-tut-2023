from screen import Screen
from tcod.console import Console
from gamestate import GameState
from tcod.event import KeySym
from geom import Point, Direction
from typing import Optional
from action import Action
from gamemap import arena
from ui import Camera, draw_map, draw_on_map

import components as comps


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, gs: GameState):
        super().__init__("main", gs)
        self.camera = Camera(30, 20)

    def on_draw(self, con: Console):
        draw_map(self.gs.cur_map, self.camera, con)
        for e in self.gs.world.Q.all_of(
            components=[comps.Renderable, comps.Location],
            relations=[("map_id", self.gs.cur_map.id)],
        ):
            p = e.components[comps.Location].pos
            render = e.components[comps.Renderable]
            draw_on_map(
                p.x, p.y, render.glyph, self.camera, con, self.gs.cur_map, render.color
            )

    def try_move(self, pt: Point):
        if self.gs.cur_map.walkable(pt.x, pt.y):
            pos = self.gs.player.components[comps.Location]
            pos.pos = pt
            self.camera.center = pt

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
            self.try_move(new_point)

        return Action(running, None)
