"""Integrated player-flow tests from movement through game victory."""

import pytest

from pacman.app import GameState, GameStateController, update_active_gameplay
from pacman.config import GameConfig
from pacman.context import GameSession
from pacman.level_generator import LevelGenerator
from pacman.pacgums import PacgumField, collect_pacgum
from pacman.player import Direction, Player
from pacman.progression import LevelCompletionOutcome, handle_level_completion
from tests.gameplay_fakes import FixedMazeAdapter, corridor_world


def test_complete_player_flow_reaches_victory() -> None:
    """Verify rules cooperate from movement and scoring through victory."""
    world = corridor_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.RIGHT
    session = GameSession(
        lives=3,
        total_levels=2,
        remaining_level_time=5.0,
    )
    controller = GameStateController(GameState.PLAYING)
    first_pacgums = PacgumField(pacgums={(2, 1)}, super_pacgums=set())

    def move_and_collect(dt: float) -> None:
        player.update(dt, world)
        session.score += collect_pacgum(player.position, first_pacgums)

    session.pause_gameplay()
    update_active_gameplay(session, controller, 0.2, move_and_collect)

    assert player.position == (1.5, 1.5)
    assert session.score == 0
    assert session.remaining_level_time == 5.0

    session.resume_gameplay()
    update_active_gameplay(session, controller, 0.2, move_and_collect)

    assert player.position == (2.5, 1.5)
    assert first_pacgums.is_complete
    assert session.score == 10
    assert session.remaining_level_time == pytest.approx(4.8)

    config = GameConfig(level_max_time=30)
    generator = LevelGenerator(config=config, adapter=FixedMazeAdapter())
    outcome, next_level = handle_level_completion(
        session,
        player,
        generator,
        controller,
    )

    assert outcome is LevelCompletionOutcome.ADVANCED
    assert next_level is not None
    assert next_level.spawns is not None
    assert next_level.pellets is not None
    assert session.current_level == 1
    assert session.score == 10
    assert session.lives == 3
    assert session.remaining_level_time == 30.0
    assert player.position == next_level.world.tile_center(
        next_level.spawns.player,
    )

    normal_count = len(next_level.pellets.pacgums)
    super_count = len(next_level.pellets.super_pacgums)
    expected_final_score = (
        session.score
        + normal_count * config.points_per_pacgum
        + super_count * config.points_per_super_pacgum
    )
    remaining_pacgums = (
        next_level.pellets.pacgums
        | next_level.pellets.super_pacgums
    )
    for x, y in tuple(remaining_pacgums):
        session.score += collect_pacgum(
            (x + 0.5, y + 0.5),
            next_level.pellets,
            points_per_pacgum=config.points_per_pacgum,
            points_per_super_pacgum=config.points_per_super_pacgum,
        )

    assert next_level.pellets.is_complete
    assert session.score == expected_final_score

    outcome, generated_level = handle_level_completion(
        session,
        player,
        generator,
        controller,
    )

    assert outcome is LevelCompletionOutcome.VICTORY
    assert generated_level is None
    assert session.is_victory
    assert session.lives == 3
    assert controller.state is GameState.END_SCREEN
