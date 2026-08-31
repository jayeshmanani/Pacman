"""Pygame startup and frame-loop orchestration."""

import importlib
from typing import cast

from pacman.application.contracts import (
    Event,
    KeyboardEvent,
    PygameModule,
    Surface,
)
from pacman.application.rendering import (
    WindowSettings,
    create_render_fonts,
    render_state,
)
from pacman.application.state import (
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
        fonts = create_render_fonts(pygame_instance)
        controller = GameStateController()
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
                    controller.handle_key(
                        cast(KeyboardEvent, event).key,
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
