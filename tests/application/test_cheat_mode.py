"""Application tests for cheat-mode activation state."""

from pacman.application.cheat_mode import CheatMode
from pacman.application.context import AppContext


def test_cheat_mode_toggles_on_and_off() -> None:
    """Verify activation is explicit and reversible."""
    cheat_mode = CheatMode()

    assert cheat_mode.toggle()
    assert cheat_mode.enabled
    assert not cheat_mode.toggle()
    assert not cheat_mode.enabled


def test_new_game_disables_previous_cheat_mode() -> None:
    """Verify a new session cannot inherit stale cheat activation."""
    context = AppContext()
    context.cheat_mode.toggle()

    context.start_new_game()

    assert not context.cheat_mode.enabled


def test_individual_cheats_require_active_cheat_mode() -> None:
    """Verify evaluation effects cannot activate before the master mode."""
    cheat_mode = CheatMode()

    assert not cheat_mode.toggle_invincibility()
    assert not cheat_mode.toggle_ghost_freeze()
    assert not cheat_mode.invincibility_enabled
    assert not cheat_mode.ghost_freeze_enabled


def test_individual_cheats_toggle_independently() -> None:
    """Verify one evaluation effect does not overwrite the other."""
    cheat_mode = CheatMode(enabled=True)

    assert cheat_mode.toggle_invincibility()
    assert cheat_mode.toggle_ghost_freeze()
    assert not cheat_mode.toggle_invincibility()

    assert not cheat_mode.invincibility_enabled
    assert cheat_mode.ghost_freeze_enabled


def test_disabling_cheat_mode_clears_individual_effects() -> None:
    """Verify no active effect remains after master mode is disabled."""
    cheat_mode = CheatMode(enabled=True)
    cheat_mode.toggle_invincibility()
    cheat_mode.toggle_ghost_freeze()

    assert not cheat_mode.toggle()

    assert not cheat_mode.invincibility_enabled
    assert not cheat_mode.ghost_freeze_enabled
