from dataclasses import dataclass
from typing import Tuple
from geom import Point
from tcod.ecs import Entity


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
        low, high = self.dmg
        return f"{low}-{high}"

    @property
    def hp_str(self) -> str:
        return f"{self.cur_hp}/{self.max_hp}"

    @property
    def dead(self) -> bool:
        return self.cur_hp <= 0

    def heal(self):
        self.cur_hp = self.max_hp

    def restore(self, amt: int):
        self.cur_hp = min(self.max_hp, self.cur_hp + amt)

    def damage(self, amt: int):
        self.cur_hp -= amt


# Named components
Name = ("name", str)
Messages = ("messages", list[str])
BumpAttacking = ("bump_attacking", Entity)
CollidesWith = ("collides_with", Entity)
GameVersion = ("game_version", str)

# Relation tags
MapId = "map_id"
HostileTo = "hostile_to"
