"""Verify the real pygame orchestration reaches live gameplay models."""

from pacman.app import run_app
from pacman.application.sprites import PACMAN_YELLOW
from tests.support.app_fakes import _FakeEvent, _FakePygame


def test_direction_event_moves_the_rendered_player_between_frames() -> None:
    """Verify keyboard input changes Pac-Man's visible screen position."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_UP)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])
    pygame.clock.elapsed_ms = 100

    run_app(pygame_module=pygame)

    pacman_centers = [
        center
        for color, center, _, _ in pygame.draw.circles
        if color == PACMAN_YELLOW
    ]
    assert len(pacman_centers) == 3
    assert pacman_centers[-1][1] < pacman_centers[0][1]
