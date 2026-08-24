"""Level completion and multi-level progression orchestration."""

from enum import Enum

from pacman.application.state import GameStateController
from pacman.context import GameSession
from pacman.level_generator import LevelData, LevelGenerator
from pacman.player import Player


class LevelCompletionOutcome(Enum):
    """Describe the outcome of completing a level."""

    ADVANCED = "advanced"
    VICTORY = "victory"


def handle_level_completion(
    session: GameSession,
    player: Player,
    level_generator: LevelGenerator,
    state_controller: GameStateController,
) -> tuple[LevelCompletionOutcome, LevelData | None]:
    """Complete current level and advance to the next or trigger victory."""
    if session.is_final_level:
        session.trigger_victory()
        state_controller.end_game()
        return LevelCompletionOutcome.VICTORY, None

    next_level_index = session.advance_level()
    next_level = level_generator.generate_level(next_level_index)

    if next_level.spawns is not None:
        player.respawn(next_level.spawns.player, next_level.world)

    session.start_level_timer(next_level.time_limit)
    return LevelCompletionOutcome.ADVANCED, next_level
