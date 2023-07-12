from gamemap import GameMap
from geom import Point
from tcod.console import Console
from numpy import arange
from typing import Tuple


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


def draw_map(m: GameMap, cam: Camera, con: Console):
    st = cam.start_point(m)
    x_end = st.x + min(m.width, cam.width)
    y_end = st.y + min(m.height, cam.height)
    s_xend = x_end - st.x
    s_yend = y_end - st.y
    viewport = m.chars[st.x : x_end, st.y : y_end]
    con.rgb[:s_xend, :s_yend]["ch"] = viewport
