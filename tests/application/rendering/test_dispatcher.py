"""Tests for application-state rendering dispatch."""

from pacman.app import (
    GameState,
    GameStateController,
    RenderFonts,
    WindowSettings,
    render_state,
)
from tests.support.app_fakes import _FakeFont, _FakePygame


def test_rendering_does_not_change_current_game_state() -> None:
    """Verify rendering remains a read-only operation."""
    controller = GameStateController(GameState.PLAYING)
    pygame = _FakePygame([])
    fonts = RenderFonts(title=_FakeFont(64), body=_FakeFont(28))

    render_state(
        pygame.surface,
        fonts,
        pygame,
        WindowSettings(),
        controller.state,
    )

    assert controller.state is GameState.PLAYING
    assert pygame.display.caption == "Pacman - Playing"
