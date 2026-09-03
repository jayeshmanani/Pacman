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


def test_start_game_transitions_to_playing() -> None:
    """Verify that start_game enters active gameplay."""
    controller = GameStateController()

    controller.start_game()

    assert controller.state is GameState.PLAYING


def test_show_highscores_transitions_to_highscores() -> None:
    """Verify the controller can open the highscores state."""
    controller = GameStateController()

    controller.show_highscores()

    assert controller.state is GameState.HIGHSCORES


def test_show_instructions_transitions_to_instructions() -> None:
    """Verify the controller can open the instructions state."""
    controller = GameStateController()

    controller.show_instructions()

    assert controller.state is GameState.INSTRUCTIONS


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


def test_escape_returns_from_highscores_to_main_menu() -> None:
    """Verify Escape returns from highscores to the main menu."""
    controller = GameStateController(GameState.HIGHSCORES)

    controller.handle_key(_FakePygame.K_ESCAPE, state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_confirm_returns_from_instructions_to_main_menu() -> None:
    """Verify confirm returns from instructions to the main menu."""
    controller = GameStateController(GameState.INSTRUCTIONS)

    controller.handle_key(_FakePygame.K_RETURN, state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_irrelevant_key_does_not_change_state() -> None:
    """Verify that irrelevant keys do not trigger transitions."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(999, state_controls())

    assert controller.state is GameState.PLAYING


def test_pause_game_moves_to_paused_state() -> None:
    """Verify that pause_game transitions to PAUSED."""
    controller = GameStateController(GameState.PLAYING)

    controller.pause_game()

    assert controller.state is GameState.PAUSED


def test_resume_game_moves_to_playing_state() -> None:
    """Verify that resume_game returns to PLAYING."""
    controller = GameStateController(GameState.PAUSED)

    controller.resume_game()

    assert controller.state is GameState.PLAYING


def test_playing_transitions_to_paused_on_pause_key() -> None:
    """Verify pressing P while playing enters PAUSED."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_p, state_controls())

    assert controller.state is GameState.PAUSED


def test_paused_transitions_to_playing_on_pause_key() -> None:
    """Verify pressing P while paused resumes to PLAYING."""
    controller = GameStateController(GameState.PAUSED)

    controller.handle_key(_FakePygame.K_p, state_controls())

    assert controller.state is GameState.PLAYING


def test_paused_transitions_to_main_menu_on_escape() -> None:
    """Verify pressing Escape while paused returns to MAIN_MENU."""
    controller = GameStateController(GameState.PAUSED)

    controller.handle_key(_FakePygame.K_ESCAPE, state_controls())

    assert controller.state is GameState.MAIN_MENU
