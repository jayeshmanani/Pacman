"""Tests for completed-game highscore application flow."""


from pathlib import Path

import pytest

from pacman.application.context import AppContext
from pacman.application.highscore_flow import handle_completed_game_input
from pacman.application.state import GameState, GameStateController
from pacman.infrastructure.config import GameConfig
from pacman.infrastructure.highscore import HighscoreEntry


BACKSPACE_KEY = 8
SUBMIT_KEY = 13


@pytest.mark.parametrize("completed_state", [
    GameState.GAME_OVER,
    GameState.VICTORY,
])
def test_completed_game_saves_once_and_returns_to_menu(
    tmp_path: Path,
    completed_state: GameState,
) -> None:
    """Verify both completion paths persist once before returning."""
    score_file = tmp_path / "scores.json"
    context = AppContext(
        config=GameConfig(highscore_filename=str(score_file))
    )
    context.session.score = 2400
    controller = GameStateController(completed_state)

    for character in "Maria":
        assert handle_completed_game_input(
            key=ord(character),
            character=character,
            backspace_key=BACKSPACE_KEY,
            submit_key=SUBMIT_KEY,
            controller=controller,
            context=context,
        )

    assert handle_completed_game_input(
        key=SUBMIT_KEY,
        character="\r",
        backspace_key=BACKSPACE_KEY,
        submit_key=SUBMIT_KEY,
        controller=controller,
        context=context,
    )

    assert controller.state is GameState.MAIN_MENU
    assert context.storage.load() == [
        HighscoreEntry(name="Maria", score=2400)
    ]
    assert context.session.score == 0
    assert context.player_name_input.value == ""

    assert not handle_completed_game_input(
        key=SUBMIT_KEY,
        character="\r",
        backspace_key=BACKSPACE_KEY,
        submit_key=SUBMIT_KEY,
        controller=controller,
        context=context,
    )
    assert context.storage.load() == [
        HighscoreEntry(name="Maria", score=2400)
    ]
