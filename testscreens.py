import tcod
from typing import Optional

from screen import Screen
from action import Action, QuitAction


class TestScreen(Screen):
    """A test screen,"""

    def __init__(self):
        super().__init__("test")

    def on_key(self, key: tcod.event.KeySym) -> Optional[Action]:
        match key:
            case tcod.event.KeySym.ESCAPE:
                return QuitAction()
            case _ as k:
                print(f"Key pressed: {k}")

        return None


class WinScreen(Screen):
    """A test screen for screen navigation."""

    def __init__(self):
        super().__init__("win")

    def on_draw(self, con: tcod.console.Console):
        con.print(0, 0, "You win! :)")
        con.print(0, 1, "Pres [ESC] to return to main screen.")

    def on_key(self, key: tcod.event.KeySym) -> Optional[Action]:
        match key:
            case tcod.event.KeySym.ESCAPE:
                return Action(True, "main")

        return None


class LoseScreen(Screen):
    """A test screen for screen navigation."""

    def __init__(self):
        super().__init__("lose")

    def on_draw(self, con: tcod.console.Console):
        con.print(0, 0, "You lose :(")
        con.print(0, 1, "Press [ESC] to return to main screen.")

    def on_key(self, key: tcod.event.KeySym) -> Optional[Action]:
        match key:
            case tcod.event.KeySym.ESCAPE:
                return Action(True, "main")

        return None


class MainScreen(Screen):
    """A test screen for screen navigation."""

    def __init__(self):
        super().__init__("main")

    def on_draw(self, con: tcod.console.Console):
        con.print(0, 0, "Press [w] to win.")
        con.print(0, 1, "Press [l] to lose.")
        con.print(0, 2, "Press [ESC] to quit.")

    def on_key(self, key: tcod.event.KeySym) -> Optional[Action]:
        match key:
            case tcod.event.KeySym.ESCAPE:
                return QuitAction()
            case tcod.event.KeySym.w:
                return Action(True, "win")
            case tcod.event.KeySym.l:
                return Action(True, "lose")

        return None
