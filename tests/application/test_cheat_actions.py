"""Application tests for one-shot evaluation cheat actions."""

from pacman.application.cheat_actions import (
    add_extra_life,
    skip_current_level,
    synchronize_player_speed,
    toggle_player_speed_boost,
)
from pacman.application.cheat_mode import CheatMode
from pacman.application.context import GameSession
from pacman.application.state import GameState, GameStateController
from pacman.gameplay.player import Direction, Player
from pacman.gameplay.progression import LevelCompletionOutcome
from pacman.infrastructure.config import GameConfig
from pacman.maze.level_generator import LevelGenerator
from tests.support.gameplay_fakes import FixedMazeAdapter


def _generator() -> LevelGenerator:
    """Create deterministic levels for cheat progression tests."""
    return LevelGenerator(
        config=GameConfig(level_max_time=60),
        adapter=FixedMazeAdapter(),
    )


def test_extra_life_requires_active_cheat_mode() -> None:
    """Verify the extra-life action cannot bypass master activation."""
    session = GameSession(lives=3)

    assert not add_extra_life(CheatMode(), session)
    assert session.lives == 3


def test_extra_life_adds_exactly_one_without_other_state_changes() -> None:
    """Verify one activation preserves score, level, and timer."""
    session = GameSession(
        score=700,
        lives=2,
        current_level=3,
        remaining_level_time=42.5,
    )

    assert add_extra_life(CheatMode(enabled=True), session)

    assert session.lives == 3
    assert session.score == 700
    assert session.current_level == 3
    assert session.remaining_level_time == 42.5


def test_level_skip_requires_active_cheat_mode() -> None:
    """Verify a disabled cheat cannot change progression state."""
    session = GameSession(current_level=2, remaining_level_time=30.0)
    player = Player.from_spawn((3, 3))
    controller = GameStateController(GameState.PLAYING)

    result = skip_current_level(
        CheatMode(), session, player, _generator(), controller
    )

    assert result is None
    assert session.current_level == 2
    assert session.remaining_level_time == 30.0
    assert controller.state is GameState.PLAYING


def test_level_skip_uses_normal_progression_and_preserves_session() -> None:
    """Verify skip advances once, resets time, and preserves score/lives."""
    session = GameSession(
        score=900,
        lives=4,
        current_level=2,
        remaining_level_time=11.0,
        total_levels=10,
    )
    player = Player(
        position=(1.5, 1.5),
        direction=Direction.RIGHT,
        queued_direction=Direction.UP,
    )
    controller = GameStateController(GameState.PLAYING)

    result = skip_current_level(
        CheatMode(enabled=True),
        session,
        player,
        _generator(),
        controller,
    )

    assert result is not None
    outcome, next_level = result
    assert outcome is LevelCompletionOutcome.ADVANCED
    assert next_level is not None
    assert session.current_level == 3
    assert session.score == 900
    assert session.lives == 4
    assert session.remaining_level_time == 60.0
    assert player.position == (3.5, 3.5)
    assert player.direction is Direction.NONE
    assert player.queued_direction is Direction.NONE


def test_level_skip_on_final_level_triggers_victory() -> None:
    """Verify skipping the final level follows the normal victory path."""
    session = GameSession(
        score=1200,
        lives=3,
        current_level=9,
        total_levels=10,
    )
    controller = GameStateController(GameState.PLAYING)

    result = skip_current_level(
        CheatMode(enabled=True),
        session,
        Player.from_spawn((3, 3)),
        _generator(),
        controller,
    )

    assert result == (LevelCompletionOutcome.VICTORY, None)
    assert session.is_victory
    assert session.score == 1200
    assert session.lives == 3
    assert controller.state is GameState.VICTORY


def test_speed_boost_is_reversible_without_changing_base_speed() -> None:
    """Verify repeated toggles apply 2x then restore exact normal speed."""
    cheat_mode = CheatMode(enabled=True)
    player = Player.from_spawn((1, 1), speed=6.5)
    original_state = (
        player.position,
        player.direction,
        player.queued_direction,
    )

    assert toggle_player_speed_boost(cheat_mode, player) is True
    assert player.speed == 6.5
    assert player.movement_speed == 13.0

    assert toggle_player_speed_boost(cheat_mode, player) is False
    assert player.speed == 6.5
    assert player.movement_speed == 6.5
    assert (
        player.position,
        player.direction,
        player.queued_direction,
    ) == original_state


def test_speed_boost_requires_active_cheat_mode() -> None:
    """Verify speed cannot change while evaluation mode is disabled."""
    player = Player.from_spawn((1, 1), speed=5.0)

    assert toggle_player_speed_boost(CheatMode(), player) is None
    assert player.speed_multiplier == 1.0
    assert player.movement_speed == 5.0


def test_disabling_cheat_mode_restores_normal_player_speed() -> None:
    """Verify synchronization removes boost after master deactivation."""
    cheat_mode = CheatMode(enabled=True)
    player = Player.from_spawn((1, 1))
    toggle_player_speed_boost(cheat_mode, player)

    cheat_mode.toggle()
    synchronize_player_speed(cheat_mode, player)

    assert not cheat_mode.speed_boost_enabled
    assert player.speed_multiplier == 1.0
    assert player.movement_speed == 5.0
