from gamemap import GameMap, SHROUD
from geom import Point
from tcod.console import Console
from typing import Tuple
from tcod.ecs import World
from queries import messages

import numpy as np

MAP_W = 25
MAP_H = 20
SCR_W = 40
SCR_H = 30
MSG_W = MAP_W
MSG_H = 10


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
        condlist=[(not m.dark) or vw_visible, vw_explored],
        choicelist=[viewport["light"], viewport["dark"]],
        default=SHROUD,
    )


def draw_msgs(w: World, con: Console):
    con.draw_frame(0, MAP_H, MSG_W, MSG_H, title="Messages")
    counter = 0
    for msg in messages(w)[::-1]:
        counter += con.print_box(1, MAP_H + counter + 1, MSG_W - 2, MSG_H - 2, msg)
        if counter >= MSG_H - 2:
            break


def draw_dmap(m: GameMap, cam: Camera, con: Console):
    st = cam.start_point(m)
    x_end = st.x + min(m.width, cam.width)
    y_end = st.y + min(m.height, cam.height)
    for y in np.arange(st.y, y_end):
        for x in np.arange(st.x, x_end):
            d = m.dist[x, y]
            if d < 10:
                draw_on_map(x, y, str(d), cam, con, m)


def draw_bar(
    x: int,
    y: int,
    bar_cur: int,
    bar_max: int,
    width: int,
    fill_color: Tuple[int, int, int],
    empty_color: Tuple[int, int, int],
    con: Console,
    draw_values: bool = False,
):
    ratio = bar_cur / bar_max
    ch = 0x2588
    fill_w = int(min(ratio, 1.0) * width)
    con.draw_rect(x, y, width, 1, ch, fg=empty_color)
    con.draw_rect(x, y, fill_w, 1, ch, fg=fill_color)
    if draw_values:
        s = f"{bar_cur}/{bar_max}"
        sx = (width - len(s)) // 2
        if sx >= 0:
            con.print(sx + x, y, s)


class Menu:
    """
    Describes an in-game menu.
    TODO: Week 4
    """

    pass
