"""Boundary between Pacman and the assigned maze generator package."""

import importlib
import random
from typing import Protocol, cast

from pacman.maze_grid import Coordinate, MazeGrid, Tile

_NORTH_WALL = 1
_EAST_WALL = 2
_SOUTH_WALL = 4
_WEST_WALL = 8


class MazeAdapterError(RuntimeError):
    """Report a failure at the external maze-generator boundary."""


class _ExternalMaze(Protocol):
    """Describe only the external result attributes used by the adapter."""

    maze: list[list[int]]
    maze_entry: Coordinate
    maze_exit: Coordinate


class _GeneratorFactory(Protocol):
    """Describe the constructor exposed by the assigned package."""

    def __call__(
        self,
        *,
        size: tuple[int, int],
        perfect: bool,
        entry_cell: Coordinate,
        exit_cell: Coordinate,
        seed: int,
    ) -> _ExternalMaze:
        """Create and return an external maze generator instance."""


def _skip_shortest_path(generator: object) -> None:
    """Skip the package's optional, slow shortest-path calculation."""


def _load_generator_factory() -> _GeneratorFactory:
    """Load the package's real class behind the adapter boundary."""
    try:
        module = importlib.import_module("mazegenerator.mazegenerator")
    except ImportError as error:
        raise MazeAdapterError(
            "The assigned mazegenerator package is not installed."
        ) from error

    generator_class = getattr(module, "MazeGenerator", None)
    if not isinstance(generator_class, type):
        raise MazeAdapterError(
            "The assigned package does not expose MazeGenerator."
        )

    # MazeGenerator calls _find_short_path() from its constructor. That
    # optional routine becomes extremely slow for configured maze sizes and
    # is not needed by Pacman. A local subclass keeps the wheel unchanged
    # while disabling only that optional calculation.
    pacman_generator_class = type(
        "_PacmanMazeGenerator",
        (generator_class,),
        {"_find_short_path": _skip_shortest_path},
    )
    return cast(_GeneratorFactory, pacman_generator_class)


def _validate_dimension(value: int, name: str) -> None:
    """Reject invalid dimensions before calling the external package."""
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _validate_native_grid(
    raw_grid: object,
    width: int,
    height: int,
) -> tuple[tuple[int, ...], ...]:
    """Validate and freeze the package's native wall-bitmask grid."""
    if not isinstance(raw_grid, list) or len(raw_grid) != height:
        raise MazeAdapterError(
            "Maze generator returned an unexpected number of rows."
        )

    frozen_rows: list[tuple[int, ...]] = []
    for row in raw_grid:
        if not isinstance(row, list) or len(row) != width:
            raise MazeAdapterError(
                "Maze generator returned an unexpected row width."
            )
        if any(type(cell) is not int or not 0 <= cell <= 15 for cell in row):
            raise MazeAdapterError(
                "Maze generator returned an invalid wall bitmask."
            )
        frozen_rows.append(tuple(row))

    return tuple(frozen_rows)


def _to_internal_coordinate(coordinate: Coordinate) -> Coordinate:
    """Convert one native logical-cell coordinate to an internal tile."""
    x, y = coordinate
    return 2 * x + 1, 2 * y + 1


def _normalize_grid(
    native_grid: tuple[tuple[int, ...], ...],
    entry: Coordinate,
    exit: Coordinate,
) -> MazeGrid:
    """Convert native wall bitmasks to stable wall/corridor tiles."""
    native_height = len(native_grid)
    native_width = len(native_grid[0])
    rows = [
        [Tile.WALL for _ in range(2 * native_width + 1)]
        for _ in range(2 * native_height + 1)
    ]

    for native_y, native_row in enumerate(native_grid):
        for native_x, walls in enumerate(native_row):
            tile_x = 2 * native_x + 1
            tile_y = 2 * native_y + 1
            rows[tile_y][tile_x] = Tile.CORRIDOR

            if walls & _NORTH_WALL == 0:
                rows[tile_y - 1][tile_x] = Tile.CORRIDOR
            if walls & _EAST_WALL == 0:
                rows[tile_y][tile_x + 1] = Tile.CORRIDOR
            if walls & _SOUTH_WALL == 0:
                rows[tile_y + 1][tile_x] = Tile.CORRIDOR
            if walls & _WEST_WALL == 0:
                rows[tile_y][tile_x - 1] = Tile.CORRIDOR

    return MazeGrid(
        tiles=tuple(tuple(row) for row in rows),
        entry=_to_internal_coordinate(entry),
        exit=_to_internal_coordinate(exit),
    )


def _validate_coordinate(
    value: object,
    name: str,
    width: int,
    height: int,
) -> Coordinate:
    """Validate a coordinate returned by the external package."""
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or any(type(part) is not int for part in value)
    ):
        raise MazeAdapterError(
            f"Maze generator returned an invalid {name} coordinate."
        )

    x, y = value
    if not 0 <= x < width or not 0 <= y < height:
        raise MazeAdapterError(
            f"Maze generator returned an out-of-range {name} coordinate."
        )
    return x, y


class MazeGeneratorAdapter:
    """Call A-Maze-ing without exposing its implementation to Pacman."""

    def __init__(
        self,
        generator_factory: _GeneratorFactory | None = None,
    ) -> None:
        """Allow a controlled generator factory to be supplied for tests."""
        self._generator_factory = generator_factory

    def generate(
        self,
        width: int,
        height: int,
        seed: int = 0,
        entry: Coordinate = (0, 0),
        exit: Coordinate = (-1, -1),
    ) -> MazeGrid:
        """Generate an imperfect maze in Pacman's internal grid format."""
        _validate_dimension(width, "width")
        _validate_dimension(height, "height")
        if type(seed) is not int:
            raise ValueError("seed must be an integer")

        factory = self._generator_factory or _load_generator_factory()
        random_state = random.getstate()
        try:
            generated = factory(
                size=(width, height),
                perfect=False,
                entry_cell=entry,
                exit_cell=exit,
                seed=seed,
            )
        except Exception as error:
            raise MazeAdapterError(
                "The assigned package could not generate a maze."
            ) from error
        finally:
            # The package calls random.seed() globally. Restore Pacman's
            # random stream so maze creation cannot alter later gameplay.
            random.setstate(random_state)

        native_grid = _validate_native_grid(generated.maze, width, height)
        validated_entry = _validate_coordinate(
            generated.maze_entry,
            "entry",
            width,
            height,
        )
        validated_exit = _validate_coordinate(
            generated.maze_exit,
            "exit",
            width,
            height,
        )
        return _normalize_grid(native_grid, validated_entry, validated_exit)
