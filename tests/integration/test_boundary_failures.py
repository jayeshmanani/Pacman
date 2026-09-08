"""Integration tests for external boundary failures and diagnostics."""

from unittest.mock import patch
import pytest

from pacman.app import GameState, GameStateController
from pacman.application.context import GameSession
from pacman.gameplay.player import Player
from pacman.gameplay.progression import (
    LevelCompletionOutcome,
    handle_level_completion,
)
from pacman.maze.level_generator import (
    LevelData,
    LevelGenerationError,
    LevelGenerator,
)
from scripts.preview_mazes import main as preview_main


class _FailingGenerator(LevelGenerator):
    """Generator fake that simulates external maze package failures."""

    def generate_level(
        self,
        level_index: int = 0,
        seed: int | None = None,
    ) -> LevelData:
        raise LevelGenerationError(
            f"Simulated package failure on level {level_index + 1}"
        )


def test_level_completion_handles_generation_failure_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify level progression handles generator error without crashing."""
    session = GameSession(
        score=100,
        lives=3,
        current_level=0,
        remaining_level_time=42.0,
    )
    player = Player.from_spawn((3, 3))
    controller = GameStateController(GameState.PLAYING)
    failing_gen = _FailingGenerator()

    outcome, next_level = handle_level_completion(
        session,
        player,
        failing_gen,
        controller,
    )

    assert outcome is LevelCompletionOutcome.FAILED
    assert next_level is None
    assert controller.state is GameState.MAIN_MENU
    assert session.current_level == 0
    assert session.score == 100
    assert session.lives == 3
    assert session.remaining_level_time == 42.0

    captured = capsys.readouterr()
    assert "Error: Simulated package failure on level 2" in captured.err


def test_preview_mazes_handles_generator_failure_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify preview_mazes catches generator failures and logs error."""
    with patch.object(
        LevelGenerator,
        "generate_level",
        side_effect=LevelGenerationError("mazegenerator wheel broken"),
    ):
        preview_main()

    captured = capsys.readouterr()
    assert (
        "Error generating preview: mazegenerator wheel broken" in captured.err
    )
