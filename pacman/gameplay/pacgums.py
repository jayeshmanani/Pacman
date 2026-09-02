"""Place and track normal pacgums and super-pacgums."""


from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from pacman.maze.grid import Coordinate, MazeGrid
from pacman.maze.spawns import SpawnPositions
from pacman.gameplay.power_state import PowerState
from pacman.gameplay.ghost import Ghost


class PacgumPlacementError(RuntimeError):
    """Report that a valid pacgum layout cannot be created."""


class PacgumKind(Enum):
    """Identify the type of pacgum consumed by the player."""

    NORMAL = "pacgum"
    SUPER = "super_pacgum"


@dataclass
class PacgumField:
    """Track remaining pacgums and the level-completion condition."""

    pacgums: set[Coordinate]
    super_pacgums: set[Coordinate]

    def __post_init__(self) -> None:
        """Require normal and super-pacgum positions to be disjoint."""
        if self.pacgums & self.super_pacgums:
            raise ValueError("normal and super-pacgums cannot overlap")

    @property
    def remaining_count(self) -> int:
        """Return the number of all uneaten pacgums."""
        return len(self.pacgums) + len(self.super_pacgums)

    @property
    def is_complete(self) -> bool:
        """Return whether every normal and super-pacgum was eaten."""
        return self.remaining_count == 0

    def consume(self, coordinate: Coordinate) -> PacgumKind | None:
        """Remove and identify the pacgum at a coordinate, if present."""
        if coordinate in self.pacgums:
            self.pacgums.remove(coordinate)
            return PacgumKind.NORMAL
        if coordinate in self.super_pacgums:
            self.super_pacgums.remove(coordinate)
            return PacgumKind.SUPER
        return None


def _reachable_corridors(
    maze: MazeGrid,
    start: Coordinate,
) -> set[Coordinate]:
    """Return all corridor tiles reachable from the player spawn."""
    if not maze.contains(start) or not maze.is_corridor(start):
        raise PacgumPlacementError(
            "Player spawn must be a walkable maze corridor."
        )

    reachable = {start}
    pending = [start]
    while pending:
        x, y = pending.pop()
        for neighbor in (
            (x, y - 1),
            (x + 1, y),
            (x, y + 1),
            (x - 1, y),
        ):
            if (
                neighbor not in reachable
                and maze.contains(neighbor)
                and maze.is_corridor(neighbor)
            ):
                reachable.add(neighbor)
                pending.append(neighbor)
    return reachable


def _closest_available(
    available: set[Coordinate],
    target: Coordinate,
) -> Coordinate:
    """Return the available coordinate nearest to a target corner."""
    if not available:
        raise PacgumPlacementError(
            "Maze does not contain enough corridors for four super-pacgums."
        )
    target_x, target_y = target
    return min(
        available,
        key=lambda coordinate: (
            (coordinate[0] - target_x) ** 2
            + (coordinate[1] - target_y) ** 2,
            coordinate[1],
            coordinate[0],
        ),
    )


def _select_evenly(
    candidates: set[Coordinate],
    count: int,
) -> set[Coordinate]:
    """Select a deterministic, evenly distributed subset of coordinates."""
    ordered = sorted(
        candidates,
        key=lambda coordinate: (coordinate[1], coordinate[0]),
    )
    if count >= len(ordered):
        return set(ordered)
    return {
        ordered[index * len(ordered) // count]
        for index in range(count)
    }


def place_pacgums(
    maze: MazeGrid,
    spawns: SpawnPositions,
    normal_count: int | None = None,
) -> PacgumField:
    """Place normal pacgums and four corner super-pacgums safely."""
    if normal_count is not None and (
        type(normal_count) is not int or normal_count < 0
    ):
        raise ValueError("normal_count must be a non-negative integer")

    excluded = {spawns.player, *spawns.ghosts.as_tuple()}
    available = _reachable_corridors(maze, spawns.player) - excluded
    corner_targets = (
        (0, 0),
        (maze.width - 1, 0),
        (0, maze.height - 1),
        (maze.width - 1, maze.height - 1),
    )

    super_pacgums: set[Coordinate] = set()
    for target in corner_targets:
        position = _closest_available(available, target)
        super_pacgums.add(position)
        available.remove(position)

    resolved_count = len(available) if normal_count is None else normal_count
    pacgums = _select_evenly(available, min(resolved_count, len(available)))
    return PacgumField(
        pacgums=pacgums,
        super_pacgums=super_pacgums,
    )


def collect_pacgum(
    player_position: tuple[float, float],
    field: PacgumField,
    points_per_pacgum: int = 10,
    points_per_super_pacgum: int = 50,
    power_state: PowerState | None = None,
    frightened_duration: float = 7.0,
    ghosts: Iterable[Ghost] = (),
) -> int:
    """Consume a normal pacgum at the player's tile position.

    Returns the score gained.
    """
    tile = (int(player_position[0]), int(player_position[1]))
    kind = field.consume(tile)
    if kind == PacgumKind.NORMAL:
        return points_per_pacgum
    if kind == PacgumKind.SUPER:
        if power_state is not None:
            power_state.activate(frightened_duration, ghosts)
        return points_per_super_pacgum
    return 0
