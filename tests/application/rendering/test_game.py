"""Focused tests for the game view and heads-up display."""

from pacman.app import (
    RenderFonts,
    WindowSettings,
    render_game_view,
    render_hud,
)
from pacman.application.context import GameSession
from pacman.application.context import AppContext
from pacman.application.rendering.game import (
    GHOST_RADIUS_RATIO,
    PACMAN_RADIUS_RATIO,
)
from pacman.application.scaling import calculate_maze_viewport
from pacman.application.sprites import GHOST_PALETTES, PACMAN_YELLOW
from pacman.infrastructure.config import GameConfig
from pacman.maze.level_generator import LevelGenerator
from tests.support.app_fakes import _FakeFont, _FakePygame
from tests.support.gameplay_fakes import FixedMazeAdapter


def _fonts() -> RenderFonts:
    """Return deterministic fonts for rendering assertions."""
    return RenderFonts(title=_FakeFont(64), body=_FakeFont(28))


def test_game_view_renders_placeholder_and_session_values() -> None:
    """Verify the current game shell renders its HUD and session values."""
    pygame = _FakePygame([])
    session = GameSession(lives=7, score=120, remaining_level_time=42.0)

    render_game_view(
        pygame.surface,
        _fonts(),
        WindowSettings(),
        session,
    )

    assert "Game View" in pygame.surface.rendered_texts
    assert "Press E to End" in pygame.surface.rendered_texts
    assert "SCORE: 120" in pygame.surface.rendered_texts
    assert "LIVES: 7" in pygame.surface.rendered_texts
    assert "Lives: 7 | Score: 120" in pygame.surface.rendered_texts


def test_game_view_renders_generated_level_and_entities() -> None:
    """Verify the active maze, pellets, player, and ghosts are visible."""
    pygame = _FakePygame([])
    context = AppContext(config=GameConfig())
    context.level_generator = LevelGenerator(
        config=context.config,
        adapter=FixedMazeAdapter(),
    )
    context.start_new_game()
    assert context.active_level is not None
    assert context.player is not None
    assert context.ghost_gameplay is not None

    render_game_view(
        pygame.surface,
        _fonts(),
        WindowSettings(),
        context.session,
        draw=pygame.draw,
        active_level=context.active_level,
        player=context.player,
        ghosts=context.ghost_gameplay.ghosts,
    )

    assert pygame.draw.rectangles
    assert pygame.draw.circles
    assert "Game View" not in pygame.surface.rendered_texts
    assert "Press E to End" not in pygame.surface.rendered_texts

    viewport = calculate_maze_viewport(
        window_width=WindowSettings().width,
        window_height=WindowSettings().height,
        grid_width=context.active_level.maze.width,
        grid_height=context.active_level.maze.height,
    )
    pacman_circles = [
        circle
        for circle in pygame.draw.circles
        if circle[0] == PACMAN_YELLOW
    ]
    ghost_circles = [
        circle
        for circle in pygame.draw.circles
        if circle[0] in GHOST_PALETTES.values()
    ]
    assert pacman_circles[0][2] == viewport.tile_size * PACMAN_RADIUS_RATIO
    assert all(
        circle[2] == viewport.tile_size * GHOST_RADIUS_RATIO
        for circle in ghost_circles
    )


def test_default_window_keeps_first_level_tiles_comfortably_sized() -> None:
    """Verify the default viewport does not shrink gameplay to tiny tiles."""
    settings = WindowSettings()
    assert settings.width == 900
    assert settings.height == 800


def test_hud_renders_default_metrics_and_background() -> None:
    """Verify default HUD content and bar geometry."""
    pygame = _FakePygame([])
    settings = WindowSettings(width=520, height=496)

    render_hud(pygame.surface, _fonts(), settings)

    assert ((12, 16, 36), (0, 0, 520, 40)) in (
        pygame.surface.fill_rectangles
    )
    assert ((82, 113, 214), (0, 38, 520, 2)) in (
        pygame.surface.fill_rectangles
    )
    assert pygame.surface.rendered_texts == [
        "SCORE: 0",
        "LIVES: 3",
        "LEVEL: 1",
        "TIME: 90s",
    ]


def test_hud_renders_active_session_values() -> None:
    """Verify the HUD reads live score, life, level, and timer values."""
    pygame = _FakePygame([])
    session = GameSession(
        score=1450,
        lives=2,
        current_level=3,
        remaining_level_time=42.1,
    )

    render_hud(pygame.surface, _fonts(), WindowSettings(), session)

    assert pygame.surface.rendered_texts == [
        "SCORE: 1450",
        "LIVES: 2",
        "LEVEL: 4",
        "TIME: 43s",
    ]


def test_hud_renders_cheat_controls_and_active_effects() -> None:
    """Verify evaluation controls and all enabled effects stay visible."""
    pygame = _FakePygame([])

    render_hud(
        pygame.surface,
        _fonts(),
        WindowSettings(),
        GameSession(),
        cheat_mode_enabled=True,
        invincibility_enabled=True,
        ghost_freeze_enabled=True,
        speed_boost_enabled=True,
    )

    assert "CHEAT MODE: ON (F1 to disable)" in pygame.surface.rendered_texts
    assert "1 Invincible | 2 Skip | 3 Freeze" in (
        pygame.surface.rendered_texts
    )
    assert "4 Extra Life | 5 Speed Boost" in pygame.surface.rendered_texts
    assert "ACTIVE: INVINCIBLE | GHOST FREEZE | SPEED BOOST" in (
        pygame.surface.rendered_texts
    )


def test_hud_renders_urgent_low_time_and_life_values() -> None:
    """Verify urgent values remain visible at their rounded values."""
    pygame = _FakePygame([])
    session = GameSession(lives=1, remaining_level_time=8.5)

    render_hud(pygame.surface, _fonts(), WindowSettings(), session)

    assert "LIVES: 1" in pygame.surface.rendered_texts
    assert "TIME: 9s" in pygame.surface.rendered_texts
