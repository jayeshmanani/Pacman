"""Application rendering tests for states and configured data."""

import json
from pathlib import Path

from pacman.app import (
    GameState,
    GameStateController,
    RenderFonts,
    WindowSettings,
    render_highscores_screen,
    render_state,
    run_app,
)
from pacman.infrastructure.config import GameConfig
from pacman.infrastructure.highscore import HighscoreEntry
from tests.support.app_fakes import _FakeEvent, _FakeFont, _FakePygame


def test_main_menu_renders_expected_text() -> None:
    """Verify that the main menu options are rendered."""
    pygame = _FakePygame([[_FakeEvent(type=_FakePygame.QUIT)]])

    run_app(pygame_module=pygame)

    assert "PACMAN" in pygame.surface.rendered_texts
    assert "> Start Game <" in pygame.surface.rendered_texts
    assert "View Highscores" in pygame.surface.rendered_texts
    assert "Instructions" in pygame.surface.rendered_texts
    assert "Exit" in pygame.surface.rendered_texts
    assert pygame.surface.blit_destinations == [
        {"center": (224, 180)},
        {"center": (224, 240)},
        {"center": (224, 272)},
        {"center": (224, 304)},
        {"center": (224, 336)},
    ]


def test_menu_selection_highlight_follows_keyboard_navigation() -> None:
    """Verify that keyboard navigation updates the rendered menu selection."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert "> View Highscores <" in pygame.surface.rendered_texts


def test_highscores_screen_displays_scores_from_configured_storage(
    tmp_path: Path,
) -> None:
    """Verify that the highscores screen renders scores loaded at startup."""
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
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(
        pygame_module=pygame,
        config=GameConfig(highscore_filename=str(score_file)),
    )

    assert "HIGHSCORES" in pygame.surface.rendered_texts
    assert "Maria" in pygame.surface.rendered_texts
    assert "1200" in pygame.surface.rendered_texts
    assert "Player 2" in pygame.surface.rendered_texts
    assert "800" in pygame.surface.rendered_texts


def test_playing_renders_expected_placeholder_text() -> None:
    """Verify that the game view placeholder text is rendered."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert "Game View" in pygame.surface.rendered_texts
    assert "Press E to End" in pygame.surface.rendered_texts


def test_highscores_screen_renders_loaded_scores() -> None:
    """Verify that the highscores state renders the loaded score entries."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert "HIGHSCORES" in pygame.surface.rendered_texts
    assert "No highscores yet" in pygame.surface.rendered_texts


def test_highscores_screen_renders_only_top_ten_in_score_order() -> None:
    """Verify twelve unordered entries render as a descending Top 10."""
    pygame = _FakePygame([])
    fonts = RenderFonts(
        title=_FakeFont(64),
        body=_FakeFont(28),
    )
    highscores = [
        HighscoreEntry(name=f"P{score}", score=score)
        for score in (40, 110, 20, 90, 70, 10, 120, 50, 100, 30, 80, 60)
    ]

    render_highscores_screen(
        pygame.surface,
        fonts,
        WindowSettings(),
        highscores,
    )

    assert pygame.surface.rendered_texts[1:4] == [
        "RANK",
        "PLAYER",
        "SCORE",
    ]
    assert pygame.surface.rendered_texts[4:34] == [
        "1", "P120", "120",
        "2", "P110", "110",
        "3", "P100", "100",
        "4", "P90", "90",
        "5", "P80", "80",
        "6", "P70", "70",
        "7", "P60", "60",
        "8", "P50", "50",
        "9", "P40", "40",
        "10", "P30", "30",
    ]
    assert "P20" not in pygame.surface.rendered_texts
    assert "P10" not in pygame.surface.rendered_texts
    assert pygame.surface.blit_destinations[1:4] == [
        {"center": (74, 112)},
        {"center": (224, 112)},
        {"center": (373, 112)},
    ]
    assert pygame.surface.blit_destinations[4:7] == [
        {"center": (74, 144)},
        {"center": (224, 144)},
        {"center": (373, 144)},
    ]
    assert pygame.surface.blit_destinations[31:34] == [
        {"center": (74, 396)},
        {"center": (224, 396)},
        {"center": (373, 396)},
    ]
    assert pygame.surface.blit_destinations[-1] == {
        "center": (224, 448),
    }


def test_instructions_screen_renders_minimal_content() -> None:
    """Verify that the instructions state renders minimal valid content."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert "Instructions" in pygame.surface.rendered_texts
    assert "Guide Pacman through the maze." in pygame.surface.rendered_texts


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
