"""Tests for frame-level ghost collision edge cases."""

from pacman.app import GameState, GameStateController
from pacman.application.context import GameSession
from pacman.gameplay.ghost import Ghost, GhostIdentity, GhostState
from pacman.gameplay.ghost_collision import (
    GhostCollisionGuard,
    resolve_ghost_collisions,
)
from pacman.gameplay.lives import handle_normal_ghost_collision
from pacman.gameplay.player import Player
from pacman.gameplay.power_state import PowerState
from tests.support.gameplay_fakes import corridor_world


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


def test_repeated_normal_overlap_reports_only_first_player_hit() -> None:
    """Verify continuous contact cannot kill the player every frame."""
    session = GameSession(lives=3)
    ghost = _ghost(GhostIdentity.BLINKY, GhostState.NORMAL)
    guard = GhostCollisionGuard()

    first = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )
    repeated = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )

    assert first.player_hit is True
    assert repeated.player_hit is False
    assert session.lives == 3


def test_separation_allows_a_later_normal_collision() -> None:
    """Verify ending contact rearms the guard for a new collision."""
    session = GameSession(lives=3)
    ghost = _ghost(GhostIdentity.BLINKY, GhostState.NORMAL)
    guard = GhostCollisionGuard()

    first = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )
    separated = resolve_ghost_collisions(
        session,
        (),
        PowerState(),
        guard=guard,
    )
    later = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )

    assert first.player_hit is True
    assert separated.player_hit is False
    assert later.player_hit is True


def test_repeated_frame_guard_prevents_multiple_life_losses() -> None:
    """Verify one continuous overlap removes only one of three lives."""
    session = GameSession(lives=3)
    player = Player.from_spawn((1, 1))
    ghost = _ghost(GhostIdentity.BLINKY, GhostState.NORMAL)
    controller = GameStateController(GameState.PLAYING)
    guard = GhostCollisionGuard()
    world = corridor_world()

    first = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )
    if first.player_hit:
        handle_normal_ghost_collision(
            session,
            player,
            (1, 1),
            world,
            controller,
        )

    repeated = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )
    if repeated.player_hit:
        handle_normal_ghost_collision(
            session,
            player,
            (1, 1),
            world,
            controller,
        )

    assert first.player_hit is True
    assert repeated.player_hit is False
    assert session.lives == 2


def test_power_expiry_before_collision_makes_ghost_dangerous() -> None:
    """Verify collision uses the state produced by the current timer update."""
    session = GameSession()
    ghost = _ghost(GhostIdentity.PINKY, GhostState.FRIGHTENED)
    power_state = PowerState(remaining_time=0.1)

    power_state.update(0.1, (ghost,))
    result = resolve_ghost_collisions(session, (ghost,), power_state)

    assert ghost.state is GhostState.NORMAL
    assert result.player_hit is True
    assert result.eaten_ghosts == 0
    assert result.score_gained == 0
    assert session.score == 0


def test_respawn_transition_creates_one_new_normal_contact() -> None:
    """Verify respawning is safe and its normal return is handled once."""
    session = GameSession()
    ghost = _ghost(GhostIdentity.CLYDE, GhostState.EATEN)
    ghost.start_respawn(0.5)
    guard = GhostCollisionGuard()

    while_respawning = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )
    ghost.update(0.5)
    after_respawn = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )
    repeated = resolve_ghost_collisions(
        session,
        (ghost,),
        PowerState(),
        guard=guard,
    )

    assert while_respawning.player_hit is False
    assert ghost.state is GhostState.NORMAL
    assert after_respawn.player_hit is True
    assert repeated.player_hit is False
