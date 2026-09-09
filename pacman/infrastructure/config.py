"""Configuration structures and parser for Pacman game settings."""


from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import sys
from typing import Any, cast


def load_commented_json(filepath: Path) -> dict[str, Any]:
    """Read a JSON file while ignoring comment lines (# or //)."""
    clean_lines = []
    with filepath.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not (stripped.startswith("#") or stripped.startswith("//")):
                clean_lines.append(line)
    content = "".join(clean_lines)
    if not content.strip():
        return {}
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("JSON root must be an object (dict)")
    return cast(dict[str, Any], parsed)


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
    pacgum_configured: bool = False
    seed: int = 42
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    frightened_duration: float = 7.0
    ghost_respawn_delay: float = 5.0
    level_max_time: int = 90
    levels: list[LevelConfig] = field(default_factory=lambda: [LevelConfig()])


def parse_game_config(data: dict[str, Any]) -> GameConfig:
    """Parse raw JSON dict into a GameConfig, clamping/falling back safely."""
    raw_levels = data.get("levels")
    levels = []
    if raw_levels is not None:
        if not isinstance(raw_levels, list) or len(raw_levels) == 0:
            print(
                "Warning: Invalid 'levels' list in config. "
                "Using default level.",
                file=sys.stderr,
            )
        else:
            for idx, lvl in enumerate(raw_levels):
                if not isinstance(lvl, dict):
                    print(
                        f"Warning: Level {idx + 1} config is not an object. "
                        "Using default 21x21.",
                        file=sys.stderr,
                    )
                    levels.append(LevelConfig())
                    continue
                w_raw = lvl.get("width", 21)
                try:
                    w = int(w_raw)
                    if w < 5:
                        print(
                            f"Warning: Level {idx + 1} width {w} is below "
                            "minimum 5. Clamped to 5.",
                            file=sys.stderr,
                        )
                        w = 5
                except (ValueError, TypeError):
                    print(
                        f"Warning: Invalid width '{w_raw}' in "
                        f"level {idx + 1}. Using default 21.",
                        file=sys.stderr,
                    )
                    w = 21

                h_raw = lvl.get("height", 21)
                try:
                    h = int(h_raw)
                    if h < 5:
                        print(
                            f"Warning: Level {idx + 1} height {h} is below "
                            "minimum 5. Clamped to 5.",
                            file=sys.stderr,
                        )
                        h = 5
                except (ValueError, TypeError):
                    print(
                        f"Warning: Invalid height '{h_raw}' in "
                        f"level {idx + 1}. Using default 21.",
                        file=sys.stderr,
                    )
                    h = 21
                levels.append(LevelConfig(width=w, height=h))

    if not levels:
        levels = [LevelConfig()]

    def _safe_int(key: str, default: int, min_val: int | None = None) -> int:
        if key not in data:
            return default
        raw_val = data[key]
        try:
            val = int(raw_val)
        except (ValueError, TypeError):
            print(
                f"Warning: Invalid value '{raw_val}' for key '{key}'. "
                f"Using default {default}.",
                file=sys.stderr,
            )
            return default

        if min_val is not None and val < min_val:
            print(
                f"Warning: Value {val} for key '{key}' is below minimum "
                f"{min_val}. Clamped to {min_val}.",
                file=sys.stderr,
            )
            return min_val
        return val

    def _safe_float(
        key: str,
        default: float,
        min_val: float | None = None,
    ) -> float:
        if key not in data:
            return default
        raw_val = data[key]
        try:
            val = float(raw_val)
            if not math.isfinite(val):
                print(
                    f"Warning: Non-finite value '{raw_val}' for key '{key}'. "
                    f"Using default {default}.",
                    file=sys.stderr,
                )
                return default
        except (ValueError, TypeError):
            print(
                f"Warning: Invalid value '{raw_val}' for key '{key}'. "
                f"Using default {default}.",
                file=sys.stderr,
            )
            return default

        if min_val is not None and val < min_val:
            print(
                f"Warning: Value {val} for key '{key}' is below minimum "
                f"{min_val}. Clamped to {min_val}.",
                file=sys.stderr,
            )
            return min_val
        return val

    raw_filename = data.get("highscore_filename", "highscores.json")
    if not isinstance(raw_filename, str) or not raw_filename.strip():
        print(
            "Warning: Invalid 'highscore_filename'. Using 'highscores.json'.",
            file=sys.stderr,
        )
        filename = "highscores.json"
    else:
        filename = raw_filename.strip()

    return GameConfig(
        highscore_filename=filename,
        pacgum=_safe_int("pacgum", 42, min_val=1),
        pacgum_configured="pacgum" in data,
        seed=_safe_int("seed", 42),
        lives=_safe_int("lives", 3, min_val=1),
        points_per_pacgum=_safe_int("points_per_pacgum", 10, min_val=0),
        points_per_super_pacgum=_safe_int(
            "points_per_super_pacgum", 50, min_val=0
        ),
        points_per_ghost=_safe_int("points_per_ghost", 200, min_val=0),
        frightened_duration=_safe_float(
            "frightened_duration", 7.0, min_val=0.0
        ),
        ghost_respawn_delay=_safe_float(
            "ghost_respawn_delay", 5.0, min_val=0.0
        ),
        level_max_time=_safe_int("level_max_time", 90, min_val=1),
        levels=levels,
    )
