"""Resolve collisions between the player and ghosts by ghost state."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from pacman.context import GameSession
from pacman.ghost import Ghost, GhostState
from pacman.player import Player
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


@dataclass
class GhostCollisionGuard:
    """Suppress repeated player hits during one continuous overlap."""

    normal_contact_active: bool = False

    def register_normal_contact(self, is_contacting: bool) -> bool:
        """Return True only when a new normal-ghost contact begins."""
        if not is_contacting:
            self.normal_contact_active = False
            return False

        if self.normal_contact_active:
            return False

        self.normal_contact_active = True
        return True


def find_colliding_ghosts(
    player: Player,
    ghosts: Iterable[Ghost],
) -> tuple[Ghost, ...]:
    """Return ghosts whose bounds overlap the player's bounds."""
    player_x, player_y = player.position
    player_half_width, player_half_height = player.half_size
    colliding: list[Ghost] = []

    for ghost in ghosts:
        ghost_x, ghost_y = ghost.position
        ghost_half_width, ghost_half_height = ghost.half_size
        overlaps_horizontally = (
            abs(player_x - ghost_x)
            < player_half_width + ghost_half_width
        )
        overlaps_vertically = (
            abs(player_y - ghost_y)
            < player_half_height + ghost_half_height
        )
        if overlaps_horizontally and overlaps_vertically:
            colliding.append(ghost)

    return tuple(colliding)


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
    guard: GhostCollisionGuard | None = None,
) -> GhostCollisionFrameResult:
    """Resolve every overlapping ghost deterministically for one frame."""
    colliding_ghosts = tuple(ghosts)
    has_normal_contact = any(
        ghost.state is GhostState.NORMAL
        for ghost in colliding_ghosts
    )
    if has_normal_contact:
        is_new_contact = (
            guard.register_normal_contact(True)
            if guard is not None
            else True
        )
        return GhostCollisionFrameResult(player_hit=is_new_contact)

    if guard is not None:
        guard.register_normal_contact(False)

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
