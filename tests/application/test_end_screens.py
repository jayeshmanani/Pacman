"""Application rendering tests for distinct Game Over and Victory screens."""

from pacman.app import (
    GameState,
    RenderFonts,
    WindowSettings,
    render_end_screen,
    render_game_over_screen,
    render_state,
    render_victory_screen,
)
from pacman.application.context import AppContext, GameSession
from tests.support.app_fakes import _FakeFont, _FakePygame, _FakeSurface


def _test_fonts() -> RenderFonts:
    """Create test fonts for render calls."""
    return RenderFonts(
        title=_FakeFont(64),
        body=_FakeFont(28),
    )


def test_render_game_over_screen_out_of_lives() -> None:
    """Verify Game Over screen renders score and out-of-lives message."""
    surface = _FakeSurface()
    fonts = _test_fonts()
    settings = WindowSettings()
    session = GameSession(score=1250, lives=0)

    render_game_over_screen(surface, fonts, settings, session)

    assert surface.fill_colors == [(72, 16, 24)]
    assert surface.rendered_texts == [
        "GAME OVER",
        "OUT OF LIVES!",
        "FINAL SCORE: 1250",
        "Press Enter or Space to Continue",
    ]


def test_render_game_over_screen_time_expired() -> None:
    """Verify Game Over screen renders time expired message on timeout."""
    surface = _FakeSurface()
    fonts = _test_fonts()
    settings = WindowSettings()
    session = GameSession(score=450, lives=2, level_timed_out=True)

    render_game_over_screen(surface, fonts, settings, session)

    assert surface.fill_colors == [(72, 16, 24)]
    assert surface.rendered_texts == [
        "GAME OVER",
        "TIME EXPIRED!",
        "FINAL SCORE: 450",
        "Press Enter or Space to Continue",
    ]


def test_render_victory_screen() -> None:
    """Verify Victory screen renders congratulatory text and final score."""
    surface = _FakeSurface()
    fonts = _test_fonts()
    settings = WindowSettings()
    session = GameSession(score=9900, is_victory=True)

    render_victory_screen(surface, fonts, settings, session)

    assert surface.fill_colors == [(16, 72, 40)]
    assert surface.rendered_texts == [
        "VICTORY!",
        "YOU CLEARED ALL LEVELS!",
        "FINAL SCORE: 9900",
        "Press Enter or Space to Continue",
    ]


def test_render_end_screen_delegates_based_on_session_victory() -> None:
    """Verify render_end_screen routes to victory or game over screen."""
    surface_loss = _FakeSurface()
    surface_win = _FakeSurface()
    fonts = _test_fonts()
    settings = WindowSettings()

    session_loss = GameSession(score=300, lives=0)
    render_end_screen(surface_loss, fonts, settings, session_loss)
    assert "GAME OVER" in surface_loss.rendered_texts

    session_win = GameSession(score=5000, is_victory=True)
    render_end_screen(surface_win, fonts, settings, session_win)
    assert "VICTORY!" in surface_win.rendered_texts


def test_render_state_dispatches_game_over_and_victory() -> None:
    """Verify render_state sets window captions for GAME_OVER and VICTORY."""
    surface = _FakeSurface()
    fonts = _test_fonts()
    settings = WindowSettings()
    pygame = _FakePygame([])
    context = AppContext()
    context.session.score = 750

    render_state(
        surface,
        fonts,
        pygame,
        settings,
        GameState.GAME_OVER,
        context,
    )
    assert pygame.display.caption == "Pacman - Game Over"
    assert "GAME OVER" in surface.rendered_texts

    surface = _FakeSurface()
    context.session.is_victory = True
    render_state(
        surface,
        fonts,
        pygame,
        settings,
        GameState.VICTORY,
        context,
    )
    assert pygame.display.caption == "Pacman - Victory"
    assert "VICTORY!" in surface.rendered_texts
