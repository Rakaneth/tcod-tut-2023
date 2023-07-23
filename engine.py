import os
import pickle
import tcod

from tcod.ecs import World
from components import GameFileName, GameSaved, Messages
from gamelog import dump_log
from screen import Screen
from mainscreen import MainScreen
from action import Action
from typing import Optional
from titlescreen import TitleScreen
from ui import SCR_W, SCR_H
from constants import SAVING


class Engine:
    """Holds the game state and data."""

    def __init__(self):
        self.screens: dict[str, Screen] = dict()
        self.cur_scr_name = "title"
        self.tileset = tcod.tileset.load_tilesheet(
            "./assets/gfx/Sir_Henrys_32x32.png",
            16,
            16,
            tcod.tileset.CHARMAP_CP437,
        )
        self.world = World()
        self.root = tcod.console.Console(SCR_W, SCR_H, order="F")

    @property
    def cur_screen(self) -> Screen:
        return self.screens[self.cur_scr_name]

    def _register_sc(self, sc: Screen):
        self.screens[sc.name] = sc

    def setup(self):
        if not os.path.exists("saves/"):
            os.mkdir("saves")
        if not os.path.exists("logs/"):
            os.mkdir("logs")
        self._register_sc(MainScreen(self.world))
        self._register_sc(TitleScreen(self.world, self.root, self))

    def run(self):
        with tcod.context.new(
            columns=SCR_W,
            rows=SCR_H,
            tileset=self.tileset,
            title="Roguelike Summer Tutorial 2023",
            vsync=True,
        ) as ctx:
            running = True
            update = True
            action: Optional[Action] = None

            while running:
                self.root.clear()
                self.cur_screen.on_draw(self.root)
                ctx.present(self.root)

                for evt in tcod.event.wait():
                    ctx.convert_event(evt)
                    action = self.cur_screen.dispatch(evt)
                    if action is not None:
                        running = action.running
                        update = action.update
                        if action.new_scr is not None:
                            self.cur_scr_name = action.new_scr

                if update:
                    self.cur_screen.on_update()
                    update = False

            self.shutdown()

    def shutdown(self):
        dump_log(self.world)
        game_file = self.world[None].components[GameFileName]
        msgs = self.world[None].components[Messages]

        if SAVING:
            self.world[None].components[GameSaved] = True

            with open(f"saves/{game_file}", "wb") as f:
                pickle.dump(self.world, f)

        with open(f"logs/{game_file}".replace(".sav", ".msgs"), "w") as fl:
            msg_list = [f"{msg.message}\n" for msg in msgs]
            fl.writelines(msg_list)
