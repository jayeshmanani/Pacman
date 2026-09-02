"""Deterministic multi-frame scenarios for ghost behaviour."""

import random
from dataclasses import dataclass

from pacman.context import GameSession
from pacman.ghost import Ghost, GhostIdentity, GhostState
from pacman.ghost_collision import (
    GhostCollisionGuard,
    resolve_ghost_collisions,
)
from pacman.player import Direction
from pacman.power_state import PowerState
from pacman.world import WorldMap, WorldPosition
from tests.gameplay_fakes import FixedMazeAdapter


@dataclass(frozen=True)
class GhostSnapshot:
    """Capture observable ghost behaviour after one simulated frame."""

    position: WorldPosition
    direction: Direction
    state: GhostState
    target_tile: tuple[int, int] | None


def _open_world() -> WorldMap:
    """Create the same bounded open maze for every scenario."""
    maze = FixedMazeAdapter().generate(width=7, height=7)
    return WorldMap(maze)


def _snapshot(ghost: Ghost) -> GhostSnapshot:
    """Return the observable state used for deterministic comparisons."""
    return GhostSnapshot(
        position=ghost.position,
        direction=ghost.direction,
        state=ghost.state,
        target_tile=ghost.target_tile,
    )


def _run_seeded_frightened_route(seed: int) -> list[GhostSnapshot]:
    """Run a frightened route with an isolated pseudo-random generator."""
    world = _open_world()
    ghost = Ghost.from_spawn(GhostIdentity.BLINKY, (3, 3))
    ghost.frighten(duration=5.0, reverse_direction=False)
    rng = random.Random(seed)
    route: list[GhostSnapshot] = []

    for _ in range(6):
        ghost.update(
            dt=0.125,
            world=world,
            base_speed=2.0,
            rng=rng,
            player_position=(4.5, 4.5),
            player_direction=Direction.LEFT,
        )
        assert world.can_occupy(ghost.position, half_size=(0.35, 0.35))
        route.append(_snapshot(ghost))

    return route


def test_normal_chase_route_is_repeatable_and_legal() -> None:
    """Verify a fixed chase scenario follows the same legal route."""
    routes: list[list[GhostSnapshot]] = []

    for _ in range(2):
        world = _open_world()
        ghost = Ghost.from_spawn(GhostIdentity.BLINKY, (3, 3))
        route: list[GhostSnapshot] = []

        for _ in range(4):
            ghost.update(
                dt=0.125,
                world=world,
                base_speed=2.0,
                player_position=(5.5, 3.5),
                player_direction=Direction.LEFT,
            )
            assert world.can_occupy(
                ghost.position,
                half_size=(0.35, 0.35),
            )
            route.append(_snapshot(ghost))

        routes.append(route)

    assert routes[0] == routes[1]
    assert [snapshot.position for snapshot in routes[0]] == [
        (3.75, 3.5),
        (4.0, 3.5),
        (4.25, 3.5),
        (4.5, 3.5),
    ]
    assert all(
        snapshot.direction is Direction.RIGHT
        and snapshot.state is GhostState.NORMAL
        and snapshot.target_tile == (5, 3)
        for snapshot in routes[0]
    )


def test_seeded_frightened_route_is_repeatable_and_legal() -> None:
    """Verify equal seeds reproduce the complete frightened route."""
    first_route = _run_seeded_frightened_route(seed=42)
    repeated_route = _run_seeded_frightened_route(seed=42)

    assert first_route == repeated_route
    assert all(
        snapshot.state is GhostState.FRIGHTENED
        and snapshot.target_tile is None
        for snapshot in first_route
    )


def test_frightened_expiration_changes_collision_at_exact_boundary() -> None:
    """Verify an exact timer expiry makes the ghost dangerous again."""
    session = GameSession()
    ghost = Ghost.from_spawn(GhostIdentity.PINKY, (3, 3))
    power_state = PowerState()
    power_state.activate(duration=0.75, ghosts=(ghost,))

    expired_early = power_state.update(dt=0.5, ghosts=(ghost,))

    assert expired_early is False
    assert power_state.remaining_time == 0.25
    assert ghost.state is GhostState.FRIGHTENED

    expired_at_boundary = power_state.update(dt=0.25, ghosts=(ghost,))
    collision = resolve_ghost_collisions(session, (ghost,), power_state)
    state_after_expiry: GhostState = ghost.state

    assert expired_at_boundary is True
    assert power_state.remaining_time == 0.0
    assert state_after_expiry is GhostState.NORMAL
    assert collision.player_hit is True
    assert collision.eaten_ghosts == 0
    assert collision.score_gained == 0
    assert session.score == 0


def test_eaten_ghost_is_safe_until_delayed_respawn_completes() -> None:
    """Verify eating, collision safety, and delayed return in one scenario."""
    session = GameSession()
    ghost = Ghost.from_spawn(GhostIdentity.INKY, (3, 3))
    power_state = PowerState()
    power_state.activate(duration=5.0, ghosts=(ghost,))
    guard = GhostCollisionGuard()

    eaten = resolve_ghost_collisions(
        session,
        (ghost,),
        power_state,
        points_per_ghost=200,
        respawn_delay=1.5,
        guard=guard,
    )
    repeated_while_respawning = resolve_ghost_collisions(
        session,
        (ghost,),
        power_state,
        guard=guard,
    )

    assert eaten.player_hit is False
    assert eaten.eaten_ghosts == 1
    assert eaten.score_gained == 200
    assert session.score == 200
    assert ghost.state is GhostState.RESPAWNING
    assert ghost.respawn_timer == 1.5
    assert repeated_while_respawning.player_hit is False
    assert repeated_while_respawning.eaten_ghosts == 0
    assert repeated_while_respawning.score_gained == 0

    ghost.update(dt=1.0)
    collision_before_return = resolve_ghost_collisions(
        session,
        (ghost,),
        power_state,
        guard=guard,
    )

    assert ghost.state is GhostState.RESPAWNING
    assert ghost.respawn_timer == 0.5
    assert collision_before_return.player_hit is False

    ghost.update(dt=0.5)
    collision_after_return = resolve_ghost_collisions(
        session,
        (ghost,),
        power_state,
        guard=guard,
    )
    repeated_normal_contact = resolve_ghost_collisions(
        session,
        (ghost,),
        power_state,
        guard=guard,
    )
    state_after_respawn: GhostState = ghost.state

    assert state_after_respawn is GhostState.NORMAL
    assert ghost.respawn_timer == 0.0
    assert collision_after_return.player_hit is True
    assert repeated_normal_contact.player_hit is False
    assert session.score == 200
