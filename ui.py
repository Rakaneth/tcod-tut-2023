from gamemap import GameMap, SHROUD
from geom import Point
from tcod.console import Console
from typing import Tuple

import numpy as np


class Camera:
    """Defines a viewport for the visible map."""

    def __init__(self, width: int, height: int):
        self.center = Point(0, 0)
        self.width = width
        self.height = height

    def __cam_calc(self, p: int, m: int, s: int) -> int:
        return sorted((p - s // 2, 0, max(0, m - s)))[1]

    def start_point(self, m: GameMap):
        left = self.__cam_calc(self.center.x, m.width, self.width)
        top = self.__cam_calc(self.center.y, m.height, self.height)
        return Point(left, top)

    def in_view(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height


def draw_on_map(
    x: int,
    y: int,
    glyph: str,
    cam: Camera,
    con: Console,
    m: GameMap,
    fg: Tuple[int, int, int] = None,
):
    st = cam.start_point(m)
    sx = x - st.x
    sy = y - st.y
    if cam.in_view(sx, sy):
        cell = con.rgb[sx, sy]
        cell["ch"] = ord(glyph)
        if fg is not None:
            cell["fg"] = fg


def draw_map(m: GameMap, cam: Camera, con: Console):
    st = cam.start_point(m)
    x_end = st.x + min(m.width, cam.width)
    y_end = st.y + min(m.height, cam.height)
    s_xend = x_end - st.x
    s_yend = y_end - st.y
    viewport = m.tiles[st.x : x_end, st.y : y_end]
    vw_visible = m.visible[st.x : x_end, st.y : y_end]
    vw_explored = m.explored[st.x : x_end, st.y : y_end]

    con.rgb[0:s_xend, 0:s_yend] = np.select(
        condlist=[vw_visible, vw_explored],
        choicelist=[viewport["light"], viewport["dark"]],
        default=SHROUD,
    )
