"""Integration tests for live configuration propagation."""

import json
from pathlib import Path

from pacman.application.context import AppContext
from pacman.application.state import GameState, GameStateController
from pacman.gameplay.ghost_gameplay import GhostGameplay
from pacman.gameplay.pacgums import PacgumField, collect_pacgum
from pacman.gameplay.progression import (
    LevelCompletionOutcome,
    handle_level_completion,
)
from pacman.infrastructure.config import (
    GameConfig,
    LevelConfig,
    load_commented_json,
    parse_game_config,
)
from pacman.infrastructure.highscore import HighscoreEntry
from pacman.maze.adapter import MazeGeneratorAdapter
from pacman.maze.grid import MazeGrid, Tile
from pacman.maze.level_generator import LevelGenerator


class RecordingMazeAdapter(MazeGeneratorAdapter):
    """Record maze generation requests and return an open maze."""

    def __init__(self) -> None:
        """Initialize the adapter call log."""
        super().__init__()
        self.calls: list[dict[str, object]] = []

    def generate(
        self,
        width: int,
        height: int,
        seed: int = 0,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] = (-1, -1),
        include_42: bool = True,
    ) -> MazeGrid:
        """Record generation arguments and return a matching open grid."""
        self.calls.append({
            "width": width,
            "height": height,
            "seed": seed,
            "entry": entry,
            "exit": exit,
            "include_42": include_42,
        })
        rows = tuple(
            tuple(Tile.CORRIDOR for _ in range(width))
            for _ in range(height)
        )
        return MazeGrid(
            tiles=rows,
            entry=(0, 0),
            exit=(width - 1, height - 1),
        )


def _write_config(tmp_path: Path, data: dict[str, object]) -> GameConfig:
    """Parse config through the same commented-JSON file boundary."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return parse_game_config(load_commented_json(config_file))


def test_parsed_lives_reach_initial_and_restarted_sessions(
    tmp_path: Path,
) -> None:
    """Verify configured lives are used for initial and restarted games."""
    config = _write_config(
        tmp_path,
        {
            "lives": 6,
            "level_max_time": 44,
            "levels": [{"width": 7, "height": 7}],
        },
    )
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=RecordingMazeAdapter(),
    )

    assert context.session.lives == 6

    first_session = context.start_new_game()
    first_session.lives = 1
    first_session.score = 900
    restarted_session = context.start_new_game()

    assert restarted_session is context.session
    assert restarted_session is not first_session
    assert restarted_session.lives == 6
    assert restarted_session.score == 0
    assert restarted_session.remaining_level_time == 44.0


def test_minimum_valid_lives_reach_new_session(tmp_path: Path) -> None:
    """Verify the minimum valid lives value reaches gameplay sessions."""
    config = _write_config(tmp_path, {"lives": 1})
    context = AppContext(config=config)

    assert context.session.lives == 1
    assert context.start_new_game().lives == 1


def test_parsed_scoring_values_affect_actual_score_awards(
    tmp_path: Path,
) -> None:
    """Verify changed score config affects collection and collision rules."""
    config = _write_config(
        tmp_path,
        {
            "points_per_pacgum": 12,
            "points_per_super_pacgum": 80,
            "points_per_ghost": 300,
            "frightened_duration": 4.5,
            "ghost_respawn_delay": 1.75,
        },
    )
    context = AppContext(config=config)
    field = PacgumField(pacgums={(1, 1)}, super_pacgums={(2, 2)})

    normal_score = collect_pacgum(
        (1.5, 1.5),
        field,
        points_per_pacgum=config.points_per_pacgum,
    )
    super_score = collect_pacgum(
        (2.5, 2.5),
        field,
        points_per_super_pacgum=config.points_per_super_pacgum,
    )

    context.session.score += normal_score + super_score
    assert context.session.score == 92

    level = context.level_generator.generate_level(0)
    assert level.spawns is not None
    ghost_gameplay = GhostGameplay.create(
        level.spawns.ghosts,
        config,
    )
    ghost = ghost_gameplay.ghosts[0]
    ghost_gameplay.activate_frightened()
    result = ghost_gameplay.resolve_collisions(context.session, (ghost,))

    assert result.score_gained == 300
    assert context.session.score == 392
    assert ghost.respawn_timer == 1.75
    assert ghost_gameplay.power_state.remaining_time == 4.5


def test_level_timer_initializes_and_resets_from_parsed_config(
    tmp_path: Path,
) -> None:
    """Verify configured level time is used for new games and transitions."""
    config = _write_config(
        tmp_path,
        {
            "level_max_time": 33,
            "levels": [
                {"width": 7, "height": 7},
                {"width": 9, "height": 9},
            ],
        },
    )
    adapter = RecordingMazeAdapter()
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=adapter,
    )
    controller = GameStateController(GameState.PLAYING)
    session = context.start_new_game()
    assert context.player is not None

    session.remaining_level_time = 4.0
    outcome, next_level = handle_level_completion(
        session,
        context.player,
        context.level_generator,
        controller,
    )

    assert outcome is LevelCompletionOutcome.ADVANCED
    assert next_level is not None
    assert session.remaining_level_time == 33.0
    assert next_level.time_limit == 33
    assert adapter.calls[1]["width"] == 9
    assert adapter.calls[1]["height"] == 9


def test_configured_levels_define_session_total_level_count(
    tmp_path: Path,
) -> None:
    """Verify session victory boundaries follow configured level entries."""
    config = _write_config(
        tmp_path,
        {
            "levels": [
                {"width": 7, "height": 7},
                {"width": 9, "height": 9},
                {"width": 11, "height": 11},
            ],
        },
    )
    context = AppContext(config=config)

    assert context.session.total_levels == 3
    assert context.start_new_game().total_levels == 3


def test_configured_pacgum_count_limits_generated_normal_pacgums(
    tmp_path: Path,
) -> None:
    """Verify configured pacgum count reaches level generation."""
    config = _write_config(
        tmp_path,
        {
            "pacgum": 3,
            "levels": [{"width": 7, "height": 7}],
        },
    )
    adapter = RecordingMazeAdapter()
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=adapter,
    )

    context.start_new_game()

    assert context.active_level is not None
    assert context.active_level.pellets is not None
    assert len(context.active_level.pellets.pacgums) == 3
    assert len(context.active_level.pellets.super_pacgums) == 4


def test_omitted_pacgum_config_fills_all_eligible_corridors(
    tmp_path: Path,
) -> None:
    """Verify omitted pacgum config preserves fill-all gameplay mode."""
    config = _write_config(
        tmp_path,
        {"levels": [{"width": 7, "height": 7}]},
    )
    adapter = RecordingMazeAdapter()
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=adapter,
    )

    context.start_new_game()

    assert context.active_level is not None
    assert context.active_level.spawns is not None
    assert context.active_level.pellets is not None
    spawn_positions = {
        context.active_level.spawns.player,
        *context.active_level.spawns.ghosts.as_tuple(),
    }
    eligible_corridors = {
        (x, y)
        for y in range(context.active_level.maze.height)
        for x in range(context.active_level.maze.width)
        if context.active_level.maze.is_corridor((x, y))
    } - spawn_positions
    placed_pacgums = (
        context.active_level.pellets.pacgums
        | context.active_level.pellets.super_pacgums
    )

    assert not config.pacgum_configured
    assert placed_pacgums == eligible_corridors


def test_second_context_uses_its_own_parsed_configuration(
    tmp_path: Path,
) -> None:
    """Verify separate parsed configs do not leak values across contexts."""
    first = AppContext(
        config=_write_config(
            tmp_path,
            {"lives": 2, "level_max_time": 20},
        )
    )
    second = AppContext(
        config=_write_config(
            tmp_path,
            {"lives": 8, "level_max_time": 70},
        )
    )

    assert first.session.lives == 2
    assert first.session.remaining_level_time == 20.0
    assert second.session.lives == 8
    assert second.session.remaining_level_time == 70.0


def test_changing_one_config_value_preserves_unrelated_defaults(
    tmp_path: Path,
) -> None:
    """Verify one live config change does not mutate unrelated settings."""
    config = _write_config(tmp_path, {"lives": 5})

    assert config.lives == 5
    assert config.points_per_pacgum == 10
    assert config.points_per_super_pacgum == 50
    assert config.points_per_ghost == 200
    assert config.level_max_time == 90
    assert config.levels == [LevelConfig()]


def test_parsed_maze_dimensions_reach_generation_requests(
    tmp_path: Path,
) -> None:
    """Verify configured level dimensions reach the maze adapter."""
    config = _write_config(
        tmp_path,
        {
            "levels": [
                {"width": 7, "height": 9},
                {"width": 11, "height": 13},
            ],
        },
    )
    adapter = RecordingMazeAdapter()
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=adapter,
    )

    first_level = context.level_generator.generate_level(0)
    second_level = context.level_generator.generate_level(1)

    assert first_level.maze.width == 7
    assert first_level.maze.height == 9
    assert second_level.maze.width == 11
    assert second_level.maze.height == 13
    assert adapter.calls[0]["width"] == 7
    assert adapter.calls[0]["height"] == 9
    assert adapter.calls[1]["width"] == 11
    assert adapter.calls[1]["height"] == 13


def test_parsed_seed_reaches_deterministic_first_level_generation(
    tmp_path: Path,
) -> None:
    """Verify configured seed controls repeatable first-level requests."""
    first_config = _write_config(
        tmp_path,
        {"seed": 1234, "levels": [{"width": 7, "height": 7}]},
    )
    second_config = _write_config(
        tmp_path,
        {"seed": 5678, "levels": [{"width": 7, "height": 7}]},
    )
    first_adapter = RecordingMazeAdapter()
    repeated_adapter = RecordingMazeAdapter()
    second_adapter = RecordingMazeAdapter()
    first_generator = context_generator(first_config, first_adapter)
    repeated_generator = context_generator(first_config, repeated_adapter)
    second_generator = context_generator(second_config, second_adapter)

    first_level = first_generator.generate_level(0)
    repeated_level = repeated_generator.generate_level(0)
    second_level = second_generator.generate_level(0)

    assert first_level.seed == repeated_level.seed == 1234
    assert second_level.seed == 5678
    assert first_adapter.calls[0]["seed"] == 1234
    assert repeated_adapter.calls[0]["seed"] == 1234
    assert second_adapter.calls[0]["seed"] == 5678
    assert first_adapter.calls[0]["include_42"] is True


def context_generator(
    config: GameConfig,
    adapter: RecordingMazeAdapter,
) -> LevelGenerator:
    """Create a configured level generator through AppContext."""
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=adapter,
    )
    return context.level_generator


def test_configured_highscore_filename_is_used_for_load_and_save(
    tmp_path: Path,
) -> None:
    """Verify highscore persistence uses the parsed configured path."""
    score_file = tmp_path / "custom-scores.json"
    score_file.write_text(
        json.dumps([{"name": "Maria", "score": 1200}]),
        encoding="utf-8",
    )
    config = _write_config(
        tmp_path,
        {"highscore_filename": str(score_file)},
    )
    context = AppContext(config=config)

    assert context.storage.path == score_file
    assert context.highscores == [
        HighscoreEntry(name="Maria", score=1200)
    ]

    context.session.score = 1500
    context.player_name_input.value = "Jayesh"

    assert context.save_completed_game_score()
    assert context.storage.load() == [
        HighscoreEntry(name="Jayesh", score=1500),
        HighscoreEntry(name="Maria", score=1200),
    ]


def test_separate_configured_highscore_files_do_not_leak_state(
    tmp_path: Path,
) -> None:
    """Verify distinct configured storage paths remain isolated."""
    first_file = tmp_path / "first-scores.json"
    second_file = tmp_path / "second-scores.json"
    first_context = AppContext(
        config=_write_config(
            tmp_path,
            {"highscore_filename": str(first_file)},
        )
    )
    second_context = AppContext(
        config=_write_config(
            tmp_path,
            {"highscore_filename": str(second_file)},
        )
    )

    first_context.session.score = 700
    first_context.player_name_input.value = "First"
    second_context.session.score = 900
    second_context.player_name_input.value = "Second"

    assert first_context.save_completed_game_score()
    assert second_context.save_completed_game_score()

    assert first_context.storage.load() == [
        HighscoreEntry(name="First", score=700)
    ]
    assert second_context.storage.load() == [
        HighscoreEntry(name="Second", score=900)
    ]
