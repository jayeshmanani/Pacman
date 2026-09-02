"""Application tests for the pygame window lifecycle and event loop."""

import pytest

from pacman.app import WindowSettings, run_app
from tests.support.app_fakes import (
    _FailingPygame,
    _FakeEvent,
    _FakePygame,
)


def test_run_app_opens_configured_pygame_window() -> None:
    """Verify that the app initializes pygame and configures the window."""
    pygame = _FakePygame([[_FakeEvent(type=_FakePygame.QUIT)]])

    run_app(
        WindowSettings(
            title="Pacman Test",
            width=320,
            height=240,
            frames_per_second=30,
            background_color=(1, 2, 3),
        ),
        pygame_module=pygame,
    )

    assert pygame.init_calls == 1
    assert pygame.display.size == (320, 240)
    assert pygame.display.caption == "Pacman Test - Main Menu"
    assert pygame.surface.fill_colors == [(16, 24, 72)]
    assert pygame.surface.rendered_texts == [
        "PACMAN",
        "> Start Game <",
        "View Highscores",
        "Instructions",
        "Exit",
    ]
    assert pygame.font.created_fonts == [(None, 64), (None, 28)]
    assert pygame.display.flip_calls == 1
    assert pygame.clock.framerates == [30]


def test_event_loop_applies_state_transitions() -> None:
    """Verify that the pygame loop routes key presses to the controller."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_e)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_SPACE)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert pygame.display.captions == [
        "Pacman - Playing",
        "Pacman - End Screen",
        "Pacman - Main Menu",
        "Pacman - Main Menu",
    ]
    assert pygame.surface.fill_colors == [
        (0, 0, 0),
        (72, 16, 24),
        (16, 24, 72),
        (16, 24, 72),
    ]
    assert pygame.clock.framerates == [60, 60, 60, 60]


def test_menu_highscores_action_transitions_to_highscores() -> None:
    """Verify the main menu opens the highscores screen."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert pygame.display.captions == [
        "Pacman - Main Menu",
        "Pacman - Highscores",
        "Pacman - Highscores",
    ]


def test_menu_instructions_action_transitions_to_instructions() -> None:
    """Verify the main menu opens the instructions screen."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert pygame.display.captions == [
        "Pacman - Main Menu",
        "Pacman - Main Menu",
        "Pacman - Instructions",
        "Pacman - Instructions",
    ]


def test_highscores_screen_can_return_to_main_menu() -> None:
    """Verify Escape returns from highscores to the main menu."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert pygame.display.captions == [
        "Pacman - Main Menu",
        "Pacman - Highscores",
        "Pacman - Main Menu",
        "Pacman - Main Menu",
    ]


def test_menu_exit_action_stops_application_cleanly() -> None:
    """Verify the main menu Exit option shuts down the pygame app."""
    pygame = _FakePygame([
        [
            _FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN),
            _FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN),
            _FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN),
            _FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN),
        ],
    ])

    run_app(pygame_module=pygame)

    assert pygame.quit_calls == 1
    assert pygame.display.flip_calls == 1
    assert "> Exit <" in pygame.surface.rendered_texts


def test_pygame_quit_event_stops_application() -> None:
    """Verify that pygame QUIT still exits the loop cleanly."""
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame)

    assert pygame.display.flip_calls == 1
    assert pygame.quit_calls == 1


def test_pygame_quits_when_window_setup_fails() -> None:
    """Verify that pygame is shut down if startup raises."""
    pygame = _FailingPygame()

    with pytest.raises(RuntimeError, match="display failed"):
        run_app(pygame_module=pygame)

    assert pygame.init_calls == 1
    assert pygame.quit_calls == 1
