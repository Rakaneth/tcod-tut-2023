from tcod.ecs import World, Entity
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


def make_player(world: World, temp_id: str, name: str) -> Entity:
    template = CHARDATA.data[temp_id]
    color = tuple(template["color"])
    glyph = template["glyph"]
    c = {
        ("name", str): name,
        comps.Renderable: comps.Renderable(glyph, color),
        comps.Location: comps.Location(Point(0, 0)),
    }

    e = world["player"]
    e.components.update(c)
    for tag in ["player", "actor"]:
        e.tags.add(tag)

    return e


def make_char(world: World, id: str, tags: str = "", name: str = None) -> Entity:
    template = CHARDATA.data[id]
    color = tuple(template["color"])
    glyph = template["glyph"]
    nm = name if name is not None else template["name"]
    e = None

    c = {
        ("name", str): nm,
        comps.Renderable: comps.Renderable(glyph, color),
        comps.Location: comps.Location(Point(0, 0)),
    }

    if template.get("named", False):
        e = world[nm]
    else:
        e = world.new_entity()

    e.components.update(c)

    if len(tags) > 0:
        for tag in tags.split():
            e.tags.add(tag)

    return e


def place_entity(e: Entity, m: GameMap, pt: Point = None):
    pos = e.components.get(comps.Location)
    if pt is None:
        pt = m.get_random_floor()
    if pos is None:
        e.components[comps.Location] = comps.Location(pt)
    else:
        pos.pos = pt
        e.relation_tag["map_id"] = m.id
