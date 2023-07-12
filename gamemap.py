import numpy as np
from geom import Point, Rect
from swatch import STONE_LIGHT, STONE_DARK
from typing import Tuple


class GameMap:
    """Describes a game map."""

    TILE_NULL = 0
    TILE_WALL = 1
    TILE_FLOOR = 2

    def __init__(
        self,
        id: str,
        width: int,
        height: int,
        dark: bool = False,
        wall_fg: Tuple[int, int, int] = STONE_LIGHT,
        floor_fg: Tuple[int, int, int] = STONE_DARK,
    ):
        self.__tiles = np.zeros((width, height), dtype=np.uint8, order="F")
        self.__explored = np.zeros((width, height), dtype=bool, order="F")
        self.dark = dark
        self.__id = id
        self.wall_fg = wall_fg
        self.floor_fg = floor_fg

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

    def get(self, x: int, y: int) -> int:
        if self.in_bounds(x, y):
            return self.__tiles[x, y]

        return self.TILE_NULL

    def set(self, x: int, y: int, t: int):
        if self.in_bounds(x, y):
            self.__tiles[x, y] = t

    def carve_rect(self, r: Rect):
        for pt_r in r.perimeter:
            self.set(pt_r.x, pt_r.y, self.TILE_WALL)

        for pt_i in r.interior:
            self.set(pt_i.x, pt_i.y, self.TILE_FLOOR)

    @property
    def chars(self) -> np.ndarray:
        def __to_char(t: int):
            match t:
                case GameMap.TILE_NULL:
                    return 0
                case GameMap.TILE_WALL:
                    return ord("#")
                case GameMap.TILE_FLOOR:
                    return ord(".")

        applyall = np.vectorize(__to_char)

        return applyall(self.__tiles)

    def write_to_file(self):
        with open(f"./{self.id}.map", "w") as f:
            v_char = np.vectorize(chr)
            f.write(str(v_char(self.chars)))


def arena(id: str, width: int, height: int, dark: bool = True) -> GameMap:
    m = GameMap(id, width, height, dark)
    m.carve_rect(Rect.from_xywh(0, 0, width, height))
    return m
