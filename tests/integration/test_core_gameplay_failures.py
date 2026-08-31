"""Integrated gameplay tests for blocked, timeout, and death paths."""


import pytest

from pacman.app import GameState, GameStateController, update_active_gameplay
from pacman.application.context import GameSession
from pacman.gameplay.lives import (
    PlayerDeathOutcome,
    handle_normal_ghost_collision,
)
from pacman.gameplay.player import Direction, Player
from tests.support.gameplay_fakes import blocked_world, corridor_world


def test_wall_collision_and_timeout_preserve_session_data() -> None:
    """Verify a blocked move and timeout end play without corrupting data."""
    world = blocked_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.RIGHT
    session = GameSession(
        score=120,
        lives=2,
        remaining_level_time=0.1,
    )
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(
        session,
        controller,
        0.2,
        lambda dt: player.update(dt, world),
    )

    assert player.position == (1.5, 1.5)
    assert player.direction is Direction.NONE
    assert session.remaining_level_time == 0.0
    assert session.level_timed_out
    assert session.is_game_over
    assert session.score == 120
    assert session.lives == 2
    assert controller.state is GameState.END_SCREEN


def test_repeated_normal_collisions_lead_to_game_over() -> None:
    """Verify respawn after one death and game over after the final life."""
    world = corridor_world()
    player = Player(
        position=(2.5, 1.5),
        direction=Direction.LEFT,
        queued_direction=Direction.RIGHT,
    )
    session = GameSession(
        score=75,
        lives=2,
        remaining_level_time=8.0,
    )
    controller = GameStateController(GameState.PLAYING)

    first_outcome = handle_normal_ghost_collision(
        session,
        player,
        (1, 1),
        world,
        controller,
    )

    assert first_outcome is PlayerDeathOutcome.RESPAWNED
    assert session.lives == 1
    assert session.score == 75
    assert session.remaining_level_time == 8.0
    assert player.position == (1.5, 1.5)
    assert player.direction is Direction.NONE
    assert player.queued_direction is Direction.NONE
    assert controller.state.value == GameState.PLAYING.value

    player.position = (2.5, 1.5)
    final_position = player.position
    final_outcome = handle_normal_ghost_collision(
        session,
        player,
        (1, 1),
        world,
        controller,
    )

    assert final_outcome is PlayerDeathOutcome.GAME_OVER
    assert session.lives == 0
    assert session.is_game_over
    assert session.score == 75
    assert player.position == final_position
    assert controller.state is GameState.END_SCREEN


@pytest.mark.parametrize("paused", [True, False])
def test_timer_only_advances_during_unpaused_gameplay(paused: bool) -> None:
    """Verify the shared update gate controls the timer consistently."""
    session = GameSession(remaining_level_time=4.0, is_paused=paused)
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(session, controller, 1.0)

    expected_time = 4.0 if paused else 3.0
    assert session.remaining_level_time == expected_time
    assert controller.state is GameState.PLAYING
