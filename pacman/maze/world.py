"""Shared world coordinates and collision queries for game systems."""


from dataclasses import dataclass
import math

from pacman.maze.grid import MazeGrid, TileCoordinate

WorldPosition = tuple[float, float]
WorldSize = tuple[float, float]


def _validate_world_values(values: tuple[float, float], name: str) -> None:
    """Require a finite pair of real coordinates or dimensions."""
    if any(
        type(value) not in (int, float) or not math.isfinite(value)
        for value in values
    ):
        raise ValueError(f"{name} must contain two finite numbers")


@dataclass(frozen=True)
class WorldMap:
    """Expose one resolution-independent coordinate and collision model."""

    maze: MazeGrid

    def tile_center(self, tile: TileCoordinate) -> WorldPosition:
        """Return the world-space center of an in-bounds maze tile."""
        x, y = tile
        if (
            type(x) is not int
            or type(y) is not int
            or not self.maze.contains(tile)
        ):
            raise ValueError("tile must be an in-bounds integer coordinate")
        return x + 0.5, y + 0.5

    def world_to_tile(self, position: WorldPosition) -> TileCoordinate:
        """Return the tile containing a world-space position."""
        _validate_world_values(position, "world position")
        x, y = position
        return math.floor(x), math.floor(y)

    def contains_world(self, position: WorldPosition) -> bool:
        """Return whether a world-space point lies inside the maze bounds."""
        tile = self.world_to_tile(position)
        return self.maze.contains(tile)

    def is_walkable_tile(self, tile: TileCoordinate) -> bool:
        """Return whether a tile is in bounds and contains a corridor."""
        x, y = tile
        if type(x) is not int or type(y) is not int:
            return False
        return self.maze.contains(tile) and self.maze.is_corridor(tile)

    def is_walkable_world(self, position: WorldPosition) -> bool:
        """Return whether a world-space point lies on a corridor tile."""
        return self.is_walkable_tile(self.world_to_tile(position))

    def collides_with_wall(
        self,
        center: WorldPosition,
        half_size: WorldSize = (0.0, 0.0),
    ) -> bool:
        """Return whether an entity overlaps a wall or world boundary."""
        _validate_world_values(center, "entity center")
        _validate_world_values(half_size, "entity half-size")
        half_width, half_height = half_size
        if half_width < 0 or half_height < 0:
            raise ValueError("entity half-size cannot be negative")

        center_x, center_y = center
        left = center_x - half_width
        right = center_x + half_width
        top = center_y - half_height
        bottom = center_y + half_height

        left_tile = math.floor(left)
        right_tile = math.floor(
            center_x if half_width == 0 else math.nextafter(right, -math.inf)
        )
        top_tile = math.floor(top)
        bottom_tile = math.floor(
            center_y if half_height == 0 else math.nextafter(bottom, -math.inf)
        )

        return any(
            not self.is_walkable_tile((x, y))
            for y in range(top_tile, bottom_tile + 1)
            for x in range(left_tile, right_tile + 1)
        )

    def can_occupy(
        self,
        center: WorldPosition,
        half_size: WorldSize = (0.0, 0.0),
    ) -> bool:
        """Return whether an entity can occupy an area without a collision."""
        return not self.collides_with_wall(center, half_size)
