from random import choices, randint
from typing import Callable, Literal
from tcod.ecs import World, Entity
from queries import blockers_at, items_at, get_map
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
ITEMDATA = GameData(f"{DATAFOLDER}/itemdata.yml")
EQUIPDATA = GameData(f"{DATAFOLDER}/equipdata.yml")

EFFS = {
    "bleed": effects.BleedEffect,
    "burning": effects.BurningEffect,
    "stunned": effects.StunnedEffect,
}


def _check_on_hits(tbl: dict, eff_id: str, eff_type):
    _data = tbl.get(eff_id)
    if _data:
        duration = _data.get("duration", 0)
        potency = _data.get("potency", 0)
        chance = _data["chance"]
        if eff_id == "stunned":
            eff = eff_type(duration)
        else:
            eff = eff_type(duration, potency)
        return {comps.OnHit: comps.OnHit(eff, chance)}

    return None


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
    inv_max = template.get("inventory", None)

    c = {
        comps.Name: nm,
        comps.Renderable: comps.Renderable(glyph, color, z),
        comps.Location: Point(0, 0),
        comps.Actor: comps.Actor(-100, speed),
        comps.EffectsList: list(),
    }

    if not any(s is None for s in [hp, atp, dfp, dmg, st, ag, wl]):
        cbt = comps.Combatant(hp, hp, atp, dfp, tuple(sorted(dmg)), st, ag, wl)
        cbt.heal()
        c |= {comps.Combatant: cbt}

    if on_hit:
        for eff_type in on_hit.keys():
            oh = _check_on_hits(on_hit, eff_type, EFFS[eff_type])
            if c:
                c |= oh

    if full_name:
        c |= {comps.FullName: full_name}

    if desc:
        c |= {comps.Description: desc}

    if inv_max:
        c |= {comps.InventoryMax: inv_max}

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


def make_consumable(w: World, item_id: str) -> Entity:
    template = ITEMDATA.data[item_id]
    name = template["name"]
    glyph = template["glyph"]
    color = tuple(template["color"])
    tags = template["tags"]
    desc = template["desc"]
    effect = template["effect"]
    duration = template.get("duration", 0)
    potency = template.get("potency", 0)
    delivery = template["delivery"]

    c = {
        comps.Name: name,
        comps.Renderable: comps.Renderable(glyph, color, 2),
        comps.Description: desc,
        comps.Item: comps.Item(delivery, effect, duration, potency),
    }

    e = w.new_entity(c)

    for tag in tags:
        e.tags.add(tag)

    return e


def make_equipment(w: World, build_id: str) -> Entity:
    template = EQUIPDATA.data[build_id]
    name = template["name"]
    desc = template["desc"]
    glyph = template["glyph"]
    color = template["color"]
    tags = template["tags"]
    encumbrance = template.get("encumbrance", 0)
    on_hit = template.get("on_hit")
    dmg = template.get("dmg")
    atp = template.get("atp", 0)
    dfp = template.get("dfp", 0)
    reduction = template.get("reduction", 0)
    durability = template.get("durability", 0)

    c = {
        comps.Name: name,
        comps.Renderable: comps.Renderable(glyph, color, 2),
        comps.Description: desc,
        comps.Equipment: comps.Equipment(
            atp, dfp, dmg, encumbrance, durability, reduction
        ),
    }

    if on_hit:
        for eff_id in on_hit.keys():
            oh = _check_on_hits(on_hit, eff_id, EFFS[eff_id])
            if oh:
                c |= oh

    e = w.new_entity(components=c)

    for tag in tags:
        e.tags.add(tag)

    return e


def add_map(w: World, m: GameMap):
    m_e = w[m.id]
    m_e.components[comps.GameMapComp] = m


def connect_map(w: World, m_from: GameMap, m_to: GameMap):
    e_m_from = w[m_from.id]
    e_m_to = w[m_to.id]
    stairs_down = m_from.get_random_floor()
    stairs_up = m_to.get_random_floor()
    m_from.add_down_stair(stairs_down.x, stairs_down.y)
    m_to.add_up_stair(stairs_up.x, stairs_up.y)
    e_m_from.relation_components[comps.MapConnection][e_m_to] = comps.MapConnection(
        m_to.id, stairs_down, stairs_up
    )
    gl.write_log(w, "factory", f"Connecting {m_from.id} to {m_to.id}")


def place_entity(w: World, e: Entity, map_id: str, pt: Point = None):
    m_e = w[map_id]
    e.relation_tag[comps.MapId] = m_e
    m = m_e.components[comps.GameMapComp]
    if pt is None:
        pt = m.get_random_floor()

    blockers_here = bool(len(list(blockers_at(w, pt))))
    items_here = bool(len(list(items_at(w, pt))))

    while blockers_here or items_here:
        pt = m.get_random_floor()
        blockers_here = bool(len(list(blockers_at(w, pt))))
        items_here = bool(len(list(items_at(w, pt))))

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
    for _, m in w.Q[Entity, comps.GameMapComp]:
        gl.write_log(w, "factory", f"Populating map {m.id}")
        populate_map(w, m)


def connect_all_maps(w: World):
    for map_id, map_data in MAPDATA.data.items():
        downto = map_data.get("downto")
        if downto:
            map_from = get_map(w, map_id)
            map_to = get_map(w, downto)
            connect_map(w, map_from, map_to)


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


Repo = Literal["monsters", "items", "equips"]


def populate_map(w: World, m: GameMap):
    template = MAPDATA.data[m.id]

    def _cands(
        repo: GameData, type_list: list, default_tier: int, tier_list: list = None
    ):
        return {
            key: val["freq"]
            for key, val in repo.data.items()
            if val.get("freq", 0) > 0
            if (tier_list and val.get("tier", -1) in tier_list)
            or val.get("tier", -1) == default_tier
            if any(tag in val.get("tags", []) for tag in type_list)
        }

    def _popu(tbl: dict, fn: Callable[[World, str], Entity], num: int, repo: Repo):
        if tbl:
            choice_ids = choices(list(tbl.keys()), list(tbl.values()), k=num)

            for c_id in choice_ids:
                thing = fn(w, c_id)
                place_entity(w, thing, m.id)
        else:
            gl.write_log(
                w, "factory", f"No valid choices for {repo} in map {m.id}; check data"
            )

    tier = template["tier"]
    monster_data = template.get("monsters")
    item_data = template.get("items")
    equip_data = template.get("equips")

    if monster_data:
        m_low, m_high = monster_data["number"]
        num_monsters = randint(m_low, m_high)
        m_types = monster_data["types"]
        m_tiers = monster_data.get("tiers", list())
        monster_cands = _cands(CHARDATA, m_types, tier, m_tiers)
        _popu(monster_cands, make_char, num_monsters, "monsters")

    if item_data:
        i_low, i_high = item_data["number"]
        num_items = randint(i_low, i_high)
        i_types = item_data["types"]
        i_tiers = item_data.get("tiers", list())
        item_cands = _cands(ITEMDATA, i_types, tier, i_tiers)
        _popu(item_cands, make_consumable, num_items, "items")

    if equip_data:
        e_low, e_high = equip_data["number"]
        num_equips = randint(e_low, e_high)
        e_types = equip_data["types"]
        e_tiers = equip_data.get("tiers", list())
        equip_cands = _cands(EQUIPDATA, e_types, tier, e_tiers)
        _popu(equip_cands, make_equipment, num_equips, "equips")
