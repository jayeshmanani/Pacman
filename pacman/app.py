"""Graphical application shell for Pacman."""

from collections.abc import Iterable
from dataclasses import dataclass
import importlib
from typing import Protocol, cast


@dataclass(frozen=True)
class WindowSettings:
    """Settings for the initial Pacman window."""

    title: str = "Pacman"
    width: int = 448
    height: int = 496
    frames_per_second: int = 60
    background_color: tuple[int, int, int] = (0, 0, 0)


class _Event(Protocol):
    type: int


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
        pygame_instance.display.set_caption(window_settings.title)
        clock = pygame_instance.time.Clock()
        running = True

        while running:
            for event in pygame_instance.event.get():
                if cast(_Event, event).type == pygame_instance.QUIT:
                    running = False

            screen.fill(window_settings.background_color)
            pygame_instance.display.flip()
            clock.tick(window_settings.frames_per_second)
    finally:
        pygame_instance.quit()
