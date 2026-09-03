"""Player life-loss, respawn, and game-over handling."""


from enum import Enum

from pacman.application.state import GameStateController
from pacman.application.context import GameSession
from pacman.maze.grid import TileCoordinate
from pacman.gameplay.player import Player
from pacman.maze.world import WorldMap


class PlayerDeathOutcome(Enum):
    """Describe the result of handling a player death."""

    RESPAWNED = "respawned"
    GAME_OVER = "game_over"


def handle_normal_ghost_collision(
    session: GameSession,
    player: Player,
    spawn_tile: TileCoordinate,
    world: WorldMap,
    state_controller: GameStateController,
) -> PlayerDeathOutcome:
    """Remove one life, then respawn the player or end the game."""
    session.lose_life()

    if session.is_game_over:
        state_controller.end_game(session)
        return PlayerDeathOutcome.GAME_OVER

    player.respawn(spawn_tile, world)
    return PlayerDeathOutcome.RESPAWNED
