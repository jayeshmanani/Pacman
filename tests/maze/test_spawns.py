"""Maze tests for player and ghost spawn positions."""

import pytest

from pacman.infrastructure.config import GameConfig
from pacman.maze.level_generator import LevelData, LevelGenerator
from pacman.maze.adapter import MazeGeneratorAdapter
from pacman.maze.grid import Coordinate, MazeGrid, Tile
from pacman.maze.spawns import (
    GhostSpawns,
    SpawnPositions,
    find_closest_walkable_tile,
    find_ghost_spawns,
    find_player_spawn,
    find_spawn_positions,
)


def _make_grid_with_corridors(
    corridors: set[Coordinate],
    width: int = 5,
    height: int = 5,
) -> MazeGrid:
    """Create a test MazeGrid with specified corridor coordinates."""
    rows = [
        [
            Tile.CORRIDOR if (x, y) in corridors else Tile.WALL
            for x in range(width)
        ]
        for y in range(height)
    ]
    # Pick first available corridor for entry/exit
    sorted_corridors = sorted(corridors)
    entry = sorted_corridors[0]
    exit_coord = sorted_corridors[-1]
    return MazeGrid(
        tiles=tuple(tuple(r) for r in rows),
        entry=entry,
        exit=exit_coord,
    )


def test_player_spawn_near_center() -> None:
    """Verify player spawn selects the walkable tile closest to center."""
    # 5x5 grid: center is (2, 2). Place corridors at (2, 2) and (0, 0).
    grid = _make_grid_with_corridors({(0, 0), (2, 2)})
    player_spawn = find_player_spawn(grid)
    assert player_spawn == (2, 2)
    assert grid.is_corridor(player_spawn)


def test_player_spawn_when_center_is_wall() -> None:
    """Verify player spawn finds closest corridor when center is a wall."""
    # 5x5 grid: center is (2, 2) which is a wall. Corridor at (2, 1).
    grid = _make_grid_with_corridors({(0, 0), (2, 1), (4, 4)})
    player_spawn = find_player_spawn(grid)
    assert player_spawn == (2, 1)
    assert grid.is_corridor(player_spawn)


def test_ghost_spawns_in_four_corners() -> None:
    """Verify ghost spawns match the 4 corner corridors."""
    # 5x5 grid: corners at (1, 1), (3, 1), (1, 3), (3, 3)
    corridors = {(1, 1), (3, 1), (1, 3), (3, 3), (2, 2)}
    grid = _make_grid_with_corridors(corridors, width=5, height=5)

    ghosts = find_ghost_spawns(grid)

    assert ghosts.top_left == (1, 1)
    assert ghosts.top_right == (3, 1)
    assert ghosts.bottom_left == (1, 3)
    assert ghosts.bottom_right == (3, 3)

    for coord in (
        ghosts.top_left,
        ghosts.top_right,
        ghosts.bottom_left,
        ghosts.bottom_right,
    ):
        assert grid.is_corridor(coord)


def test_ghost_spawns_helpers() -> None:
    """Verify GhostSpawns helper methods as_tuple and as_list."""
    spawns = GhostSpawns(
        top_left=(1, 1),
        top_right=(5, 1),
        bottom_left=(1, 5),
        bottom_right=(5, 5),
    )
    assert spawns.as_tuple() == ((1, 1), (5, 1), (1, 5), (5, 5))
    assert spawns.as_list() == [(1, 1), (5, 1), (1, 5), (5, 5)]


def test_no_entity_spawns_inside_a_wall() -> None:
    """Verify all 5 entities spawn exclusively on walkable corridor tiles."""
    adapter = MazeGeneratorAdapter()
    maze = adapter.generate(width=5, height=5, seed=42)

    spawns = find_spawn_positions(maze)

    assert maze.is_corridor(spawns.player)
    assert maze.tile_at(spawns.player) == Tile.CORRIDOR

    for ghost_coord in spawns.ghosts.as_list():
        assert maze.is_corridor(ghost_coord)
        assert maze.tile_at(ghost_coord) == Tile.CORRIDOR


def test_find_closest_walkable_tile_raises_on_empty_corridors() -> None:
    """Verify finding walkable tile raises error when no corridors exist."""
    # Build invalid mock grid without corridors
    rows = ((Tile.WALL, Tile.WALL), (Tile.WALL, Tile.WALL))
    # MazeGrid requires entry/exit corridors so bypass validation for test
    mock_grid = object.__new__(MazeGrid)
    object.__setattr__(mock_grid, "tiles", rows)

    with pytest.raises(ValueError, match="no walkable corridors"):
        find_closest_walkable_tile(mock_grid, (0.0, 0.0))


def test_find_spawn_positions_combines_player_and_ghosts() -> None:
    """Verify find_spawn_positions returns a complete SpawnPositions object."""
    grid = _make_grid_with_corridors({(0, 0), (4, 0), (0, 4), (4, 4), (2, 2)})
    spawns = find_spawn_positions(grid)

    assert isinstance(spawns, SpawnPositions)
    assert spawns.player == (2, 2)
    assert spawns.ghosts.top_left == (0, 0)
    assert spawns.ghosts.top_right == (4, 0)
    assert spawns.ghosts.bottom_left == (0, 4)
    assert spawns.ghosts.bottom_right == (4, 4)


def test_level_data_auto_populates_spawns() -> None:
    """Verify LevelData automatically calculates spawns when not provided."""
    grid = _make_grid_with_corridors({(0, 0), (4, 0), (0, 4), (4, 4), (2, 2)})
    level = LevelData(level_number=1, maze=grid, seed=42)

    assert level.spawns is not None
    assert level.spawns.player == (2, 2)
    assert level.spawns.ghosts.top_left == (0, 0)


def test_level_generator_populates_valid_spawns() -> None:
    """Verify LevelGenerator produces LevelData with valid spawn positions."""
    config = GameConfig(seed=42)
    generator = LevelGenerator(config=config)

    level = generator.generate_level(0)

    assert level.spawns is not None
    assert level.maze.is_corridor(level.spawns.player)
    for ghost_pos in level.spawns.ghosts.as_list():
        assert level.maze.is_corridor(ghost_pos)
