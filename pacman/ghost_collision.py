"""Resolve collisions between the player and ghosts by ghost state."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from pacman.context import GameSession
from pacman.ghost import Ghost, GhostState
from pacman.power_state import PowerState


class GhostCollisionOutcome(Enum):
    """Describe the gameplay result of touching a ghost."""

    PLAYER_HIT = "player_hit"
    GHOST_EATEN = "ghost_eaten"
    IGNORED = "ignored"


@dataclass(frozen=True)
class GhostCollisionFrameResult:
    """Summarize all ghost collision effects resolved for one frame."""

    player_hit: bool = False
    eaten_ghosts: int = 0
    score_gained: int = 0


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


def resolve_ghost_collisions(
    session: GameSession,
    ghosts: Iterable[Ghost],
    power_state: PowerState,
    points_per_ghost: int = 200,
    respawn_delay: float = 5.0,
) -> GhostCollisionFrameResult:
    """Resolve every overlapping ghost deterministically for one frame."""
    colliding_ghosts = tuple(ghosts)
    if any(
        ghost.state is GhostState.NORMAL
        for ghost in colliding_ghosts
    ):
        return GhostCollisionFrameResult(player_hit=True)

    score_before = session.score
    eaten_ghosts = 0
    for ghost in colliding_ghosts:
        outcome = handle_ghost_collision(
            session,
            ghost,
            power_state,
            points_per_ghost,
            respawn_delay,
        )
        if outcome is GhostCollisionOutcome.GHOST_EATEN:
            eaten_ghosts += 1

    return GhostCollisionFrameResult(
        eaten_ghosts=eaten_ghosts,
        score_gained=session.score - score_before,
    )
