"""Dispatch application states to focused rendering functions."""

from typing import cast

from pacman.application.context import AppContext
from pacman.application.contracts import PygameModule, Surface
from pacman.application.rendering.game import render_game_view
from pacman.application.menu import MainMenu, PauseMenu
from pacman.application.rendering.common import (
    RenderFonts,
    WindowSettings,
)
from pacman.application.rendering.completion import (
    render_end_screen,
    render_game_over_screen,
    render_victory_screen,
)
from pacman.application.rendering.information import (
    render_highscores_screen,
    render_instructions_screen,
)
from pacman.application.rendering.menus import (
    render_main_menu,
    render_pause_menu,
)
from pacman.application.state import GameState


def render_state(
    screen: Surface,
    fonts: RenderFonts,
    pygame_module: object,
    window_settings: WindowSettings,
    state: GameState,
    context: AppContext | None = None,
    menu: MainMenu | None = None,
    pause_menu: PauseMenu | None = None,
) -> None:
    """Render one application state and update the window caption."""
    pygame_instance = cast(PygameModule, pygame_module)

    if state is GameState.MAIN_MENU:
        render_main_menu(screen, fonts, window_settings, menu)
    elif state is GameState.PLAYING:
        render_game_view(
            screen,
            fonts,
            window_settings,
            context.session if context is not None else None,
            context.cheat_mode.enabled if context is not None else False,
            (
                context.cheat_mode.invincibility_enabled
                if context is not None
                else False
            ),
            (
                context.cheat_mode.ghost_freeze_enabled
                if context is not None
                else False
            ),
            (
                context.cheat_mode.speed_boost_enabled
                if context is not None
                else False
            ),
        )
    elif state is GameState.PAUSED:
        render_pause_menu(
            screen,
            fonts,
            window_settings,
            pause_menu,
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
    elif state is GameState.GAME_OVER:
        render_game_over_screen(
            screen,
            fonts,
            window_settings,
            context.session if context is not None else None,
            context.player_name_input if context is not None else None,
        )
    elif state is GameState.VICTORY:
        render_victory_screen(
            screen,
            fonts,
            window_settings,
            context.session if context is not None else None,
            context.player_name_input if context is not None else None,
        )
    elif state is GameState.END_SCREEN:
        render_end_screen(
            screen,
            fonts,
            window_settings,
            context.session if context is not None else None,
        )

    pygame_instance.display.set_caption(
        f"{window_settings.title} - {state.value}"
    )
