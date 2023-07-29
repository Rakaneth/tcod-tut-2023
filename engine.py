import os
import pickle
import tcod
import factory as fac
import components as comps

from tcod.ecs import World
from gamelog import dump_log
from screens.gameoverscreen import GameOverScreen
from screen import Screen, ScreenNames
from screens import MainScreen, TitleScreen, TestUIScreen
from ui import SCR_W, SCR_H
from constants import SAVING, VERSION
from datetime import datetime


class Engine:
    """Holds the game state and data."""

    def __init__(self):
        tileset = tcod.tileset.load_tilesheet(
            "./assets/gfx/Sir_Henrys_32x32.png",
            16,
            16,
            tcod.tileset.CHARMAP_CP437,
        )
        self.screens: dict[str, Screen] = dict()
        self.cur_scr_name = ""
        self.context = tcod.context.new(
            columns=SCR_W, rows=SCR_H, tileset=tileset, vsync=True
        )
        self.world = World()
        self.root = tcod.console.Console(SCR_W, SCR_H, order="F")
        self.should_update = True
        self.running = True

    def __del__(self):
        self.context.close()

    @property
    def cur_screen(self) -> Screen:
        return self.screens[self.cur_scr_name]

    def _register_sc(self, sc: Screen):
        self.screens[sc.name] = sc

    def switch_screen(self, scr_id: str):
        self.cur_scr_name = scr_id
        self.should_update = True
        self.cur_screen.on_enter()

    def setup(self):
        if not os.path.exists("saves/"):
            os.mkdir("saves")
        if not os.path.exists("logs/"):
            os.mkdir("logs")

        for sc in [MainScreen, TitleScreen, TestUIScreen, GameOverScreen]:
            self._register_sc(sc(self))

        self.switch_screen(ScreenNames.TITLE)

    def input(self):
        for evt in tcod.event.wait():
            self.context.convert_event(evt)
            self.cur_screen.dispatch(evt)

    def update(self):
        if self.should_update:
            self.cur_screen.on_update()
            self.should_update = False

    def draw(self):
        self.root.clear()
        self.cur_screen.on_draw(self.root)
        self.context.present(self.root)

    def run(self):
        while self.running:
            self.input()
            self.update()
            self.draw()

        self.shutdown()

    def save_game(self):
        if SAVING:
            save_file = self.world[None].components.get(comps.GameFileName)
            if save_file:
                with open(f"saves/{save_file}.sav", "wb") as f:
                    pickle.dump(self.world, f)

    def load_game(self, world: World):
        if SAVING:
            self.world = world
            self.setup_screens()

    def new_game(self, hero_id: str):
        now = datetime.now()
        world = World()
        world[None].components[comps.Messages] = list()
        world[None].components[comps.GameVersion] = VERSION
        world[None].components[comps.GameSaved] = False
        world[None].components[
            comps.GameFileName
        ] = f"{hero_id}-{(now.strftime('%Y%m%d_%H%M%S'))}"
        world[None].components[comps.GameTicks] = 0
        world[None].components[comps.GameTurn] = 0
        player = fac.make_char(world, hero_id, player=True)
        fac.build_all_maps(world)
        fac.place_entity(world, player, "cave")
        fac.populate_all_maps(world)
        self.world = world
        self.setup_screens()

    def dump_game_file(self):
        game_file = self.world[None].components[comps.GameFileName]
        msgs = self.world[None].components[comps.Messages]

        with open(f"logs/{game_file}.txt", "w") as fl:
            msg_list = [f"{msg.message}\n" for msg in msgs]
            fl.writelines(msg_list)

    def shutdown(self):
        dump_log(self.world)
        self.dump_game_file()
        self.save_game()

    def setup_screens(self):
        for sc in self.screens.values():
            sc.setup()
