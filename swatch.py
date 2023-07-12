from typing import Tuple

STONE_LIGHT = (192, 192, 192)
STONE_DARK = (64, 64, 64)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def tuple_from_int(color_code: int) -> Tuple[int, int, int]:
    r = (color_code & 0xFF0000) >> 16
    g = (color_code & 0x00FF00) >> 8
    b = color_code & 0x0000FF
    return (r, g, b)


def tuple_to_int(color_tuple: Tuple[int, int, int]) -> int:
    r, g, b = color_tuple
    return (r << 16) + (g << 8) + b
