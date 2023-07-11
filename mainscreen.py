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
        for render, posi in self.world.Q[comps.Renderable, comps.Location]:
            p = posi.pos
            cell = con.rgb[p.x, p.y]
            cell["fg"] = render.color
            cell["ch"] = ord(render.glyph)

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
        pos = player.components[comps.Location]
        new_point = pos.pos + dp

        player.components[comps.Location].pos = new_point
