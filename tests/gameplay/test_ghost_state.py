"""Unit tests for ghost state model transitions and timers."""

import pytest

from pacman.ghost import Ghost, GhostIdentity, GhostState
from pacman.player import Direction


def test_ghost_initialization_from_spawn() -> None:
    """Verify factory initializes tile-centered position and default state."""
    ghost = Ghost.from_spawn(
        identity=GhostIdentity.BLINKY,
        spawn_tile=(2, 4),
        speed_multiplier=1.2,
    )
    assert ghost.identity == GhostIdentity.BLINKY
    assert ghost.home_spawn == (2, 4)
    assert ghost.position == (2.5, 4.5)
    assert ghost.direction == Direction.NONE
    assert ghost.state == GhostState.NORMAL
    assert ghost.speed_multiplier == 1.2
    assert ghost.frightened_timer == 0.0
    assert ghost.respawn_timer == 0.0


def test_ghost_frighten_transition() -> None:
    """Verify frighten transition updates state and duration timer."""
    ghost = Ghost.from_spawn(GhostIdentity.PINKY, (0, 0))
    assert ghost.frighten(6.0) is True
    assert ghost.state == GhostState.FRIGHTENED
    assert ghost.frightened_timer == 6.0

    # Re-frightening resets timer duration
    assert ghost.frighten(8.0) is True
    assert ghost.frightened_timer == 8.0


def test_ghost_frighten_rejected_when_frozen() -> None:
    """Verify frighten is rejected when ghost is frozen."""
    ghost = Ghost.from_spawn(GhostIdentity.INKY, (1, 1))
    ghost.freeze()
    assert ghost.frighten(5.0) is False
    assert ghost.state == GhostState.FROZEN


def test_ghost_frighten_rejected_when_eaten() -> None:
    """Verify frighten is rejected when ghost is eaten."""
    ghost = Ghost.from_spawn(GhostIdentity.INKY, (1, 1))
    ghost.frighten(5.0)
    ghost.eat()
    assert ghost.state == GhostState.EATEN
    assert ghost.frighten(5.0) is False


def test_ghost_frighten_rejected_when_respawning() -> None:
    """Verify frighten is rejected when ghost is respawning."""
    ghost = Ghost.from_spawn(GhostIdentity.INKY, (1, 1))
    ghost.start_respawn(3.0)
    assert ghost.state == GhostState.RESPAWNING
    assert ghost.frighten(5.0) is False


def test_ghost_eat_transition_success() -> None:
    """Verify eat transition succeeds when ghost is frightened."""
    ghost = Ghost.from_spawn(GhostIdentity.CLYDE, (5, 5))
    ghost.frighten(5.0)
    assert ghost.eat() is True
    assert ghost.state == GhostState.EATEN
    assert ghost.frightened_timer == 0.0


def test_ghost_eat_transition_failure_when_normal() -> None:
    """Verify eat transition fails when ghost is normal."""
    ghost = Ghost.from_spawn(GhostIdentity.CLYDE, (5, 5))
    assert ghost.eat() is False
    assert ghost.state == GhostState.NORMAL


def test_ghost_start_respawn_transition() -> None:
    """Verify start_respawn resets position to home spawn center."""
    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, (10, 12))
    ghost.position = (15.5, 20.5)
    ghost.direction = Direction.UP
    ghost.start_respawn(4.0)

    assert ghost.state == GhostState.RESPAWNING
    assert ghost.position == (10.5, 12.5)
    assert ghost.direction == Direction.NONE
    assert ghost.respawn_timer == 4.0
    assert ghost.frightened_timer == 0.0


def test_ghost_freeze_and_unfreeze() -> None:
    """Verify freeze preserves previous state and unfreeze restores it."""
    ghost = Ghost.from_spawn(GhostIdentity.PINKY, (3, 3))
    ghost.frighten(5.0)

    assert ghost.freeze() is True
    state_after_freeze: GhostState = ghost.state
    assert state_after_freeze == GhostState.FROZEN
    assert ghost.previous_state == GhostState.FRIGHTENED

    assert ghost.freeze() is False

    assert ghost.unfreeze() is True
    state_after_unfreeze: GhostState = ghost.state
    assert state_after_unfreeze == GhostState.FRIGHTENED
    assert ghost.previous_state is None

    assert ghost.unfreeze() is False


def test_ghost_update_frightened_timer_countdown() -> None:
    """Verify update ticks frightened timer and auto-transitions to NORMAL."""
    ghost = Ghost.from_spawn(GhostIdentity.INKY, (1, 1))
    ghost.frighten(2.0)
    ghost.update(1.0)
    state_midway: GhostState = ghost.state
    assert state_midway == GhostState.FRIGHTENED
    assert ghost.frightened_timer == 1.0

    ghost.update(1.0)
    state_final: GhostState = ghost.state
    assert state_final == GhostState.NORMAL
    assert ghost.frightened_timer == 0.0


def test_ghost_update_respawn_timer_countdown() -> None:
    """Verify update ticks respawn timer and auto-transitions to NORMAL."""
    ghost = Ghost.from_spawn(GhostIdentity.INKY, (1, 1))
    ghost.start_respawn(1.5)
    ghost.update(1.0)
    state_midway: GhostState = ghost.state
    assert state_midway == GhostState.RESPAWNING
    assert ghost.respawn_timer == 0.5

    ghost.update(1.0)
    state_final: GhostState = ghost.state
    assert state_final == GhostState.NORMAL
    assert ghost.respawn_timer == 0.0


def test_ghost_update_ignored_when_frozen_or_zero_dt() -> None:
    """Verify update ignores non-positive dt and frozen state."""
    ghost = Ghost.from_spawn(GhostIdentity.CLYDE, (1, 1))
    ghost.frighten(5.0)

    ghost.update(0.0)
    assert ghost.frightened_timer == 5.0

    ghost.freeze()
    ghost.update(2.0)
    assert ghost.frightened_timer == 5.0
    assert ghost.state == GhostState.FROZEN


def test_ghost_invalid_timer_values_raise_error() -> None:
    """Verify negative duration and delay raise ValueError."""
    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, (1, 1))

    with pytest.raises(ValueError, match="frightened duration"):
        ghost.frighten(-1.0)

    with pytest.raises(ValueError, match="respawn delay"):
        ghost.start_respawn(-1.0)
