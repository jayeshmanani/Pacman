"""Rendering for the active game view and its heads-up display."""

import math

from pacman.application.context import GameSession
from pacman.application.contracts import Color, Surface
from pacman.application.rendering.common import (
    RenderFonts,
    WindowSettings,
    draw_centered_text,
)


def render_hud(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
    cheat_mode_enabled: bool = False,
    invincibility_enabled: bool = False,
    ghost_freeze_enabled: bool = False,
    speed_boost_enabled: bool = False,
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

    time_color: Color = (255, 230, 0)
    if remaining_time <= 10:
        time_color = (255, 70, 70)
    elif remaining_time <= 20:
        time_color = (255, 170, 0)

    lives_color: Color = (255, 70, 70) if lives <= 1 else (255, 230, 0)
    hud_items = (
        (f"SCORE: {score}", quarter_w // 2, (255, 230, 0)),
        (f"LIVES: {lives}", quarter_w + quarter_w // 2, lives_color),
        (f"LEVEL: {level}", quarter_w * 2 + quarter_w // 2, (255, 230, 0)),
        (
            f"TIME: {remaining_time}s",
            quarter_w * 3 + quarter_w // 2,
            time_color,
        ),
    )

    for text, center_x, color in hud_items:
        draw_centered_text(
            screen,
            fonts.body,
            text,
            color,
            (center_x, center_y),
        )

    if cheat_mode_enabled:
        draw_centered_text(
            screen,
            fonts.body,
            "CHEAT MODE: ON (F1 to disable)",
            (255, 90, 90),
            (window_settings.width // 2, hud_height + 14),
        )
        draw_centered_text(
            screen,
            fonts.body,
            "1 Invincible | 2 Skip | 3 Freeze",
            (255, 230, 0),
            (window_settings.width // 2, hud_height + 38),
        )
        draw_centered_text(
            screen,
            fonts.body,
            "4 Extra Life | 5 Speed Boost",
            (255, 230, 0),
            (window_settings.width // 2, hud_height + 62),
        )
        active_cheats = []
        if invincibility_enabled:
            active_cheats.append("INVINCIBLE")
        if ghost_freeze_enabled:
            active_cheats.append("GHOST FREEZE")
        if speed_boost_enabled:
            active_cheats.append("SPEED BOOST")
        if active_cheats:
            draw_centered_text(
                screen,
                fonts.body,
                f"ACTIVE: {' | '.join(active_cheats)}",
                (100, 255, 100),
                (window_settings.width // 2, hud_height + 86),
            )


def render_game_view(
    screen: Surface,
    fonts: RenderFonts,
    window_settings: WindowSettings,
    session: GameSession | None = None,
    cheat_mode_enabled: bool = False,
    invincibility_enabled: bool = False,
    ghost_freeze_enabled: bool = False,
    speed_boost_enabled: bool = False,
) -> None:
    """Render the current placeholder game view with the HUD."""
    center_x = window_settings.width // 2
    center_y = window_settings.height // 2
    screen.fill(window_settings.background_color)
    render_hud(
        screen,
        fonts,
        window_settings,
        session,
        cheat_mode_enabled,
        invincibility_enabled,
        ghost_freeze_enabled,
        speed_boost_enabled,
    )
    draw_centered_text(
        screen,
        fonts.title,
        "Game View",
        (255, 255, 255),
        (center_x, center_y - 24),
    )
    draw_centered_text(
        screen,
        fonts.body,
        "Press E to End",
        (255, 230, 0),
        (center_x, center_y + 32),
    )
    draw_centered_text(
        screen,
        fonts.body,
        "Press V for Victory",
        (100, 255, 100),
        (center_x, center_y + 56),
    )
    if session is not None:
        draw_centered_text(
            screen,
            fonts.body,
            f"Lives: {session.lives} | Score: {session.score}",
            (255, 255, 255),
            (center_x, center_y + 88),
        )
