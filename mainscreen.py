from screen import Screen
from tcod.console import Console
from tcod.ecs import World, Entity
from tcod.event import KeySym
from geom import Point, Direction
from typing import Optional
from action import Action

import components as comps


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, world: World):
        super().__init__("main", world)

    def on_draw(self, con: Console):
        for render, posi in self.world.Q[comps.Renderable, comps.Location]:
            p = posi.pos
            cell = con.rgb[p.x, p.y]
            cell["fg"] = render.color
            cell["ch"] = ord(render.glyph)

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
            player = self.world["Farin"]
            pos = player.components[comps.Location]
            new_point = pos.pos + dp
            player.components[comps.Location].pos = new_point

        return Action(running, None)
