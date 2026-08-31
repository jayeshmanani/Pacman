"""Rendering functions for the current application states."""

from dataclasses import dataclass
from typing import Final, cast

from pacman.application.contracts import Color, Font, PygameModule, Surface
from pacman.application.state import GameState
from pacman.application.context import AppContext, GameSession
from pacman.infrastructure.highscore import HighscoreEntry


@dataclass(frozen=True)
class WindowSettings:
    """Settings for the initial Pacman window."""

    title: str = "Pacman"
    width: int = 448
    height: int = 496
    frames_per_second: int = 60
    background_color: Color = (0, 0, 0)


@dataclass(frozen=True)
class RenderFonts:
    """Fonts reused by the placeholder renderers."""

    title: Font
    body: Font


_STATE_BACKGROUNDS: Final = {
    GameState.MAIN_MENU: (16, 24, 72),
    GameState.PLAYING: (0, 0, 0),
    GameState.END_SCREEN: (72, 16, 24),
}


def create_render_fonts(pygame_instance: PygameModule) -> RenderFonts:
    """Create fonts once for reuse across frames."""
    return RenderFonts(
        title=pygame_instance.font.SysFont(None, 64),
        body=pygame_instance.font.SysFont(None, 28),
    )


def _draw_centered_text(
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


def render_main_menu(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    highscores: list[HighscoreEntry] | None = None,
) -> None:
    """Render the main menu and any loaded highscore entries."""
    center_x = window_settings.width // 2
    screen.fill(_STATE_BACKGROUNDS[GameState.MAIN_MENU])
    _draw_centered_text(
        screen, fonts.title, "PACMAN", (255, 230, 0), (center_x, 56)
    )
    _draw_centered_text(
        screen,
        fonts.body,
        "Press Enter or Space to Start",
        (255, 255, 255),
        (center_x, 118),
    )

    if highscores:
        _draw_centered_text(
            screen, fonts.body, "HIGHSCORES", (255, 230, 0), (center_x, 158)
        )
        for position, entry in enumerate(highscores, start=1):
            _draw_centered_text(
                screen,
                fonts.body,
                f"{position}. {entry.name}  {entry.score}",
                (255, 255, 255),
                (center_x, 158 + position * 26),
            )


def render_game_view(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
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
    if session is not None:
        _draw_centered_text(
            screen,
            fonts.body,
            f"Lives: {session.lives} | Score: {session.score}",
            (255, 255, 255),
            (center_x, center_y + 64),
        )


def render_end_screen(
    screen: Surface,
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
    screen: Surface,
    fonts: RenderFonts,
    pygame_module: object,
    window_settings: WindowSettings,
    state: GameState,
    context: AppContext | None = None,
) -> None:
    """Render the minimal visual representation of a state."""
    pygame_instance = cast(PygameModule, pygame_module)

    if state is GameState.MAIN_MENU:
        render_main_menu(
            screen,
            fonts,
            window_settings,
            context.highscores if context is not None else None,
        )
    elif state is GameState.PLAYING:
        render_game_view(
            screen,
            fonts,
            window_settings,
            context.session if context is not None else None,
        )
    else:
        render_end_screen(screen, fonts, window_settings)

    pygame_instance.display.set_caption(
        f"{window_settings.title} - {state.value}"
    )
