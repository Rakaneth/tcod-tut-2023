from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Point:
    """Simple X,Y data. Includes convenience functions."""

    x: int
    y: int

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)
