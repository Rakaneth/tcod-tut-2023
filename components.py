from dataclasses import dataclass
from typing import Tuple
from geom import Point


@dataclass
class Renderable:
    """Describes a renderable object."""

    glyph: str
    color: Tuple[int, int, int]
    z: int = 4


@dataclass
class Location:
    """Describes an entity's position on a map."""

    pos: Point

    def __str__(self) -> str:
        return f"{self.pos}"


@dataclass
class TryMove:
    """Represents an entity wanting to move to a location."""

    pos: Point


@dataclass
class Actor:
    """Describes an entity that can take actions."""

    energy: int
    speed: int


# Named components
Name = ("name", str)

# Relation tags
CollidesWith = "collides_with"
MapId = "map_id"
