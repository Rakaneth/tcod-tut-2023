from __future__ import annotations
from typing import TYPE_CHECKING
from tcod.ecs import World
from constants import DEBUG
import components as comps


GAMELOG = list()


def write_log(w: World, category: str, text: str):
    if DEBUG:
        game_turn = w[None].components.get(comps.GameTurn, 0)
        GAMELOG.append(f"[Turn {game_turn}] [{category}] {text}\n")


def dump_log(w: World):
    if DEBUG:
        log_file = w[None].components[comps.GameFileName].replace(".sav", ".log")
        with open(f"logs/{log_file}", "a") as f:
            f.writelines(GAMELOG)
