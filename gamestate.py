from tcod.ecs import World, Entity
from typing import Dict
from gamemap import GameMap
from geom import Point
from components import Location


class GameState:
    """Holds game maps and world data."""

    def __init__(self, world: World):
        self.world = world
        self.maps: Dict[str, GameMap] = dict()

    @property
    def player(self) -> Entity:
        return self.world["player"]

    @property
    def cur_map(self) -> GameMap:
        map_id = self.player.relation_tag["map_id"]
        return self.maps[map_id]

    def add_map(self, m: GameMap):
        self.maps[m.id] = m
    
    def get_entities_at(self, pt: Point):
        return filter(
            lambda i: i.components[Location].pos == pt,
            self.world.Q.all_of(
                components=[Location],
                relations=[("map_id", self.cur_map.id)],
        ))
    
    def is_enemy(self, e: Entity):
        return "enemy" in e.tags
    
    def is_friendly(self, e: Entity):
        return "friendly" in e.tags
