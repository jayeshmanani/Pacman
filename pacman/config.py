"""Configuration structures and parser for Pacman game settings."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LevelConfig:
    """Configuration for an individual maze level."""

    width: int = 21
    height: int = 21


@dataclass(frozen=True)
class GameConfig:
    """Global game configuration options."""

    highscore_filename: str = "highscores.json"
    pacgum: int = 42
    seed: int = 42
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    level_max_time: int = 90
    levels: list[LevelConfig] = field(default_factory=lambda: [LevelConfig()])


def parse_game_config(data: dict[str, Any]) -> GameConfig:
    """Parse raw JSON dict into a GameConfig, clamping/falling back safely."""
    raw_levels = data.get("levels", [])
    levels = []
    if isinstance(raw_levels, list) and len(raw_levels) > 0:
        for lvl in raw_levels:
            if isinstance(lvl, dict):
                try:
                    w = max(5, int(lvl.get("width", 21)))
                except (ValueError, TypeError):
                    w = 21
                try:
                    h = max(5, int(lvl.get("height", 21)))
                except (ValueError, TypeError):
                    h = 21
                levels.append(LevelConfig(width=w, height=h))
    if not levels:
        levels = [LevelConfig()]

    def _safe_int(key: str, default: int, min_val: int | None = None) -> int:
        try:
            val = int(data.get(key, default))
            return max(min_val, val) if min_val is not None else val
        except (ValueError, TypeError):
            return default

    filename = str(data.get("highscore_filename", "highscores.json"))
    return GameConfig(
        highscore_filename=filename,
        pacgum=_safe_int("pacgum", 42, min_val=1),
        seed=_safe_int("seed", 42),
        lives=_safe_int("lives", 3, min_val=1),
        points_per_pacgum=_safe_int("points_per_pacgum", 10, min_val=0),
        points_per_super_pacgum=_safe_int(
            "points_per_super_pacgum", 50, min_val=0
        ),
        points_per_ghost=_safe_int("points_per_ghost", 200, min_val=0),
        level_max_time=_safe_int("level_max_time", 90, min_val=1),
        levels=levels,
    )
