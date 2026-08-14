"""Tests for the assigned maze-generator adapter."""

from collections.abc import Callable
import random
from typing import cast

import pytest

from pacman.maze_adapter import (
    MazeAdapterError,
    MazeGenerationResult,
    MazeGeneratorAdapter,
)
from pacman.maze_grid import MazeGrid, Tile


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

    assert maze == MazeGrid(
        tiles=(
            (Tile.WALL,) * 5,
            (
                Tile.WALL,
                Tile.CORRIDOR,
                Tile.CORRIDOR,
                Tile.CORRIDOR,
                Tile.WALL,
            ),
            (
                Tile.WALL,
                Tile.CORRIDOR,
                Tile.WALL,
                Tile.CORRIDOR,
                Tile.WALL,
            ),
            (
                Tile.WALL,
                Tile.CORRIDOR,
                Tile.CORRIDOR,
                Tile.CORRIDOR,
                Tile.WALL,
            ),
            (Tile.WALL,) * 5,
        ),
        entry=(1, 1),
        exit=(3, 3),
    )


def test_adapter_result_does_not_share_mutable_package_data() -> None:
    """Verify external mutations cannot change the normalized grid."""
    source_grid = [[9, 3], [12, 6]]

    def factory(**arguments: object) -> FakeMazeGenerator:
        return FakeMazeGenerator(source_grid)

    maze = MazeGeneratorAdapter(factory).generate(2, 2)
    normalized_tiles = maze.tiles

    source_grid[0][0] = 0

    assert maze.tiles == normalized_tiles
    assert maze.tile_at((1, 1)) is Tile.CORRIDOR
    assert maze.width == 5
    assert maze.height == 5


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

    assert maze.width == 43
    assert maze.height == 43
    assert maze.entry == (1, 1)
    assert maze.exit == (41, 41)


def test_adapter_preserves_the_application_random_state() -> None:
    """Verify package seeding cannot alter Pacman's random stream."""
    random.seed(123)
    expected_value = random.random()
    random.seed(123)

    MazeGeneratorAdapter().generate(15, 15, seed=42)

    assert random.random() == expected_value


def test_safe_generation_returns_maze_without_error() -> None:
    """Verify callers receive a successful result without exceptions."""

    def factory(**arguments: object) -> FakeMazeGenerator:
        return FakeMazeGenerator([[9, 3], [12, 6]])

    result = MazeGeneratorAdapter(factory).generate_safely(
        2,
        2,
        seed=42,
    )

    assert result.succeeded
    assert result.maze is not None
    assert result.error_message is None


@pytest.mark.parametrize(
    ("width", "height", "expected_message"),
    [
        (0, 2, "width must be an integer of at least 2"),
        (2, 1, "height must be an integer of at least 2"),
        (True, 2, "width must be an integer of at least 2"),
    ],
)
def test_safe_generation_handles_invalid_dimensions(
    width: int,
    height: int,
    expected_message: str,
) -> None:
    """Verify invalid dimensions become clear failure results."""
    result = MazeGeneratorAdapter().generate_safely(width, height)

    assert not result.succeeded
    assert result.maze is None
    assert expected_message in str(result.error_message)


def test_safe_generation_handles_missing_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify a missing package produces a clear message without raising."""

    def fail_import(name: str) -> object:
        error = ModuleNotFoundError(
            "No module named 'mazegenerator'"
        )
        error.name = "mazegenerator"
        raise error

    monkeypatch.setattr(
        "pacman.maze_adapter.importlib.import_module",
        fail_import,
    )

    result = MazeGeneratorAdapter().generate_safely(2, 2)

    assert not result.succeeded
    assert result.error_message == (
        "The assigned mazegenerator package is not installed."
    )


def test_safe_generation_handles_package_dependency_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify internal package import failures get a distinct message."""

    def fail_import(name: str) -> object:
        error = ModuleNotFoundError(
            "No module named 'missing_dependency'"
        )
        error.name = "missing_dependency"
        raise error

    monkeypatch.setattr(
        "pacman.maze_adapter.importlib.import_module",
        fail_import,
    )

    result = MazeGeneratorAdapter().generate_safely(2, 2)

    assert not result.succeeded
    assert result.error_message == (
        "The assigned mazegenerator package could not be imported."
    )


def test_safe_generation_handles_generator_failure() -> None:
    """Verify package failures become messages instead of tracebacks."""

    def failing_factory(**arguments: object) -> FakeMazeGenerator:
        raise RuntimeError("external failure")

    result = MazeGeneratorAdapter(
        failing_factory
    ).generate_safely(2, 2)

    assert not result.succeeded
    assert result.error_message == (
        "The assigned package could not generate a maze."
    )


class IncompleteMazeGenerator:
    """Represent an unexpected package object with missing attributes."""


def test_safe_generation_handles_unexpected_result_object() -> None:
    """Verify missing result attributes cannot leak AttributeError."""

    def factory(**arguments: object) -> FakeMazeGenerator:
        return cast(
            FakeMazeGenerator,
            IncompleteMazeGenerator(),
        )

    result = MazeGeneratorAdapter(factory).generate_safely(2, 2)

    assert not result.succeeded
    assert result.error_message == (
        "Maze generator returned an unexpected number of rows."
    )


@pytest.mark.parametrize(
    ("grid", "expected_message"),
    [
        (
            [[8, 3], [12, 6]],
            "open outer boundary",
        ),
        (
            [[11, 3], [12, 6]],
            "inconsistent shared walls",
        ),
    ],
)
def test_safe_generation_rejects_invalid_wall_structure(
    grid: list[list[int]],
    expected_message: str,
) -> None:
    """Verify broken boundaries and mismatched walls are rejected."""

    def factory(**arguments: object) -> FakeMazeGenerator:
        return FakeMazeGenerator(grid)

    result = MazeGeneratorAdapter(factory).generate_safely(2, 2)

    assert not result.succeeded
    assert expected_message in str(result.error_message)


def test_safe_generation_rejects_unreachable_exit() -> None:
    """Verify a disconnected entry and exit are rejected before use."""

    def factory(**arguments: object) -> FakeMazeGenerator:
        return FakeMazeGenerator([[15, 15], [15, 15]])

    result = MazeGeneratorAdapter(factory).generate_safely(2, 2)

    assert not result.succeeded
    assert result.error_message == (
        "Maze generator returned a maze with no path from entry to exit."
    )


def test_generation_result_requires_one_outcome() -> None:
    """Verify an ambiguous safe result cannot be constructed."""
    with pytest.raises(ValueError, match="must contain"):
        MazeGenerationResult()


def test_safe_generation_handles_generic_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify generic import failures get a clear message."""

    def fail_import(name: str) -> object:
        raise ImportError("broken import inside mazegenerator")

    monkeypatch.setattr(
        "pacman.maze_adapter.importlib.import_module",
        fail_import,
    )

    result = MazeGeneratorAdapter().generate_safely(2, 2)

    assert not result.succeeded
    assert result.error_message == (
        "The assigned mazegenerator package could not be imported."
    )
