"""Reusable controlled worlds and adapters for gameplay rule tests."""

from pacman.maze_adapter import MazeGeneratorAdapter
from pacman.maze_grid import MazeGrid, Tile
from pacman.world import WorldMap


class FixedMazeAdapter(MazeGeneratorAdapter):
    """Return the same open maze for deterministic level transitions."""

    def generate(
        self,
        width: int,
        height: int,
        seed: int = 0,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] = (-1, -1),
        include_42: bool = True,
    ) -> MazeGrid:
        """Return a compact corridor grid independent of package output."""
        rows = tuple(
            tuple(Tile.CORRIDOR for _ in range(7))
            for _ in range(7)
        )
        return MazeGrid(tiles=rows, entry=(0, 0), exit=(6, 6))


def corridor_world() -> WorldMap:
    """Return a corridor where the player can move one tile to the right."""
    wall = Tile.WALL
    corridor = Tile.CORRIDOR
    maze = MazeGrid(
        tiles=(
            (wall, wall, wall, wall),
            (wall, corridor, corridor, wall),
            (wall, wall, wall, wall),
        ),
        entry=(1, 1),
        exit=(2, 1),
    )
    return WorldMap(maze)


def blocked_world() -> WorldMap:
    """Return a world with a wall immediately right of the player spawn."""
    wall = Tile.WALL
    corridor = Tile.CORRIDOR
    maze = MazeGrid(
        tiles=(
            (wall, wall, wall),
            (wall, corridor, wall),
            (wall, wall, wall),
        ),
        entry=(1, 1),
        exit=(1, 1),
    )
    return WorldMap(maze)
