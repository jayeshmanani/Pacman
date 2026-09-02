"""Gameplay tests for pacgum placement and consumption."""

import pytest

from pacman.infrastructure.config import GameConfig
from pacman.maze.level_generator import LevelGenerator
from pacman.maze.grid import Coordinate, MazeGrid, Tile
from pacman.gameplay.pacgums import (
    PacgumField,
    PacgumKind,
    PacgumPlacementError,
    place_pacgums,
    collect_pacgum,
)
from pacman.maze.spawns import GhostSpawns, SpawnPositions
from pacman.gameplay.power_state import PowerState


def _open_grid(
    width: int = 7,
    height: int = 7,
    walls: set[Coordinate] | None = None,
) -> MazeGrid:
    """Create a connected test grid with optional wall tiles."""
    wall_positions = walls or set()
    rows = tuple(
        tuple(
            Tile.WALL if (x, y) in wall_positions else Tile.CORRIDOR
            for x in range(width)
        )
        for y in range(height)
    )
    return MazeGrid(tiles=rows, entry=(0, 0), exit=(width - 1, height - 1))


def _spawns() -> SpawnPositions:
    """Return distinct player and ghost spawn coordinates for tests."""
    return SpawnPositions(
        player=(3, 3),
        ghosts=GhostSpawns(
            top_left=(0, 0),
            top_right=(6, 0),
            bottom_left=(0, 6),
            bottom_right=(6, 6),
        ),
    )


def test_placement_uses_only_corridors_and_excludes_spawns() -> None:
    """Verify no normal or super-pacgum occupies a wall or spawn tile."""
    maze = _open_grid(walls={(2, 2), (4, 4)})
    spawns = _spawns()

    field = place_pacgums(maze, spawns, normal_count=20)

    all_pacgums = field.pacgums | field.super_pacgums
    excluded = {spawns.player, *spawns.ghosts.as_tuple()}
    assert len(field.pacgums) == 20
    assert len(field.super_pacgums) == 4
    assert all_pacgums.isdisjoint(excluded)
    assert all(maze.is_corridor(position) for position in all_pacgums)


def test_super_pacgums_are_near_four_corners() -> None:
    """Verify one unique super-pacgum is placed by each corner."""
    field = place_pacgums(_open_grid(), _spawns(), normal_count=0)

    assert field.super_pacgums == {
        (1, 0),
        (5, 0),
        (0, 5),
        (6, 5),
    }


def test_default_placement_fills_all_remaining_reachable_corridors() -> None:
    """Verify default placement covers every eligible corridor tile."""
    maze = _open_grid()
    spawns = _spawns()

    field = place_pacgums(maze, spawns)

    excluded_count = 5
    assert field.remaining_count == maze.width * maze.height - excluded_count
    assert len(field.super_pacgums) == 4


def test_unreachable_corridors_do_not_receive_pacgums() -> None:
    """Verify unreachable pockets cannot prevent level completion."""
    walls = {(3, y) for y in range(7)}
    maze = _open_grid(walls=walls)
    spawns = SpawnPositions(
        player=(1, 3),
        ghosts=GhostSpawns(
            top_left=(0, 0),
            top_right=(2, 0),
            bottom_left=(0, 6),
            bottom_right=(2, 6),
        ),
    )

    field = place_pacgums(maze, spawns)

    assert all(position[0] < 3 for position in field.pacgums)
    assert all(position[0] < 3 for position in field.super_pacgums)


def test_consumption_exposes_clear_completion_condition() -> None:
    """Verify consuming every pellet marks the level complete."""
    field = PacgumField(
        pacgums={(1, 1)},
        super_pacgums={(2, 2)},
    )

    assert field.remaining_count == 2
    assert not field.is_complete
    assert field.consume((1, 1)) is PacgumKind.NORMAL
    assert field.consume((1, 1)) is None
    assert field.consume((2, 2)) is PacgumKind.SUPER
    assert field.remaining_count == 0
    assert field.is_complete


def test_placement_requires_space_for_four_super_pacgums() -> None:
    """Verify an undersized reachable area fails with a clear message."""
    maze = _open_grid(width=3, height=3, walls={(1, 0)})
    spawns = SpawnPositions(
        player=(1, 1),
        ghosts=GhostSpawns(
            top_left=(0, 0),
            top_right=(2, 0),
            bottom_left=(0, 2),
            bottom_right=(2, 2),
        ),
    )

    with pytest.raises(PacgumPlacementError, match="four super-pacgums"):
        place_pacgums(maze, spawns)


def test_level_generator_fills_all_eligible_corridors() -> None:
    """Verify generated levels fill every eligible reachable corridor."""
    generator = LevelGenerator(config=GameConfig(seed=42))

    level = generator.generate_level(0)

    assert level.spawns is not None
    assert level.pellets is not None
    spawn_positions = {
        level.spawns.player,
        *level.spawns.ghosts.as_tuple(),
    }
    eligible_corridors = {
        (x, y)
        for y in range(level.maze.height)
        for x in range(level.maze.width)
        if level.maze.is_corridor((x, y))
    } - spawn_positions
    placed_pacgums = (
        level.pellets.pacgums | level.pellets.super_pacgums
    )
    assert placed_pacgums == eligible_corridors
    assert len(level.pellets.super_pacgums) == 4
    assert not level.pellets.is_complete


def test_collect_pacgum_returns_configured_points_once() -> None:
    """Verify normal pacgums award score once and disappear."""
    field = PacgumField(
        pacgums={(1, 1)},
        super_pacgums=set(),
    )
    player_pos = (1.75, 1.25)  # Maps to tile (1, 1)

    # First collection awards points
    gained = collect_pacgum(player_pos, field, points_per_pacgum=10)
    assert gained == 10
    assert (1, 1) not in field.pacgums

    # Second collection on same spot awards 0 points
    gained_again = collect_pacgum(player_pos, field, points_per_pacgum=10)
    assert gained_again == 0


def test_collect_pacgum_on_empty_tile_returns_zero() -> None:
    """Verify collecting on a tile without pacgum returns 0."""
    field = PacgumField(
        pacgums={(1, 1)},
        super_pacgums=set(),
    )
    empty_pos = (2.5, 2.5)  # Tile (2, 2) has no pacgum

    gained = collect_pacgum(empty_pos, field, points_per_pacgum=10)
    assert gained == 0
    assert field.remaining_count == 1


def test_collect_super_pacgum_activates_power_state() -> None:
    """Verify super-pacgums award super points and activate power mode."""
    field = PacgumField(
        pacgums=set(),
        super_pacgums={(2, 2)},
    )
    power_state = PowerState()
    player_pos = (2.4, 2.6)  # Maps to tile (2, 2)
    gained = collect_pacgum(
        player_pos,
        field,
        points_per_super_pacgum=50,
        power_state=power_state,
        frightened_duration=7.0,
    )
    assert gained == 50
    assert (2, 2) not in field.super_pacgums
    assert power_state.is_active
    assert power_state.remaining_time == 7.0


def test_collect_super_pacgum_frightens_all_active_ghosts() -> None:
    """Verify one collection synchronizes all eligible active ghosts."""
    from pacman.gameplay.ghost import Ghost, GhostIdentity, GhostState

    field = PacgumField(pacgums=set(), super_pacgums={(2, 2)})
    ghosts = [
        Ghost.from_spawn(GhostIdentity.BLINKY, (1, 1)),
        Ghost.from_spawn(GhostIdentity.PINKY, (3, 1)),
    ]
    power_state = PowerState()

    collect_pacgum(
        (2.5, 2.5),
        field,
        power_state=power_state,
        frightened_duration=4.5,
        ghosts=ghosts,
    )

    assert all(ghost.state == GhostState.FRIGHTENED for ghost in ghosts)
    assert all(ghost.frightened_timer == 4.5 for ghost in ghosts)


def test_collect_super_pacgum_without_power_state_object() -> None:
    """Verify super-pacgum collection works when power_state is None."""
    field = PacgumField(
        pacgums=set(),
        super_pacgums={(2, 2)},
    )
    gained = collect_pacgum((2.1, 2.1), field, points_per_super_pacgum=50)
    assert gained == 50
    assert (2, 2) not in field.super_pacgums
