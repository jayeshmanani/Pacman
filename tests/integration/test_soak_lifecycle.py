"""Multi-cycle session stress and highscore I/O endurance tests for PK-92."""

import gc
import json
from pathlib import Path
import random

from pacman.application.context import AppContext
from pacman.application.state import GameState, GameStateController
from pacman.gameplay.player import Direction
from pacman.infrastructure.config import GameConfig, LevelConfig
from pacman.infrastructure.highscore import HighscoreEntry
from tests.support.gameplay_fakes import FixedMazeAdapter
from tests.support.soak_harness import SoakSimulationHarness


def test_50_consecutive_game_cycles_zero_leakage(tmp_path: Path) -> None:
    """Verify 50 game cycles completely reset cheats, entities, and inputs."""
    score_file = tmp_path / "scores_soak.json"
    config = GameConfig(
        highscore_filename=str(score_file),
        levels=[LevelConfig(width=7, height=7)],
        seed=42,
    )
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=FixedMazeAdapter(),
    )
    controller = GameStateController(GameState.MAIN_MENU)

    for cycle in range(50):
        # 1. Start from Main Menu
        assert controller.state is GameState.MAIN_MENU
        assert context.player is None
        assert context.active_level is None
        assert not context.cheat_mode.enabled
        assert not context.cheat_mode.invincibility_enabled
        assert not context.cheat_mode.ghost_freeze_enabled

        # 2. Enable cheats before starting
        context.cheat_mode.enabled = True
        context.cheat_mode.invincibility_enabled = True
        context.cheat_mode.ghost_freeze_enabled = True

        # 3. Start Game
        controller.start_game(context.session)
        context.start_new_game()
        assert context.active_level is not None
        assert context.player is not None
        assert context.session.lives == config.lives
        assert context.session.score == 0

        # 4. Simulate active gameplay frames
        harness = SoakSimulationHarness(
            context=context,
            controller=controller,
        )
        for turn_dir in (Direction.UP, Direction.RIGHT, Direction.DOWN):
            harness.tick(dt=1.0 / 60.0, player_turn=turn_dir)

        context.session.score = (cycle + 1) * 150

        # 5. End Game -> Name Entry
        controller.trigger_game_over()
        player_name = f"PLYR {cycle % 10}"
        context.player_name_input.value = player_name
        saved = context.save_completed_game_score()
        assert saved

        # 6. Return to Main Menu
        context.reset_session()
        controller.return_to_main_menu(context.session)

        # 7. Assert complete zero-leakage reset
        assert not context.cheat_mode.enabled
        assert not context.cheat_mode.invincibility_enabled
        assert not context.cheat_mode.ghost_freeze_enabled
        assert context.player_name_input.value == ""
        assert context.active_level is None
        assert context.player is None
        assert context.session.score == 0
        assert context.session.lives == config.lives


def test_highscore_io_endurance_under_100_submissions(
    tmp_path: Path,
) -> None:
    """Verify 100 consecutive writes maintain valid, ordered, top-10 JSON."""
    score_file = tmp_path / "stress_highscores.json"
    config = GameConfig(highscore_filename=str(score_file))
    context = AppContext(config=config)

    rng = random.Random(999)
    highest_score_seen = 0

    valid_names = [
        "A",
        "PACMAN",
        "ACE 1",
        "CHAMP 99",
        "MAX SCORE",
        "TEN CHARS!",  # Has exclamation, should fail validation
        "VALIDNAME",
        "SPACES OK",
    ]

    successful_saves = 0

    for i in range(100):
        name = valid_names[i % len(valid_names)]
        score = rng.randint(10, 5000)

        context.session.score = score
        context.player_name_input.value = name
        saved = context.save_completed_game_score()

        # "TEN CHARS!" contains exclamation mark, should be rejected cleanly
        if "!" in name:
            assert not saved
            continue

        assert saved
        successful_saves += 1
        if score > highest_score_seen:
            highest_score_seen = score

        # Verify persistent JSON file on disk after every write
        raw_data = json.loads(score_file.read_text(encoding="utf-8"))
        assert isinstance(raw_data, list)
        assert len(raw_data) <= 10

        # Verify strict descending order
        scores = [entry["score"] for entry in raw_data]
        assert scores == sorted(scores, reverse=True)
        assert all(s >= 0 for s in scores)
        assert raw_data[0]["score"] == highest_score_seen

    assert successful_saves > 80
    assert len(context.highscores) == 10
    assert context.highscores[0].score == highest_score_seen


def test_session_lifecycle_with_rapid_interrupted_play(
    tmp_path: Path,
) -> None:
    """Verify rapid start-and-abort cycles do not corrupt state or storage."""
    score_file = tmp_path / "abort_scores.json"
    score_file.write_text(
        json.dumps([{"name": "BASE", "score": 100}]),
        encoding="utf-8",
    )
    config = GameConfig(
        highscore_filename=str(score_file),
        levels=[LevelConfig(width=7, height=7)],
        seed=42,
    )
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=FixedMazeAdapter(),
    )
    harness = SoakSimulationHarness(context=context)

    for _ in range(30):
        context.start_new_game()
        # Advance 3 ticks
        harness.step_n(frames=3, dt=1.0 / 60.0)

        # Mutate partial state
        context.session.score = 9999
        context.session.lose_life()
        context.player_name_input.value = "ABORT"

        # Abort immediately without saving
        context.reset_session()

        assert context.session.score == 0
        assert context.session.lives == config.lives
        assert context.player is None
        assert context.active_level is None

    # Verify highscore file on disk was never touched by aborted runs
    persisted = context.storage.load()
    assert persisted == [HighscoreEntry(name="BASE", score=100)]


def test_object_reference_cleanup_after_50_cycles(
    tmp_path: Path,
) -> None:
    """Verify entities are garbage-collected without accumulating leaks."""
    config = GameConfig(
        highscore_filename=str(tmp_path / "gc_scores.json"),
        levels=[LevelConfig(width=7, height=7)],
        seed=42,
    )
    context = AppContext(config=config)
    context.level_generator = context.level_generator.__class__(
        config=config,
        adapter=FixedMazeAdapter(),
    )

    gc.collect()
    initial_objects = len(gc.get_objects())

    for _ in range(50):
        context.start_new_game()
        harness = SoakSimulationHarness(context=context)
        harness.step_n(frames=10, dt=1.0 / 60.0)
        context.reset_session()

    gc.collect()
    final_objects = len(gc.get_objects())

    # Object count should not balloon (allow small interpreter variance <= 100)
    delta = final_objects - initial_objects
    assert delta < 100
