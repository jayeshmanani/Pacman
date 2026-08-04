"""Tests for the pygame application shell."""

from dataclasses import dataclass

import pytest

from pacman.app import (
    GameState,
    GameStateController,
    StateControls,
    WindowSettings,
    run_app,
)


@dataclass(frozen=True, kw_only=True)
class _FakeEvent:
    type: int
    key: int = 0


class _FakeEventModule:
    def __init__(self, event_batches: list[list[_FakeEvent]]) -> None:
        self.event_batches = event_batches

    def get(self) -> list[_FakeEvent]:
        if not self.event_batches:
            return []

        return self.event_batches.pop(0)


class _FakeSurface:
    def __init__(self) -> None:
        self.fill_colors: list[tuple[int, int, int]] = []

    def fill(self, color: tuple[int, int, int]) -> None:
        self.fill_colors.append(color)


class _FakeDisplay:
    def __init__(self, surface: _FakeSurface) -> None:
        self.surface = surface
        self.caption = ""
        self.captions: list[str] = []
        self.size: tuple[int, int] | None = None
        self.flip_calls = 0

    def set_mode(self, size: tuple[int, int]) -> _FakeSurface:
        self.size = size
        return self.surface

    def set_caption(self, title: str) -> None:
        self.caption = title
        self.captions.append(title)

    def flip(self) -> None:
        self.flip_calls += 1


class _FailingDisplay:
    def set_mode(self, size: tuple[int, int]) -> _FakeSurface:
        raise RuntimeError("display failed")

    def set_caption(self, title: str) -> None:
        raise AssertionError("caption should not be set")

    def flip(self) -> None:
        raise AssertionError("frame should not be presented")


class _FakeClock:
    def __init__(self) -> None:
        self.framerates: list[int] = []

    def tick(self, framerate: int) -> int:
        self.framerates.append(framerate)
        return 0


class _FakeTime:
    def __init__(self, clock: _FakeClock) -> None:
        self.clock = clock

    def Clock(self) -> _FakeClock:
        return self.clock


class _FakePygame:
    QUIT = 256
    KEYDOWN = 768
    K_RETURN = 13
    K_SPACE = 32
    K_e = 101
    K_ESCAPE = 27

    def __init__(self, event_batches: list[list[_FakeEvent]]) -> None:
        self.surface = _FakeSurface()
        self.display = _FakeDisplay(self.surface)
        self.event = _FakeEventModule(event_batches)
        self.clock = _FakeClock()
        self.time = _FakeTime(self.clock)
        self.init_calls = 0
        self.quit_calls = 0

    def init(self) -> tuple[int, int]:
        self.init_calls += 1
        return (1, 0)

    def quit(self) -> None:
        self.quit_calls += 1


class _FailingPygame:
    QUIT = 256
    KEYDOWN = 768
    K_RETURN = 13
    K_SPACE = 32
    K_e = 101
    K_ESCAPE = 27

    def __init__(self) -> None:
        self.surface = _FakeSurface()
        self.display = _FailingDisplay()
        self.event = _FakeEventModule([])
        self.clock = _FakeClock()
        self.time = _FakeTime(self.clock)
        self.init_calls = 0
        self.quit_calls = 0

    def init(self) -> tuple[int, int]:
        self.init_calls += 1
        return (1, 0)

    def quit(self) -> None:
        self.quit_calls += 1


def test_initial_state_is_main_menu() -> None:
    """Verify that the state controller starts on the main menu."""
    controller = GameStateController()

    assert controller.state is GameState.MAIN_MENU


def test_main_menu_transitions_to_playing() -> None:
    """Verify that confirm starts the game from the main menu."""
    controller = GameStateController()

    controller.handle_key(_FakePygame.K_RETURN, _state_controls())

    assert controller.state is GameState.PLAYING


def test_playing_transitions_to_end_screen() -> None:
    """Verify that the temporary end key finishes play."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_e, _state_controls())

    assert controller.state is GameState.END_SCREEN


def test_end_screen_transitions_to_main_menu() -> None:
    """Verify that confirm returns from the end screen to the main menu."""
    controller = GameStateController(GameState.END_SCREEN)

    controller.handle_key(_FakePygame.K_SPACE, _state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_escape_returns_from_playing_to_main_menu() -> None:
    """Verify that Escape returns from playing to the main menu."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_ESCAPE, _state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_escape_returns_from_end_screen_to_main_menu() -> None:
    """Verify that Escape returns from the end screen to the main menu."""
    controller = GameStateController(GameState.END_SCREEN)

    controller.handle_key(_FakePygame.K_ESCAPE, _state_controls())

    assert controller.state is GameState.MAIN_MENU


def test_irrelevant_key_does_not_change_state() -> None:
    """Verify that irrelevant keys do not trigger transitions."""
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(999, _state_controls())

    assert controller.state is GameState.PLAYING


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


def _state_controls() -> StateControls:
    return StateControls(
        confirm_keys=frozenset({
            _FakePygame.K_RETURN,
            _FakePygame.K_SPACE,
        }),
        end_screen_key=_FakePygame.K_e,
        main_menu_key=_FakePygame.K_ESCAPE,
    )
