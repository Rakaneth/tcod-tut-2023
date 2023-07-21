import pickle
import tcod

from tcod.ecs import World
from components import Messages
from screen import Screen
from mainscreen import MainScreen
from action import Action
from typing import Optional
from factory import make_char, place_entity, add_map
from gamemap import drunk_walk
from ui import SCR_W, SCR_H


class Engine:
    """Holds the game state and data."""

    def __init__(self):
        self.screens: dict[str, Screen] = dict()
        self.cur_scr_name = "main"
        self.tileset = tcod.tileset.load_tilesheet(
            "./assets/gfx/Sir_Henrys_32x32.png",
            16,
            16,
            tcod.tileset.CHARMAP_CP437,
        )
        self.world = World()

    @property
    def cur_screen(self) -> Screen:
        return self.screens[self.cur_scr_name]

    def _register_sc(self, sc: Screen):
        self.screens[sc.name] = sc

    def setup(self):
        try:
            self.load_save()
        except FileNotFoundError:
            print("No save game found.")
            self.new_game()

        self._register_sc(MainScreen(self.world))

    def new_game(self):
        world = self.world
        drunk_m = drunk_walk("arena", 31, 15, 0.4)
        add_map(world, drunk_m)
        world[None].components[Messages] = list()
        farin = make_char(world, "test", name="Farin", player=True)
        bad_guy = make_char(world, "bad_guy")
        good_guy = make_char(world, "good_guy")
        neut_guy = make_char(world, "neut_guy")
        place_entity(world, farin, drunk_m)
        place_entity(world, bad_guy, drunk_m)
        place_entity(world, good_guy, drunk_m)
        place_entity(world, neut_guy, drunk_m)

    def run(self):
        with tcod.context.new(
            columns=SCR_W,
            rows=SCR_H,
            tileset=self.tileset,
            title="Roguelike Summer Tutorial 2023",
            vsync=True,
        ) as ctx:
            root = tcod.console.Console(SCR_W, SCR_H, order="F")
            running = True
            update = True
            action: Optional[Action] = None

            while running:
                root.clear()
                self.cur_screen.on_draw(root)
                ctx.present(root)

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

    def load_save(self):
        with open("game.sav", "rb") as f:
            self.world = pickle.load(f)

    def shutdown(self):
        with open("game.sav", "wb") as f:
            pickle.dump(self.world, f)
