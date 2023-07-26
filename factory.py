from random import choices, randint
from tcod.ecs import World, Entity
from queries import blockers_at, get_map
from geom import Point
from yaml import load, SafeLoader
from gamemap import GameMap, arena, drunk_walk

import components as comps
import effects
import gamelog as gl


class GameData:
    """Describes game data, stored in YAML files."""

    def __init__(self, fn: str):
        with open(fn, "r") as f:
            self.data = load(f, SafeLoader)


DATAFOLDER = "./assets/data/"

CHARDATA = GameData(f"{DATAFOLDER}characterdata.yml")
MAPDATA = GameData(f"{DATAFOLDER}/mapdata.yml")


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
    st = template.get("st", None)
    wl = template.get("wl", None)
    ag = template.get("ag", None)
    e = None
    z = 4 if player else 3
    on_hit = template.get("on_hit", None)
    desc = template.get("desc", None)
    full_name = template.get("full_name", None)

    c = {
        comps.Name: nm,
        comps.Renderable: comps.Renderable(glyph, color, z),
        comps.Location: Point(0, 0),
        comps.Actor: comps.Actor(0, speed),
        comps.EffectsList: list(),
    }

    if not any(s is None for s in [hp, atp, dfp, dmg, st, ag, wl]):
        c |= {
            comps.Combatant: comps.Combatant(
                hp, hp, atp, dfp, tuple(sorted(dmg)), st, ag, wl
            )
        }

    if on_hit:
        bleed_data = on_hit.get("bleed", None)
        if bleed_data:
            duration = bleed_data["duration"]
            potency = bleed_data["potency"]
            chance = bleed_data["chance"]
            c |= {
                comps.OnHit: comps.OnHit(effects.BleedEffect(duration, potency), chance)
            }

    if full_name:
        c |= {comps.FullName: full_name}

    if desc:
        c |= {comps.Description: desc}

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

    gl.write_log(world, "factory", f"Creating character {nm}")

    return e


def add_map(w: World, m: GameMap):
    w[None].components[(m.id, GameMap)] = m


def place_entity(w: World, e: Entity, map_id: str, pt: Point = None):
    e.relation_tag[comps.MapId] = map_id
    m = get_map(w, map_id)
    if pt is None:
        pt = m.get_random_floor()

    while len(list(blockers_at(w, pt))) > 0:
        pt = m.get_random_floor()

    e.components[comps.Location] = pt

    gl.write_log(
        w, "factory", f"Adding entity {e.components[comps.Name]} to {map_id} at {pt}"
    )


def build_all_maps(w: World):
    for map_id in MAPDATA.data.keys():
        gl.write_log(w, "factory", f"Building map {map_id}")
        m = make_map(map_id)
        add_map(w, m)


def populate_all_maps(w: World):
    maps = (item for item in w[None].components.values() if isinstance(item, GameMap))
    for m in maps:
        gl.write_log(w, "factory", f"Populating map {m.id}")
        populate_map(w, m)


def make_map(build_id: str) -> GameMap:
    """Creates a map based on map data."""
    template = MAPDATA.data[build_id]
    gen = template["gen"]
    w_low, w_high = template["width"]
    h_low, h_high = template["height"]
    tier = template["tier"]
    dark = template.get("dark", False)
    name = template["name"]

    width = randint(w_low, w_high)
    height = randint(h_low, h_high)
    cov = 0.3 + 0.1 * tier
    m = None

    match gen:
        case "drunkard":
            m = drunk_walk(build_id, name, width, height, cov, dark)
        case "arena":
            m = arena(build_id, name, width, height, dark)
        case _:
            raise NotImplementedError(f"Map type {gen} not yet implemented.")

    return m


def populate_map(w: World, m: GameMap):
    template = MAPDATA.data[m.id]

    tier = template["tier"]
    monster_data = template["monsters"]
    m_low, m_high = monster_data["number"]
    num_monsters = randint(m_low, m_high)
    m_types = monster_data["types"]
    m_tiers = monster_data.get("tiers", list())

    monster_cands = {
        key: val["freq"]
        for key, val in CHARDATA.data.items()
        if val.get("freq", 0) > 0
        if (m_tiers and val.get("tier", 99) in m_tiers) or val.get("tier", 99) == tier
        if any(tag in val.get("tags", []) for tag in m_types)
    }

    if monster_cands:
        monster_choice_ids = choices(
            list(monster_cands.keys()), list(monster_cands.values()), k=num_monsters
        )

        for m_id in monster_choice_ids:
            monster = make_char(w, m_id)
            place_entity(w, monster, m.id)
    else:
        gl.write_log(w, "factory", f"No monster choices for map {m.id}; check data")
