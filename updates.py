from __future__ import annotations

from typing import TYPE_CHECKING
from tcod.ecs import World, Entity
import components as comps

from queries import find_effect
from swatch import WHITE

if TYPE_CHECKING:
    from effects import GameEffect


def kill(e: Entity):
    render = e.components[comps.Renderable]
    render.glyph = "%"
    render.z = 2
    e.tags.add("dead")
    e.tags.remove("blocker")
    if comps.TryMove in e.components:
        e.components.pop(comps.TryMove)
    if comps.CollidesWith in e.components:
        e.components.pop(comps.CollidesWith)


def add_msg(w: World, txt: str, fg: tuple[int, int, int] = WHITE):
    new_msg = comps.GameMessage(txt, fg)
    w[None].components[comps.Messages].append(new_msg)


def add_msg_about(e: Entity, txt: str):
    color = e.components[comps.Renderable].color
    name = e.components[comps.Name]
    r = txt.replace("<entity>", name)
    add_msg(e.world, r, color)


def apply_effect(e: Entity, eff: GameEffect):
    maybe_eff = find_effect(e, eff.name)
    if maybe_eff:
        maybe_eff.on_merge(eff)
        return

    e.components[comps.EffectsList].append(eff)
    eff.on_apply(e)


def tick_effects(e: Entity, num_ticks: int):
    for eff in e.components[comps.EffectsList]:
        eff.tick(e, num_ticks)
        if eff.expired:
            remove_effect(e, eff.name)


def remove_effect(e: Entity, eff_name: str):
    maybe_eff = find_effect(e, eff_name)
    if maybe_eff:
        maybe_eff.on_remove(e)
        e.components[comps.EffectsList].remove(maybe_eff)
