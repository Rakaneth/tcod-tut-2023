import tcod

from tcod.ecs import World
from screen import Screen
from mainscreen import MainScreen
from action import Action
from typing import Optional
from factory import make_char, place_entity
from gamemap import drunk_walk
from gamestate import GameState
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
        world = World()
        self.gs = GameState(world)

    @property
    def cur_screen(self) -> Screen:
        return self.screens[self.cur_scr_name]

    def _register_sc(self, sc: Screen):
        self.screens[sc.name] = sc

    def setup(self):
        self._register_sc(MainScreen(self.gs))
        world = self.gs.world
        drunk_m = drunk_walk("arena", 31, 15, 0.4)
        self.gs.add_map(drunk_m)
        farin = make_char(world, "test", name="Farin", player=True)
        bad_guy = make_char(world, "bad_guy")
        good_guy = make_char(world, "good_guy")
        neut_guy = make_char(world, "neut_guy")
        place_entity(self.gs, farin, drunk_m)
        place_entity(self.gs, bad_guy, drunk_m)
        place_entity(self.gs, good_guy, drunk_m)
        place_entity(self.gs, neut_guy, drunk_m)

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
