from dataclasses import dataclass
from typing import Tuple
from geom import Point


@dataclass
class Renderable:
    """Describes a renderable object."""

    glyph: str
    color: Tuple[int, int, int]


@dataclass
class Location:
    """Describes a position on a map."""

    pos: Point
