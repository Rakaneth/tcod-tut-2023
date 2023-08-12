from __future__ import annotations

from tcod.ecs import World, Entity
from geom import Point
from swatch import WHITE
from gamelog import write_log
from typing import Any


import components as comps
import queries as q
import effects as eff


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
    for item in q.inventory(e):
        drop_item(item, e)
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
    if item in q.get_equipped(holder):
        unequip_item(item, holder)
    write_log(item.world, "inventory", f"{q.name(holder)} drops {q.name(item)}")


def apply_item(
    item: Entity, target: Entity, *, duration: int = None, potency: int = None
):
    item_comp = item.components[comps.Item]
    ef: eff.GameEffect = None
    dur = item_comp.eff_duration if duration is None else duration
    pot = item_comp.eff_potency if potency is None else potency
    applicators = {
        "health": eff.HealingEffect(dur, pot),
        "poison": eff.PoisonEffect(dur, pot),
        "lightning": eff.LightningEffect(pot),
    }

    ef = applicators[item_comp.item_effect]
    write_log(item.world, "item", f"{q.name(item)} used on {q.name(target)}")
    apply_effect(target, ef)


def _eq_item(item: Entity, tag: Any, wielder: Entity):
    wielder.relation_tag[tag] = item
    wielder.relation_tags_many[comps.Equipped].add(item)
    write_log(wielder.world, "equip", f"{q.name(wielder)} equips {q.name(item)}")


def _uneq_item(item: Entity, tag: Any, wielder: Entity):
    wielder.relation_tag.pop(tag)
    wielder.relation_tags_many[comps.Equipped].discard(item)
    write_log(wielder.world, "equip", f"{q.name(wielder)} unequips {q.name(item)}")


def unequip_item(item: Entity, wielder: Entity):
    if q.is_armor(item):
        _uneq_item(item, comps.EquippedArmor, wielder)
    elif q.is_weapon(item):
        _uneq_item(item, comps.EquippedWeapon, wielder)
    elif q.is_trinket(item):
        _uneq_item(item, comps.EquippedTrinket, wielder)

    if q.is_visible(wielder):
        add_msg_about(wielder, f"<entity> removes {q.name(item)}.")


def equip_item(item: Entity, wielder: Entity):
    if q.is_armor(item):
        prev_armor = q.get_armor(wielder)
        if prev_armor:
            _uneq_item(prev_armor, comps.EquippedArmor, wielder)
        _eq_item(item, comps.EquippedArmor, wielder)
    elif q.is_weapon(item):
        prev_weapon = q.get_weapon(wielder)
        if prev_weapon:
            _uneq_item(prev_weapon, comps.EquippedWeapon, wielder)
        _eq_item(item, comps.EquippedWeapon, wielder)
    elif q.is_trinket(item):
        prev_trink = q.get_trinket(wielder)
        if prev_trink:
            _uneq_item(prev_trink, comps.EquippedTrinket, wielder)
        _eq_item(item, comps.EquippedTrinket, wielder)

    if q.is_visible(wielder):
        add_msg_about(wielder, f"<entity> equips {q.name(item)}.")


def change_map(e: Entity, map_id: str, pt: Point):
    e.relation_tag[comps.MapId] = e.world[map_id]
    e.components[comps.Location] = pt


def gain_xp(e: Entity, victim: Entity):
    stats = victim.components.get(comps.Combatant)
    lvl = e.components.get(comps.Level)
    xp = 0

    if not lvl:
        return

    if stats:
        xp = (stats.atp + stats.dfp) // 2 + (stats.st + stats.ag + stats.wl) // 3

    lvl.xp += xp
    maybe_lvl = q.check_gain_levels(e)
    write_log(e.world, "xp", f"{q.name(e)} gains {xp} xp from {q.name(victim)}")
    if maybe_lvl > 0:
        gain_levels(e, maybe_lvl)


def gain_levels(e: Entity, lvls: int):
    maybe_fight = e.components.get(comps.Combatant)
    maybe_lvl = e.components.get(comps.Level)

    if not (maybe_fight and maybe_lvl):
        return

    for _ in range(lvls):
        maybe_fight.base_max_hp += 5
        maybe_fight.st += 1
        maybe_fight.ag += 1
        maybe_fight.wl += 1
        maybe_fight.at += 5
        maybe_fight.df += 5

    maybe_lvl.level += lvls
    add_msg_about(e, f"<entity> gains {lvls} level{('s' if lvls > 1 else '')}!")
    write_log(e.world, "xp", f"{q.name(e)} gains {lvls} levels")
