import tcod

from tcod.ecs import World
from screen import Screen
from mainscreen import MainScreen
from action import Action
from typing import Optional
from geom import Point

SCR_W = 80
SCR_H = 50


class Engine:
    """Holds the game state and data."""

    def __init__(self):
        self.screens: dict[str, Screen] = dict()
        self.cur_scr_name = "main"
        self.tileset = tcod.tileset.load_tilesheet(
            "./assets/gfx/Cooz_curses_square_16x16.png",
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

        test_ent_comps = {
            ("name", str): "Hero",
            ("pos", Point): Point(SCR_W // 2, SCR_H // 2),
            ("glyph", str): "@",
            ("color", tuple): (255, 0, 255),
        }
        e = self.world["player"]
        for k, v in test_ent_comps.items():
            e.components[k] = v
        
        for tag in ["Actor", "Player"]:
            e.tags.add(tag)

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
