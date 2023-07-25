from __future__ import annotations
from typing import TYPE_CHECKING
from tcod.console import Console
from screen import Screen, ScreenNames

import ui
import components as comps

if TYPE_CHECKING:
    from engine import Engine


class GameOverScreen(Screen):
    def __init__(self, engine: Engine):
        super().__init__(ScreenNames.GAME_OVER, engine)
        self.dialog: ui.Dialog = None

    def setup(self):
        full_name = self.player.components[comps.FullName]
        death_text = f"Alas, the brave hero {full_name} has been slain."
        opts = ["Return to Title", "Exit Game"]
        self.dialog = ui.Dialog(
            self.engine.root, 20, death_text, opts, title="Game Over"
        )

    def on_draw(self, con: Console):
        self.dialog.draw()

    def on_up(self):
        self.dialog.move_up()

    def on_down(self):
        self.dialog.move_down()

    def on_confirm(self):
        result = self.dialog.selected
        match result:
            case "Return to Title":
                self.engine.switch_screen(ScreenNames.TITLE)
            case "Exit Game":
                raise SystemExit()
