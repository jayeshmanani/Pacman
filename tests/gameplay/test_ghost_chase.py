"""Unit tests for Step 1: Normal ghost chase target calculation."""

from pacman.ghost import (
    GhostIdentity,
    calculate_ghost_target,
    select_chase_direction,
)
from pacman.player import Direction


def test_calculate_ghost_target_blinky() -> None:
    """Verify Blinky directly targets Pacman's current tile."""
    target = calculate_ghost_target(
        identity=GhostIdentity.BLINKY,
        ghost_tile=(1, 1),
        player_tile=(5, 10),
        player_direction=Direction.RIGHT,
        home_spawn=(1, 1),
    )
    assert target == (5, 10)


def test_calculate_ghost_target_pinky() -> None:
    """Verify Pinky targets 4 tiles ahead in Pacman's facing direction."""
    target = calculate_ghost_target(
        identity=GhostIdentity.PINKY,
        ghost_tile=(1, 1),
        player_tile=(5, 10),
        player_direction=Direction.RIGHT,
        home_spawn=(1, 1),
    )
    # Right vector is (+1, 0), so (5 + 4, 10 + 0) = (9, 10)
    assert target == (9, 10)

    target_up = calculate_ghost_target(
        identity=GhostIdentity.PINKY,
        ghost_tile=(1, 1),
        player_tile=(5, 10),
        player_direction=Direction.UP,
        home_spawn=(1, 1),
    )
    # Up vector is (0, -1), so (5, 10 - 4) = (5, 6)
    assert target_up == (5, 6)


def test_calculate_ghost_target_inky() -> None:
    """Verify Inky targets vector doubled from Blinky through Pacman offset."""
    # Pacman at (5, 5) facing RIGHT, pivot = (5 + 2, 5) = (7, 5)
    # Blinky at (3, 5). Vector from Blinky to pivot = (7 - 3, 5 - 5) = (4, 0)
    # Target = pivot + (4, 0) = (11, 5)
    target = calculate_ghost_target(
        identity=GhostIdentity.INKY,
        ghost_tile=(1, 1),
        player_tile=(5, 5),
        player_direction=Direction.RIGHT,
        home_spawn=(1, 1),
        blinky_tile=(3, 5),
    )
    assert target == (11, 5)


def test_calculate_ghost_target_clyde() -> None:
    """Verify Clyde targets Pacman when far and home spawn when close."""
    home = (1, 1)
    # Far: Ghost at (1, 1), Pacman at (10, 10) -> distance squared > 64
    target_far = calculate_ghost_target(
        identity=GhostIdentity.CLYDE,
        ghost_tile=(1, 1),
        player_tile=(10, 10),
        player_direction=Direction.LEFT,
        home_spawn=home,
    )
    assert target_far == (10, 10)

    # Close: Ghost at (2, 2), Pacman at (3, 3) -> distance squared = 2 <= 64
    target_close = calculate_ghost_target(
        identity=GhostIdentity.CLYDE,
        ghost_tile=(2, 2),
        player_tile=(3, 3),
        player_direction=Direction.LEFT,
        home_spawn=home,
    )
    assert target_close == home


def test_select_chase_direction_minimizes_distance() -> None:
    """Verify direction choice selects neighbor tile closest to target."""
    # Current tile (2, 2), target (5, 2) [to the right]
    # Options: UP (2, 1), DOWN (2, 3), RIGHT (3, 2)
    # RIGHT is closest to (5, 2)
    chosen = select_chase_direction(
        current_tile=(2, 2),
        target_tile=(5, 2),
        legal_directions=[Direction.UP, Direction.DOWN, Direction.RIGHT],
    )
    assert chosen == Direction.RIGHT


def test_select_chase_direction_tiebreaker() -> None:
    """Verify tiebreaking priority order UP > LEFT > DOWN > RIGHT."""
    # Current tile (2, 2), target (3, 3)
    # UP -> (2, 1): dist_sq = (2-3)^2 + (1-3)^2 = 1 + 4 = 5
    # LEFT -> (1, 2): dist_sq = (1-3)^2 + (2-3)^2 = 4 + 1 = 5
    # Distance is equal (5 vs 5). Tiebreak order UP > LEFT chooses UP.
    chosen = select_chase_direction(
        current_tile=(2, 2),
        target_tile=(3, 3),
        legal_directions=[Direction.UP, Direction.LEFT],
    )
    assert chosen == Direction.UP
