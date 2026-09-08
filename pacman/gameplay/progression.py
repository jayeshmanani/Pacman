"""Level completion and multi-level progression orchestration."""


from enum import Enum
import sys

from pacman.application.state import GameStateController
from pacman.application.context import GameSession
from pacman.maze.level_generator import (
    LevelData,
    LevelGenerationError,
    LevelGenerator,
)
from pacman.gameplay.player import Player


class LevelCompletionOutcome(Enum):
    """Describe the outcome of completing a level."""

    ADVANCED = "advanced"
    VICTORY = "victory"
    FAILED = "failed"


def handle_level_completion(
    session: GameSession,
    player: Player,
    level_generator: LevelGenerator,
    state_controller: GameStateController,
) -> tuple[LevelCompletionOutcome, LevelData | None]:
    """Complete current level and advance to the next or trigger victory."""
    if session.is_final_level:
        session.trigger_victory()
        state_controller.end_game(session)
        return LevelCompletionOutcome.VICTORY, None

    next_level_index = session.advance_level()
    try:
        next_level = level_generator.generate_level(next_level_index)
    except LevelGenerationError as error:
        print(f"Error: {error}", file=sys.stderr)
        state_controller.return_to_main_menu(session)
        return LevelCompletionOutcome.FAILED, None

    if next_level.spawns is not None:
        player.respawn(next_level.spawns.player, next_level.world)

    session.start_level_timer(next_level.time_limit)
    return LevelCompletionOutcome.ADVANCED, next_level
