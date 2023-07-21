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


@dataclass
class Combatant:
    """Describes an entity that can fight."""

    cur_hp: int
    max_hp: int
    atp: int
    dfp: int
    dmg: Tuple[int, int]

    @property
    def dmg_str(self) -> str:
        a, b = self.dmg
        low = min(a, b)
        high = max(a, b)
        return f"{low}-{high}"

    @property
    def hp_str(self) -> str:
        return f"{self.cur_hp}/{self.max_hp}"


# Named components
Name = ("name", str)
Messages = ("messages", list[str])

# Relation tags
CollidesWith = "collides_with"
MapId = "map_id"
