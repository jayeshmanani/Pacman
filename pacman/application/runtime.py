"""Pygame startup and frame-loop orchestration."""

import importlib
from typing import cast

from pacman.application.contracts import (
    Event,
    KeyboardEvent,
    PygameModule,
    Surface,
)
from pacman.application.menu import (
    MainMenu,
    MainMenuAction,
    MenuControls,
    PauseMenu,
    PauseMenuAction,
)
from pacman.application.rendering import (
    WindowSettings,
    create_render_fonts,
    render_state,
)
from pacman.application.state import (
    GameState,
    GameStateController,
    StateControls,
    update_active_gameplay,
)
from pacman.infrastructure.config import GameConfig
from pacman.application.context import AppContext


def _load_pygame() -> PygameModule:
    """Load pygame only when the graphical app starts."""
    return cast(PygameModule, importlib.import_module("pygame"))


def _create_state_controls(pygame_instance: PygameModule) -> StateControls:
    """Create state controls from pygame key constants."""
    return StateControls(
        confirm_keys=frozenset({
            pygame_instance.K_RETURN,
            pygame_instance.K_SPACE,
        }),
        end_screen_key=pygame_instance.K_e,
        main_menu_key=pygame_instance.K_ESCAPE,
        pause_key=pygame_instance.K_p,
    )


def _create_menu_controls(pygame_instance: PygameModule) -> MenuControls:
    """Create main-menu controls from pygame key constants."""
    return MenuControls(
        up_keys=frozenset({pygame_instance.K_UP}),
        down_keys=frozenset({pygame_instance.K_DOWN}),
        confirm_keys=frozenset({
            pygame_instance.K_RETURN,
            pygame_instance.K_SPACE,
        }),
    )


def _handle_menu_action(
    action: MainMenuAction,
    controller: GameStateController,
    context: AppContext,
) -> bool:
    """Apply a menu action and return whether the app should keep running."""
    if action is MainMenuAction.START_GAME:
        controller.start_game(context.start_new_game())
    elif action is MainMenuAction.VIEW_HIGHSCORES:
        controller.show_highscores()
    elif action is MainMenuAction.INSTRUCTIONS:
        controller.show_instructions()
    elif action is MainMenuAction.EXIT:
        return False
    return True


def _handle_pause_menu_action(
    action: PauseMenuAction,
    controller: GameStateController,
    context: AppContext,
    pause_menu: PauseMenu,
) -> None:
    """Apply a pause-menu action."""
    pause_menu.reset_selection()
    if action is PauseMenuAction.RESUME:
        controller.resume_game(context.session)
    elif action is PauseMenuAction.RETURN_TO_MAIN_MENU:
        context.reset_session()
        controller.return_to_main_menu(context.session)


def run_app(
    settings: WindowSettings | None = None,
    pygame_module: object | None = None,
    config: GameConfig | None = None,
) -> None:
    """Open the Pacman window and run until the user closes it."""
    window_settings = settings or WindowSettings()
    pygame_instance = (
        cast(PygameModule, pygame_module)
        if pygame_module is not None
        else _load_pygame()
    )

    pygame_instance.init()
    try:
        screen = cast(
            Surface,
            pygame_instance.display.set_mode(
                (window_settings.width, window_settings.height)
            ),
        )
        clock = pygame_instance.time.Clock()
        controls = _create_state_controls(pygame_instance)
        menu_controls = _create_menu_controls(pygame_instance)
        fonts = create_render_fonts(pygame_instance)
        controller = GameStateController()
        main_menu = MainMenu()
        pause_menu = PauseMenu()
        app_context = AppContext(
            config=config or GameConfig(),
            state_controller=controller,
        )
        running = True

        while running:
            for event in pygame_instance.event.get():
                event_type = cast(Event, event).type
                if event_type == pygame_instance.QUIT:
                    running = False
                elif event_type == pygame_instance.KEYDOWN:
                    key = cast(KeyboardEvent, event).key
                    if controller.state is GameState.MAIN_MENU:
                        action = main_menu.handle_key(key, menu_controls)
                        if action is not None:
                            running = _handle_menu_action(
                                action,
                                controller,
                                app_context,
                            )
                    elif controller.state in (
                        GameState.GAME_OVER,
                        GameState.VICTORY,
                    ):
                        keyboard_event = cast(KeyboardEvent, event)
                        if key == pygame_instance.K_BACKSPACE:
                            app_context.player_name_input.backspace()
                        elif key == pygame_instance.K_RETURN:
                            if app_context.save_completed_game_score():
                                app_context.reset_session()
                                controller.return_to_main_menu(
                                    app_context.session
                                )
                        elif keyboard_event.unicode:
                            app_context.player_name_input.add_character(
                                keyboard_event.unicode
                            )
                    elif controller.state is GameState.PAUSED:
                        if key == controls.pause_key:
                            pause_menu.reset_selection()
                            controller.resume_game(app_context.session)
                        elif key == controls.main_menu_key:
                            pause_menu.reset_selection()
                            app_context.reset_session()
                            controller.return_to_main_menu(app_context.session)
                        else:
                            pause_action = pause_menu.handle_key(
                                key, menu_controls
                            )
                            if pause_action is not None:
                                _handle_pause_menu_action(
                                    pause_action,
                                    controller,
                                    app_context,
                                    pause_menu,
                                )
                    else:
                        if (
                            controller.state is GameState.PLAYING
                            and key == controls.pause_key
                        ):
                            pause_menu.reset_selection()
                        elif (
                            controller.state is GameState.PLAYING
                            and key == controls.main_menu_key
                        ):
                            app_context.reset_session()
                        controller.handle_key(
                            key,
                            controls,
                            app_context.session,
                        )

            render_state(
                screen,
                fonts,
                pygame_instance,
                window_settings,
                controller.state,
                app_context,
                main_menu,
                pause_menu,
            )
            pygame_instance.display.flip()
            elapsed_ms = clock.tick(window_settings.frames_per_second)
            update_active_gameplay(
                app_context.session,
                controller,
                elapsed_ms / 1000.0,
            )
    finally:
        pygame_instance.quit()
