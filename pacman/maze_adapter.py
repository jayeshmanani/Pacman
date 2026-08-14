"""Boundary between Pacman and the assigned maze generator package."""

from dataclasses import dataclass
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


@dataclass(frozen=True)
class MazeGenerationResult:
    """Return either a generated maze or a user-facing error message."""

    maze: MazeGrid | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Require exactly one success or failure value."""
        if (self.maze is None) == (self.error_message is None):
            raise ValueError(
                "maze generation result must contain a maze or an error"
            )

    @property
    def succeeded(self) -> bool:
        """Return whether maze generation completed successfully."""
        return self.maze is not None


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
    except ModuleNotFoundError as error:
        if (error.name or "").split(".")[0] == "mazegenerator":
            raise MazeAdapterError(
                "The assigned mazegenerator package is not installed."
            ) from error
        raise MazeAdapterError(
            "The assigned mazegenerator package could not be imported."
        ) from error
    except ImportError as error:
        raise MazeAdapterError(
            "The assigned mazegenerator package could not be imported."
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
    if type(value) is not int or value < 2:
        raise MazeAdapterError(
            f"Cannot generate maze: {name} must be an integer of at least 2."
        )


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

    frozen_grid = tuple(frozen_rows)
    _validate_wall_connections(frozen_grid)
    return frozen_grid


def _validate_wall_connections(
    native_grid: tuple[tuple[int, ...], ...],
) -> None:
    """Require closed boundaries and matching walls between cells."""
    height = len(native_grid)
    width = len(native_grid[0])

    for y, row in enumerate(native_grid):
        for x, walls in enumerate(row):
            if y == 0 and walls & _NORTH_WALL == 0:
                raise MazeAdapterError(
                    "Maze generator returned an open outer boundary."
                )
            if x == 0 and walls & _WEST_WALL == 0:
                raise MazeAdapterError(
                    "Maze generator returned an open outer boundary."
                )
            if y == height - 1 and walls & _SOUTH_WALL == 0:
                raise MazeAdapterError(
                    "Maze generator returned an open outer boundary."
                )
            if x == width - 1 and walls & _EAST_WALL == 0:
                raise MazeAdapterError(
                    "Maze generator returned an open outer boundary."
                )

            if x + 1 < width:
                east_wall = walls & _EAST_WALL != 0
                west_wall = row[x + 1] & _WEST_WALL != 0
                if east_wall != west_wall:
                    raise MazeAdapterError(
                        "Maze generator returned inconsistent shared walls."
                    )

            if y + 1 < height:
                south_wall = walls & _SOUTH_WALL != 0
                north_wall = native_grid[y + 1][x] & _NORTH_WALL != 0
                if south_wall != north_wall:
                    raise MazeAdapterError(
                        "Maze generator returned inconsistent shared walls."
                    )


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

    normalized_grid = MazeGrid(
        tiles=tuple(tuple(row) for row in rows),
        entry=_to_internal_coordinate(entry),
        exit=_to_internal_coordinate(exit),
    )
    _validate_exit_is_reachable(normalized_grid)
    return normalized_grid


def _validate_exit_is_reachable(grid: MazeGrid) -> None:
    """Require at least one corridor path from entry to exit."""
    pending = [grid.entry]
    visited = {grid.entry}

    while pending:
        x, y = pending.pop()
        if (x, y) == grid.exit:
            return

        for neighbor in (
            (x, y - 1),
            (x + 1, y),
            (x, y + 1),
            (x - 1, y),
        ):
            if (
                neighbor not in visited
                and grid.contains(neighbor)
                and grid.is_corridor(neighbor)
            ):
                visited.add(neighbor)
                pending.append(neighbor)

    raise MazeAdapterError(
        "Maze generator returned a maze with no path from entry to exit."
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
            raise MazeAdapterError(
                "Cannot generate maze: seed must be an integer."
            )

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

        native_grid = _validate_native_grid(
            getattr(generated, "maze", None),
            width,
            height,
        )
        validated_entry = _validate_coordinate(
            getattr(generated, "maze_entry", None),
            "entry",
            width,
            height,
        )
        validated_exit = _validate_coordinate(
            getattr(generated, "maze_exit", None),
            "exit",
            width,
            height,
        )
        try:
            return _normalize_grid(
                native_grid,
                validated_entry,
                validated_exit,
            )
        except (IndexError, TypeError, ValueError) as error:
            raise MazeAdapterError(
                "Maze generator returned data that could not be used."
            ) from error

    def generate_safely(
        self,
        width: int,
        height: int,
        seed: int = 0,
        entry: Coordinate = (0, 0),
        exit: Coordinate = (-1, -1),
    ) -> MazeGenerationResult:
        """Generate a maze without exposing an exception or traceback."""
        try:
            maze = self.generate(width, height, seed, entry, exit)
        except MazeAdapterError as error:
            return MazeGenerationResult(error_message=str(error))
        except Exception:
            return MazeGenerationResult(
                error_message=(
                    "Maze generation failed because the package returned "
                    "unexpected data."
                )
            )
        return MazeGenerationResult(maze=maze)
