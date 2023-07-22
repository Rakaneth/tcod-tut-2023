from tcod.ecs import World, Entity
from queries import blockers_at
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


def make_char(
    world: World, id: str, *, name: str = None, player: bool = False
) -> Entity:
    template = CHARDATA.data[id]
    color = tuple(template["color"])
    glyph = template["glyph"]
    tags = template.get("tags", list())
    speed = template.get("speed", 20)
    nm = name if name is not None else template["name"]
    hp = template.get("hp", None)
    atp = template.get("atp", None)
    dfp = template.get("dfp", None)
    dmg = template.get("dmg", None)
    e = None
    z = 4 if player else 3

    c = {
        comps.Name: nm,
        comps.Renderable: comps.Renderable(glyph, color, z),
        comps.Location: comps.Location(Point(0, 0)),
        comps.Actor: comps.Actor(100, speed),
    }

    if hp is not None and atp is not None and dfp is not None and dmg is not None:
        c |= {comps.Combatant: comps.Combatant(hp, hp, atp, dfp, tuple(sorted(dmg)))}

    if player:
        e = world["player"]
    elif template.get("named", False):
        e = world[nm]
    else:
        e = world.new_entity()

    e.components.update(c)

    if "enemy" in tags:
        e.relation_tags_many[comps.HostileTo].add("player")
        e.relation_tags_many[comps.HostileTo].add("friendly")

    for tag in ["blocker"] + tags:
        e.tags.add(tag)

    if player:
        e.tags.add("player")
        e.relation_tags_many[comps.HostileTo].add("enemy")

    return e


def add_map(w: World, m: GameMap):
    w[None].components[(m.id, GameMap)] = m


def place_entity(w: World, e: Entity, m: GameMap, pt: Point = None):
    e.relation_tag[comps.MapId] = m.id
    pos = e.components.get(comps.Location)
    if pt is None:
        pt = m.get_random_floor()

    while len(list(blockers_at(w, pt))) > 0:
        pt = m.get_random_floor()

    if pos is None:
        e.components[comps.Location] = comps.Location(pt)
    else:
        pos.pos = pt
