"""Application tests for one-shot evaluation cheat actions."""

from pacman.application.cheat_actions import add_extra_life, skip_current_level
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
