"""Application tests for high-level game-state transitions."""

from pacman.app import GameState, GameStateController
from tests.support.app_fakes import _FakePygame, state_controls


def test_initial_state_is_main_menu() -> None:
    """Verify that the state controller starts on the main menu."""
    controller = GameStateController()

    assert controller.state is GameState.MAIN_MENU


def test_main_menu_transitions_to_playing() -> None:
    """Verify that confirm starts the game from the main menu."""
    controller = GameStateController()

    controller.handle_key(_FakePygame.K_RETURN, state_controls())

    assert controller.state is GameState.PLAYING


def test_playing_transitions_to_end_screen() -> None:
    """Verify that the temporary end key finishes play."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_e, state_controls())

    assert controller.state is GameState.END_SCREEN


def test_end_screen_transitions_to_main_menu() -> None:
    """Verify that confirm returns from the end screen to the main menu."""
    controller = GameStateController(GameState.END_SCREEN)

    controller.handle_key(_FakePygame.K_SPACE, state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_escape_returns_from_playing_to_main_menu() -> None:
    """Verify that Escape returns from playing to the main menu."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_ESCAPE, state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_escape_returns_from_end_screen_to_main_menu() -> None:
    """Verify that Escape returns from the end screen to the main menu."""
    controller = GameStateController(GameState.END_SCREEN)

    controller.handle_key(_FakePygame.K_ESCAPE, state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_irrelevant_key_does_not_change_state() -> None:
    """Verify that irrelevant keys do not trigger transitions."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(999, state_controls())

    assert controller.state is GameState.PLAYING
