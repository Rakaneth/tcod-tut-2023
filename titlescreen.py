from __future__ import annotations
import re

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
from components import Actor, GameFileName, GameSaved, GameVersion, Messages
from ui import Menu
from datetime import datetime

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
        opts = [
            "New Game - Thrakir",
            "New Game - Farin",
            "New Game - Rikkas",
            "New Game - Falwyn",
        ]
        files = glob.glob("saves/*.sav")
        opts += sorted(
            [
                f.replace(".sav", "")
                .replace("/", "")
                .replace("\\", "")
                .replace("saves", "")
                for f in files
            ]
        )

        self.menu = Menu(opts, con, title="Select File")
        self.engine = e

    def on_quit(self) -> Action | None:
        raise SystemExit()

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

        if result:
            mo = re.fullmatch(
                r"New Game - (?P<hero>(Thrakir|Falwyn|Rikkas|Farin))", result
            )
            if mo:
                hero = mo.group("hero")
                self.new_game(hero)
                new_scr = "main"
                update = True
            elif SAVING:
                self.load_game(f"saves/{result}.sav")
                new_scr = "main"
                update = True
            elif result is not None:
                print(f"File {result}.sav was picked, but saving is disabled.")
                print("Starting a new game with Farin.")
                self.new_game("Farin")
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
            print(f"File {game_file} not found, creating new game with Falwyn.")
            self.new_game("Falwyn")
        except EOFError:
            print(f"File {game_file} has no data; likely a testing file.")
            print("Creating new game with Thrakir.")
            self.new_game("Thrakir")

    def new_game(self, hero: str):
        now = datetime.now()
        world = self.world
        world[None].components[Messages] = list()
        world[None].components[GameVersion] = VERSION
        world[None].components[GameSaved] = False
        world[None].components[
            GameFileName
        ] = f"{hero}-{(now.strftime('%Y%m%d-%H%M%S'))}.sav"
        world[None].components[Actor] = Actor(0, 20)
        thrakir = make_char(world, hero.lower(), player=True)
        build_all_maps(world)
        place_entity(world, thrakir, "cave")
        populate_all_maps(world)
