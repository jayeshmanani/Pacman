"""Shared rendering values and text helpers."""

from dataclasses import dataclass
from typing import Final

from pacman.application.contracts import Color, Font, PygameModule, Surface
from pacman.application.state import GameState


@dataclass(frozen=True)
class WindowSettings:
    """Settings for the Pacman window."""

    title: str = "Pacman"
    width: int = 900
    height: int = 800
    frames_per_second: int = 60
    background_color: Color = (0, 0, 0)


@dataclass(frozen=True)
class RenderFonts:
    """Fonts reused by application renderers."""

    title: Font
    body: Font


STATE_BACKGROUNDS: Final = {
    GameState.MAIN_MENU: (16, 24, 72),
    GameState.PLAYING: (0, 0, 0),
    GameState.PAUSED: (16, 24, 72),
    GameState.HIGHSCORES: (20, 62, 50),
    GameState.INSTRUCTIONS: (16, 24, 72),
    GameState.END_SCREEN: (72, 16, 24),
    GameState.GAME_OVER: (72, 16, 24),
    GameState.VICTORY: (16, 72, 40),
}


def create_render_fonts(pygame_instance: PygameModule) -> RenderFonts:
    """Create fonts once for reuse across frames."""
    return RenderFonts(
        title=pygame_instance.font.SysFont(None, 64),
        body=pygame_instance.font.SysFont(None, 28),
    )


def draw_centered_text(
    screen: Surface,
    font: Font,
    text: str,
    color: Color,
    center: tuple[int, int],
) -> None:
    """Render text centered on the screen."""
    rendered_text = font.render(text, True, color)
    text_rectangle = rendered_text.get_rect(center=center)
    screen.blit(rendered_text, text_rectangle)


def draw_left_text(
    screen: Surface,
    font: Font,
    text: str,
    color: Color,
    midleft: tuple[int, int],
) -> None:
    """Render text from a consistent left edge."""
    rendered_text = font.render(text, True, color)
    text_rectangle = rendered_text.get_rect(midleft=midleft)
    screen.blit(rendered_text, text_rectangle)
