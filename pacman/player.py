"""Player entity model and movement logic."""

from enum import Enum
from dataclasses import dataclass

from pacman.maze_grid import TileCoordinate
from pacman.world import WorldPosition, WorldSize


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


@dataclass
class Player:
    """Represent the playable Pacman entity."""

    position: WorldPosition
    direction: Direction = Direction.NONE
    queued_direction: Direction = Direction.NONE
    speed: float = 5.0
    half_size: WorldSize = (0.4, 0.4)

    @classmethod
    def from_spawn(
        cls,
        spawn_tile: TileCoordinate,
        speed: float = 5.0,
        half_size: WorldSize = (0.4, 0.4),
    ) -> "Player":
        """Create a player centered at a given spawn tile coordinate."""
        x, y = spawn_tile
        return cls(
            position=(x+0.5, y+0.5),
            direction=Direction.NONE,
            queued_direction=Direction.NONE,
            speed=speed,
            half_size=half_size,
        )
