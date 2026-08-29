"""Unit tests for frightened ghost fleeing and direction selection."""

import random

from pacman.ghost import (
    select_frightened_direction,
)
from pacman.player import Direction


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
    from pacman.ghost import Ghost, GhostIdentity

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
