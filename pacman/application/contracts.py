"""Small pygame protocols used by the application layer."""

from collections.abc import Iterable
from typing import Protocol

Color = tuple[int, int, int]
Rectangle = tuple[int, int, int, int]


Coordinate = tuple[int, int]


class Event(Protocol):
    """Describe the common part of a pygame event."""

    type: int


class KeyboardEvent(Protocol):
    """Describe a pygame keyboard event."""

    type: int
    key: int
    unicode: str


class EventModule(Protocol):
    """Describe pygame's event module."""

    def get(self) -> Iterable[object]:
        """Return pending graphical events."""


class Surface(Protocol):
    """Describe the drawing operations used by the renderers."""

    def fill(self, color: Color, rectangle: Rectangle | None = None) -> None:
        """Fill the window surface."""

    def blit(self, source: object, destination: object) -> object:
        """Draw one surface onto another."""


class DrawModule(Protocol):
    """Describe pygame's draw module operations."""

    def circle(
        self,
        surface: Surface,
        color: Color,
        center: Coordinate,
        radius: float,
        width: int = 0,
    ) -> None:
        """Draw a circle on a surface."""

    def rect(
        self,
        surface: Surface,
        color: Color,
        rect: Rectangle,
        width: int = 0,
        border_radius: int = 0,
    ) -> None:
        """Draw a rectangle on a surface."""

    def polygon(
        self,
        surface: Surface,
        color: Color,
        points: list[Coordinate],
        width: int = 0,
    ) -> None:
        """Draw a polygon on a surface."""

    def line(
        self,
        surface: Surface,
        color: Color,
        start_pos: Coordinate,
        end_pos: Coordinate,
        width: int = 1,
    ) -> None:
        """Draw a straight line segment on a surface."""


class RenderedText(Protocol):
    """Describe rendered text returned by a font."""

    def get_rect(self, **kwargs: object) -> object:
        """Return a rectangle for positioning rendered text."""


class Font(Protocol):
    """Describe the font method used by the renderers."""

    def render(
        self,
        text: str,
        antialias: bool,
        color: Color,
    ) -> RenderedText:
        """Render text to a surface-like object."""


class FontModule(Protocol):
    """Describe pygame's font module."""

    def SysFont(self, name: str | None, size: int) -> Font:
        """Create a system font."""


class DisplayModule(Protocol):
    """Describe pygame's display module."""

    def set_mode(self, size: tuple[int, int]) -> object:
        """Create the graphical window surface."""

    def set_caption(self, title: str) -> None:
        """Set the graphical window title."""

    def flip(self) -> None:
        """Present the latest frame."""


class Clock(Protocol):
    """Describe pygame's frame clock."""

    def tick(self, framerate: int) -> int:
        """Limit the loop to the requested frame rate."""


class TimeModule(Protocol):
    """Describe pygame's time module."""

    def Clock(self) -> Clock:
        """Create a frame-rate clock."""


class PygameModule(Protocol):
    """Describe the pygame surface required by the application runtime."""

    QUIT: int
    KEYDOWN: int
    K_RETURN: int
    K_SPACE: int
    K_UP: int
    K_DOWN: int
    K_BACKSPACE: int
    K_e: int
    K_ESCAPE: int
    K_p: int
    display: DisplayModule
    draw: DrawModule
    event: EventModule
    font: FontModule
    time: TimeModule

    def init(self) -> tuple[int, int]:
        """Initialize pygame modules."""

    def quit(self) -> None:
        """Shut down pygame modules."""
