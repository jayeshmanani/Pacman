"""Rendering functions for the current application states."""

from dataclasses import dataclass
from typing import Final, cast

from pacman.application.contracts import Color, Font, PygameModule, Surface
from pacman.application.menu import MAIN_MENU_OPTIONS, MainMenu
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
    GameState.HIGHSCORES: (20, 62, 50),
    GameState.INSTRUCTIONS: (64, 48, 18),
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
    menu: MainMenu | None = None,
) -> None:
    """Render the main menu and any loaded highscore entries."""
    center_x = window_settings.width // 2
    screen.fill(_STATE_BACKGROUNDS[GameState.MAIN_MENU])
    _draw_centered_text(
        screen, fonts.title, "PACMAN", (255, 230, 0), (center_x, 56)
    )

    menu_options = menu.options if menu is not None else MAIN_MENU_OPTIONS
    selected_index = menu.selected_index if menu is not None else 0
    for index, option in enumerate(menu_options):
        is_selected = index == selected_index
        label = f"> {option.label} <" if is_selected else option.label
        color = (255, 230, 0) if is_selected else (255, 255, 255)
        _draw_centered_text(
            screen,
            fonts.body,
            label,
            color,
            (center_x, 116 + index * 32),
        )

    if highscores:
        _draw_centered_text(
            screen, fonts.body, "HIGHSCORES", (255, 230, 0), (center_x, 278)
        )
        for position, entry in enumerate(highscores, start=1):
            _draw_centered_text(
                screen,
                fonts.body,
                f"{position}. {entry.name}  {entry.score}",
                (255, 255, 255),
                (center_x, 278 + position * 26),
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


def render_highscores_screen(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    highscores: list[HighscoreEntry] | None = None,
) -> None:
    """Render the minimal highscores screen."""
    center_x = window_settings.width // 2
    screen.fill(_STATE_BACKGROUNDS[GameState.HIGHSCORES])
    _draw_centered_text(
        screen, fonts.title, "HIGHSCORES", (255, 230, 0), (center_x, 64)
    )
    if highscores:
        for position, entry in enumerate(highscores, start=1):
            _draw_centered_text(
                screen,
                fonts.body,
                f"{position}. {entry.name}  {entry.score}",
                (255, 255, 255),
                (center_x, 106 + position * 28),
            )
    else:
        _draw_centered_text(
            screen,
            fonts.body,
            "No highscores yet",
            (255, 255, 255),
            (center_x, 148),
        )
    _draw_centered_text(
        screen,
        fonts.body,
        "Press Escape for Menu",
        (255, 230, 0),
        (center_x, window_settings.height - 48),
    )


def render_instructions_screen(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
) -> None:
    """Render the minimal instructions screen."""
    center_x = window_settings.width // 2
    screen.fill(_STATE_BACKGROUNDS[GameState.INSTRUCTIONS])
    _draw_centered_text(
        screen,
        fonts.title,
        "Instructions",
        (255, 230, 0),
        (center_x, 64),
    )
    _draw_centered_text(
        screen,
        fonts.body,
        "Guide Pacman through the maze.",
        (255, 255, 255),
        (center_x, 148),
    )
    _draw_centered_text(
        screen,
        fonts.body,
        "Avoid ghosts and collect pacgums.",
        (255, 255, 255),
        (center_x, 184),
    )
    _draw_centered_text(
        screen,
        fonts.body,
        "Press Escape for Menu",
        (255, 230, 0),
        (center_x, window_settings.height - 48),
    )


def render_state(
    screen: Surface,
    fonts: RenderFonts,
    pygame_module: object,
    window_settings: WindowSettings,
    state: GameState,
    context: AppContext | None = None,
    menu: MainMenu | None = None,
) -> None:
    """Render the minimal visual representation of a state."""
    pygame_instance = cast(PygameModule, pygame_module)

    if state is GameState.MAIN_MENU:
        render_main_menu(
            screen,
            fonts,
            window_settings,
            context.highscores if context is not None else None,
            menu,
        )
    elif state is GameState.PLAYING:
        render_game_view(
            screen,
            fonts,
            window_settings,
            context.session if context is not None else None,
        )
    elif state is GameState.HIGHSCORES:
        render_highscores_screen(
            screen,
            fonts,
            window_settings,
            context.highscores if context is not None else None,
        )
    elif state is GameState.INSTRUCTIONS:
        render_instructions_screen(screen, fonts, window_settings)
    elif state is GameState.END_SCREEN:
        render_end_screen(screen, fonts, window_settings)

    pygame_instance.display.set_caption(
        f"{window_settings.title} - {state.value}"
    )
