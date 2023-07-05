from screen import Screen
from tcod.console import Console
from tcod.ecs import World
from tcod.event import KeySym
from geom import Point
from typing import Optional
from action import Action


class MainScreen(Screen):
    """Main playing area."""

    def __init__(self, world: World):
        super().__init__("main", world)

    def on_draw(self, con: Console):
        player = self.world["player"]
        glyph = player.components[("glyph", str)]
        color = player.components[("color", tuple)]
        p = player.components[("pos", Point)]

        con.print(p.x, p.y, glyph, color)

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

        player = self.world["player"]
        pos = player.components[("pos", Point)]

        player.components[("pos", Point)] = pos + dp
