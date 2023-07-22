from __future__ import annotations

from typing import TYPE_CHECKING
from action import Action
from constants import SAVING, VERSION
from screen import Screen
from tcod.ecs import World
from tcod.console import Console
from tcod.event import KeySym
from factory import (
    build_all_maps,
    make_char,
    place_entity,
    populate_all_maps,
)
from components import GameVersion, Messages
from ui import Menu

import pickle
import glob

if TYPE_CHECKING:
    from engine import Engine


class VersionError(Exception):
    pass


class TitleScreen(Screen):
    """Title screen."""

    def __init__(self, world: World, con: Console, e: Engine):
        super().__init__("title", world)
        opts = ["New Game"]
        files = glob.glob("*.sav")
        opts += files
        self.menu = Menu(opts, con, title="Select File")
        self.engine = e

    def on_draw(self, con: Console):
        self.menu.draw(con)

    def on_key(self, key: KeySym) -> Action | None:
        new_scr = None
        result = None
        update = False

        match key:
            case KeySym.w:
                self.menu.move_up()
            case KeySym.s:
                self.menu.move_down()
            case KeySym.RETURN:
                result = self.menu.selected

        if result == "New Game":
            self.new_game()
            new_scr = "main"
            update = True
        elif result is not None and SAVING:
            self.load_game(result)
            new_scr = "main"
            update = True
        elif result is not None:
            print(f"File {result} was picked, but saving is disabled.")
            self.new_game()
            new_scr = "main"
            update = True

        return Action(True, new_scr, update)

    def load_game(self, game_file: str):
        world = None
        try:
            with open(game_file, "rb") as f:
                world = pickle.load(f)
            load_ver = world[None].components[GameVersion]
            if load_ver != VERSION:
                raise VersionError(
                    f"Version mismatch: loaded {load_ver}, current {VERSION}"
                )
            for screen in self.engine.screens.values():
                screen.world = world
            self.engine.world = world
        except FileNotFoundError:
            print(f"File {game_file} not found, creating new game")
            self.new_game()
        except EOFError:
            print(f"File {game_file} has no data; likely a testing file.")
            print("Creating new game.")
            self.new_game()

    def new_game(self):
        world = self.world
        world[None].components[Messages] = list()
        world[None].components[GameVersion] = VERSION
        thrakir = make_char(world, "thrakir", player=True)
        build_all_maps(world)
        place_entity(world, thrakir, "cave")
        populate_all_maps(world)
