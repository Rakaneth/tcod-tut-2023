from __future__ import annotations

from tcod.ecs import World, Entity, Query
from typing import TYPE_CHECKING
from gamemap import GameMap
from geom import Point
import components as comps

if TYPE_CHECKING:
    from effects import GameEffect


def player(w: World) -> Entity:
    return w["player"]


def name(e: Entity) -> str:
    return e.components[comps.Name]


def get_map(w: World, map_id: str) -> GameMap:
    return w[None].components[(map_id, GameMap)]


def cur_map(w: World) -> GameMap:
    cur_map_id = player(w).relation_tag[comps.MapId]
    return get_map(w, cur_map_id)


def current_actors(w: World) -> list[Entity]:
    q = entities(w).all_of(components=[comps.Actor]).none_of(tags=["dead"])
    return sorted(list(q), key=lambda i: i.components[comps.Actor].speed)


def turn_actors(w: World):
    def f(e: Entity) -> bool:
        return (
            e.components[comps.Actor].energy >= 100
            and not e.components[comps.Combatant].dead
        )

    return filter(f, current_actors(w))


def entities(w: World, map_id: str = None) -> Query:
    if map_id is None:
        map_id = cur_map(w).id
    return w.Q.all_of(components=[comps.Location], relations=[(comps.MapId, map_id)])


def entities_at(w: World, pt: Point, map_id: str = None):
    es = entities(w, map_id)
    return filter(lambda e: e.components[comps.Location].pos == pt, es)


def blockers_at(w: World, pt: Point, map_id: str = None):
    return filter(lambda e: "blocker" in e.tags, entities_at(w, pt, map_id))


def drawable_entities(w: World) -> list[Entity]:
    fil = w.Q.all_of(
        components=[comps.Renderable, comps.Location],
        relations=[(comps.MapId, cur_map(w).id)],
    )
    return sorted(list(fil), key=lambda i: i.components[comps.Renderable].z)


def is_enemy(e: Entity) -> bool:
    return "enemy" in e.tags


def is_friendly(e: Entity) -> bool:
    return "friendly" in e.tags


def is_neutral(e: Entity) -> bool:
    return not (is_friendly(e) or is_enemy(e))


def is_hostile(e1: Entity, e2: Entity) -> bool:
    hostile_groups = e1.relation_tags_many[comps.HostileTo]
    return any(group in e2.tags for group in hostile_groups)


def messages(w: World) -> list[comps.GameMessage]:
    return w[None].components[comps.Messages]


def find_effect(e: Entity, eff_name: str) -> GameEffect | None:
    f = list(filter(lambda eff: eff.name == eff_name, e.components[comps.EffectsList]))
    if f:
        return f[0]

    return None
