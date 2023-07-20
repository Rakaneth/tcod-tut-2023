from tcod.ecs import World, Entity
from typing import Dict, List
from gamemap import GameMap
from geom import Point
from components import Actor, Location, MapId, Renderable


class GameState:
    """Holds game maps and world data."""

    def __init__(self, world: World):
        self.world = world
        self.maps: Dict[str, GameMap] = dict()
        self.messages: List[str] = list()

    @property
    def player(self) -> Entity:
        return self.world["player"]

    @property
    def cur_map(self) -> GameMap:
        map_id = self.player.relation_tag[MapId]
        return self.maps[map_id]

    def add_map(self, m: GameMap):
        self.maps[m.id] = m

    def get_current_entities(self):
        return self.world.Q.all_of(
            components=[Location], relations=[(MapId, self.cur_map.id)]
        )

    def get_current_actors(self):
        q = self.get_current_entities().all_of(components=[Actor])
        return sorted(list(q), key=lambda i: i.components[Actor].speed, reverse=True)

    def get_turn_actors(self):
        def f(e: Entity):
            return e.components[Actor].energy >= 100

        return filter(f, self.get_current_actors())

    def get_entities_at(self, pt: Point, map_id=None):
        id = map_id if map_id is not None else self.cur_map.id
        return filter(
            lambda i: i.components[Location].pos == pt,
            self.world.Q.all_of(
                components=[Location],
                relations=[(MapId, id)],
            ),
        )

    def get_blockers_at(self, pt: Point, map_id=None):
        def is_blocker(e: Entity):
            return "blocker" in e.tags

        return filter(is_blocker, self.get_entities_at(pt, map_id))

    def is_enemy(self, e: Entity) -> bool:
        return "enemy" in e.tags

    def is_friendly(self, e: Entity) -> bool:
        return "friendly" in e.tags

    def is_neutral(self, e: Entity) -> bool:
        return not (self.is_enemy(e) or self.is_friendly(e))

    def add_msg(self, txt):
        self.messages.append(txt)

    def drawable_entities(self):
        fil = self.world.Q.all_of(
            components=[Renderable, Location],
            relations=[(MapId, self.cur_map.id)],
        )
        return sorted(list(fil), key=lambda i: i.components[Renderable].z)
