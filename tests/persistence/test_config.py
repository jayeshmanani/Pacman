"""Persistence tests for configuration structures and JSON parsing."""

from pathlib import Path
import pytest
from pacman.config import LevelConfig, parse_game_config
from pac_man import load_commented_json


def test_parse_game_config_defaults() -> None:
    """Verify that an empty dict returns default GameConfig values."""
    config = parse_game_config({})

    assert config.highscore_filename == "highscores.json"
    assert config.pacgum == 42
    assert config.seed == 42
    assert config.lives == 3
    assert config.points_per_pacgum == 10
    assert config.points_per_super_pacgum == 50
    assert config.points_per_ghost == 200
    assert config.level_max_time == 90
    assert len(config.levels) == 1
    assert config.levels[0] == LevelConfig(width=21, height=21)


def test_parse_game_config_valid_custom_values() -> None:
    """Verify that valid custom values are parsed accurately."""
    data = {
        "highscore_filename": "scores.json",
        "pacgum": 100,
        "seed": 123,
        "lives": 5,
        "points_per_pacgum": 20,
        "points_per_super_pacgum": 100,
        "points_per_ghost": 500,
        "level_max_time": 120,
        "levels": [
            {"width": 25, "height": 25},
            {"width": 31, "height": 31},
        ],
    }

    config = parse_game_config(data)

    assert config.highscore_filename == "scores.json"
    assert config.pacgum == 100
    assert config.seed == 123
    assert config.lives == 5
    assert config.points_per_pacgum == 20
    assert config.points_per_super_pacgum == 100
    assert config.points_per_ghost == 500
    assert config.level_max_time == 120
    assert len(config.levels) == 2
    assert config.levels[0] == LevelConfig(width=25, height=25)
    assert config.levels[1] == LevelConfig(width=31, height=31)


def test_parse_game_config_clamps_invalid_and_negative_values() -> None:
    """Verify that invalid or negative numbers are clamped or defaulted."""
    data = {
        "pacgum": -10,
        "lives": 0,
        "points_per_pacgum": -5,
        "level_max_time": "invalid",
        "levels": [{"width": 2, "height": "invalid"}],
    }

    config = parse_game_config(data)

    assert config.pacgum == 1
    assert config.lives == 1
    assert config.points_per_pacgum == 0
    assert config.level_max_time == 90
    assert config.levels[0].width == 5
    assert config.levels[0].height == 21


def test_load_commented_json_strips_comments(tmp_path: Path) -> None:
    """Verify that load_commented_json ignores # and // lines."""
    config_file = tmp_path / "test_config.json"
    config_file.write_text(
        "# This is a comment line\n"
        "// Another comment line\n"
        "{\n"
        '    "pacgum": 50,\n'
        '    "lives": 4\n'
        "}\n",
        encoding="utf-8",
    )

    data = load_commented_json(config_file)

    assert data == {"pacgum": 50, "lives": 4}


def test_load_commented_json_empty_file(tmp_path: Path) -> None:
    """Verify that loading an empty or all-comment file returns empty dict."""
    config_file = tmp_path / "empty.json"
    config_file.write_text("# Only comments\n\n", encoding="utf-8")

    data = load_commented_json(config_file)

    assert data == {}


def test_load_commented_json_non_dict_root_raises(tmp_path: Path) -> None:
    """Verify that a JSON array at root raises a ValueError."""
    config_file = tmp_path / "array.json"
    config_file.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON root must be an object"):
        load_commented_json(config_file)
