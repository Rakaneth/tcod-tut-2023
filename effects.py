from __future__ import annotations

from tcod.ecs import Entity
from updates import add_msg_about

import components as comps
import combat as cbt


class GameEffect:
    """Describes a persistent effect on an Entity."""

    def __init__(self, name: str, duration: int = -1, potency: int = 0):
        self.duration = duration
        self.potency = potency
        self.name = name

    def on_tick(self, e: Entity, num_ticks: int):
        pass

    def on_apply(self, e: Entity):
        pass

    def on_remove(self, e: Entity):
        pass

    def on_merge(self, eff: GameEffect):
        """Effects refresh duration on merge by default."""
        self.duration = max(self.duration, eff.duration)

    @property
    def expired(self) -> bool:
        return self.duration == 0

    def tick(self, e: Entity, num_ticks: int = 1):
        self.on_tick(e, num_ticks)
        if self.duration > 0:
            self.duration = max(self.duration - num_ticks, 0)

    def __str__(self) -> str:
        addendum = ""
        has_duration = self.duration > 0
        has_potency = self.potency > 0

        if has_duration and has_potency:
            addendum = f" {self.potency}({self.duration} t)"
        elif has_duration:
            addendum = f"({self.duration} t)"
        elif has_potency:
            addendum = f" {self.potency}"

        return f"{self.name}{addendum}"


class BleedEffect(GameEffect):
    """Describes damage over time caused by bleeding."""

    def __init__(self, duration: int, potency: int):
        super().__init__("Bleed", duration, potency)

    def on_apply(self, e: Entity):
        add_msg_about(e, "<entity> is bleeding!")

    def on_tick(self, e: Entity, num_ticks: int):
        dmg = self.potency * num_ticks
        e.components[comps.Combatant].damage(1)
        add_msg_about(e, f"<entity> bleeds for {dmg} damage!")

    def on_merge(self, eff: GameEffect):
        """Bleed is nasty, stacking potency AND refreshing duration."""
        self.potency += eff.potency
        super().on_merge(eff)

    def on_remove(self, e: Entity):
        add_msg_about(e, "<entity> is no longer bleeding.")


class HealingEffect(GameEffect):
    def __init__(self, duration: int, potency: int):
        super().__init__("Healing", duration, potency)

    def on_apply(self, e: Entity):
        add_msg_about(e, "<entity> is healing!")

    def on_tick(self, e: Entity, num_ticks: int):
        amt = self.potency * num_ticks
        e.components[comps.Combatant].heal(amt)
        add_msg_about(e, f"<entity> heals {amt} damage!")

    def on_remove(self, e: Entity):
        add_msg_about(e, "<entity> is no longer healing.")


class PoisonEffect(GameEffect):
    def __init__(self, duration: int, potency: int):
        super().__init__("Poison", duration, potency)

    def on_apply(self, e: Entity):
        add_msg_about(e, "<entity> is poisoned!")

    def on_tick(self, e: Entity, num_ticks: int):
        amt = self.potency * num_ticks
        e.components[comps.Combatant].damage(amt)
        add_msg_about(e, f"<entity> takes {amt} damage from poison!")

    def on_remove(self, e: Entity):
        add_msg_about(e, "<entity> is no longer poisoned.")


class LightningEffect(GameEffect):
    def __init__(self, potency: int):
        super().__init__("Lightning", 0, potency)

    def on_apply(self, e: Entity):
        low = max(0, self.potency - 3)
        high = self.potency + 3
        dmg = cbt.gauss_roll(low, high)
        e.components[comps.Combatant].damage(dmg)
        add_msg_about(e, f"<entity> is struck by lightning for {dmg} damage!")


class BurningEffect(GameEffect):
    def __init__(self, duration: int, potency: int):
        super().__init__("Burning", duration, potency)

    def on_apply(self, e: Entity):
        add_msg_about(e, "<entity> is burning!")

    def on_tick(self, e: Entity, num_ticks: int):
        e.components[comps.comps.Combatant].damage(self.potency)
        add_msg_about(e, f"<entity> burns for {self.potency} damage!")

    def on_merge(self, eff: GameEffect):
        # Burn stacks duration
        self.duration += eff.duration

    def on_remove(self, e: Entity):
        add_msg_about(e, "<entity>'s flames burn out.")


class StunnedEffect(GameEffect):
    def __init__(self, duration):
        super().__init__("Stunned", duration, 0)

    def on_apply(self, e: Entity):
        add_msg_about(e, "<entity> is stunned!")

    def on_remove(self, e: Entity):
        add_msg_about(e, "<entity> is no longer stunned.")
