"""Rendering for the main and pause menus."""

from pacman.application.context import GameSession
from pacman.application.contracts import Surface
from pacman.application.menu import (
    MAIN_MENU_OPTIONS,
    PAUSE_MENU_OPTIONS,
    MainMenu,
    PauseMenu,
)
from pacman.application.rendering.common import (
    RenderFonts,
    STATE_BACKGROUNDS,
    WindowSettings,
    draw_centered_text,
)
from pacman.application.rendering.game import render_hud
from pacman.application.state import GameState


def render_main_menu(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    menu: MainMenu | None = None,
) -> None:
    """Render the main menu centered vertically in the window."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    screen.fill(STATE_BACKGROUNDS[GameState.MAIN_MENU])
    draw_centered_text(
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
        draw_centered_text(
            screen,
            fonts.body,
            label,
            color,
            (center_x, center_y - 8 + index * 32),
        )


def render_pause_menu(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    menu: PauseMenu | None = None,
    session: GameSession | None = None,
) -> None:
    """Render the pause menu with active HUD and selectable options."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    screen.fill(STATE_BACKGROUNDS[GameState.PAUSED])
    render_hud(screen, fonts, window_settings, session)
    draw_centered_text(
        screen,
        fonts.title,
        "PAUSED",
        (255, 230, 0),
        (center_x, center_y - 68),
    )

    menu_options = menu.options if menu is not None else PAUSE_MENU_OPTIONS
    selected_index = menu.selected_index if menu is not None else 0
    for index, option in enumerate(menu_options):
        is_selected = index == selected_index
        label = f"> {option.label} <" if is_selected else option.label
        color = (255, 230, 0) if is_selected else (255, 255, 255)
        draw_centered_text(
            screen,
            fonts.body,
            label,
            color,
            (center_x, center_y - 8 + index * 32),
        )

    draw_centered_text(
        screen,
        fonts.body,
        "P: Resume | Esc: Main Menu",
        (255, 230, 0),
        (center_x, window_settings.height - 48),
    )
