"""Graphical application shell for Pacman."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
import importlib
from typing import Final, Protocol, cast


@dataclass(frozen=True)
class WindowSettings:
    """Settings for the initial Pacman window."""

    title: str = "Pacman"
    width: int = 448
    height: int = 496
    frames_per_second: int = 60
    background_color: tuple[int, int, int] = (0, 0, 0)


class GameState(Enum):
    """High-level application states."""

    MAIN_MENU = "Main Menu"
    PLAYING = "Playing"
    END_SCREEN = "End Screen"


@dataclass(frozen=True)
class StateControls:
    """Keyboard controls for state transitions."""

    confirm_keys: frozenset[int]
    end_screen_key: int
    main_menu_key: int


class GameStateController:
    """Track and update the current game state."""

    def __init__(self, initial_state: GameState = GameState.MAIN_MENU) -> None:
        """Initialize the controller with a starting state."""
        self._state = initial_state

    @property
    def state(self) -> GameState:
        """Return the current game state."""
        return self._state

    def handle_key(self, key: int, controls: StateControls) -> None:
        """Apply a state transition for a pressed key."""
        if self._state is GameState.MAIN_MENU:
            if key in controls.confirm_keys:
                self._state = GameState.PLAYING
            return

        if self._state is GameState.PLAYING:
            if key == controls.end_screen_key:
                self._state = GameState.END_SCREEN
            elif key == controls.main_menu_key:
                self._state = GameState.MAIN_MENU
            return

        if self._state is GameState.END_SCREEN:
            if key in controls.confirm_keys or key == controls.main_menu_key:
                self._state = GameState.MAIN_MENU


_STATE_BACKGROUNDS: Final = {
    GameState.MAIN_MENU: (16, 24, 72),
    GameState.PLAYING: (0, 0, 0),
    GameState.END_SCREEN: (72, 16, 24),
}


class _Event(Protocol):
    type: int


class _KeyboardEvent(Protocol):
    type: int
    key: int


class _EventModule(Protocol):
    def get(self) -> Iterable[object]:
        """Return pending graphical events."""


class _Surface(Protocol):
    def fill(self, color: tuple[int, int, int]) -> None:
        """Fill the window surface."""


class _DisplayModule(Protocol):
    def set_mode(self, size: tuple[int, int]) -> object:
        """Create the graphical window surface."""

    def set_caption(self, title: str) -> None:
        """Set the graphical window title."""

    def flip(self) -> None:
        """Present the latest frame."""


class _Clock(Protocol):
    def tick(self, framerate: int) -> int:
        """Limit the loop to the requested frame rate."""


class _TimeModule(Protocol):
    def Clock(self) -> _Clock:
        """Create a frame-rate clock."""


class _PygameModule(Protocol):
    QUIT: int
    KEYDOWN: int
    K_RETURN: int
    K_SPACE: int
    K_e: int
    K_ESCAPE: int
    display: _DisplayModule
    event: _EventModule
    time: _TimeModule

    def init(self) -> tuple[int, int]:
        """Initialize pygame modules."""

    def quit(self) -> None:
        """Shut down pygame modules."""


def _load_pygame() -> _PygameModule:
    """Load pygame only when the graphical app starts."""
    return cast(_PygameModule, importlib.import_module("pygame"))


def _create_state_controls(pygame_instance: _PygameModule) -> StateControls:
    """Create state controls from pygame key constants."""
    return StateControls(
        confirm_keys=frozenset({
            pygame_instance.K_RETURN,
            pygame_instance.K_SPACE,
        }),
        end_screen_key=pygame_instance.K_e,
        main_menu_key=pygame_instance.K_ESCAPE,
    )


def _render_state(
    screen: _Surface,
    pygame_instance: _PygameModule,
    window_settings: WindowSettings,
    state: GameState,
) -> None:
    """Render the minimal visual representation of a state."""
    background_color = (
        window_settings.background_color
        if state is GameState.PLAYING
        else _STATE_BACKGROUNDS[state]
    )
    screen.fill(background_color)
    pygame_instance.display.set_caption(
        f"{window_settings.title} - {state.value}",
    )


def run_app(
    settings: WindowSettings | None = None,
    pygame_module: object | None = None,
) -> None:
    """Open the Pacman window and run until the user closes it."""
    window_settings = settings or WindowSettings()
    pygame_instance = (
        cast(_PygameModule, pygame_module)
        if pygame_module is not None
        else _load_pygame()
    )

    pygame_instance.init()
    try:
        screen = cast(
            _Surface,
            pygame_instance.display.set_mode(
                (window_settings.width, window_settings.height),
            ),
        )
        clock = pygame_instance.time.Clock()
        controls = _create_state_controls(pygame_instance)
        controller = GameStateController()
        running = True

        while running:
            for event in pygame_instance.event.get():
                event_type = cast(_Event, event).type
                if event_type == pygame_instance.QUIT:
                    running = False
                elif event_type == pygame_instance.KEYDOWN:
                    controller.handle_key(
                        cast(_KeyboardEvent, event).key,
                        controls,
                    )

            _render_state(
                screen,
                pygame_instance,
                window_settings,
                controller.state,
            )
            pygame_instance.display.flip()
            clock.tick(window_settings.frames_per_second)
    finally:
        pygame_instance.quit()
