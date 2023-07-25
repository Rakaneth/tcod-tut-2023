from __future__ import annotations
import re

from typing import TYPE_CHECKING
from constants import VERSION
from screen import Screen, ScreenNames
from tcod.ecs import World
from tcod.console import Console
from components import (
    GameVersion,
    Name,
)
from ui import Menu

import pickle
import glob

if TYPE_CHECKING:
    from engine import Engine


def _load_world(fn: str) -> World:
    world: World = None
    with open(fn, "rb") as f:
        world = pickle.load(f)

    return world


class TitleScreen(Screen):
    """Title screen."""

    def __init__(self, engine: Engine):
        super().__init__(ScreenNames.TITLE, engine)
        file_list = sorted(glob.glob("saves/*.sav"))
        world_list = [_load_world(file) for file in file_list]
        self.load_choices = dict()
        last_name = ""
        counter = 1

        for w in world_list:
            fn = w["player"].components[Name]
            if w[None].components[GameVersion] == VERSION:
                if fn == last_name:
                    counter += 1
                    fn = f"{fn}-{counter}"
                else:
                    last_name = fn
                    counter = 1

                self.load_choices[fn] = w

        self.new_choices = {
            "Falwyn": "falwyn",
            "Farin": "farin",
            "Rikkas": "rikkas",
            "Thrakir": "thrakir",
        }
        new_game_list = [f"New Game - {hero}" for hero in self.new_choices.keys()]
        save_games = list(self.load_choices.keys())

        self.menu = Menu(
            new_game_list + save_games, self.engine.root, title="Select File"
        )

    def on_quit(self):
        raise SystemExit()

    def on_draw(self, con: Console):
        self.menu.draw()

    def on_up(self):
        self.menu.move_up()

    def on_down(self):
        self.menu.move_down()

    def on_confirm(self):
        result = self.menu.selected
        mo = re.search(r"New Game - (?P<hero>(Falwyn|Farin|Rikkas|Thrakir))", result)

        if mo:
            self.engine.new_game(self.new_choices[mo.group("hero")])
        else:
            self.engine.load_game(self.load_choices[result])

        self.engine.switch_screen(ScreenNames.MAIN)
