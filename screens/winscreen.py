from __future__ import annotations
from typing import TYPE_CHECKING

import tcod
from screen import Screen, ScreenNames
from tcod.console import Console

import ui

if TYPE_CHECKING:
    from engine import Engine


class WinScreen(Screen):
    def __init__(self, engine: Engine):
        super().__init__(ScreenNames.WIN, engine)
        txt = "Congratulations! You have escaped with the Proof of Bravery!"
        self.win_text = ui.TextBox(self.engine.root, 25, 5, txt, title="Winner!")

    def on_draw(self, con: Console):
        self.win_text.draw()

    def on_enter(self):
        self.world[None].tags.add("winner")
        self.engine.save_game()

    def on_cancel(self):
        raise SystemExit()

    def on_confirm(self):
        raise SystemExit()
