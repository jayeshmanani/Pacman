"""Application-context and service-integration tests."""

import json
from pathlib import Path

from pacman.infrastructure.config import GameConfig
from pacman.application.context import AppContext, GameSession
from pacman.infrastructure.highscore import HighscoreEntry


def test_app_context_baseline_initialization() -> None:
    """Verify AppContext initializes with config, storage, and session."""
    config = GameConfig(highscore_filename="custom_scores.json", lives=5)
    context = AppContext(config=config)

    assert context.config.lives == 5
    assert context.storage.path == Path("custom_scores.json")
    assert isinstance(context.session, GameSession)
    assert context.session.score == 0
    assert context.session.lives == 5
    assert context.highscores == []


def test_app_context_loads_highscores_from_configured_storage(
    tmp_path: Path,
) -> None:
    """Verify context loads highscores using the configured file path."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(
        json.dumps([{"name": "Maria", "score": 1200}]),
        encoding="utf-8",
    )

    context = AppContext(
        config=GameConfig(
            highscore_filename=str(score_file),
            lives=7,
        )
    )

    assert context.storage.path == score_file
    assert context.session.lives == 7
    assert context.highscores == [
        HighscoreEntry(name="Maria", score=1200)
    ]


def test_start_new_game_resets_session_with_configured_defaults() -> None:
    """Verify starting a game replaces stale session state."""
    context = AppContext(config=GameConfig(lives=7, level_max_time=45))
    context.session.score = 900
    context.session.lives = 1
    context.session.current_level = 4
    context.session.remaining_level_time = 3.0
    context.session.level_timed_out = True
    context.session.is_paused = True
    context.session.is_victory = True

    session = context.start_new_game()

    assert session is context.session
    assert session.score == 0
    assert session.lives == 7
    assert session.current_level == 0
    assert session.remaining_level_time == 45.0
    assert not session.level_timed_out
    assert not session.is_paused
    assert not session.is_victory


def test_save_completed_game_score_persists_entry_and_refreshes_list(
    tmp_path: Path,
) -> None:
    """Verify a completed score is saved and available to the application."""
    score_file = tmp_path / "scores.json"
    context = AppContext(
        config=GameConfig(highscore_filename=str(score_file))
    )
    context.session.score = 1250
    context.player_name_input.value = " Maria "

    assert context.save_completed_game_score()
    assert context.highscores == [
        HighscoreEntry(name="Maria", score=1250)
    ]
    assert context.storage.load() == context.highscores
    assert context.player_name_input.value == ""


def test_save_completed_game_score_rejects_empty_name(
    tmp_path: Path,
) -> None:
    """Verify invalid input does not create or update highscore storage."""
    score_file = tmp_path / "scores.json"
    context = AppContext(
        config=GameConfig(highscore_filename=str(score_file))
    )
    context.session.score = 500

    assert not context.save_completed_game_score()
    assert context.player_name_input.error_message == "Enter a player name"
    assert context.highscores == []
    assert not score_file.exists()
