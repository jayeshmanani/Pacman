"""Tests for baseline application context container."""

from pathlib import Path
from pacman.config import GameConfig
from pacman.context import AppContext, GameSession


def test_app_context_baseline_initialization() -> None:
    """Verify AppContext initializes with config, storage, and session."""
    config = GameConfig(highscore_filename="custom_scores.json", lives=5)
    context = AppContext(config=config)

    assert context.config.lives == 5
    assert context.storage.path == Path("custom_scores.json")
    assert isinstance(context.session, GameSession)
    assert context.session.score == 0
    assert context.session.lives == 3
