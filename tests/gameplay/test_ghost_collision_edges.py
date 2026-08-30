"""Tests for frame-level ghost collision edge cases."""

from pacman.context import GameSession
from pacman.ghost import Ghost, GhostIdentity, GhostState
from pacman.ghost_collision import resolve_ghost_collisions
from pacman.power_state import PowerState


def _ghost(identity: GhostIdentity, state: GhostState) -> Ghost:
    """Create a ghost in the requested state for frame tests."""
    ghost = Ghost.from_spawn(identity, (1, 1))
    ghost.state = state
    if state is GhostState.FRIGHTENED:
        ghost.frightened_timer = 5.0
    return ghost


def test_multiple_normal_collisions_report_one_player_hit() -> None:
    """Verify one frame cannot report multiple player deaths."""
    session = GameSession(score=100, lives=3)
    ghosts = [
        _ghost(GhostIdentity.BLINKY, GhostState.NORMAL),
        _ghost(GhostIdentity.PINKY, GhostState.NORMAL),
    ]

    result = resolve_ghost_collisions(session, ghosts, PowerState())

    assert result.player_hit is True
    assert result.eaten_ghosts == 0
    assert result.score_gained == 0
    assert session.score == 100
    assert session.lives == 3


def test_multiple_frightened_collisions_score_each_ghost_once() -> None:
    """Verify simultaneous edible ghosts advance the score chain once each."""
    session = GameSession()
    ghosts = [
        _ghost(GhostIdentity.BLINKY, GhostState.FRIGHTENED),
        _ghost(GhostIdentity.PINKY, GhostState.FRIGHTENED),
    ]
    power_state = PowerState(remaining_time=5.0)

    result = resolve_ghost_collisions(
        session,
        ghosts,
        power_state,
        points_per_ghost=200,
        respawn_delay=5.0,
    )

    assert result.player_hit is False
    assert result.eaten_ghosts == 2
    assert result.score_gained == 600
    assert session.score == 600
    assert all(ghost.state is GhostState.RESPAWNING for ghost in ghosts)


def test_normal_collision_wins_independently_of_ghost_order() -> None:
    """Verify mixed-state collision outcome is deterministic."""
    for normal_first in (True, False):
        normal = _ghost(GhostIdentity.BLINKY, GhostState.NORMAL)
        frightened = _ghost(
            GhostIdentity.PINKY,
            GhostState.FRIGHTENED,
        )
        ghosts = (
            [normal, frightened]
            if normal_first
            else [frightened, normal]
        )
        session = GameSession()

        result = resolve_ghost_collisions(
            session,
            ghosts,
            PowerState(remaining_time=5.0),
        )

        assert result.player_hit is True
        assert result.eaten_ghosts == 0
        assert result.score_gained == 0
        assert session.score == 0
        assert frightened.state is GhostState.FRIGHTENED


def test_inactive_ghost_group_produces_no_collision_effect() -> None:
    """Verify eaten and respawning ghosts remain harmless for the frame."""
    session = GameSession(score=300)
    ghosts = [
        _ghost(GhostIdentity.INKY, GhostState.EATEN),
        _ghost(GhostIdentity.CLYDE, GhostState.RESPAWNING),
    ]

    result = resolve_ghost_collisions(session, ghosts, PowerState())

    assert result.player_hit is False
    assert result.eaten_ghosts == 0
    assert result.score_gained == 0
    assert session.score == 300
