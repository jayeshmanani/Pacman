"""Application rendering tests for states and configured data."""

import json
from pathlib import Path

from pacman.app import (
    GameState,
    GameStateController,
    RenderFonts,
    WindowSettings,
    render_state,
    run_app,
)
from pacman.infrastructure.config import GameConfig
from tests.support.app_fakes import _FakeEvent, _FakeFont, _FakePygame


def test_main_menu_renders_expected_text() -> None:
    """Verify that the main menu placeholder text is rendered."""
    pygame = _FakePygame([[_FakeEvent(type=_FakePygame.QUIT)]])

    run_app(pygame_module=pygame)

    assert "PACMAN" in pygame.surface.rendered_texts
    assert "Press Enter or Space to Start" in pygame.surface.rendered_texts


def test_main_menu_displays_highscores_from_configured_storage(
    tmp_path: Path,
) -> None:
    """Verify that the main menu renders highscores loaded at startup."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(
        json.dumps(
            [
                {"name": "Maria", "score": 1200},
                {"name": "Player 2", "score": 800},
            ]
        ),
        encoding="utf-8",
    )
    pygame = _FakePygame([[_FakeEvent(type=_FakePygame.QUIT)]])

    run_app(
        pygame_module=pygame,
        config=GameConfig(highscore_filename=str(score_file)),
    )

    assert "HIGHSCORES" in pygame.surface.rendered_texts
    assert "1. Maria  1200" in pygame.surface.rendered_texts
    assert "2. Player 2  800" in pygame.surface.rendered_texts


def test_playing_renders_expected_placeholder_text() -> None:
    """Verify that the game view placeholder text is rendered."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert "Game View" in pygame.surface.rendered_texts
    assert "Press E to End" in pygame.surface.rendered_texts


def test_game_view_uses_configured_starting_lives() -> None:
    """Verify that gameplay starts with lives from the loaded config."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(
        pygame_module=pygame,
        config=GameConfig(lives=7),
    )

    assert "Lives: 7 | Score: 0" in pygame.surface.rendered_texts


def test_rendering_does_not_change_current_game_state() -> None:
    """Verify that rendering has no effect on state transitions."""
    controller = GameStateController(GameState.PLAYING)
    pygame = _FakePygame([])
    fonts = RenderFonts(
        title=_FakeFont(64),
        body=_FakeFont(28),
    )

    render_state(
        pygame.surface,
        fonts,
        pygame,
        WindowSettings(),
        controller.state,
    )

    assert controller.state is GameState.PLAYING
