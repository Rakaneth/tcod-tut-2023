import tcod

from tcod.ecs import World
from screen import Screen
from mainscreen import MainScreen
from action import Action
from typing import Optional
from geom import Point
from factory import make_char

SCR_W = 40
SCR_H = 30


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
        self._register_sc(MainScreen(self.world))
        make_char(self.world, "test", "Player Actor", "Farin")
        make_char(self.world, "npc", "actor")

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
            action: Optional[Action] = None

            while running:
                root.clear()
                self.cur_screen.on_draw(root)
                ctx.present(root)

                for evt in tcod.event.wait():
                    action = self.cur_screen.dispatch(evt)
                    if action is not None:
                        running = action.running
                        self.cur_scr_name = action.new_scr
