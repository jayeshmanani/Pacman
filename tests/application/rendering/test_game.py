"""Focused tests for the game view and heads-up display."""

from pacman.app import (
    RenderFonts,
    WindowSettings,
    render_game_view,
    render_hud,
)
from pacman.application.context import GameSession
from tests.support.app_fakes import _FakeFont, _FakePygame


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
