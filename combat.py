from dataclasses import dataclass
from random import randint
from tcod.ecs import Entity
from components import Combatant


@dataclass(frozen=True)
class AttackResult:
    hit: bool
    margin: int


def d(sides, num=1) -> int:
    acc = 0
    for _ in range(num):
        acc += randint(1, sides)

    return acc


def pct() -> int:
    return d(100)


def pct_chance(chance: int) -> bool:
    return d(100) <= chance


def bump_attack(attacker: Entity, defender: Entity) -> AttackResult:
    atk_stat = attacker.components[Combatant].atp
    def_stat = defender.components[Combatant].dfp

    roll = pct()
    target = (atk_stat * (100 - def_stat)) // 100
    raw_margin = target - roll
    hit = raw_margin > 0
    return AttackResult(hit, abs(raw_margin))


def gauss_roll(low: int, high: int) -> int:
    acc = 0
    for _ in range(3):
        acc += randint(low, high)

    return acc // 3


def roll_dmg(attacker: Entity) -> int:
    low, high = attacker.components[Combatant].dmg
    return gauss_roll(low, high)
