"""Rendering for highscores and game instructions."""

from typing import Final

from pacman.application.contracts import Surface
from pacman.application.rendering.common import (
    RenderFonts,
    STATE_BACKGROUNDS,
    WindowSettings,
    draw_centered_text,
)
from pacman.application.state import GameState
from pacman.infrastructure.config import GameConfig
from pacman.infrastructure.highscore import HighscoreEntry


MAX_DISPLAYED_HIGHSCORES: Final = 10


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
    )[:MAX_DISPLAYED_HIGHSCORES]
    screen.fill(STATE_BACKGROUNDS[GameState.HIGHSCORES])
    draw_centered_text(
        screen, fonts.title, "HIGHSCORES", (255, 230, 0), (center_x, 64)
    )
    if ranked_highscores:
        for label, column_x in (
            ("RANK", rank_x),
            ("PLAYER", player_x),
            ("SCORE", score_x),
        ):
            draw_centered_text(
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
                draw_centered_text(
                    screen,
                    fonts.body,
                    value,
                    (255, 255, 255),
                    (column_x, row_y),
                )
    else:
        draw_centered_text(
            screen,
            fonts.body,
            "No highscores yet",
            (255, 255, 255),
            (center_x, 148),
        )
    draw_centered_text(
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
    table_height = 282
    table_top = (window_settings.height - table_height) // 2
    table_middle_y = table_top + 142
    table_bottom = table_top + table_height
    title_y = table_top - 36
    footer_y = table_bottom + 48
    table_middle_x = window_settings.width // 2
    left_center_x = (table_left + table_middle_x) // 2
    right_center_x = (table_middle_x + table_right) // 2
    screen.fill(STATE_BACKGROUNDS[GameState.INSTRUCTIONS])
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
    draw_centered_text(
        screen,
        fonts.title,
        "Instructions",
        (255, 230, 0),
        (center_x, title_y),
    )

    sections = (
        (
            left_center_x,
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
            right_center_x,
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
        column_center_x,
        first_heading,
        first_lines,
        second_heading,
        second_lines,
    ) in sections:
        draw_centered_text(
            screen,
            fonts.body,
            first_heading,
            (255, 230, 0),
            (column_center_x, table_top + 20),
        )
        for index, line in enumerate(first_lines):
            draw_centered_text(
                screen,
                fonts.body,
                line,
                (255, 255, 255),
                (column_center_x, table_top + 52 + index * 30),
            )
        draw_centered_text(
            screen,
            fonts.body,
            second_heading,
            (255, 230, 0),
            (column_center_x, table_middle_y + 22),
        )
        for index, line in enumerate(second_lines):
            draw_centered_text(
                screen,
                fonts.body,
                line,
                (255, 255, 255),
                (column_center_x, table_middle_y + 54 + index * 30),
            )
    draw_centered_text(
        screen,
        fonts.body,
        "Esc / Enter / Space: Main Menu",
        (255, 230, 0),
        (center_x, footer_y),
    )
