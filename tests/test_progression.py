"""Tests for level completion and multi-level progression."""

from pacman.app import GameState, GameStateController
from pacman.config import GameConfig
from pacman.context import GameSession
from pacman.level_generator import LevelGenerator
from pacman.maze_adapter import MazeGeneratorAdapter
from pacman.maze_grid import MazeGrid, Tile
from pacman.player import Direction, Player
from pacman.progression import LevelCompletionOutcome, handle_level_completion


class _FakeAdapter(MazeGeneratorAdapter):
    """Simple adapter returning a walkable 7x7 corridor grid."""

    def generate(
        self,
        width: int,
        height: int,
        seed: int = 0,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] = (-1, -1),
        include_42: bool = True,
    ) -> MazeGrid:
        rows = tuple(
            tuple(Tile.CORRIDOR for _ in range(7))
            for _ in range(7)
        )
        return MazeGrid(tiles=rows, entry=(0, 0), exit=(6, 6))


def test_level_completion_preserves_score_and_lives() -> None:
    """Verify completing a level keeps score and lives and resets timer."""
    session = GameSession(
        score=350,
        lives=2,
        current_level=0,
        total_levels=10,
        remaining_level_time=12.5,
    )
    player = Player(
        position=(1.5, 1.5),
        direction=Direction.RIGHT,
        queued_direction=Direction.UP,
    )
    generator = LevelGenerator(adapter=_FakeAdapter())
    controller = GameStateController(GameState.PLAYING)

    outcome, next_level = handle_level_completion(
        session,
        player,
        generator,
        controller,
    )

    assert outcome is LevelCompletionOutcome.ADVANCED
    assert next_level is not None
    assert session.current_level == 1
    assert session.score == 350                  # Score preserved
    assert session.lives == 2                    # Lives preserved
    assert session.remaining_level_time == 90.0  # Timer reset for new level
    assert not session.level_timed_out
    assert player.position == (3.5, 3.5)         # Repositioned to center
    assert player.direction is Direction.NONE
    assert player.queued_direction is Direction.NONE
    assert controller.state is GameState.PLAYING


def test_final_level_completion_triggers_game_victory() -> None:
    """Verify completing the final level ends game and marks victory."""
    session = GameSession(
        score=1500,
        lives=3,
        current_level=9,                         # 10th level (0-indexed)
        total_levels=10,
    )
    player = Player.from_spawn((3, 3))
    generator = LevelGenerator(adapter=_FakeAdapter())
    controller = GameStateController(GameState.PLAYING)

    outcome, next_level = handle_level_completion(
        session,
        player,
        generator,
        controller,
    )

    assert outcome is LevelCompletionOutcome.VICTORY
    assert next_level is None
    assert session.is_victory is True
    assert session.score == 1500
    assert controller.state is GameState.END_SCREEN


def test_progression_supports_at_least_ten_consecutive_levels() -> None:
    """Verify completing 10 levels consecutively leads to victory."""
    config = GameConfig(level_max_time=60)
    generator = LevelGenerator(config=config, adapter=_FakeAdapter())
    session = GameSession(score=0, lives=3, total_levels=10)
    player = Player.from_spawn((3, 3))
    controller = GameStateController(GameState.PLAYING)

    for level_idx in range(9):  # Levels 0 through 8
        outcome, next_level = handle_level_completion(
            session,
            player,
            generator,
            controller,
        )
        assert outcome is LevelCompletionOutcome.ADVANCED
        assert next_level is not None
        assert session.current_level == level_idx + 1
        assert session.remaining_level_time == 60.0

    # Final level (Level 9)
    outcome, next_level = handle_level_completion(
        session,
        player,
        generator,
        controller,
    )
    assert outcome is LevelCompletionOutcome.VICTORY
    assert next_level is None
    assert session.is_victory is True
    assert controller.state is GameState.END_SCREEN
