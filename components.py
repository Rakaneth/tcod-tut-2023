from dataclasses import dataclass
from typing import Tuple
from geom import Point
from tcod.ecs import Entity

import effects


@dataclass
class Renderable:
    """Describes a renderable object."""

    glyph: str
    color: Tuple[int, int, int]
    z: int = 4


@dataclass
class Actor:
    """Describes an entity that can take actions."""

    energy: int
    speed: int


@dataclass
class Combatant:
    """Describes an entity that can fight."""

    cur_hp: int
    base_max_hp: int
    at: int
    df: int
    dm: Tuple[int, int]
    st: int
    ag: int
    wl: int

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

    @property
    def atp(self) -> int:
        return (self.ag * 2) + self.at

    @property
    def dfp(self) -> int:
        return (self.ag * 2) + self.df

    @property
    def str_mod(self) -> int:
        return self.st // 4

    @property
    def max_hp(self) -> int:
        return self.str_mod * 2 + self.base_max_hp

    @property
    def dmg(self) -> Tuple[int, int]:
        bl, bh = self.dm
        return (bl + self.str_mod, bh + self.str_mod)

    @property
    def base_reduce(self) -> int:
        return self.st // 10

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

    eff: effects.GameEffect
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
EffectsList = ("effect_list", list[effects.GameEffect])
CheckOnHits = ("check_on_hits", Entity)
Location = ("location", Point)
TryMove = ("try_move", Point)
FullName = ("full_name", str)
Description = ("desc", str)

# Relation tags
MapId = "map_id"
HostileTo = "hostile_to"
