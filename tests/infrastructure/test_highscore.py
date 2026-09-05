"""Infrastructure tests for the highscore entry model."""

import pytest

from pacman.infrastructure.highscore import HighscoreEntry


def test_highscore_entry_accepts_valid_values() -> None:
    """Verify that a valid player name and score are stored."""
    entry = HighscoreEntry(name="Player 1", score=1200)

    assert entry.name == "Player 1"
    assert entry.score == 1200


def test_highscore_entry_accepts_boundary_values() -> None:
    """Verify that a ten-character name and zero score are accepted."""
    entry = HighscoreEntry(name="Pac Man 01", score=0)

    assert entry.name == "Pac Man 01"
    assert entry.score == 0


def test_highscore_entry_rejects_name_longer_than_ten_characters() -> None:
    """Verify that names longer than ten characters are rejected."""
    with pytest.raises(ValueError, match="no longer than 10"):
        HighscoreEntry(name="Player 1234", score=100)


@pytest.mark.parametrize("name", ["", "   "])
def test_highscore_entry_rejects_empty_name(name: str) -> None:
    """Verify empty and whitespace-only names are rejected."""
    with pytest.raises(ValueError, match="must not be empty"):
        HighscoreEntry(name=name, score=100)


@pytest.mark.parametrize("name", ["Player!", "Pac_Man", "Name-"])
def test_highscore_entry_rejects_invalid_name_characters(name: str) -> None:
    """Verify that punctuation and symbols are rejected in names."""
    with pytest.raises(ValueError, match="only letters, numbers, and spaces"):
        HighscoreEntry(name=name, score=100)


def test_highscore_entry_rejects_non_string_name() -> None:
    """Verify that a non-string name is rejected."""
    with pytest.raises(TypeError, match="name must be a string"):
        HighscoreEntry(name=123, score=100)  # type: ignore[arg-type]


def test_highscore_entry_rejects_negative_score() -> None:
    """Verify that a negative score is rejected."""
    with pytest.raises(ValueError, match="non-negative"):
        HighscoreEntry(name="Player", score=-1)


@pytest.mark.parametrize("score", [10.5, "100", True])
def test_highscore_entry_rejects_non_integer_score(score: object) -> None:
    """Verify that only genuine integers are accepted as scores."""
    with pytest.raises(TypeError, match="score must be an integer"):
        HighscoreEntry(name="Player", score=score)  # type: ignore[arg-type]
