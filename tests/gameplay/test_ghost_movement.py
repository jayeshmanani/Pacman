"""Tests for ghost movement and legal direction query logic."""

from pacman.ghost import get_legal_ghost_directions
from pacman.maze_grid import MazeGrid, Tile, TileCoordinate
from pacman.player import Direction
from pacman.world import WorldMap


def create_test_world(grid_pattern: list[str]) -> WorldMap:
    """Create a WorldMap from a string grid pattern."""
    rows: list[tuple[Tile, ...]] = []
    first_corridor: TileCoordinate | None = None
    last_corridor: TileCoordinate | None = None

    for r_idx, line in enumerate(grid_pattern):
        row_tiles: list[Tile] = []
        for c_idx, char in enumerate(line):
            if char == "#":
                row_tiles.append(Tile.WALL)
            else:
                row_tiles.append(Tile.CORRIDOR)
                coord = (c_idx, r_idx)
                if first_corridor is None:
                    first_corridor = coord
                last_corridor = coord
        rows.append(tuple(row_tiles))

    entry = first_corridor if first_corridor is not None else (0, 0)
    exit_tile = last_corridor if last_corridor is not None else (0, 0)
    grid = MazeGrid(tiles=tuple(rows), entry=entry, exit=exit_tile)
    return WorldMap(maze=grid)


def test_get_legal_ghost_directions_corridor_intersections() -> None:
    """Verify open directions returned at a 4-way intersection."""
    pattern = [
        "#####",
        "#...#",
        "#...#",
        "#...#",
        "#####",
    ]
    world = create_test_world(pattern)
    directions = get_legal_ghost_directions(
        tile=(2, 2),
        current_direction=Direction.RIGHT,
        world=world,
    )
    assert set(directions) == {Direction.UP, Direction.DOWN, Direction.RIGHT}


def test_get_legal_ghost_directions_dead_end_reversal() -> None:
    """Verify ghost reverses 180 degrees when stuck in a dead end."""
    pattern = [
        "#####",
        "#####",
        "#..##",  # (1, 2) is dead end, (2, 2) is open corridor to right
        "#####",
        "#####",
    ]
    world = create_test_world(pattern)
    directions = get_legal_ghost_directions(
        tile=(1, 2),
        current_direction=Direction.LEFT,
        world=world,
    )
    assert directions == [Direction.RIGHT]


def test_get_legal_ghost_directions_allow_explicit_reversal() -> None:
    """Verify allow_reversal=True allows turning 180 degrees."""
    pattern = [
        "#####",
        "#...#",
        "#...#",
        "#...#",
        "#####",
    ]
    world = create_test_world(pattern)
    directions = get_legal_ghost_directions(
        tile=(2, 2),
        current_direction=Direction.RIGHT,
        world=world,
        allow_reversal=True,
    )
    assert set(directions) == {
        Direction.UP,
        Direction.DOWN,
        Direction.LEFT,
        Direction.RIGHT,
    }


def test_get_legal_ghost_directions_surrounded_by_walls() -> None:
    """Verify returning NONE when no walkable corridor exists."""
    pattern = [
        "###",
        "#.#",
        "###",
    ]
    world = create_test_world(pattern)
    directions = get_legal_ghost_directions(
        tile=(0, 0),
        current_direction=Direction.RIGHT,
        world=world,
    )
    assert directions == [Direction.NONE]
