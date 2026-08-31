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
