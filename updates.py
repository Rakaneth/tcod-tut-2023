from __future__ import annotations

from tcod.ecs import World, Entity
import components as comps
import queries as q
import effects as eff

from swatch import WHITE
from gamelog import write_log


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
    write_log(e.world, "kill", f"{q.name(e)} dies")


def add_msg(w: World, txt: str, fg: tuple[int, int, int] = WHITE):
    new_msg = comps.GameMessage(txt, fg)
    w[None].components[comps.Messages].append(new_msg)


def add_msg_about(e: Entity, txt: str):
    color = e.components[comps.Renderable].color
    name = e.components[comps.Name]
    r = txt.replace("<entity>", name)
    add_msg(e.world, r, color)


def apply_effect(e: Entity, eff: eff.GameEffect):
    maybe_eff = q.find_effect(e, eff.name)
    if maybe_eff:
        maybe_eff.on_merge(eff)
        write_log(e.world, "effect", f"Merging existing {eff.name} on {q.name(e)}")
        return

    e.components[comps.EffectsList].append(eff)
    eff.on_apply(e)
    write_log(e.world, "effect", f"Applying new {eff.name} effect to {q.name(e)}")


def tick_effects(e: Entity, num_ticks: int):
    for ef in e.components[comps.EffectsList]:
        ef.tick(e, num_ticks)
        if ef.expired:
            remove_effect(e, ef.name)
        write_log(
            e.world, "upkeep", f"Ticking effect {ef.name} on {q.name(e)} ({num_ticks})"
        )


def remove_effect(e: Entity, eff_name: str):
    maybe_eff = q.find_effect(e, eff_name)
    if maybe_eff:
        maybe_eff.on_remove(e)
        e.components[comps.EffectsList].remove(maybe_eff)
        write_log(e.world, "effect", f"Removing effect {maybe_eff} from {q.name(e)}")


def rename(e: Entity, new_name: str):
    e.components[comps.Name] = new_name


def add_to_inventory(item: Entity, holder: Entity):
    item.relation_tag[comps.HeldBy] = holder
    item.components.pop(comps.Location)


def pick_up_item(item: Entity, holder: Entity) -> bool:
    capacity = holder.components[comps.InventoryMax]
    num_items = len(q.inventory(holder))
    holder_name = q.name(holder)
    item_name = q.name(item)
    if num_items < capacity:
        add_to_inventory(item, holder)
        if q.is_visible(holder):
            add_msg_about(holder, f"<entity> picks up {item_name}")
        write_log(item.world, "inventory", f"{holder_name} picks up {item_name}")
        return True
    else:
        if q.is_player(holder):
            add_msg_about(holder, f"<entity>'s bags are too full for {item_name}.")
        write_log(
            item.world,
            "inventory",
            f"{holder_name} can't pick up {item_name}, inventory full",
        )

    return False


def drop_item(item: Entity, holder: Entity):
    pos = holder.components[comps.Location]
    item.relation_tag.pop(comps.HeldBy)
    item.components[comps.Location] = pos
    write_log(item.world, "inventory", f"{q.name(holder)} drops {q.name(item)}")


def apply_item(item: Entity, target: Entity):
    item_comp = item.components[comps.Item]
    ef: eff.GameEffect = None
    applicators = {
        "health": eff.HealingEffect,
        "poison": eff.PoisonEffect,
    }

    ef = applicators[item_comp.item_effect](
        item_comp.eff_duration, item_comp.eff_potency
    )
    write_log(item.world, "item", f"{q.name(item)} used on {q.name(target)}")
    apply_effect(target, ef)


# def remove_entity(e: Entity):
#     """DANGEROUS! DO NOT DO THIS IN A LOOP"""
#     e.world.
