from tcod.ecs import World, Entity
from gamestate import GameState
from geom import Point
from yaml import load, SafeLoader
from gamemap import GameMap

import components as comps


class GameData:
    """Describes game data, stored in YAML files."""

    def __init__(self, fn: str):
        with open(fn, "r") as f:
            self.data = load(f, SafeLoader)


CHARDATA = GameData("./assets/data/characterdata.yml")


# def make_player(world: World, temp_id: str, name: str) -> Entity:
#     template = CHARDATA.data[temp_id]
#     color = tuple(template["color"])
#     tags = template.get("tags", list())
#     glyph = template["glyph"]
#     c = {
#         comps.Name: name,
#         comps.Renderable: comps.Renderable(glyph, color, 4),
#         comps.Location: comps.Location(Point(0, 0)),
#         comps.Actor: comps.Actor(100, 20),
#     }

#     e = world["player"]
#     e.components.update(c)
#     for tag in ["player", "blocker"] + tags:
#         e.tags.add(tag)

#     return e


def make_char(
    world: World, id: str, *, name: str = None, player: bool = False
) -> Entity:
    template = CHARDATA.data[id]
    color = tuple(template["color"])
    glyph = template["glyph"]
    tags = template.get("tags", list())
    speed = template.get("speed", 20)
    nm = name if name is not None else template["name"]
    e = None

    c = {
        comps.Name: nm,
        comps.Renderable: comps.Renderable(glyph, color, 3),
        comps.Location: comps.Location(Point(0, 0)),
        comps.Actor: comps.Actor(100, speed),
    }

    if player:
        e = world["player"]
    elif template.get("named", False):
        e = world[nm]
    else:
        e = world.new_entity()

    e.components.update(c)

    for tag in ["blocker"] + tags:
        e.tags.add(tag)

    if player:
        e.tags.add("player")

    return e


def place_entity(gs: GameState, e: Entity, m: GameMap, pt: Point = None):
    e.relation_tag[comps.MapId] = m.id
    pos = e.components.get(comps.Location)
    if pt is None:
        pt = m.get_random_floor()

    while len(list(gs.get_blockers_at(pt))) > 0:
        pt = m.get_random_floor()

    if pos is None:
        e.components[comps.Location] = comps.Location(pt)
    else:
        pos.pos = pt
