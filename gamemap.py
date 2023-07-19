import numpy as np
from geom import Point, Rect
from swatch import STONE_LIGHT, STONE_DARK, BLACK
from typing import Tuple

render_dt = np.dtype([("ch", np.int32), ("fg", "3B"), ("bg", "3B")])

tile_dt = np.dtype(
    [
        ("walkable", bool),
        ("transparent", bool),
        ("dark", render_dt),
        ("light", render_dt),
    ]
)


def new_tile(
    *,
    walkable: int,
    transparent: int,
    dark=Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light=Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)


SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=render_dt)


class GameMap:
    """Describes a game map."""

    def __init__(
        self,
        id: str,
        width: int,
        height: int,
        dark: bool = False,
        wall_fg: Tuple[int, int, int] = STONE_LIGHT,
        floor_fg: Tuple[int, int, int] = STONE_DARK,
    ):
        self.explored = np.zeros((width, height), dtype=bool, order="F")
        self.visible = np.zeros((width, height), dtype=bool, order="F")
        self.dark = dark
        self.__id = id
        wr, wb, wg = wall_fg
        fr, fg, fb = floor_fg
        wall_fg_dark = (wr // 2, wg // 2, wb // 2)
        floor_fg_dark = (fr // 2, fg // 2, fb // 2)
        self.wall_tile = new_tile(
            transparent=False,
            walkable=False,
            light=(ord("#"), wall_fg, BLACK),
            dark=(ord("#"), wall_fg_dark, BLACK),
        )
        self.floor_tile = new_tile(
            transparent=True,
            walkable=True,
            light=(ord("."), floor_fg, BLACK),
            dark=(ord("."), floor_fg_dark, BLACK),
        )
        self.__tiles = np.full((width, height), fill_value=self.floor_tile, order="F")

    @property
    def id(self) -> str:
        return self.__id

    @property
    def width(self) -> int:
        return self.__tiles.shape[0]

    @property
    def height(self) -> int:
        return self.__tiles.shape[1]

    @property
    def tiles(self) -> np.ndarray:
        return self.__tiles

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def walkable(self, x: int, y: int) -> bool:
        return self.__tiles[x, y]["walkable"]

    def transparent(self, x: int, y: int) -> bool:
        return self.__tiles[x, y]["transparent"]

    def carve_rect(self, r: Rect):
        self.tiles[r.x1 : r.x2 + 1, r.y1 : r.y2 + 1] = self.wall_tile
        self.tiles[r.x1 + 1 : r.x2, r.y1 + 1 : r.y2] = self.floor_tile


def arena(id: str, width: int, height: int, dark: bool = True) -> GameMap:
    m = GameMap(id, width, height, dark)
    m.carve_rect(Rect.from_xywh(0, 0, width, height))
    return m
