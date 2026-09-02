"""Gameplay tests for player and ghost collision outcomes."""

from pacman.infrastructure.config import GameConfig
from pacman.application.context import GameSession
from pacman.gameplay.ghost import Ghost, GhostIdentity, GhostState
from pacman.gameplay.ghost_collision import (
    GhostCollisionOutcome,
    handle_ghost_collision,
)
from pacman.gameplay.power_state import PowerState


def _ghost(state: GhostState) -> Ghost:
    """Create a ghost in the requested state for collision tests."""
    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, (1, 1))
    ghost.state = state
    return ghost


def test_frightened_collision_scores_and_starts_respawn() -> None:
    """Verify an edible ghost awards points and starts its return delay."""
    session = GameSession(score=100)
    ghost = _ghost(GhostState.FRIGHTENED)
    ghost.frightened_timer = 4.0
    power_state = PowerState(remaining_time=4.0)

    outcome = handle_ghost_collision(
        session=session,
        ghost=ghost,
        power_state=power_state,
        points_per_ghost=200,
        respawn_delay=5.0,
    )

    assert outcome is GhostCollisionOutcome.GHOST_EATEN
    assert session.score == 300
    assert ghost.state is GhostState.RESPAWNING
    assert ghost.respawn_timer == 5.0
    assert ghost.frightened_timer == 0.0
    assert ghost.position == (1.5, 1.5)


def test_normal_collision_reports_player_hit_without_changing_score() -> None:
    """Verify a normal ghost delegates player damage to the caller."""
    session = GameSession(score=100)
    ghost = _ghost(GhostState.NORMAL)
    power_state = PowerState()

    outcome = handle_ghost_collision(
        session,
        ghost,
        power_state,
        points_per_ghost=200,
    )

    assert outcome is GhostCollisionOutcome.PLAYER_HIT
    assert session.score == 100
    assert ghost.state is GhostState.NORMAL


def test_inactive_ghost_collision_is_ignored() -> None:
    """Verify eaten and respawning ghosts cannot harm the player."""
    for state in (GhostState.EATEN, GhostState.RESPAWNING):
        session = GameSession(score=100)
        ghost = _ghost(state)
        power_state = PowerState()

        outcome = handle_ghost_collision(session, ghost, power_state)

        assert outcome is GhostCollisionOutcome.IGNORED
        assert session.score == 100
        assert ghost.state is state


def test_repeated_collision_does_not_award_points_twice() -> None:
    """Verify one frightened ghost can score only once per activation."""
    session = GameSession(score=0)
    ghost = _ghost(GhostState.FRIGHTENED)
    power_state = PowerState(remaining_time=4.0)

    first = handle_ghost_collision(
        session,
        ghost,
        power_state,
        points_per_ghost=200,
    )
    second = handle_ghost_collision(
        session,
        ghost,
        power_state,
        points_per_ghost=200,
    )

    assert first is GhostCollisionOutcome.GHOST_EATEN
    assert second is GhostCollisionOutcome.IGNORED
    assert session.score == 200


def test_ghost_score_doubles_during_one_frightened_period() -> None:
    """Verify four quick ghost captures award 200, 400, 800, and 1600."""
    ghosts = [
        Ghost.from_spawn(identity, (index, 1))
        for index, identity in enumerate(GhostIdentity)
    ]
    session = GameSession()
    power_state = PowerState()
    power_state.activate(7.0, ghosts)
    gained_scores: list[int] = []

    for ghost in ghosts:
        previous_score = session.score
        handle_ghost_collision(
            session,
            ghost,
            power_state,
            points_per_ghost=200,
        )
        gained_scores.append(session.score - previous_score)

    assert gained_scores == [200, 400, 800, 1600]
    assert session.score == 3000


def test_new_power_activation_resets_ghost_score_chain() -> None:
    """Verify another super-pacgum starts ghost scoring again at 200."""
    first_ghost = _ghost(GhostState.NORMAL)
    second_ghost = Ghost.from_spawn(GhostIdentity.PINKY, (2, 1))
    session = GameSession()
    power_state = PowerState()
    power_state.activate(7.0, (first_ghost, second_ghost))
    handle_ghost_collision(session, first_ghost, power_state)
    assert session.score == 200

    power_state.activate(7.0, (second_ghost,))
    handle_ghost_collision(session, second_ghost, power_state)

    assert session.score == 400


def test_eaten_ghost_returns_after_configured_respawn_delay() -> None:
    """Verify configured scoring and the complete delayed return lifecycle."""
    config = GameConfig(points_per_ghost=250, ghost_respawn_delay=3.5)
    session = GameSession()
    ghost = _ghost(GhostState.FRIGHTENED)
    power_state = PowerState(remaining_time=7.0)

    outcome = handle_ghost_collision(
        session,
        ghost,
        power_state,
        points_per_ghost=config.points_per_ghost,
        respawn_delay=config.ghost_respawn_delay,
    )

    assert outcome is GhostCollisionOutcome.GHOST_EATEN
    assert session.score == 250
    assert ghost.state is GhostState.RESPAWNING
    assert ghost.respawn_timer == 3.5

    ghost.update(3.0)
    assert ghost.state is GhostState.RESPAWNING
    assert ghost.respawn_timer == 0.5

    ghost.update(0.5)
    state_after_respawn: GhostState = ghost.state
    assert state_after_respawn is GhostState.NORMAL
    assert ghost.respawn_timer == 0.0
