"""Infrastructure tests for highscore storage."""

import json
from pathlib import Path

import pytest

from pacman.infrastructure.highscore import HighscoreEntry
from pacman.infrastructure.storage import HighscoreStorage


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


def test_update_adds_sorts_and_persists_highscores(tmp_path: Path) -> None:
    """Verify that update stores all entries from highest to lowest score."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(
        json.dumps(
            [
                {"name": "Second", "score": 200},
                {"name": "Third", "score": 100},
            ]
        ),
        encoding="utf-8",
    )
    storage = HighscoreStorage(str(score_file))

    updated_entries = storage.update(
        HighscoreEntry(name="First", score=300)
    )

    expected_entries = [
        HighscoreEntry(name="First", score=300),
        HighscoreEntry(name="Second", score=200),
        HighscoreEntry(name="Third", score=100),
    ]
    assert updated_entries == expected_entries
    assert storage.load() == expected_entries


def test_update_creates_storage_for_first_entry(tmp_path: Path) -> None:
    """Verify that the first highscore creates the storage file."""
    score_file = tmp_path / "nested" / "scores.json"
    storage = HighscoreStorage(str(score_file))
    entry = HighscoreEntry(name="Maria", score=500)

    assert storage.update(entry) == [entry]
    assert storage.load() == [entry]


def test_update_keeps_only_ten_best_highscores(tmp_path: Path) -> None:
    """Verify that only the ten highest scores remain persisted."""
    storage = HighscoreStorage(str(tmp_path / "scores.json"))

    for score in range(12):
        storage.update(HighscoreEntry(name=f"P{score}", score=score))

    entries = storage.load()

    assert len(entries) == 10
    assert [entry.score for entry in entries] == list(range(11, 1, -1))


def test_update_with_invalid_entry_preserves_stored_data(
    tmp_path: Path,
) -> None:
    """Verify that an invalid new entry cannot overwrite stored highscores."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(
        '[{"name": "Maria", "score": 500}]',
        encoding="utf-8",
    )
    original_contents = score_file.read_text(encoding="utf-8")
    storage = HighscoreStorage(str(score_file))
    invalid_entry: object = {"name": "Invalid!", "score": -1}

    result = storage.update(invalid_entry)  # type: ignore[arg-type]

    assert result == [HighscoreEntry(name="Maria", score=500)]
    assert score_file.read_text(encoding="utf-8") == original_contents


def test_update_replaces_corrupted_file_with_valid_data(
    tmp_path: Path,
) -> None:
    """Verify that a valid entry can safely recover corrupted storage."""
    score_file = tmp_path / "scores.json"
    score_file.write_text("{broken json", encoding="utf-8")
    storage = HighscoreStorage(str(score_file))
    entry = HighscoreEntry(name="Maria", score=500)

    assert storage.update(entry) == [entry]
    assert storage.load() == [entry]


def test_update_preserves_file_when_atomic_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that a failed write cannot corrupt the existing file."""
    score_file = tmp_path / "scores.json"
    score_file.write_text(
        '[{"name": "Maria", "score": 500}]',
        encoding="utf-8",
    )
    original_contents = score_file.read_text(encoding="utf-8")
    storage = HighscoreStorage(str(score_file))

    def fail_replace(source: Path, target: Path) -> Path:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(Path, "replace", fail_replace)

    result = storage.update(HighscoreEntry(name="Player", score=900))

    assert result == [HighscoreEntry(name="Maria", score=500)]
    assert score_file.read_text(encoding="utf-8") == original_contents
    assert not (tmp_path / ".scores.json.tmp").exists()
