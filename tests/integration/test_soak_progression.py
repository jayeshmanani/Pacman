"""Multi-level marathon and progression soak tests for PK-92."""

from pathlib import Path

from pacman.application.context import AppContext
from pacman.application.state import GameState
from pacman.gameplay.progression import LevelCompletionOutcome
from pacman.infrastructure.config import (
    GameConfig,
    LevelConfig,
    load_commented_json,
    parse_game_config,
)
from tests.support.soak_harness import SoakSimulationHarness


def _load_default_project_config() -> GameConfig:
    """Load and parse the project's root config.json."""
    config_file = Path("config.json")
    data = load_commented_json(config_file)
    return parse_game_config(data)


def test_full_10_level_campaign_reaches_victory() -> None:
    """Verify an unbroken marathon through all 10 levels reaches victory."""
    config = _load_default_project_config()
    assert len(config.levels) >= 10

    context = AppContext(config=config)
    context.start_new_game()
    context.cheat_mode.enabled = True
    context.cheat_mode.invincibility_enabled = True

    harness = SoakSimulationHarness(context=context)

    total_levels = len(config.levels)
    for level_idx in range(total_levels):
        assert context.session.current_level == level_idx
        assert context.active_level is not None
        expected_width = 2 * config.levels[level_idx].width + 1
        expected_height = 2 * config.levels[level_idx].height + 1
        assert context.active_level.maze.width == expected_width
        assert context.active_level.maze.height == expected_height

        # Run 30 active frames of gameplay per level
        harness.step_n(frames=30, dt=1.0 / 60.0)

        # Clear pellets to trigger level advancement
        assert context.active_level.pellets is not None
        context.active_level.pellets.pacgums.clear()
        context.active_level.pellets.super_pacgums.clear()

        outcome = harness.advance_to_next_level()
        if level_idx < total_levels - 1:
            assert outcome is LevelCompletionOutcome.ADVANCED
            assert harness.controller.state is GameState.PLAYING
            assert harness.ghost_gameplay is not None
        else:
            assert outcome is LevelCompletionOutcome.VICTORY
            assert harness.controller.state is GameState.VICTORY
            assert context.session.is_victory
            assert harness.ghost_gameplay is None

    assert harness.metrics.levels_completed == total_levels
    assert context.session.lives == config.lives
    assert harness.metrics.total_frames == total_levels * 30


def test_multi_level_entity_isolation_and_spawns() -> None:
    """Verify entity coordinates and spawns stay fresh across levels."""
    config = GameConfig(
        levels=[
            LevelConfig(width=7, height=7),
            LevelConfig(width=9, height=9),
            LevelConfig(width=11, height=11),
        ],
        seed=100,
    )
    context = AppContext(config=config)
    context.start_new_game()

    harness = SoakSimulationHarness(context=context)

    previous_pellet_ids: set[int] = set()

    for level_idx in range(len(config.levels)):
        active_level = context.active_level
        assert active_level is not None
        assert active_level.spawns is not None
        assert active_level.pellets is not None

        # Verify pellet container is fresh and not reused
        pellet_id = id(active_level.pellets)
        assert pellet_id not in previous_pellet_ids
        previous_pellet_ids.add(pellet_id)

        # Verify player is at level-specific center spawn
        expected_player_pos = active_level.world.tile_center(
            active_level.spawns.player
        )
        assert context.player is not None
        assert context.player.position == expected_player_pos

        # Verify ghost spawns match the new level corner bounds
        assert harness.ghost_gameplay is not None
        ghost_spawns = active_level.spawns.ghosts.as_tuple()
        for ghost in harness.ghost_gameplay.ghosts:
            assert ghost.home_spawn in ghost_spawns
            assert active_level.world.is_walkable_tile(ghost.home_spawn)

        # Clear level
        active_level.pellets.pacgums.clear()
        active_level.pellets.super_pacgums.clear()
        harness.advance_to_next_level()


def test_multi_level_preserves_score_and_lives_after_loss() -> None:
    """Verify lives and scores carry over cleanly after mid-game life loss."""
    config = GameConfig(
        levels=[
            LevelConfig(width=7, height=7),
            LevelConfig(width=7, height=7),
            LevelConfig(width=7, height=7),
        ],
        seed=42,
        points_per_pacgum=10,
    )
    context = AppContext(config=config)
    context.start_new_game()

    harness = SoakSimulationHarness(context=context)

    # Level 0: Earn 50 points
    context.session.score += 50
    assert context.active_level is not None
    assert context.active_level.pellets is not None
    context.active_level.pellets.pacgums.clear()
    context.active_level.pellets.super_pacgums.clear()
    harness.advance_to_next_level()

    # Level 1: Player loses a life (3 -> 2) and earns 30 points
    assert context.session.lives == 3
    context.session.lose_life()
    assert context.session.lives == 2
    context.session.score += 30

    assert context.active_level is not None
    assert context.active_level.pellets is not None
    context.active_level.pellets.pacgums.clear()
    context.active_level.pellets.super_pacgums.clear()
    harness.advance_to_next_level()

    # Level 2: Lives should still be 2, score should be 80
    assert context.session.lives == 2
    assert context.session.score == 80
    context.session.score += 20

    assert context.active_level is not None
    assert context.active_level.pellets is not None
    context.active_level.pellets.pacgums.clear()
    context.active_level.pellets.super_pacgums.clear()
    outcome = harness.advance_to_next_level()

    # Final Victory
    assert outcome is LevelCompletionOutcome.VICTORY
    assert context.session.is_victory
    assert context.session.lives == 2
    assert context.session.score == 100


def test_dynamic_campaign_lengths_scale_accurately() -> None:
    """Verify varying campaign lengths complete at exact final level."""
    for level_count in (1, 2, 4):
        config = GameConfig(
            levels=[
                LevelConfig(width=7, height=7)
                for _ in range(level_count)
            ],
            seed=42,
        )
        context = AppContext(config=config)
        context.start_new_game()

        harness = SoakSimulationHarness(context=context)

        for step in range(level_count):
            assert context.active_level is not None
            assert context.active_level.pellets is not None
            context.active_level.pellets.pacgums.clear()
            context.active_level.pellets.super_pacgums.clear()
            outcome = harness.advance_to_next_level()
            if step < level_count - 1:
                assert outcome is LevelCompletionOutcome.ADVANCED
            else:
                assert outcome is LevelCompletionOutcome.VICTORY
                assert context.session.is_victory


def test_abandoned_marathon_resets_cleanly_without_residual_state() -> None:
    """Verify abandoning a mid-campaign game resets all progression state."""
    config = GameConfig(
        levels=[
            LevelConfig(width=7, height=7),
            LevelConfig(width=7, height=7),
            LevelConfig(width=7, height=7),
        ],
        seed=42,
    )
    context = AppContext(config=config)
    context.start_new_game()
    harness = SoakSimulationHarness(context=context)

    # Advance to level 1 and modify state
    assert context.active_level is not None
    assert context.active_level.pellets is not None
    context.active_level.pellets.pacgums.clear()
    context.active_level.pellets.super_pacgums.clear()
    harness.advance_to_next_level()

    context.session.score = 500
    context.session.lose_life()
    assert context.session.current_level == 1
    assert context.session.lives == 2

    # Abandon game (e.g. Return to Main Menu)
    context.reset_session()

    assert context.session.current_level == 0
    assert context.session.score == 0
    assert context.session.lives == 3
    assert context.active_level is None
    assert context.player is None

    # Start fresh game
    context.start_new_game()
    assert context.session.current_level == 0
    assert context.session.score == 0
    assert context.session.lives == 3
    assert context.active_level is not None
    assert context.player is not None
