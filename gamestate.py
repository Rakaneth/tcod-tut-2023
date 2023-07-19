from tcod.ecs import World, Entity
from typing import Dict
from gamemap import GameMap


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
