"""Tests for the assigned maze-generator adapter."""

from collections.abc import Callable
import random

import pytest

from pacman.maze_adapter import (
    GeneratedMaze,
    MazeAdapterError,
    MazeGeneratorAdapter,
)


class FakeMazeGenerator:
    """Small package-like result used to inspect adapter calls."""

    def __init__(self, grid: list[list[int]]) -> None:
        """Store valid raw maze data and boundary coordinates."""
        self.maze = grid
        self.maze_entry = (0, 0)
        self.maze_exit = (len(grid[0]) - 1, len(grid) - 1)


def test_adapter_calls_generator_with_perfect_false() -> None:
    """Verify the adapter always requests an imperfect maze."""
    calls: list[dict[str, object]] = []

    def factory(**arguments: object) -> FakeMazeGenerator:
        calls.append(arguments)
        return FakeMazeGenerator([[9, 3], [12, 6]])

    maze = MazeGeneratorAdapter(factory).generate(
        width=2,
        height=2,
        seed=42,
    )

    assert calls == [{
        "size": (2, 2),
        "perfect": False,
        "entry_cell": (0, 0),
        "exit_cell": (-1, -1),
        "seed": 42,
    }]
    assert maze == GeneratedMaze(
        grid=((9, 3), (12, 6)),
        entry=(0, 0),
        exit=(1, 1),
    )


def test_adapter_result_is_immutable() -> None:
    """Verify external mutable rows become immutable Pacman data."""
    source_grid = [[9, 3], [12, 6]]

    def factory(**arguments: object) -> FakeMazeGenerator:
        return FakeMazeGenerator(source_grid)

    maze = MazeGeneratorAdapter(factory).generate(2, 2)
    source_grid[0][0] = 0

    assert maze.grid == ((9, 3), (12, 6))
    assert maze.width == 2
    assert maze.height == 2


@pytest.mark.parametrize(
    "factory",
    [
        lambda **arguments: FakeMazeGenerator([[9, 3]]),
        lambda **arguments: FakeMazeGenerator([[16, 3], [12, 6]]),
    ],
)
def test_adapter_rejects_invalid_package_grid(
    factory: Callable[..., FakeMazeGenerator],
) -> None:
    """Verify malformed external grids do not enter the application."""
    with pytest.raises(MazeAdapterError):
        MazeGeneratorAdapter(factory).generate(2, 2)


def test_adapter_wraps_package_failure() -> None:
    """Verify external exceptions are translated at the boundary."""
    def failing_factory(**arguments: object) -> FakeMazeGenerator:
        raise RuntimeError("external implementation detail")

    with pytest.raises(
        MazeAdapterError,
        match="could not generate a maze",
    ):
        MazeGeneratorAdapter(failing_factory).generate(2, 2)


def test_adapter_uses_the_assigned_package() -> None:
    """Verify the bundled wheel generates configured maze dimensions."""
    maze = MazeGeneratorAdapter().generate(21, 21, seed=42)

    assert maze.width == 21
    assert maze.height == 21
    assert maze.entry == (0, 0)
    assert maze.exit == (20, 20)


def test_adapter_preserves_the_application_random_state() -> None:
    """Verify package seeding cannot alter Pacman's random stream."""
    random.seed(123)
    expected_value = random.random()
    random.seed(123)

    MazeGeneratorAdapter().generate(15, 15, seed=42)

    assert random.random() == expected_value
