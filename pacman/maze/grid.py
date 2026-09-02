"""Stable internal maze representation used by Pacman systems."""


from dataclasses import dataclass
from enum import IntEnum

TileCoordinate = tuple[int, int]
Coordinate = TileCoordinate


class Tile(IntEnum):
    """Describe one tile in the internal game grid."""

    CORRIDOR = 0
    WALL = 1


@dataclass(frozen=True)
class MazeGrid:
    """Immutable grid of walls and walkable corridors."""

    tiles: tuple[tuple[Tile, ...], ...]
    entry: Coordinate
    exit: Coordinate

    def __post_init__(self) -> None:
        """Require a non-empty rectangular grid and walkable endpoints."""
        if not self.tiles or not self.tiles[0]:
            raise ValueError("maze grid cannot be empty")

        width = len(self.tiles[0])
        if any(len(row) != width for row in self.tiles):
            raise ValueError("maze grid must be rectangular")

        for name, coordinate in (("entry", self.entry), ("exit", self.exit)):
            if not self.contains(coordinate):
                raise ValueError(f"maze {name} must be inside the grid")
            if not self.is_corridor(coordinate):
                raise ValueError(f"maze {name} must be a corridor")

    @property
    def width(self) -> int:
        """Return the number of internal tiles in one row."""
        return len(self.tiles[0])

    @property
    def height(self) -> int:
        """Return the number of internal tile rows."""
        return len(self.tiles)

    def contains(self, coordinate: Coordinate) -> bool:
        """Return whether a coordinate is inside the grid."""
        x, y = coordinate
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, coordinate: Coordinate) -> Tile:
        """Return the tile at an in-bounds coordinate."""
        x, y = coordinate
        if not self.contains(coordinate):
            raise IndexError("maze coordinate is outside the grid")
        return self.tiles[y][x]

    def is_corridor(self, coordinate: Coordinate) -> bool:
        """Return whether an in-bounds coordinate is walkable."""
        return self.tile_at(coordinate) is Tile.CORRIDOR
