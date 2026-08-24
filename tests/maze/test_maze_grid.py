"""Maze tests for the stable internal grid."""

import pytest

from pacman.maze_grid import MazeGrid, Tile


def test_grid_exposes_dimensions_and_corridor_queries() -> None:
    """Verify game systems can query the grid without native bitmasks."""
    grid = MazeGrid(
        tiles=(
            (Tile.WALL, Tile.WALL, Tile.WALL),
            (Tile.WALL, Tile.CORRIDOR, Tile.WALL),
            (Tile.WALL, Tile.WALL, Tile.WALL),
        ),
        entry=(1, 1),
        exit=(1, 1),
    )

    assert grid.width == 3
    assert grid.height == 3
    assert grid.contains((1, 1))
    assert not grid.contains((3, 1))
    assert grid.tile_at((0, 0)) is Tile.WALL
    assert grid.is_corridor((1, 1))


def test_grid_rejects_non_rectangular_tiles() -> None:
    """Verify malformed internal grids fail immediately."""
    with pytest.raises(ValueError, match="rectangular"):
        MazeGrid(
            tiles=((Tile.CORRIDOR,), (Tile.CORRIDOR, Tile.WALL)),
            entry=(0, 0),
            exit=(0, 0),
        )


def test_grid_rejects_wall_endpoint() -> None:
    """Verify entry and exit always point to walkable corridors."""
    with pytest.raises(ValueError, match="entry must be a corridor"):
        MazeGrid(
            tiles=((Tile.WALL, Tile.CORRIDOR),),
            entry=(0, 0),
            exit=(1, 0),
        )


def test_tile_at_rejects_out_of_bounds_coordinate() -> None:
    """Verify invalid coordinates cannot wrap through Python indexing."""
    grid = MazeGrid(
        tiles=((Tile.CORRIDOR,),),
        entry=(0, 0),
        exit=(0, 0),
    )

    with pytest.raises(IndexError, match="outside"):
        grid.tile_at((-1, 0))
