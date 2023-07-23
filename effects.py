from __future__ import annotations

from tcod.ecs import Entity
from updates import add_msg_about


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
            addendum = f" {self.potency} ({self.duration} turns)"
        elif has_duration:
            addendum = f" ({self.duration} turns)"
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
        add_msg_about(e, f"<entity> bleeds for {dmg} damage!")

    def on_merge(self, eff: GameEffect):
        """Bleed is nasty, stacking potency AND refreshing duration."""
        self.potency += eff.potency
        super().on_merge(eff)

    def on_remove(self, e: Entity):
        add_msg_about(e, "<entity> is no longer bleeding.")
