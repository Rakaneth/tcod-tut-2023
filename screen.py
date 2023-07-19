from typing import Optional, Tuple

import tcod
import tcod.event
from gamestate import GameState

from action import Action, QuitAction


class Screen(tcod.event.EventDispatch[Optional[Action]]):
    """
    Describes a game screen.
    Handles input, update, and drawing.
    """

    def __init__(self, name: str, gs: GameState):
        super().__init__()
        self.name = name
        self.gs = gs

    def __repr__(self) -> str:
        return f"Screen(self.name)"

    def __str__(self) -> str:
        return f"Screen(self.name)"

    def on_key(self, key: tcod.event.KeySym) -> Optional[Action]:
        return None

    def on_quit(self) -> Optional[Action]:
        return QuitAction()

    def on_draw(self, con: tcod.console.Console):
        con.print(0, 0, f"This is the {self.name} screen.")
    
    def on_update(self):
        pass

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        return self.on_key(event.sym)

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        return self.on_quit()
