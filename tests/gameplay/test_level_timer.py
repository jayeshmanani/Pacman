"""Gameplay tests for level-timer countdown and timeout handling."""

import pytest

from pacman.app import GameState, GameStateController, update_active_gameplay
from pacman.infrastructure.config import GameConfig
from pacman.application.context import AppContext, GameSession


def test_timer_initializes_from_configured_time_limit() -> None:
    """Verify AppContext starts the session timer from configuration."""
    context = AppContext(config=GameConfig(level_max_time=75))

    assert context.session.remaining_level_time == 75.0
    assert not context.session.level_timed_out


def test_remaining_time_decreases_during_gameplay() -> None:
    """Verify active gameplay consumes elapsed level time."""
    session = GameSession(remaining_level_time=10.0)
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(session, controller, 2.5)

    assert session.remaining_level_time == 7.5
    assert not session.level_timed_out
    assert controller.state is GameState.PLAYING


def test_timer_reaches_exactly_zero_and_never_negative() -> None:
    """Verify large updates clamp the remaining time to zero."""
    session = GameSession(remaining_level_time=3.0)
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(session, controller, 10.0)

    assert session.remaining_level_time == 0.0
    assert session.level_timed_out
    assert controller.state is GameState.END_SCREEN


def test_timeout_flow_triggers_only_once() -> None:
    """Verify updates after timeout do not repeat timeout handling."""
    session = GameSession(remaining_level_time=1.0)
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(session, controller, 1.0)
    update_active_gameplay(session, controller, 1.0)

    assert session.remaining_level_time == 0.0
    assert session.level_timed_out
    assert controller.state is GameState.END_SCREEN


def test_timeout_leaves_session_state_consistent() -> None:
    """Verify timeout does not corrupt unrelated session state."""
    session = GameSession(
        score=250,
        lives=2,
        current_level=1,
        remaining_level_time=0.5,
    )
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(session, controller, 0.5)

    assert session.score == 250
    assert session.lives == 2
    assert session.current_level == 1
    assert session.remaining_level_time == 0.0
    assert session.level_timed_out
    assert controller.state is GameState.END_SCREEN


def test_timer_does_not_decrease_outside_playing_state() -> None:
    """Verify the app only advances the timer during active gameplay."""
    session = GameSession(remaining_level_time=10.0)
    controller = GameStateController(GameState.MAIN_MENU)

    update_active_gameplay(session, controller, 3.0)

    assert session.remaining_level_time == 10.0
    assert not session.level_timed_out
    assert controller.state is GameState.MAIN_MENU


@pytest.mark.parametrize("dt", [0.0, -1.0, float("inf"), "1"])
def test_invalid_or_non_positive_delta_is_ignored(dt: object) -> None:
    """Verify invalid elapsed time values are ignored safely."""
    session = GameSession(remaining_level_time=5.0)

    timed_out = session.update_level_timer(dt)  # type: ignore[arg-type]

    assert not timed_out
    assert session.remaining_level_time == 5.0
    assert not session.level_timed_out
