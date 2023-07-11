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
        ("render", comps.Renderable): comps.Renderable(glyph, color),
        ("pos", comps.Position): comps.Position(None, Point(0, 0)),
    }

    if name is not None:
        e = world[name]
    else:
        e = world.new_entity()

    e.components.update(c)

    if len(tags) > 0:
        for tag in tags.split():
            e.tags.add(tag)

    return e
