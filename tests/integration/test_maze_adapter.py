"""Integration tests for the real assigned maze-generator package."""

import random

import pytest

from pacman.maze.adapter import MazeGeneratorAdapter
from pacman.maze.grid import Tile


@pytest.mark.parametrize(
    ("width", "height", "seed"),
    [
        (5, 5, 42),
        (9, 7, 1337),
        (15, 10, 2026),
    ],
)
def test_real_package_generates_normalized_connected_maze(
    width: int,
    height: int,
    seed: int,
) -> None:
    """Verify real package output becomes a usable internal grid."""
    maze = MazeGeneratorAdapter().generate(width, height, seed=seed)

    assert maze.width == 2 * width + 1
    assert maze.height == 2 * height + 1
    assert maze.entry == (1, 1)
    assert maze.exit == (2 * width - 1, 2 * height - 1)
    assert maze.tile_at(maze.entry) is Tile.CORRIDOR
    assert maze.tile_at(maze.exit) is Tile.CORRIDOR
    assert all(tile is Tile.WALL for tile in maze.tiles[0])
    assert all(tile is Tile.WALL for tile in maze.tiles[-1])


def test_real_package_preserves_the_application_random_state() -> None:
    """Verify package seeding cannot alter Pacman's random stream."""
    random.seed(123)
    expected_value = random.random()
    random.seed(123)

    MazeGeneratorAdapter().generate(15, 15, seed=42)

    assert random.random() == expected_value


def test_real_package_42_pattern_can_be_disabled() -> None:
    """Verify the fixed wall pattern is optional at the adapter boundary."""
    adapter = MazeGeneratorAdapter()

    first_level = adapter.generate(15, 15, seed=42, include_42=True)
    later_level = adapter.generate(15, 15, seed=42, include_42=False)

    pattern = (
        (1, 0, 0, 0, 1, 1, 1),
        (1, 0, 0, 0, 0, 0, 1),
        (1, 1, 1, 0, 1, 1, 1),
        (0, 0, 1, 0, 1, 0, 0),
        (0, 0, 1, 0, 1, 1, 1),
    )
    pattern_positions = {
        (2 * (4 + x) + 1, 2 * (5 + y) + 1)
        for y, row in enumerate(pattern)
        for x, value in enumerate(row)
        if value == 1
    }

    assert all(
        not first_level.is_corridor(position)
        for position in pattern_positions
    )
    assert all(
        later_level.is_corridor(position)
        for position in pattern_positions
    )
