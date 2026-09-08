"""Gameplay actions exposed through the evaluation cheat mode."""

from pacman.application.cheat_mode import CheatMode
from pacman.application.context import GameSession
from pacman.application.state import GameStateController
from pacman.gameplay.player import Player
from pacman.gameplay.progression import (
    LevelCompletionOutcome,
    handle_level_completion,
)
from pacman.maze.level_generator import LevelData, LevelGenerator


PLAYER_SPEED_BOOST_MULTIPLIER = 2.0


def add_extra_life(
    cheat_mode: CheatMode,
    session: GameSession,
) -> bool:
    """Add exactly one life when evaluation cheats are available."""
    if not cheat_mode.enabled:
        return False
    session.add_life()
    return True


def skip_current_level(
    cheat_mode: CheatMode,
    session: GameSession,
    player: Player,
    level_generator: LevelGenerator,
    state_controller: GameStateController,
) -> tuple[LevelCompletionOutcome, LevelData | None] | None:
    """Complete the current level through the normal progression flow."""
    if not cheat_mode.enabled:
        return None
    return handle_level_completion(
        session,
        player,
        level_generator,
        state_controller,
    )


def toggle_player_speed_boost(
    cheat_mode: CheatMode,
    player: Player,
) -> bool | None:
    """Toggle a reversible player speed multiplier."""
    if not cheat_mode.enabled:
        return None
    enabled = cheat_mode.toggle_speed_boost()
    synchronize_player_speed(cheat_mode, player)
    return enabled


def synchronize_player_speed(
    cheat_mode: CheatMode,
    player: Player,
) -> None:
    """Apply cheat state without changing the player's base speed."""
    multiplier = (
        PLAYER_SPEED_BOOST_MULTIPLIER
        if cheat_mode.enabled and cheat_mode.speed_boost_enabled
        else 1.0
    )
    player.set_speed_multiplier(multiplier)
