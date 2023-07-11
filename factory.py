from tcod.ecs import World, Entity
from geom import Point
from yaml import load, SafeLoader

import components as comps


class GameData:
    """Describes game data, stored in YAML files."""

    def __init__(self, fn: str):
        with open(fn, "r") as f:
            self.data = load(f, SafeLoader)


CHARDATA = GameData("characterdata.yml")


def make_char(world: World, id: str, tags: str = "", name: str = None) -> Entity:
    template = CHARDATA.data[id]
    color = tuple(template["color"])
    glyph = template["glyph"]
    nm = name if name is not None else template["name"]
    e = None

    c = {
        ("name", str): nm,
        comps.Renderable: comps.Renderable(glyph, color),
        comps.Location: comps.Location(None, Point(0, 0)),
    }

    if name is not None or template.get("named", False):
        e = world[nm]
    else:
        e = world.new_entity()

    e.components.update(c)

    if len(tags) > 0:
        for tag in tags.split():
            e.tags.add(tag)

    return e


def place_entity(e: Entity, pt: Point, map_id: str = None):
    pos = e.components.get(comps.Location)
    if pos is None:
        e.components[comps.Location] = comps.Location(map_id, pt)
    else:
        pos.pos = pt
        if map_id is not None:
            pos.map_id = map_id
