"""Stable public facade for the Pacman graphical application."""

from pacman.application.rendering import (
    RenderFonts,
    WindowSettings,
    render_end_screen,
    render_game_view,
    render_highscores_screen,
    render_hud,
    render_instructions_screen,
    render_main_menu,
    render_state,
)
from pacman.application.runtime import run_app
from pacman.application.menu import (
    MAIN_MENU_OPTIONS,
    MainMenu,
    MainMenuAction,
    MainMenuOption,
    MenuControls,
)
from pacman.application.state import (
    GameState,
    GameStateController,
    StateControls,
    update_active_gameplay,
)

__all__ = [
    "GameState",
    "GameStateController",
    "MAIN_MENU_OPTIONS",
    "MainMenu",
    "MainMenuAction",
    "MainMenuOption",
    "MenuControls",
    "RenderFonts",
    "StateControls",
    "WindowSettings",
    "render_end_screen",
    "render_game_view",
    "render_highscores_screen",
    "render_hud",
    "render_instructions_screen",
    "render_main_menu",
    "render_state",
    "run_app",
    "update_active_gameplay",
]
