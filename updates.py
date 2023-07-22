from tcod.ecs import World, Entity
import components as comps


def kill(e: Entity):
    render = e.components[comps.Renderable]
    render.glyph = "%"
    render.z = 2
    e.tags.add("dead")
    e.tags.remove("blocker")
    if comps.TryMove in e.components:
        e.components.pop(comps.TryMove)
    if comps.CollidesWith in e.components:
        e.components.pop(comps.CollidesWith)


def add_msg(w: World, txt: str):
    w[None].components[comps.Messages].append(txt)
