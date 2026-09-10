"""Integration tests for the soak simulation harness and invariant checker."""

import pytest

from pacman.application.context import AppContext, GameSession
from pacman.application.state import GameState
from pacman.gameplay.ghost import GhostIdentity, GhostState
from pacman.gameplay.player import Direction, Player
from pacman.gameplay.progression import LevelCompletionOutcome
from pacman.infrastructure.config import GameConfig, LevelConfig
from tests.support.gameplay_fakes import FixedMazeAdapter
from tests.support.soak_harness import (
    SoakInvariantChecker,
    SoakInvariantViolation,
    SoakSimulationHarness,
)


def test_invariant_checker_passes_on_valid_state() -> None:
    """Verify that a valid session state passes all invariant checks."""
    checker = SoakInvariantChecker()
    session = GameSession(lives=3, score=100, remaining_level_time=60.0)

    # Should not raise any exception
    checker.check(session=session)


def test_invariant_checker_catches_negative_lives() -> None:
    """Verify that negative lives trigger a SoakInvariantViolation."""
    checker = SoakInvariantChecker()
    session = GameSession(lives=-1, score=0, remaining_level_time=60.0)

    with pytest.raises(SoakInvariantViolation, match="Negative lives"):
        checker.check(session=session)


def test_invariant_checker_catches_negative_score() -> None:
    """Verify that a negative score triggers a SoakInvariantViolation."""
    checker = SoakInvariantChecker()
    session = GameSession(lives=3, score=-50, remaining_level_time=60.0)

    with pytest.raises(SoakInvariantViolation, match="Negative score"):
        checker.check(session=session)


def test_invariant_checker_catches_decreasing_score() -> None:
    """Verify that a score decrease triggers a SoakInvariantViolation."""
    checker = SoakInvariantChecker(allow_score_reset_on_new_session=False)
    session = GameSession(lives=3, score=200, remaining_level_time=60.0)
    checker.check(session=session)

    session.score = 150
    with pytest.raises(SoakInvariantViolation, match="Score decreased"):
        checker.check(session=session)


def test_invariant_checker_catches_invalid_timer() -> None:
    """Verify that negative or NaN timers trigger an invariant violation."""
    checker = SoakInvariantChecker()
    session = GameSession(lives=3, score=0, remaining_level_time=-1.0)

    with pytest.raises(SoakInvariantViolation, match="Negative remaining"):
        checker.check(session=session)


def test_invariant_checker_catches_player_in_wall() -> None:
    """Verify that a player position inside a wall triggers a violation."""
    config = GameConfig(
        levels=[LevelConfig(width=7, height=7)],
        seed=42,
    )
    context = AppContext(config=config)
    context.start_new_game()
    assert context.active_level is not None

    checker = SoakInvariantChecker()
    # Tile (0, 0) is an outer wall in standard mazes
    wall_player = Player.from_spawn((0, 0))

    with pytest.raises(SoakInvariantViolation, match="Player in non-corridor"):
        checker.check(
            session=context.session,
            world=context.active_level.world,
            player=wall_player,
        )


def test_soak_harness_advances_simulation_frames() -> None:
    """Verify the harness advances time, frames, and runs invariant checks."""
    config = GameConfig(
        level_max_time=10,
        levels=[LevelConfig(width=7, height=7)],
        seed=42,
    )
    context = AppContext(config=config)
    context.start_new_game()

    harness = SoakSimulationHarness(context=context)

    initial_time = context.session.remaining_level_time
    # Advance 60 frames at 1/60s (1.0 second)
    harness.step_n(frames=60, dt=1.0 / 60.0)

    assert harness.metrics.total_frames == 60
    assert harness.metrics.total_simulated_time == pytest.approx(1.0)
    assert context.session.remaining_level_time == pytest.approx(
        initial_time - 1.0
    )


def test_soak_harness_handles_level_advancement() -> None:
    """Verify harness transitions cleanly to the next level."""
    config = GameConfig(
        levels=[
            LevelConfig(width=7, height=7),
            LevelConfig(width=7, height=7),
        ],
        seed=42,
    )
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=FixedMazeAdapter(),
    )
    context.start_new_game()

    harness = SoakSimulationHarness(context=context)

    # Empty pellets to satisfy completion
    assert context.active_level is not None
    assert context.active_level.pellets is not None
    context.active_level.pellets.pacgums.clear()
    context.active_level.pellets.super_pacgums.clear()

    outcome = harness.advance_to_next_level()
    assert outcome is LevelCompletionOutcome.ADVANCED
    assert harness.metrics.levels_completed == 1
    assert context.session.current_level == 1
    assert harness.ghost_gameplay is not None

    # Complete level 2 -> Victory
    assert context.active_level is not None
    assert context.active_level.pellets is not None
    context.active_level.pellets.pacgums.clear()
    context.active_level.pellets.super_pacgums.clear()

    victory_outcome = harness.advance_to_next_level()
    assert victory_outcome is LevelCompletionOutcome.VICTORY
    assert harness.metrics.levels_completed == 2
    assert harness.controller.state is GameState.VICTORY
    assert harness.ghost_gameplay is None


def test_high_speed_soak_harness_stress_1000_frames() -> None:
    """Verify 1000 simulation frames execute without error or drift."""
    config = GameConfig(
        level_max_time=90,
        levels=[LevelConfig(width=7, height=7)],
        seed=42,
    )
    context = AppContext(config=config)
    context.start_new_game()
    context.cheat_mode.enabled = True
    context.cheat_mode.invincibility_enabled = True

    harness = SoakSimulationHarness(context=context)

    # Move player in all 4 directions over 1000 ticks
    directions = [
        Direction.UP,
        Direction.RIGHT,
        Direction.DOWN,
        Direction.LEFT,
    ]
    for i in range(1000):
        harness.tick(dt=1.0 / 60.0, player_turn=directions[(i // 25) % 4])

    assert harness.metrics.total_frames == 1000
    assert harness.metrics.total_simulated_time == pytest.approx(1000.0 / 60.0)
    assert context.session.remaining_level_time == pytest.approx(
        90.0 - (1000.0 / 60.0)
    )
    # Ghosts should be running legally without exceptions
    assert harness.ghost_gameplay is not None
    for ghost in harness.ghost_gameplay.ghosts:
        assert ghost.identity in (
            GhostIdentity.BLINKY,
            GhostIdentity.PINKY,
            GhostIdentity.INKY,
            GhostIdentity.CLYDE,
        )
        assert isinstance(ghost.state, GhostState)
