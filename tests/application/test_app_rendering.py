"""Application rendering tests for states and configured data."""

import json
from pathlib import Path

from pacman.app import (
    GameState,
    GameStateController,
    PauseMenu,
    RenderFonts,
    WindowSettings,
    render_highscores_screen,
    render_hud,
    render_pause_menu,
    render_state,
    run_app,
)
from pacman.application.context import GameSession
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
        {"center": (260, 180)},
        {"center": (260, 240)},
        {"center": (260, 272)},
        {"center": (260, 304)},
        {"center": (260, 336)},
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
    """Verify that the game view placeholder text and HUD are rendered."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert "Game View" in pygame.surface.rendered_texts
    assert "Press E to End" in pygame.surface.rendered_texts
    assert "SCORE: 0" in pygame.surface.rendered_texts
    assert "LIVES: 3" in pygame.surface.rendered_texts
    assert "LEVEL: 1" in pygame.surface.rendered_texts
    assert "TIME: 90s" in pygame.surface.rendered_texts


def test_highscores_screen_renders_empty_storage(tmp_path: Path) -> None:
    """Verify that the highscores state renders an empty storage message."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(
        pygame_module=pygame,
        config=GameConfig(
            highscore_filename=str(tmp_path / "missing-scores.json")
        ),
    )

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
        {"center": (86, 112)},
        {"center": (260, 112)},
        {"center": (433, 112)},
    ]
    assert pygame.surface.blit_destinations[4:7] == [
        {"center": (86, 144)},
        {"center": (260, 144)},
        {"center": (433, 144)},
    ]
    assert pygame.surface.blit_destinations[31:34] == [
        {"center": (86, 396)},
        {"center": (260, 396)},
        {"center": (433, 396)},
    ]
    assert pygame.surface.blit_destinations[-1] == {
        "center": (260, 448),
    }


def test_instructions_screen_renders_controls_and_configured_rules() -> None:
    """Verify instructions use supported controls and configured game rules."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(
        pygame_module=pygame,
        config=GameConfig(
            lives=5,
            points_per_pacgum=12,
            points_per_super_pacgum=60,
            points_per_ghost=250,
            frightened_duration=8.0,
        ),
    )

    assert pygame.surface.rendered_texts[-16:] == [
        "Instructions",
        "CONTROLS",
        "Arrows / WASD",
        "P: Pause / Resume",
        "RULES",
        "Clear all pacgums",
        "Ghost touch: -1 life",
        "Starting lives: 5",
        "SCORING",
        "Pacgum: +12",
        "Power pellet: +60",
        "Ghost: +250 to +2000",
        "POWER MODE",
        "Ghosts become edible",
        "Lasts 8 seconds",
        "Esc / Enter / Space: Main Menu",
    ]
    assert pygame.surface.blit_destinations[-16:] == [
        {"center": (260, 52)},
        {"midleft": (42, 108)},
        {"midleft": (42, 140)},
        {"midleft": (42, 170)},
        {"midleft": (42, 252)},
        {"midleft": (42, 284)},
        {"midleft": (42, 314)},
        {"midleft": (42, 344)},
        {"midleft": (278, 108)},
        {"midleft": (278, 140)},
        {"midleft": (278, 170)},
        {"midleft": (278, 200)},
        {"midleft": (278, 252)},
        {"midleft": (278, 284)},
        {"midleft": (278, 314)},
        {"center": (260, 448)},
    ]
    assert pygame.surface.fill_colors[-1] == (16, 24, 72)
    assert pygame.surface.fill_rectangles[-6:] == [
        ((82, 113, 214), (24, 88, 472, 2)),
        ((82, 113, 214), (24, 230, 472, 2)),
        ((82, 113, 214), (24, 370, 472, 2)),
        ((82, 113, 214), (24, 88, 2, 282)),
        ((82, 113, 214), (260, 88, 2, 282)),
        ((82, 113, 214), (494, 88, 2, 282)),
    ]


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


def test_hud_renders_default_metrics_and_background() -> None:
    """Verify that HUD renders default metrics and its top background bar."""
    pygame = _FakePygame([])
    fonts = RenderFonts(
        title=_FakeFont(64),
        body=_FakeFont(28),
    )
    window_settings = WindowSettings(width=520, height=496)

    render_hud(pygame.surface, fonts, window_settings, None)

    assert ((12, 16, 36), (0, 0, 520, 40)) in pygame.surface.fill_rectangles
    assert ((82, 113, 214), (0, 38, 520, 2)) in pygame.surface.fill_rectangles
    assert "SCORE: 0" in pygame.surface.rendered_texts
    assert "LIVES: 3" in pygame.surface.rendered_texts
    assert "LEVEL: 1" in pygame.surface.rendered_texts
    assert "TIME: 90s" in pygame.surface.rendered_texts
    assert pygame.surface.blit_destinations == [
        {"center": (65, 20)},
        {"center": (195, 20)},
        {"center": (325, 20)},
        {"center": (455, 20)},
    ]


def test_hud_renders_active_session_values() -> None:
    """Verify that HUD displays dynamic metrics from the active session."""
    pygame = _FakePygame([])
    fonts = RenderFonts(
        title=_FakeFont(64),
        body=_FakeFont(28),
    )
    window_settings = WindowSettings(width=520, height=496)
    session = GameSession(
        score=1450,
        lives=2,
        current_level=3,
        remaining_level_time=42.1,
    )

    render_hud(pygame.surface, fonts, window_settings, session)

    assert "SCORE: 1450" in pygame.surface.rendered_texts
    assert "LIVES: 2" in pygame.surface.rendered_texts
    assert "LEVEL: 4" in pygame.surface.rendered_texts
    assert "TIME: 43s" in pygame.surface.rendered_texts


def test_render_pause_menu_displays_expected_elements() -> None:
    """Verify that render_pause_menu renders the title, options, and HUD."""
    pygame = _FakePygame([])
    fonts = RenderFonts(
        title=_FakeFont(64),
        body=_FakeFont(28),
    )
    window_settings = WindowSettings()
    session = GameSession(score=100, lives=3, current_level=0)
    pause_menu = PauseMenu()

    render_pause_menu(
        pygame.surface, fonts, window_settings, pause_menu, session
    )

    assert "PAUSED" in pygame.surface.rendered_texts
    assert "> Resume <" in pygame.surface.rendered_texts
    assert "Return to Main Menu" in pygame.surface.rendered_texts
    assert "P: Resume | Esc: Main Menu" in pygame.surface.rendered_texts
    assert "SCORE: 100" in pygame.surface.rendered_texts
    assert "LIVES: 3" in pygame.surface.rendered_texts


def test_render_pause_menu_highlights_return_to_main_menu() -> None:
    """Verify that moving selection highlights Return to Main Menu."""
    pygame = _FakePygame([])
    fonts = RenderFonts(
        title=_FakeFont(64),
        body=_FakeFont(28),
    )
    window_settings = WindowSettings()
    pause_menu = PauseMenu()
    pause_menu.move_next()

    render_pause_menu(pygame.surface, fonts, window_settings, pause_menu)

    assert "Resume" in pygame.surface.rendered_texts
    assert "> Return to Main Menu <" in pygame.surface.rendered_texts
