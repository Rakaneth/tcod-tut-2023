from __future__ import annotations

import ui

from typing import TYPE_CHECKING
from screen import Screen, ScreenNames
from tcod.console import Console

if TYPE_CHECKING:
    from engine import Engine


class TestUIScreen(Screen):
    """UI testing screen."""

    def __init__(self, engine: Engine):
        super().__init__(ScreenNames.TEST_UI, engine)
        self.dialog = ui.Dialog(
            self.engine.root,
            15,
            ui.SMALL_PARA,
            ["Opt 1", "Opt 2", "Opt 3"],
            title="Default Dialog",
        )
        self.dialog_moved = ui.Dialog(
            self.engine.root,
            20,
            ui.SMALL_PARA,
            ["Opt 1", "Opt 2", "Opt 3"],
            x=4,
            y=10,
            title="Moved Dialog",
        )

    def on_draw(self, con: Console):
        # self.dialog.draw()
        self.dialog_moved.draw()

    def on_quit(self):
        raise SystemExit()

    def on_up(self):
        self.dialog.move_up()
        self.dialog_moved.move_up()

    def on_down(self):
        self.dialog.move_down()
        self.dialog_moved.move_down()

    def on_cancel(self):
        self.engine.switch_screen(ScreenNames.TITLE)
