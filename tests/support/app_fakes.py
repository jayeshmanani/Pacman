"""Shared pygame fakes for application tests."""

from dataclasses import dataclass

from pacman.app import StateControls

Color = tuple[int, int, int]
Rectangle = tuple[int, int, int, int]
Coordinate = tuple[int, int]


class _FakeDrawModule:
    """Record drawing operations performed by pygame.draw."""

    def __init__(self) -> None:
        self.circles: list[tuple[Color, Coordinate, float, int]] = []
        self.rectangles: list[tuple[Color, Rectangle, int, int]] = []
        self.polygons: list[tuple[Color, list[Coordinate], int]] = []
        self.lines: list[tuple[Color, Coordinate, Coordinate, int]] = []

    def circle(
        self,
        surface: object,
        color: Color,
        center: Coordinate,
        radius: float,
        width: int = 0,
    ) -> None:
        self.circles.append((color, center, radius, width))

    def rect(
        self,
        surface: object,
        color: Color,
        rect: Rectangle,
        width: int = 0,
        border_radius: int = 0,
    ) -> None:
        self.rectangles.append((color, rect, width, border_radius))

    def polygon(
        self,
        surface: object,
        color: Color,
        points: list[Coordinate],
        width: int = 0,
    ) -> None:
        self.polygons.append((color, points, width))

    def line(
        self,
        surface: object,
        color: Color,
        start_pos: Coordinate,
        end_pos: Coordinate,
        width: int = 1,
    ) -> None:
        self.lines.append((color, start_pos, end_pos, width))


@dataclass(frozen=True, kw_only=True)
class _FakeEvent:
    """Represent a minimal pygame event."""

    type: int
    key: int = 0
    unicode: str = ""


class _FakeEventModule:
    """Return configured event batches one frame at a time."""

    def __init__(self, event_batches: list[list[_FakeEvent]]) -> None:
        self.event_batches = event_batches

    def get(self) -> list[_FakeEvent]:
        if not self.event_batches:
            return []
        return self.event_batches.pop(0)


class _FakeSurface:
    """Record drawing operations performed on the fake window."""

    def __init__(self) -> None:
        self.fill_colors: list[Color] = []
        self.fill_rectangles: list[tuple[Color, Rectangle]] = []
        self.rendered_texts: list[str] = []
        self.blit_destinations: list[object] = []

    def fill(self, color: Color, rectangle: Rectangle | None = None) -> None:
        if rectangle is None:
            self.fill_colors.append(color)
        else:
            self.fill_rectangles.append((color, rectangle))

    def blit(self, source: object, destination: object) -> object:
        if isinstance(source, _FakeRenderedText):
            self.rendered_texts.append(source.text)
            self.blit_destinations.append(destination)
        return destination


@dataclass(frozen=True)
class _FakeRenderedText:
    """Represent rendered text without requiring pygame."""

    text: str
    color: Color
    font_size: int

    def get_rect(self, **kwargs: object) -> dict[str, object]:
        return kwargs


class _FakeFont:
    """Create fake rendered text and retain the configured size."""

    def __init__(self, size: int) -> None:
        self.size = size

    def render(
        self,
        text: str,
        antialias: bool,
        color: Color,
    ) -> _FakeRenderedText:
        return _FakeRenderedText(
            text=text,
            color=color,
            font_size=self.size,
        )


class _FakeFontModule:
    """Record font creation calls."""

    def __init__(self) -> None:
        self.created_fonts: list[tuple[str | None, int]] = []

    def SysFont(self, name: str | None, size: int) -> _FakeFont:
        self.created_fonts.append((name, size))
        return _FakeFont(size)


class _FakeDisplay:
    """Record display operations performed by the application."""

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
    """Simulate a failure while creating the application window."""

    def set_mode(self, size: tuple[int, int]) -> _FakeSurface:
        raise RuntimeError("display failed")

    def set_caption(self, title: str) -> None:
        raise AssertionError("caption should not be set")

    def flip(self) -> None:
        raise AssertionError("frame should not be presented")


class _FakeClock:
    """Record requested frame rates."""

    def __init__(self) -> None:
        self.framerates: list[int] = []

    def tick(self, framerate: int) -> int:
        self.framerates.append(framerate)
        return 0


class _FakeTime:
    """Return a shared fake clock."""

    def __init__(self, clock: _FakeClock) -> None:
        self.clock = clock

    def Clock(self) -> _FakeClock:
        return self.clock


class _FakePygame:
    """Provide the pygame API surface required by application tests."""

    QUIT = 256
    KEYDOWN = 768
    K_RETURN = 13
    K_SPACE = 32
    K_UP = 273
    K_DOWN = 274
    K_BACKSPACE = 8
    K_e = 101
    K_ESCAPE = 27
    K_p = 112

    def __init__(self, event_batches: list[list[_FakeEvent]]) -> None:
        self.surface = _FakeSurface()
        self.display = _FakeDisplay(self.surface)
        self.draw = _FakeDrawModule()
        self.event = _FakeEventModule(event_batches)
        self.font = _FakeFontModule()
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
    """Provide pygame with a display that fails during startup."""

    QUIT = 256
    KEYDOWN = 768
    K_RETURN = 13
    K_SPACE = 32
    K_UP = 273
    K_DOWN = 274
    K_BACKSPACE = 8
    K_e = 101
    K_ESCAPE = 27
    K_p = 112

    def __init__(self) -> None:
        self.surface = _FakeSurface()
        self.display = _FailingDisplay()
        self.draw = _FakeDrawModule()
        self.event = _FakeEventModule([])
        self.font = _FakeFontModule()
        self.clock = _FakeClock()
        self.time = _FakeTime(self.clock)
        self.init_calls = 0
        self.quit_calls = 0

    def init(self) -> tuple[int, int]:
        self.init_calls += 1
        return (1, 0)

    def quit(self) -> None:
        self.quit_calls += 1


def state_controls() -> StateControls:
    """Create state controls matching the fake pygame constants."""
    return StateControls(
        confirm_keys=frozenset({
            _FakePygame.K_RETURN,
            _FakePygame.K_SPACE,
        }),
        end_screen_key=_FakePygame.K_e,
        main_menu_key=_FakePygame.K_ESCAPE,
        pause_key=_FakePygame.K_p,
    )
