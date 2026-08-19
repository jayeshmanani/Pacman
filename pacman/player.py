"""Player entity model and movement logic."""

from enum import Enum


class Direction(Enum):
    """Represent 4-directional movement vectors (dx, dy)."""

    NONE = (0.0, 0.0)
    UP = (0.0, -1.0)
    DOWN = (0.0, 1.0)
    LEFT = (-1.0, 0.0)
    RIGHT = (1.0, 0.0)

    @property
    def vector(self) -> tuple[float, float]:
        """Return the (dx, dy) direction vector."""
        return self.value

