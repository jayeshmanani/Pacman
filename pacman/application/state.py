"""Application state transitions and the shared gameplay update gate."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from pacman.context import GameSession


class GameState(Enum):
    """High-level application states."""

    MAIN_MENU = "Main Menu"
    PLAYING = "Playing"
    END_SCREEN = "End Screen"


@dataclass(frozen=True)
class StateControls:
    """Keyboard controls for state transitions."""

    confirm_keys: frozenset[int]
    end_screen_key: int
    main_menu_key: int
    pause_key: int


class GameStateController:
    """Track and update the current game state."""

    def __init__(self, initial_state: GameState = GameState.MAIN_MENU) -> None:
        """Initialize the controller with a starting state."""
        self._state = initial_state

    @property
    def state(self) -> GameState:
        """Return the current game state."""
        return self._state

    def end_game(self) -> None:
        """Move the application to the end screen after game over."""
        self._state = GameState.END_SCREEN

    def handle_key(
        self,
        key: int,
        controls: StateControls,
        session: GameSession | None = None,
    ) -> None:
        """Apply a state transition for a pressed key."""
        if self._state is GameState.MAIN_MENU:
            if key in controls.confirm_keys:
                if session is not None:
                    session.resume_gameplay()
                self._state = GameState.PLAYING
            return

        if self._state is GameState.PLAYING:
            if key == controls.pause_key:
                if session is not None:
                    session.toggle_pause()
            elif key == controls.end_screen_key:
                if session is not None:
                    session.resume_gameplay()
                self._state = GameState.END_SCREEN
            elif key == controls.main_menu_key:
                if session is not None:
                    session.resume_gameplay()
                self._state = GameState.MAIN_MENU
            return

        if self._state is GameState.END_SCREEN:
            if key in controls.confirm_keys or key == controls.main_menu_key:
                if session is not None:
                    session.resume_gameplay()
                self._state = GameState.MAIN_MENU


def update_active_gameplay(
    session: GameSession,
    state_controller: GameStateController,
    dt: float,
    gameplay_update: Callable[[float], None] | None = None,
) -> None:
    """Advance active gameplay systems for the elapsed frame time."""
    if state_controller.state is not GameState.PLAYING or session.is_paused:
        return

    if gameplay_update is not None:
        gameplay_update(dt)

    if session.update_level_timer(dt):
        state_controller.end_game()
