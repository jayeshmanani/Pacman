"""Deterministic multi-frame scenarios for ghost behaviour."""

import random
from dataclasses import dataclass

from pacman.ghost import Ghost, GhostIdentity, GhostState
from pacman.player import Direction
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
