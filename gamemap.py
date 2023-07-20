import numpy as np
from geom import Point, Rect
from swatch import STONE_LIGHT, STONE_DARK, BLACK
from typing import Tuple
from random import choice
from tcod.path import maxarray, dijkstra2d

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
        self.dist = maxarray((width, height), order="F")
        self.cost = np.zeros((width, height), dtype=np.int32, order="F")
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
        self.__tiles = np.full((width, height), fill_value=self.wall_tile, order="F")

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

    def update_cost(self):
        self.cost = np.select(
            condlist=[self.tiles["walkable"]], choicelist=[1], default=0
        )

    def update_dmap(self, *goals: Point):
        self.dist = maxarray((self.width, self.height), order="F")
        for goal in goals:
            self.dist[goal.x, goal.y] = 0
        dijkstra2d(self.dist, self.cost, True, out=self.dist)

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


def arena(id: str, width: int, height: int, dark: bool = True) -> GameMap:
    m = GameMap(id, width, height, dark)
    m.carve_rect(Rect.from_xywh(0, 0, width, height))
    m.update_cost()
    return m


def drunk_walk(
    id: str, width: int, height: int, coverage: float = 0.5, dark: bool = True
) -> GameMap:
    m = GameMap(id, width, height, dark)
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
