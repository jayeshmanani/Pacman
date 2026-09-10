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
from pacman.application.highscore_flow import handle_completed_game_input
from pacman.application.cheat_mode import CheatControls, handle_cheat_key
from pacman.application.cheat_actions import (
    add_extra_life,
    skip_current_level,
    synchronize_player_speed,
)


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
        victory_key=pygame_instance.K_v,
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


def _create_cheat_controls(pygame_instance: PygameModule) -> CheatControls:
    """Create evaluation cheat controls from pygame key constants."""
    return CheatControls(
        toggle_key=pygame_instance.K_F1,
        invincibility_key=pygame_instance.K_1,
        level_skip_key=pygame_instance.K_2,
        ghost_freeze_key=pygame_instance.K_3,
        extra_life_key=pygame_instance.K_4,
        speed_boost_key=pygame_instance.K_5,
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
    main_menu: MainMenu | None = None,
) -> None:
    """Apply a pause-menu action."""
    pause_menu.reset_selection()
    if action is PauseMenuAction.RESUME:
        controller.resume_game(context.session)
    elif action is PauseMenuAction.RETURN_TO_MAIN_MENU:
        if main_menu is not None:
            main_menu.reset_selection()
        context.reset_session()
        controller.return_to_main_menu(context.session)


def _handle_cheat_action(
    key: int,
    controls: CheatControls,
    context: AppContext,
    controller: GameStateController,
) -> bool:
    """Apply one active gameplay cheat control."""
    if key == controls.level_skip_key and context.cheat_mode.enabled:
        if context.player is None:
            return False
        result = skip_current_level(
            context.cheat_mode,
            context.session,
            context.player,
            context.level_generator,
            controller,
        )
        if result is not None:
            _, next_level = result
            if next_level is not None:
                context.activate_level(next_level, respawn_player=False)
        return result is not None

    if key == controls.extra_life_key and context.cheat_mode.enabled:
        return add_extra_life(context.cheat_mode, context.session)

    handled = handle_cheat_key(key, controls, context.cheat_mode)
    if handled and context.player is not None:
        synchronize_player_speed(context.cheat_mode, context.player)
    return handled


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
        cheat_controls = _create_cheat_controls(pygame_instance)
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
                        handle_completed_game_input(
                            key=key,
                            character=keyboard_event.unicode,
                            backspace_key=pygame_instance.K_BACKSPACE,
                            submit_key=pygame_instance.K_RETURN,
                            controller=controller,
                            context=app_context,
                            cancel_key=controls.main_menu_key,
                        )
                        if controller.state.value == GameState.MAIN_MENU.value:
                            main_menu.reset_selection()
                    elif controller.state is GameState.PAUSED:
                        if key == controls.pause_key:
                            pause_menu.reset_selection()
                            controller.resume_game(app_context.session)
                        elif key == controls.main_menu_key:
                            pause_menu.reset_selection()
                            main_menu.reset_selection()
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
                                    main_menu,
                                )
                    else:
                        if controller.state is GameState.PLAYING and (
                            _handle_cheat_action(
                                key,
                                cheat_controls,
                                app_context,
                                controller,
                            )
                        ):
                            continue
                        if (
                            controller.state is GameState.PLAYING
                            and key == controls.pause_key
                        ):
                            pause_menu.reset_selection()
                        elif (
                            controller.state is GameState.PLAYING
                            and key == controls.main_menu_key
                        ):
                            main_menu.reset_selection()
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
