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
    """Describes an entity's position on a map."""

    pos: Point

@dataclass
class TryMove:
    """Represents an entity wanting to move to a location."""
    pos: Point

# Named components
Name = ("name", str)

# Relation tags
CollidesWith = "collides_with"
MapId = "map_id"
