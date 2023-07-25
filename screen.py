from __future__ import annotations
from turtle import setup

import tcod
import tcod.event

from tcod.ecs import World, Entity
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from engine import Engine


SIGNALS = {
    tcod.event.KeySym.w: "up",
    tcod.event.KeySym.UP: "up",
    tcod.event.KeySym.KP_8: "up",
    tcod.event.KeySym.a: "left",
    tcod.event.KeySym.LEFT: "left",
    tcod.event.KeySym.KP_4: "left",
    tcod.event.KeySym.s: "down",
    tcod.event.KeySym.DOWN: "down",
    tcod.event.KeySym.KP_2: "down",
    tcod.event.KeySym.d: "right",
    tcod.event.KeySym.RIGHT: "right",
    tcod.event.KeySym.KP_6: "right",
    tcod.event.KeySym.RETURN: "confirm",
    tcod.event.KeySym.KP_ENTER: "confirm",
    tcod.event.KeySym.ESCAPE: "cancel",
    tcod.event.KeySym.SPACE: "wait",
}


class ScreenNames:
    MAIN = "main"
    TITLE = "title"
    TEST_UI = "test_ui"
    GAME_OVER = "game_over"


class Screen(tcod.event.EventDispatch):
    """
    Describes a game screen.
    Handles input, update, and drawing.
    """

    def __init__(self, name: str, engine: Engine):
        super().__init__()
        self.__name = name
        self.__engine = engine

    def __repr__(self) -> str:
        return f"Screen({self.name})"

    def __str__(self) -> str:
        return f"Screen({self.name})"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def engine(self) -> Engine:
        return self.__engine

    @property
    def world(self) -> World:
        return self.__engine.world

    @property
    def player(self) -> Entity:
        return self.__engine.world["player"]

    def setup(self):
        pass

    def on_quit(self):
        self.engine.running = False

    def on_draw(self, con: tcod.console.Console):
        con.print(0, 0, f"This is the {self.name} screen.")

    def on_update(self):
        pass

    def on_mouse_move(self, x: int, y: int):
        pass

    def on_up(self):
        pass

    def on_down(self):
        pass

    def on_left(self):
        pass

    def on_right(self):
        pass

    def on_confirm(self):
        pass

    def on_cancel(self):
        pass

    def on_wait(self):
        pass

    def ev_keydown(self, event: tcod.event.KeyDown):
        signal = SIGNALS.get(event.sym)
        match signal:
            case "up":
                return self.on_up()
            case "down":
                return self.on_down()
            case "left":
                return self.on_left()
            case "right":
                return self.on_right()
            case "confirm":
                return self.on_confirm()
            case "cancel":
                return self.on_cancel()
            case "wait":
                return self.on_wait()
            case _:
                return None

    def ev_quit(self, event: tcod.event.Quit):
        return self.on_quit()

    def ev_mousemotion(self, event: tcod.event.MouseMotion):
        return self.on_mouse_move(event.tile.x, event.tile.y)
