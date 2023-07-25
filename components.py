from dataclasses import dataclass
from typing import Tuple
from effects import GameEffect
from geom import Point
from tcod.ecs import Entity


@dataclass
class Renderable:
    """Describes a renderable object."""

    glyph: str
    color: Tuple[int, int, int]
    z: int = 4


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


@dataclass(frozen=True)
class GameMessage:
    """Describes a game message."""

    message: str
    color: Tuple[int, int, int]


@dataclass(frozen=True)
class OnHit:
    """Describes an on-hit attack."""

    eff: GameEffect
    chance: int


# Named components - global Entity
Messages = ("messages", list[GameMessage])
GameVersion = ("game_version", str)
GameSaved = ("game_saved", bool)
GameFileName = ("game_file_name", str)
GameTurn = ("game_turn", int)

# Named components
Name = ("name", str)
BumpAttacking = ("bump_attacking", Entity)
CollidesWith = ("collides_with", Entity)
EffectsList = ("effect_list", list[GameEffect])
CheckOnHits = ("check_on_hits", Entity)
Location = ("location", Point)

# Relation tags
MapId = "map_id"
HostileTo = "hostile_to"
