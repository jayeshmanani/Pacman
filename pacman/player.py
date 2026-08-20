"""Player entity model and movement logic."""

from enum import Enum
from dataclasses import dataclass

from pacman.maze_grid import TileCoordinate
from pacman.world import WorldPosition, WorldSize, WorldMap


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

    def is_opposite(self, other: "Direction") -> bool:
        """Return True if other is the 180-degree opposite direction."""
        dx1, dy1 = self.vector
        dx2, dy2 = other.vector
        return ((dx1 + dx2 == 0.0) and
                (dy1 + dy2 == 0.0) and self != Direction.NONE)

    def is_perpendicular(self, other: "Direction") -> bool:
        """Return True if other is a 90-degree turn relative to self."""
        if self == Direction.NONE or other == Direction.NONE:
            return False
        dx1, dy1 = self.vector
        dx2, dy2 = other.vector
        return (dx1 * dx2 + dy1 * dy2) == 0.0


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

    def update(self, dt: float, world: WorldMap) -> None:
        """Update player position and handle turn buffer & wall collisions."""
        if dt <= 0:
            return

        if self.queued_direction != Direction.NONE:
            q_dx, q_dy = self.queued_direction.vector
            q_target = (
                self.position[0] + q_dx * self.speed * dt,
                self.position[1] + q_dy * self.speed * dt,
            )
            if world.can_occupy(q_target, self.half_size):
                if self.direction.is_perpendicular(
                    self.queued_direction
                ):
                    curr_x, curr_y = self.position
                    if q_dx != 0:
                        curr_y = int(curr_y) + 0.5
                    elif q_dy != 0:
                        curr_x = int(curr_x) + 0.5
                    self.position = (curr_x, curr_y)
                self.direction = self.queued_direction
                self.queued_direction = Direction.NONE

        if self.direction != Direction.NONE:
            dx, dy = self.direction.vector
            target = (
                self.position[0] + dx * self.speed * dt,
                self.position[1] + dy * self.speed * dt,
            )
            if world.can_occupy(target, self.half_size):
                self.position = target
            else:
                self.direction = Direction.NONE


def direction_from_key(key_name: str) -> Direction | None:
    """Map WASD and Arrow key names to directional movement."""
    normalized = key_name.lower()
    if normalized in ("w", "up"):
        return Direction.UP
    if normalized in ("s", "down"):
        return Direction.DOWN
    if normalized in ("a", "left"):
        return Direction.LEFT
    if normalized in ("d", "right"):
        return Direction.RIGHT
    return None
