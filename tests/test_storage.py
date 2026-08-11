"""Tests for baseline storage abstraction."""

from pathlib import Path
from pacman.storage import HighscoreStorage


def test_highscore_storage_path_initialization() -> None:
    """Verify storage initializes with the target filename."""
    storage = HighscoreStorage("scores.json")
    assert storage.path == Path("scores.json")
