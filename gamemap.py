from geom import Point, Rect
from typing import Tuple
from random import choice
from tcod.path import maxarray, dijkstra2d
from tcod.map import compute_fov
from tcod.constants import FOV_DIAMOND

import swatch as sw
import numpy as np

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


SHROUD = np.array((ord(" "), sw.WHITE, sw.BLACK), dtype=render_dt)


class GameMap:
    """Describes a game map."""

    def __init__(
        self,
        id: str,
        name: str,
        width: int,
        height: int,
        dark: bool = False,
        wall_fg: Tuple[int, int, int] = sw.STONE_LIGHT,
        floor_fg: Tuple[int, int, int] = sw.STONE_DARK,
    ):
        self.explored = np.zeros((width, height), dtype=bool, order="F")
        self.visible = np.zeros((width, height), dtype=bool, order="F")
        self.dist = maxarray((width, height), order="F")
        self.cost = np.zeros((width, height), dtype=np.int32, order="F")
        self.dark = dark
        self.__id = id
        self.__name = name
        self.wall_tile = new_tile(
            transparent=False,
            walkable=False,
            light=(ord("#"), wall_fg, sw.BLACK),
            dark=(ord("#"), sw.dark(wall_fg), sw.BLACK),
        )
        self.floor_tile = new_tile(
            transparent=True,
            walkable=True,
            light=(ord("."), floor_fg, sw.BLACK),
            dark=(ord("."), sw.dark(floor_fg), sw.BLACK),
        )
        self.stairs_down_tile = new_tile(
            transparent=True,
            walkable=True,
            light=(ord(">"), sw.TARGET, sw.BLACK),
            dark=(ord(">"), sw.dark(sw.TARGET), sw.BLACK),
        )
        self.stairs_up_tile = new_tile(
            transparent=True,
            walkable=True,
            light=(ord("<"), sw.TARGET, sw.BLACK),
            dark=(ord("<"), sw.dark(sw.TARGET), sw.BLACK),
        )
        self.__tiles = np.full((width, height), fill_value=self.wall_tile, order="F")

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def width(self) -> int:
        return self.__tiles.shape[0]

    @property
    def height(self) -> int:
        return self.__tiles.shape[1]

    @property
    def tiles(self) -> np.ndarray:
        return self.__tiles

    def update_cost(self):
        self.cost = np.select(
            condlist=[self.tiles["walkable"]], choicelist=[1], default=0
        )

    def update_dmap(self, *goals: Point):
        self.dist = maxarray((self.width, self.height), order="F")
        for goal in goals:
            self.dist[goal.x, goal.y] = 0
        dijkstra2d(self.dist, self.cost, True, out=self.dist)

    def update_fov(self, x: int, y: int, r: int):
        self.visible = compute_fov(self.tiles["transparent"], (x, y), r, FOV_DIAMOND)
        self.explored |= self.visible

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def walkable(self, x: int, y: int) -> bool:
        return self.__tiles[x, y]["walkable"]

    def transparent(self, x: int, y: int) -> bool:
        return self.__tiles[x, y]["transparent"]

    def carve(self, x: int, y: int):
        self.tiles[x, y] = self.floor_tile

    def carve_rect(self, r: Rect):
        self.tiles[r.x1 : r.x2 + 1, r.y1 : r.y2 + 1] = self.wall_tile
        self.tiles[r.x1 + 1 : r.x2, r.y1 + 1 : r.y2] = self.floor_tile

    def neighbors(self, x: int, y: int):
        return [
            Point(i, j)
            for (i, j) in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            if self.in_bounds(i, j)
        ]

    def add_down_stair(self, x: int, y: int):
        self.tiles[x, y] = self.stairs_down_tile

    def add_up_stair(self, x: int, y: int):
        self.tiles[x, y] = self.stairs_up_tile

    def on_edge(self, x: int, y: int) -> bool:
        return x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1

    def get_random_floor(self) -> Point:
        cands = [
            Point(x, y)
            for x in range(0, self.width)
            for y in range(0, self.height)
            if self.in_bounds(x, y)
            if self.walkable(x, y)
        ]

        return choice(cands)


def arena(id: str, name: str, width: int, height: int, dark: bool = True) -> GameMap:
    m = GameMap(id, name, width, height, dark)
    m.carve_rect(Rect.from_xywh(0, 0, width, height))
    m.update_cost()
    return m


def drunk_walk(
    id: str,
    name: str,
    width: int,
    height: int,
    coverage: float = 0.5,
    dark: bool = True,
) -> GameMap:
    m = GameMap(id, name, width, height, dark)
    x = m.width // 2
    y = m.height // 2
    pt = Point(x, y)
    stack = [pt]
    floors = 0
    desired = int(width * height * max(0.1, min(coverage, 1)))
    m.carve(x, y)

    def f(pt):
        return not (m.walkable(pt.x, pt.y) or m.on_edge(pt.x, pt.y))

    while floors < desired:
        cands = list(filter(f, m.neighbors(pt.x, pt.y)))
        if len(cands) > 0:
            pt = choice(cands)
            m.carve(pt.x, pt.y)
            stack.append(pt)
            floors += 1
        else:
            pt = stack.pop()

    m.update_cost()
    return m
