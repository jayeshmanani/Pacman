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
