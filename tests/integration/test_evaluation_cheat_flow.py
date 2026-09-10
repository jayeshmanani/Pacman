"""Final evaluation journeys for difficult gameplay states."""

import json
from pathlib import Path

from pacman.app import run_app
from pacman.infrastructure.config import GameConfig, LevelConfig
from tests.support.app_fakes import (
    _FakeEvent,
    _FakePygame,
    type_text_events,
)


def test_level_skip_reaches_final_level_victory_and_saves_score(
    tmp_path: Path,
) -> None:
    """Verify the evaluation cheat can demonstrate multi-level victory."""
    score_file = tmp_path / "scores.json"
    config = GameConfig(
        levels=[
            LevelConfig(width=21, height=21),
            LevelConfig(width=21, height=21),
        ],
        highscore_filename=str(score_file),
    )
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_F1)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_2)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_2)],
        *type_text_events("CHEAT"),
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    run_app(pygame_module=pygame, config=config)

    assert "CHEAT MODE: ON (F1 to disable)" in pygame.surface.rendered_texts
    assert "LEVEL: 2" in pygame.surface.rendered_texts
    assert "VICTORY!" in pygame.surface.rendered_texts
    assert "CHEAT" in pygame.surface.rendered_texts
    assert json.loads(score_file.read_text(encoding="utf-8")) == [
        {"name": "CHEAT", "score": 0},
    ]


def test_timeout_reaches_game_over_and_saves_score(tmp_path: Path) -> None:
    """Verify a real level timeout completes the loss and score flow."""
    score_file = tmp_path / "scores.json"
    pygame = _FakePygame([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        *type_text_events("TIMER"),
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])
    pygame.clock.elapsed_ms = 1000

    run_app(
        pygame_module=pygame,
        config=GameConfig(
            highscore_filename=str(score_file),
            level_max_time=1,
        ),
    )

    assert "TIME: 1s" in pygame.surface.rendered_texts
    assert "GAME OVER" in pygame.surface.rendered_texts
    assert "TIMER" in pygame.surface.rendered_texts
    assert json.loads(score_file.read_text(encoding="utf-8")) == [
        {"name": "TIMER", "score": 0},
    ]
