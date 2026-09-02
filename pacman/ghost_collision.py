"""Resolve collisions between the player and ghosts by ghost state."""

from enum import Enum

from pacman.context import GameSession
from pacman.ghost import Ghost, GhostState
from pacman.power_state import PowerState


class GhostCollisionOutcome(Enum):
    """Describe the gameplay result of touching a ghost."""

    PLAYER_HIT = "player_hit"
    GHOST_EATEN = "ghost_eaten"
    IGNORED = "ignored"


def handle_ghost_collision(
    session: GameSession,
    ghost: Ghost,
    power_state: PowerState,
    points_per_ghost: int = 200,
    respawn_delay: float = 5.0,
) -> GhostCollisionOutcome:
    """Resolve one ghost collision without applying player respawn details."""
    if ghost.state is GhostState.NORMAL:
        return GhostCollisionOutcome.PLAYER_HIT

    if ghost.state is not GhostState.FRIGHTENED:
        return GhostCollisionOutcome.IGNORED

    if not ghost.eat():
        return GhostCollisionOutcome.IGNORED

    session.score += power_state.claim_ghost_score(points_per_ghost)
    ghost.start_respawn(respawn_delay)
    return GhostCollisionOutcome.GHOST_EATEN
