from __future__ import annotations
from functools import reduce

from tcod.ecs import World, Entity
from tcod.ecs.query import WorldQuery
from typing import TYPE_CHECKING, Literal, Tuple
from gamemap import GameMap
from geom import Point
import components as comps

if TYPE_CHECKING:
    from effects import GameEffect


def player(w: World) -> Entity:
    return w["player"]


def name(e: Entity) -> str:
    return e.components[comps.Name]


def location(e: Entity):
    return e.components[comps.Location]


def map_connections(w: World, m_from_id: str) -> dict:
    results = {}
    m_e_from = w[m_from_id]
    results["down"] = None
    results["up"] = None

    for e_up in w.Q.all_of(relations=[(comps.MapConnection, m_e_from)]):
        conn = e_up.relation_components[comps.MapConnection][m_e_from]
        results["up"] = (e_up.uid, conn.down_stair)

    for e_down in w.Q.all_of(relations=[(m_e_from, comps.MapConnection, None)]):
        conn = m_e_from.relation_components[comps.MapConnection][e_down]
        results["down"] = (conn.map_id, conn.up_stair)

    return results


def get_map(w: World, map_id: str) -> GameMap:
    return w[map_id].components[comps.GameMapComp]


def cur_map(w: World) -> GameMap:
    cur_map_e = player(w).relation_tag[comps.MapId]
    return cur_map_e.components[comps.GameMapComp]


def current_actors(w: World) -> list[Entity]:
    q = entities(w).all_of(components=[comps.Actor]).none_of(tags=["dead"])
    return sorted(list(q), key=lambda i: i.components[comps.Actor].speed)


def turn_actors(w: World):
    def f(e: Entity) -> bool:
        return (
            e.components[comps.Actor].energy >= 0
            and not e.components[comps.Combatant].dead
        )

    return filter(f, current_actors(w))


def entities(w: World, map_id: str = None) -> WorldQuery:
    m_e = player(w).relation_tag[comps.MapId] if map_id is None else w[map_id]
    return w.Q.all_of(components=[comps.Location], relations=[(comps.MapId, m_e)])


def entities_at(w: World, pt: Point, map_id: str = None):
    es = entities(w, map_id)
    return filter(lambda e: e.components[comps.Location] == pt, es)


def consumables_at(w: World, pt: Point, map_id: str = None):
    es = entities(w, map_id)
    items = es.all_of(components=[comps.Item])
    return filter(lambda e: e.components[comps.Location] == pt, items)


def blockers_at(w: World, pt: Point, map_id: str = None):
    return filter(lambda e: "blocker" in e.tags, entities_at(w, pt, map_id))


def items_at(w: World, pt: Point, map_id: str = None):
    return filter(lambda e: "item" in e.tags, entities_at(w, pt, map_id))


def is_visible(e: Entity) -> bool:
    pos = e.world["player"].components[comps.Location]
    return cur_map(e.world).visible[pos.x, pos.y]


def drawable_entities(w: World) -> list[Entity]:
    cur_map_e = player(w).relation_tag[comps.MapId]
    fil = w.Q.all_of(
        components=[comps.Renderable, comps.Location],
        relations=[(comps.MapId, cur_map_e)],
    )
    return sorted(list(fil), key=lambda i: i.components[comps.Renderable].z)


def trying_to_move(w: World) -> WorldQuery:
    m_e = player(w).relation_tag[comps.MapId]
    return w.Q.all_of(
        components=[comps.Location, comps.TryMove], relations=[(comps.MapId, m_e)]
    )


def collisions(w: World) -> WorldQuery:
    return w.Q[Entity, comps.CollidesWith]


def bumpers(w: World) -> WorldQuery:
    return w.Q[Entity, comps.BumpAttacking]


def living(w: World) -> WorldQuery:
    return w.Q.all_of(components=[comps.Combatant]).none_of(tags=["dead"])


def on_hits(w: World) -> WorldQuery:
    return w.Q[Entity, comps.CheckOnHits, comps.OnHit]


def is_enemy(e: Entity) -> bool:
    return "enemy" in e.tags


def is_friendly(e: Entity) -> bool:
    return "friendly" in e.tags


def is_neutral(e: Entity) -> bool:
    return not (is_friendly(e) or is_enemy(e))


def is_hostile(e1: Entity, e2: Entity) -> bool:
    hostile_groups = e1.relation_tags_many[comps.HostileTo]
    return any(group in e2.tags for group in hostile_groups)


def is_faction(e1: Entity, e2: Entity) -> bool:
    faction_tags = ["player", "enemy", "friendly"]
    return any(
        faction for faction in faction_tags if faction in e1.tags if faction in e2.tags
    )


def is_dead(e: Entity) -> bool:
    return "dead" in e.tags


def is_player(e: Entity) -> bool:
    return "player" in e.tags


def messages(w: World) -> list[comps.GameMessage]:
    return w[None].components[comps.Messages]


def find_effect(e: Entity, eff_name: str) -> GameEffect | None:
    f = list(filter(lambda eff: eff.name == eff_name, e.components[comps.EffectsList]))
    if f:
        return f[0]

    return None


def inventory(e: Entity) -> list[Entity]:
    return list(e.world.Q.all_of(relations=[(comps.HeldBy, e)]))


def trying_to_use_item(w: World):
    return w.Q[Entity, comps.UseItemOn]


def is_equipment(e: Entity) -> bool:
    return "equip" in e.tags


def is_armor(e: Entity) -> bool:
    return "armor" in e.tags


def is_weapon(e: Entity) -> bool:
    return "weapon" in e.tags


def is_trinket(e: Entity) -> bool:
    return "trinket" in e.tags


def get_equipped(e: Entity) -> WorldQuery:
    return e.world.Q.all_of(relations=[(e, comps.Equipped, None)])


def is_equipped_to(item: Entity, e: Entity):
    return item in e.relation_tags_many[comps.Equipped]


StatValue = Literal[
    "atp",
    "dfp",
    "reduction",
]


def get_stat(e: Entity, stat: StatValue) -> int:
    def fn(acc: int, n: Entity) -> int:
        n_stat = getattr(n.components[comps.Equipment], stat)
        return acc + n_stat

    comb = e.components[comps.Combatant]
    s = reduce(fn, get_equipped(e), 0)

    match stat:
        case "atp":
            return comb.atp + s
        case "dfp":
            return comb.dfp + s
        case "reduction":
            return comb.base_reduce + s


def get_armor(e: Entity) -> Entity | None:
    return e.relation_tag.get(comps.EquippedArmor)


def get_weapon(e: Entity) -> Entity | None:
    return e.relation_tag.get(comps.EquippedWeapon)


def get_trinket(e: Entity) -> Entity | None:
    return e.relation_tag.get(comps.EquippedTrinket)


def equips_at(w: World, pt: Point, map_id: str = None):
    base = entities_at(w, pt, map_id)
    return filter(lambda e: "equip" in e.tags, base)


def dmg(e: Entity) -> Tuple[int, int]:
    maybe_wpn = get_weapon(e)
    comb = e.components[comps.Combatant]
    st = comb.str_mod
    dmg = comb.dmg

    if maybe_wpn:
        eq_low, eq_high = maybe_wpn.components[comps.Equipment].dmg
        return (eq_low + st, eq_high + st)
    else:
        return dmg
