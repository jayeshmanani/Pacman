"""Focused tests for menu, information, and pause-screen rendering."""

from pacman.app import (
    MainMenu,
    PauseMenu,
    RenderFonts,
    WindowSettings,
    render_highscores_screen,
    render_instructions_screen,
    render_main_menu,
    render_pause_menu,
)
from pacman.application.context import GameSession
from pacman.infrastructure.config import GameConfig
from pacman.infrastructure.highscore import HighscoreEntry
from tests.support.app_fakes import _FakeFont, _FakePygame


def _fonts() -> RenderFonts:
    """Return deterministic fonts for rendering assertions."""
    return RenderFonts(title=_FakeFont(64), body=_FakeFont(28))


def test_main_menu_renders_options_and_current_selection() -> None:
    """Verify visible menu options follow the selected model item."""
    pygame = _FakePygame([])
    menu = MainMenu()
    menu.move_next()

    render_main_menu(pygame.surface, _fonts(), WindowSettings(), menu)

    assert pygame.surface.rendered_texts == [
        "PACMAN",
        "Start Game",
        "> View Highscores <",
        "Instructions",
        "Exit",
    ]


def test_highscores_render_only_the_top_ten_in_score_order() -> None:
    """Verify display ordering and top-ten trimming."""
    pygame = _FakePygame([])
    highscores = [
        HighscoreEntry(name=f"P{score}", score=score)
        for score in (40, 110, 20, 90, 70, 10, 120, 50, 100, 30, 80, 60)
    ]

    render_highscores_screen(
        pygame.surface,
        _fonts(),
        WindowSettings(),
        highscores,
    )

    texts = pygame.surface.rendered_texts
    assert texts[1:4] == ["RANK", "PLAYER", "SCORE"]
    displayed_players = texts[5:34:3]
    assert displayed_players == [
        "P120",
        "P110",
        "P100",
        "P90",
        "P80",
        "P70",
        "P60",
        "P50",
        "P40",
        "P30",
    ]
    assert "P20" not in texts
    assert "P10" not in texts


def test_highscores_render_empty_state() -> None:
    """Verify an empty score collection has a clear message."""
    pygame = _FakePygame([])

    render_highscores_screen(
        pygame.surface,
        _fonts(),
        WindowSettings(),
        [],
    )

    assert "No highscores yet" in pygame.surface.rendered_texts


def test_instructions_render_active_configuration() -> None:
    """Verify instruction values come from the loaded configuration."""
    pygame = _FakePygame([])
    config = GameConfig(
        lives=5,
        points_per_pacgum=12,
        points_per_super_pacgum=60,
        points_per_ghost=250,
        frightened_duration=8.0,
    )

    render_instructions_screen(
        pygame.surface,
        _fonts(),
        WindowSettings(),
        config,
    )

    texts = pygame.surface.rendered_texts
    assert "Starting lives: 5" in texts
    assert "Pacgum: +12" in texts
    assert "Power pellet: +60" in texts
    assert "Ghost: +250 to +2000" in texts
    assert "Lasts 8 seconds" in texts


def test_pause_menu_renders_session_and_selection() -> None:
    """Verify pause rendering combines its HUD and menu model."""
    pygame = _FakePygame([])
    menu = PauseMenu()
    menu.move_next()

    render_pause_menu(
        pygame.surface,
        _fonts(),
        WindowSettings(),
        menu,
        GameSession(score=100, lives=2),
    )

    texts = pygame.surface.rendered_texts
    assert "PAUSED" in texts
    assert "> Return to Main Menu <" in texts
    assert "SCORE: 100" in texts
    assert "LIVES: 2" in texts
