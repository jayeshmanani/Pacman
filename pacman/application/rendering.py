"""Rendering functions for the current application states."""

from dataclasses import dataclass
import math
from typing import Final, cast

from pacman.application.contracts import Color, Font, PygameModule, Surface
from pacman.application.menu import MAIN_MENU_OPTIONS, MainMenu
from pacman.application.state import GameState
from pacman.application.context import AppContext, GameSession
from pacman.infrastructure.config import GameConfig
from pacman.infrastructure.highscore import HighscoreEntry


@dataclass(frozen=True)
class WindowSettings:
    """Settings for the initial Pacman window."""

    title: str = "Pacman"
    width: int = 520
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
    GameState.INSTRUCTIONS: (16, 24, 72),
    GameState.END_SCREEN: (72, 16, 24),
}
_MAX_DISPLAYED_HIGHSCORES: Final = 10


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


def _draw_left_text(
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


def render_hud(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
) -> None:
    """Render the always-visible in-game HUD bar across the top."""
    hud_height = 40
    screen.fill((12, 16, 36), (0, 0, window_settings.width, hud_height))
    screen.fill((82, 113, 214), (0, hud_height - 2, window_settings.width, 2))

    score = session.score if session is not None else 0
    lives = session.lives if session is not None else 3
    level = (session.current_level + 1) if session is not None else 1
    remaining_time = (
        max(0, int(math.ceil(session.remaining_level_time)))
        if session is not None
        else 90
    )

    center_y = hud_height // 2
    quarter_w = window_settings.width // 4

    hud_items = (
        (f"SCORE: {score}", quarter_w // 2),
        (f"LIVES: {lives}", quarter_w + quarter_w // 2),
        (f"LEVEL: {level}", quarter_w * 2 + quarter_w // 2),
        (f"TIME: {remaining_time}s", quarter_w * 3 + quarter_w // 2),
    )

    for text, center_x in hud_items:
        _draw_centered_text(
            screen,
            fonts.body,
            text,
            (255, 230, 0),
            (center_x, center_y),
        )


def render_main_menu(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    menu: MainMenu | None = None,
) -> None:
    """Render the main menu centered vertically in the window."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    screen.fill(_STATE_BACKGROUNDS[GameState.MAIN_MENU])
    _draw_centered_text(
        screen,
        fonts.title,
        "PACMAN",
        (255, 230, 0),
        (center_x, center_y - 68),
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
            (center_x, center_y - 8 + index * 32),
        )


def render_game_view(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
) -> None:
    """Render the placeholder game view with the HUD."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    screen.fill(window_settings.background_color)
    render_hud(screen, fonts, window_settings, session)
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
    """Render the ten best stored highscores in descending order."""
    center_x = window_settings.width // 2
    rank_x = window_settings.width // 6
    player_x = center_x
    score_x = window_settings.width * 5 // 6
    ranked_highscores = sorted(
        highscores or (),
        key=lambda entry: entry.score,
        reverse=True,
    )[:_MAX_DISPLAYED_HIGHSCORES]
    screen.fill(_STATE_BACKGROUNDS[GameState.HIGHSCORES])
    _draw_centered_text(
        screen, fonts.title, "HIGHSCORES", (255, 230, 0), (center_x, 64)
    )
    if ranked_highscores:
        for label, column_x in (
            ("RANK", rank_x),
            ("PLAYER", player_x),
            ("SCORE", score_x),
        ):
            _draw_centered_text(
                screen,
                fonts.body,
                label,
                (255, 230, 0),
                (column_x, 112),
            )
        for position, entry in enumerate(ranked_highscores, start=1):
            row_y = 116 + position * 28
            for value, column_x in (
                (str(position), rank_x),
                (entry.name, player_x),
                (str(entry.score), score_x),
            ):
                _draw_centered_text(
                    screen,
                    fonts.body,
                    value,
                    (255, 255, 255),
                    (column_x, row_y),
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
        "Press Escape, Enter, or Space for Menu",
        (255, 230, 0),
        (center_x, window_settings.height - 48),
    )


def render_instructions_screen(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    config: GameConfig | None = None,
) -> None:
    """Render controls and game rules using the active configuration."""
    game_config = config or GameConfig()
    center_x = window_settings.width // 2
    table_left = 24
    table_right = window_settings.width - 24
    table_top = 88
    table_middle_y = 230
    table_bottom = 370
    table_middle_x = window_settings.width // 2
    left_x = table_left + 18
    right_x = table_middle_x + 18
    screen.fill(_STATE_BACKGROUNDS[GameState.INSTRUCTIONS])
    line_color = (82, 113, 214)
    for rectangle in (
        (table_left, table_top, table_right - table_left, 2),
        (table_left, table_middle_y, table_right - table_left, 2),
        (table_left, table_bottom, table_right - table_left, 2),
        (table_left, table_top, 2, table_bottom - table_top),
        (table_middle_x, table_top, 2, table_bottom - table_top),
        (table_right - 2, table_top, 2, table_bottom - table_top),
    ):
        screen.fill(line_color, rectangle)
    _draw_centered_text(
        screen,
        fonts.title,
        "Instructions",
        (255, 230, 0),
        (center_x, 52),
    )

    sections = (
        (
            left_x,
            "CONTROLS",
            ("Arrows / WASD", "P: Pause / Resume"),
            "RULES",
            (
                "Clear all pacgums",
                "Ghost touch: -1 life",
                f"Starting lives: {game_config.lives}",
            ),
        ),
        (
            right_x,
            "SCORING",
            (
                f"Pacgum: +{game_config.points_per_pacgum}",
                f"Power pellet: +{game_config.points_per_super_pacgum}",
                (
                    f"Ghost: +{game_config.points_per_ghost} to "
                    f"+{game_config.points_per_ghost * 8}"
                ),
            ),
            "POWER MODE",
            (
                "Ghosts become edible",
                f"Lasts {game_config.frightened_duration:g} seconds",
            ),
        ),
    )
    for (
        column_x,
        first_heading,
        first_lines,
        second_heading,
        second_lines,
    ) in sections:
        _draw_left_text(
            screen,
            fonts.body,
            first_heading,
            (255, 230, 0),
            (column_x, 108),
        )
        for index, line in enumerate(first_lines):
            _draw_left_text(
                screen,
                fonts.body,
                line,
                (255, 255, 255),
                (column_x, 140 + index * 30),
            )
        _draw_left_text(
            screen,
            fonts.body,
            second_heading,
            (255, 230, 0),
            (column_x, 252),
        )
        for index, line in enumerate(second_lines):
            _draw_left_text(
                screen,
                fonts.body,
                line,
                (255, 255, 255),
                (column_x, 284 + index * 30),
            )
    _draw_centered_text(
        screen,
        fonts.body,
        "Esc / Enter / Space: Main Menu",
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
        render_instructions_screen(
            screen,
            fonts,
            window_settings,
            context.config if context is not None else None,
        )
    elif state is GameState.END_SCREEN:
        render_end_screen(screen, fonts, window_settings)

    pygame_instance.display.set_caption(
        f"{window_settings.title} - {state.value}"
    )
