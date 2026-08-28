"""Unit tests for Step 1: Normal ghost chase target calculation."""

from pacman.ghost import (
    GhostIdentity,
    calculate_ghost_target,
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
