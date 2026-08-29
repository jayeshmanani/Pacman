"""Tests for synchronized frightened-state timing and recovery."""

from pacman.ghost import Ghost, GhostIdentity, GhostState
from pacman.power_state import PowerState


def _ghosts() -> list[Ghost]:
    """Create a small ghost group for timer tests."""
    return [
        Ghost.from_spawn(GhostIdentity.BLINKY, (1, 1)),
        Ghost.from_spawn(GhostIdentity.PINKY, (3, 1)),
        Ghost.from_spawn(GhostIdentity.INKY, (1, 3)),
        Ghost.from_spawn(GhostIdentity.CLYDE, (3, 3)),
    ]


def test_power_state_activates_and_recovers_whole_group() -> None:
    """Verify all active ghosts recover together at timer expiry."""
    ghosts = _ghosts()
    power_state = PowerState()

    power_state.activate(3.0, ghosts)
    assert all(ghost.state == GhostState.FRIGHTENED for ghost in ghosts)

    assert power_state.update(2.0, ghosts) is False
    assert all(ghost.state == GhostState.FRIGHTENED for ghost in ghosts)

    assert power_state.update(1.0, ghosts) is True
    assert all(ghost.state == GhostState.NORMAL for ghost in ghosts)
    assert all(ghost.frightened_timer == 0.0 for ghost in ghosts)


def test_reactivation_resets_shared_and_individual_timers() -> None:
    """Verify another super-pacgum restarts the full duration safely."""
    ghosts = _ghosts()
    power_state = PowerState()
    power_state.activate(3.0, ghosts)
    power_state.update(2.0, ghosts)

    power_state.activate(5.0, ghosts)

    assert power_state.remaining_time == 5.0
    assert all(ghost.frightened_timer == 5.0 for ghost in ghosts)


def test_expiry_preserves_non_frightened_states() -> None:
    """Verify recovery does not revive eaten or respawning ghosts."""
    ghosts = _ghosts()
    power_state = PowerState()
    power_state.activate(2.0, ghosts)
    ghosts[0].eat()
    ghosts[0].start_respawn(5.0)
    ghosts[1].eat()

    power_state.update(2.0, ghosts)

    assert ghosts[0].state == GhostState.RESPAWNING
    assert ghosts[0].respawn_timer == 5.0
    assert ghosts[1].state == GhostState.EATEN
    assert ghosts[2].state == GhostState.NORMAL
    assert ghosts[3].state == GhostState.NORMAL


def test_expiry_clears_saved_frightened_state_from_frozen_ghost() -> None:
    """Verify unfreezing cannot restore an expired frightened state."""
    ghosts = _ghosts()
    power_state = PowerState()
    power_state.activate(1.0, ghosts)
    ghosts[0].freeze()

    power_state.update(1.0, ghosts)

    assert ghosts[0].state == GhostState.FROZEN
    assert ghosts[0].previous_state == GhostState.NORMAL
    ghosts[0].unfreeze()
    state_after_unfreeze: GhostState = ghosts[0].state
    assert state_after_unfreeze == GhostState.NORMAL


def test_zero_duration_does_not_leave_frightened_state() -> None:
    """Verify a zero configuration value cannot create stale power state."""
    ghosts = _ghosts()
    power_state = PowerState()

    power_state.activate(0.0, ghosts)

    assert power_state.is_active is False
    assert all(ghost.state == GhostState.NORMAL for ghost in ghosts)
