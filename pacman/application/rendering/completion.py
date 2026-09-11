"""Rendering for Game Over, Victory, and player-name entry."""

from pacman.application.context import GameSession
from pacman.application.contracts import Surface
from pacman.application.player_name_input import PlayerNameInput
from pacman.application.rendering.common import (
    RenderFonts,
    STATE_BACKGROUNDS,
    WindowSettings,
    draw_centered_text,
)
from pacman.application.state import GameState


def _render_player_name_prompt(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    player_name_input: PlayerNameInput | None,
) -> None:
    """Render the shared name-entry field for either completion path."""
    input_state = player_name_input or PlayerNameInput()
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    visible_name = input_state.value or "_"
    draw_centered_text(
        screen,
        fonts.body,
        f"NAME: {visible_name}",
        (255, 255, 255),
        (center_x, center_y + 72),
    )

    if input_state.error_message is not None:
        draw_centered_text(
            screen,
            fonts.body,
            input_state.error_message,
            (255, 100, 100),
            (center_x, center_y + 108),
        )

    draw_centered_text(
        screen,
        fonts.body,
        "Enter: Save score and return to menu",
        (255, 230, 0),
        (center_x, window_settings.height - 48),
    )
    draw_centered_text(
        screen,
        fonts.body,
        "Esc: Return to menu without saving",
        (180, 180, 180),
        (center_x, window_settings.height - 24),
    )


def render_game_over_screen(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
    player_name_input: PlayerNameInput | None = None,
) -> None:
    """Render Game Over screen with final score and continuation prompt."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    screen.fill(STATE_BACKGROUNDS[GameState.GAME_OVER])
    draw_centered_text(
        screen,
        fonts.title,
        "GAME OVER",
        (255, 230, 0),
        (center_x, center_y - 68),
    )

    reason = "OUT OF LIVES!"
    if session is not None and session.level_timed_out:
        reason = "TIME EXPIRED!"
    draw_centered_text(
        screen,
        fonts.body,
        reason,
        (255, 100, 100),
        (center_x, center_y - 16),
    )

    score = session.score if session is not None else 0
    draw_centered_text(
        screen,
        fonts.body,
        f"FINAL SCORE: {score}",
        (255, 255, 255),
        (center_x, center_y + 24),
    )
    _render_player_name_prompt(
        screen,
        fonts,
        window_settings,
        player_name_input,
    )


def render_victory_screen(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
    player_name_input: PlayerNameInput | None = None,
) -> None:
    """Render Victory screen with celebratory message and final score."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    screen.fill(STATE_BACKGROUNDS[GameState.VICTORY])
    draw_centered_text(
        screen,
        fonts.title,
        "VICTORY!",
        (255, 230, 0),
        (center_x, center_y - 68),
    )
    draw_centered_text(
        screen,
        fonts.body,
        "YOU CLEARED ALL LEVELS!",
        (100, 255, 100),
        (center_x, center_y - 16),
    )

    score = session.score if session is not None else 0
    draw_centered_text(
        screen,
        fonts.body,
        f"FINAL SCORE: {score}",
        (255, 255, 255),
        (center_x, center_y + 24),
    )
    _render_player_name_prompt(
        screen,
        fonts,
        window_settings,
        player_name_input,
    )


def render_end_screen(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
) -> None:
    """Render either victory or game over screen based on session state."""
    if session is not None and session.is_victory:
        render_victory_screen(screen, fonts, window_settings, session)
    else:
        render_game_over_screen(screen, fonts, window_settings, session)
