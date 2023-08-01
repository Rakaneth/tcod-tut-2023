STONE_LIGHT = (192, 192, 192)
STONE_DARK = (64, 64, 64)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
HP_FILLED = (255, 0, 0)
HP_EMPTY = (128, 0, 0)
BLOOD = (128, 0, 0)
CAUTION = (255, 255, 0)
INFO = (64, 64, 255)
DEAD = (255, 0, 255)
TARGET = (255, 255, 0)


def dark(color_tuple: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = color_tuple
    return (r // 2, g // 2, b // 2)
