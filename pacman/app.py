"""Graphical application shell for Pacman."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
import importlib
from typing import Final, Protocol, cast

Color = tuple[int, int, int]


@dataclass(frozen=True)
class WindowSettings:
    """Settings for the initial Pacman window."""

    title: str = "Pacman"
    width: int = 448
    height: int = 496
    frames_per_second: int = 60
    background_color: Color = (0, 0, 0)


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


@dataclass(frozen=True)
class RenderFonts:
    """Fonts reused by the placeholder renderers."""

    title: "_Font"
    body: "_Font"


class _Event(Protocol):
    type: int


class _KeyboardEvent(Protocol):
    type: int
    key: int


class _EventModule(Protocol):
    def get(self) -> Iterable[object]:
        """Return pending graphical events."""


class _Surface(Protocol):
    def fill(self, color: Color) -> None:
        """Fill the window surface."""

    def blit(self, source: object, destination: object) -> object:
        """Draw one surface onto another."""


class _RenderedText(Protocol):
    def get_rect(self, **kwargs: object) -> object:
        """Return a rectangle for positioning rendered text."""


class _Font(Protocol):
    def render(
        self,
        text: str,
        antialias: bool,
        color: Color,
    ) -> _RenderedText:
        """Render text to a surface-like object."""


class _FontModule(Protocol):
    def SysFont(self, name: str | None, size: int) -> _Font:
        """Create a system font."""


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
    font: _FontModule
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


def _create_render_fonts(pygame_instance: _PygameModule) -> RenderFonts:
    """Create fonts once for reuse across frames."""
    return RenderFonts(
        title=pygame_instance.font.SysFont(None, 64),
        body=pygame_instance.font.SysFont(None, 28),
    )


def _draw_centered_text(
    screen: _Surface,
    font: _Font,
    text: str,
    color: Color,
    center: tuple[int, int],
) -> None:
    """Render text centered on the screen."""
    rendered_text = font.render(text, True, color)
    text_rectangle = rendered_text.get_rect(center=center)
    screen.blit(rendered_text, text_rectangle)


def render_main_menu(
    screen: _Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
) -> None:
    """Render the placeholder main menu."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2

    screen.fill(_STATE_BACKGROUNDS[GameState.MAIN_MENU])
    _draw_centered_text(
        screen,
        fonts.title,
        "PACMAN",
        (255, 230, 0),
        (center_x, center_y - 40),
    )
    _draw_centered_text(
        screen,
        fonts.body,
        "Press Enter or Space to Start",
        (255, 255, 255),
        (center_x, center_y + 24),
    )


def render_game_view(
    screen: _Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
) -> None:
    """Render the placeholder game view."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2

    screen.fill(window_settings.background_color)
    _draw_centered_text(
        screen,
        fonts.title,
        "Game View",
        (255, 255, 255),
        (center_x, center_y - 24),
    )
    _draw_centered_text(
        screen,
        fonts.body,
        "Press E to End",
        (255, 230, 0),
        (center_x, center_y + 32),
    )


def render_end_screen(
    screen: _Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
) -> None:
    """Render the minimal end screen placeholder."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2

    screen.fill(_STATE_BACKGROUNDS[GameState.END_SCREEN])
    _draw_centered_text(
        screen,
        fonts.title,
        "End Screen",
        (255, 255, 255),
        (center_x, center_y - 24),
    )
    _draw_centered_text(
        screen,
        fonts.body,
        "Press Enter or Space for Menu",
        (255, 230, 0),
        (center_x, center_y + 32),
    )


def render_state(
    screen: _Surface,
    fonts: RenderFonts,
    pygame_module: object,
    window_settings: WindowSettings,
    state: GameState,
) -> None:
    """Render the minimal visual representation of a state."""
    pygame_instance = cast(_PygameModule, pygame_module)

    if state is GameState.MAIN_MENU:
        render_main_menu(screen, fonts, window_settings)
    elif state is GameState.PLAYING:
        render_game_view(screen, fonts, window_settings)
    else:
        render_end_screen(screen, fonts, window_settings)

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
        fonts = _create_render_fonts(pygame_instance)
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

            render_state(
                screen,
                fonts,
                pygame_instance,
                window_settings,
                controller.state,
            )
            pygame_instance.display.flip()
            clock.tick(window_settings.frames_per_second)
    finally:
        pygame_instance.quit()
