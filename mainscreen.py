from screen import Screen
from tcod.console import Console
from tcod.ecs import World, Entity
from tcod.event import KeySym
from geom import Point
from typing import Optional
from action import Action

import components as comps


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, world: World):
        super().__init__("main", world)

    def on_draw(self, con: Console):
        query = [
            ("render", comps.Renderable),
            ("pos", comps.Position),
        ]
        for render, posi in self.world.Q[
            ("render", comps.Renderable), ("pos", comps.Position)
        ]:
            p = posi.pos
            con.print(p.x, p.y, render.glyph, render.color)

    def on_key(self, key: KeySym) -> Optional[Action]:
        dp = Point(0, 0)

        match key:
            case KeySym.w:
                dp.y = -1
            case KeySym.a:
                dp.x = -1
            case KeySym.s:
                dp.y = 1
            case KeySym.d:
                dp.x = 1

        player = self.world["Farin"]
        pos = player.components[("pos", comps.Position)]
        new_point = pos.pos + dp

        player.components[("pos", comps.Position)].pos = new_point
