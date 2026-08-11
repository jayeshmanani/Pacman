"""Tests for highscore persistent storage."""

import json
from pathlib import Path

import pytest

from pacman.highscore import HighscoreEntry
from pacman.storage import HighscoreStorage


def test_highscore_storage_path_initialization() -> None:
    """Verify storage initializes with the target filename."""
    storage = HighscoreStorage("scores.json")
    assert storage.path == Path("scores.json")


def test_load_returns_saved_highscores(tmp_path: Path) -> None:
    """Verify that valid saved highscores are loaded in file order."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(
        json.dumps(
            [
                {"name": "Maria", "score": 1200},
                {"name": "Player 2", "score": 800},
            ]
        ),
        encoding="utf-8",
    )

    entries = HighscoreStorage(str(score_file)).load()

    assert entries == [
        HighscoreEntry(name="Maria", score=1200),
        HighscoreEntry(name="Player 2", score=800),
    ]


def test_load_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    """Verify that a missing highscore file is handled safely."""
    storage = HighscoreStorage(str(tmp_path / "missing.json"))

    assert storage.load() == []


@pytest.mark.parametrize("file_contents", ["", "{broken json"])
def test_load_returns_empty_list_for_unreadable_content(
    tmp_path: Path,
    file_contents: str,
) -> None:
    """Verify that empty or corrupted JSON is handled safely."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(file_contents, encoding="utf-8")

    assert HighscoreStorage(str(score_file)).load() == []


def test_load_returns_empty_list_for_invalid_utf8(tmp_path: Path) -> None:
    """Verify that a file with invalid UTF-8 is handled safely."""
    score_file = tmp_path / "scores.json"
    score_file.write_bytes(b"\xff")

    assert HighscoreStorage(str(score_file)).load() == []


@pytest.mark.parametrize(
    "saved_data",
    [
        {"name": "Maria", "score": 100},
        ["not an entry"],
        [{"name": "Maria"}],
        [{"name": "Maria", "score": 100, "extra": True}],
        [{"name": "Player!", "score": 100}],
        [{"name": "Maria", "score": -1}],
        [{"name": "Maria", "score": 10.5}],
        [{"name": "Maria", "score": True}],
    ],
)
def test_load_returns_empty_list_for_invalid_saved_data(
    tmp_path: Path,
    saved_data: object,
) -> None:
    """Verify that an invalid JSON structure is handled safely."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(json.dumps(saved_data), encoding="utf-8")

    assert HighscoreStorage(str(score_file)).load() == []


def test_load_discards_entire_file_when_one_entry_is_invalid(
    tmp_path: Path,
) -> None:
    """Verify that mixed valid and invalid entries fall back safely."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(
        json.dumps(
            [
                {"name": "Maria", "score": 1200},
                {"name": "Invalid!", "score": 800},
            ]
        ),
        encoding="utf-8",
    )

    assert HighscoreStorage(str(score_file)).load() == []
