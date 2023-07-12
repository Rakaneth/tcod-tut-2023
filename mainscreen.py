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
        self.temp_map = arena("arena", 45, 35)

    def on_draw(self, con: Console):
        draw_map(self.temp_map, self.camera, con)
        for e in self.gs.world.Q.all_of(
            components=[comps.Renderable, comps.Location],
            relations=[("mapid", "arena")],
        ):
            p = e.components[comps.Location].pos
            render = e.components[comps.Renderable]
            draw_on_map(
                p.x, p.y, render.glyph, self.camera, con, self.temp_map, render.color
            )

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
            player.components[comps.Location].pos = new_point
            self.camera.center = new_point

        return Action(running, None)
