"""Unit tests for frightened ghost fleeing and direction selection."""

import random

from pacman.gameplay.ghost import (
    select_frightened_direction,
)
from pacman.gameplay.player import Direction
from pacman.maze.world import WorldMap


def test_select_frightened_direction_empty_or_none() -> None:
    """Verify empty or NONE direction lists return Direction.NONE."""
    assert select_frightened_direction((2, 2), (5, 5), []) == Direction.NONE
    assert (
        select_frightened_direction((2, 2), (5, 5), [Direction.NONE])
        == Direction.NONE
    )


def test_select_frightened_direction_single_legal() -> None:
    """Verify single legal option is returned directly."""
    chosen = select_frightened_direction(
        current_tile=(2, 2),
        player_tile=(10, 2),
        legal_directions=[Direction.LEFT],
    )
    assert chosen == Direction.LEFT


def test_select_frightened_direction_maximizes_distance() -> None:
    """Verify ghost chooses direction moving furthest away from player."""
    # Ghost at (5, 5), Player at (7, 5) (Player is to the right)
    # Options: LEFT (4, 5) -> dist_sq = (4-7)^2 = 9
    #          RIGHT (6, 5) -> dist_sq = (6-7)^2 = 1
    #          UP (5, 4) -> dist_sq = (5-7)^2 + (4-5)^2 = 4 + 1 = 5
    # Furthest option is LEFT (dist_sq = 9)
    chosen = select_frightened_direction(
        current_tile=(5, 5),
        player_tile=(7, 5),
        legal_directions=[Direction.LEFT, Direction.RIGHT, Direction.UP],
    )
    assert chosen == Direction.LEFT


def test_select_frightened_direction_tiebreaker() -> None:
    """Verify tiebreaking priority order UP > LEFT > DOWN > RIGHT."""
    # Ghost at (5, 5), Player at (6, 6) (Pacman diagonally down-right)
    # UP   (5, 4): dist_sq = (5 - 6)^2 + (4 - 6)^2 = 1 + 4 = 5
    # LEFT (4, 5): dist_sq = (4 - 6)^2 + (5 - 6)^2 = 4 + 1 = 5
    # Both directions are equally far from Pacman (dist_sq = 5).
    # Priority order UP > LEFT chooses UP.
    chosen = select_frightened_direction(
        current_tile=(5, 5),
        player_tile=(6, 6),
        legal_directions=[Direction.LEFT, Direction.UP],
    )
    assert chosen == Direction.UP


def test_select_frightened_direction_with_rng() -> None:
    """Verify RNG is used for tie-breaking when provided."""
    # Ghost at (5, 5), Player at (6, 6)
    # Both UP (5, 4) and LEFT (4, 5) have dist_sq = 5
    rng = random.Random(42)
    chosen = select_frightened_direction(
        current_tile=(5, 5),
        player_tile=(6, 6),
        legal_directions=[
            Direction.UP,
            Direction.LEFT,
            Direction.DOWN,
            Direction.RIGHT,
        ],
        rng=rng,
    )
    # Furthest candidates are UP and LEFT (dist_sq = 5 vs 1 for DOWN/RIGHT)
    assert chosen in [Direction.UP, Direction.LEFT]


def test_direction_opposite_property() -> None:
    """Verify opposite property for all cardinal directions and NONE."""
    assert Direction.UP.opposite == Direction.DOWN
    assert Direction.DOWN.opposite == Direction.UP
    assert Direction.LEFT.opposite == Direction.RIGHT
    assert Direction.RIGHT.opposite == Direction.LEFT
    assert Direction.NONE.opposite == Direction.NONE


def test_ghost_frighten_reverses_direction() -> None:
    """Verify ghost immediately reverses direction when frightened."""
    from pacman.gameplay.ghost import Ghost, GhostIdentity

    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, (2, 2))
    ghost.direction = Direction.RIGHT

    assert ghost.frighten(duration=5.0) is True
    assert ghost.direction == Direction.LEFT

    # Reversing when moving UP turns DOWN
    ghost.direction = Direction.UP
    assert ghost.frighten(duration=5.0) is True
    assert ghost.direction == Direction.DOWN

    # If reverse_direction=False, direction is preserved
    assert ghost.frighten(duration=5.0, reverse_direction=False) is True
    assert ghost.direction == Direction.DOWN


def _create_test_world(grid_pattern: list[str]) -> WorldMap:
    """Create a WorldMap from a string grid pattern."""
    from pacman.maze.grid import MazeGrid, Tile, TileCoordinate

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


def test_frightened_ghost_movement_flees_from_player() -> None:
    """Verify frightened ghost turns away from player at intersection."""
    from pacman.gameplay.ghost import Ghost, GhostIdentity

    # Maze with 4-way intersection at (2, 2)
    pattern = [
        "#####",
        "#...#",
        "#...#",
        "#...#",
        "#####",
    ]
    world = _create_test_world(pattern)
    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, spawn_tile=(2, 2))
    ghost.direction = Direction.RIGHT
    ghost.frighten(duration=10.0, reverse_direction=False)

    # Player is at bottom right (3.5, 3.5)
    # Available from (2, 2) going RIGHT: UP (2, 1), DOWN (2, 3), RIGHT (3, 2)
    # Distances to player at (3, 3):
    # UP (2, 1) -> (2-3)^2 + (1-3)^2 = 1 + 4 = 5 (furthest)
    # DOWN (2, 3) -> (2-3)^2 + (3-3)^2 = 1 + 0 = 1
    # RIGHT (3, 2) -> (3-3)^2 + (2-3)^2 = 0 + 1 = 1
    ghost.update(
        dt=0.1,
        world=world,
        base_speed=4.0,
        player_position=(3.5, 3.5),
        player_direction=Direction.RIGHT,
    )
    assert ghost.direction == Direction.UP


def test_frightened_ghost_moves_at_reduced_speed() -> None:
    """Verify frightened ghost moves at half speed compared to normal."""
    from pacman.gameplay.ghost import Ghost, GhostIdentity, GhostState

    pattern = [
        "#######",
        "#.....#",
        "#######",
    ]
    world = _create_test_world(pattern)

    # Normal ghost
    normal_ghost = Ghost.from_spawn(GhostIdentity.BLINKY, spawn_tile=(1, 1))
    normal_ghost.direction = Direction.RIGHT
    normal_ghost.state = GhostState.NORMAL
    normal_ghost.update(
        dt=1.0,
        world=world,
        base_speed=2.0,
        player_position=(5.5, 1.5),
    )

    # Frightened ghost
    frightened_ghost = Ghost.from_spawn(
        GhostIdentity.BLINKY, spawn_tile=(1, 1)
    )
    frightened_ghost.direction = Direction.RIGHT
    frightened_ghost.frighten(duration=10.0, reverse_direction=False)
    frightened_ghost.update(
        dt=1.0,
        world=world,
        base_speed=2.0,
        player_position=(5.5, 1.5),
    )

    # Normal moves 2.0 * 1.0 = 2.0 units -> from 1.5 to 3.5
    # Frightened moves 2.0 * 0.5 * 1.0 = 1.0 units -> from 1.5 to 2.5
    assert abs(normal_ghost.position[0] - 3.5) < 1e-3
    assert abs(frightened_ghost.position[0] - 2.5) < 1e-3


def test_frightened_ghost_recovers_at_dead_end() -> None:
    """Verify frightened ghost turns around when encountering a dead end."""
    from pacman.gameplay.ghost import Ghost, GhostIdentity

    pattern = [
        "#####",
        "#####",
        "#..##",  # (1, 2) is dead end, (2, 2) is corridor to right
        "#####",
        "#####",
    ]
    world = _create_test_world(pattern)
    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, spawn_tile=(1, 2))
    ghost.direction = Direction.LEFT
    ghost.frighten(duration=10.0, reverse_direction=False)

    # Player is at (3.5, 2.5) (to the right)
    # Ghost is moving LEFT into wall at (1, 2), dead end forces turn to RIGHT
    ghost.update(
        dt=0.1,
        world=world,
        base_speed=4.0,
        player_position=(3.5, 2.5),
    )
    assert ghost.direction == Direction.RIGHT


def test_frightened_state_expiration_resumes_normal_chase() -> None:
    """Verify ghost transitions to NORMAL on timer expiry and resumes chase."""
    from pacman.gameplay.ghost import Ghost, GhostIdentity, GhostState

    pattern = [
        "#####",
        "#...#",
        "#...#",
        "#...#",
        "#####",
    ]
    world = _create_test_world(pattern)
    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, spawn_tile=(2, 2))
    ghost.direction = Direction.RIGHT
    ghost.frighten(duration=1.0, reverse_direction=False)

    # First update: timer reduces from 1.0 to 0.5, state is still FRIGHTENED
    ghost.update(
        dt=0.5,
        world=world,
        base_speed=4.0,
        player_position=(3.5, 3.5),
    )
    state_during_frightened = ghost.state
    assert state_during_frightened == GhostState.FRIGHTENED
    assert ghost.target_tile is None

    # Second update: timer elapses by 0.6 (> 0.5), state reverts to NORMAL
    ghost.update(
        dt=0.6,
        world=world,
        base_speed=4.0,
        player_position=(3.5, 3.5),
    )
    state_after_expiry = ghost.state
    assert state_after_expiry == GhostState.NORMAL
    # In NORMAL state, Blinky directly targets Pacman's tile (3, 3)
    assert ghost.target_tile == (3, 3)


def test_multi_ghost_group_frightened_update() -> None:
    """Verify group of 4 ghosts all update positions when frightened."""
    from pacman.gameplay.ghost import create_ghost_group
    from pacman.maze.spawns import GhostSpawns

    pattern = [
        "#####",
        "#...#",
        "#...#",
        "#...#",
        "#####",
    ]
    world = _create_test_world(pattern)
    spawns = GhostSpawns(
        top_left=(1, 1),
        top_right=(3, 1),
        bottom_left=(1, 3),
        bottom_right=(3, 3),
    )
    ghosts = create_ghost_group(spawns, speed_multiplier=1.0)
    for ghost in ghosts:
        ghost.frighten(duration=5.0)

    for ghost in ghosts:
        ghost.update(
            dt=0.1,
            world=world,
            base_speed=4.0,
            player_position=(2.5, 2.5),
        )
        assert world.contains_world(ghost.position)
        assert ghost.target_tile is None
