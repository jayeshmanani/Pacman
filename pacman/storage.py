"""Storage abstraction boundary for persistent data."""

import json
from pathlib import Path

from pacman.highscore import HighscoreEntry


class HighscoreStorage:
    """Baseline storage interface for highscores."""

    def __init__(self, filename: str = "highscores.json") -> None:
        """Initialize storage with target filename."""
        self._path = Path(filename)

    @property
    def path(self) -> Path:
        """Return target file path."""
        return self._path

    def load(self) -> list[HighscoreEntry]:
        """Load valid highscore entries or return an empty list safely."""
        try:
            data: object = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return []

        if not isinstance(data, list):
            return []

        entries: list[HighscoreEntry] = []
        for item in data:
            if not isinstance(item, dict):
                return []
            if set(item) != {"name", "score"}:
                return []

            name = item["name"]
            score = item["score"]
            if not isinstance(name, str):
                return []
            if not isinstance(score, int) or isinstance(score, bool):
                return []

            try:
                entries.append(HighscoreEntry(name=name, score=score))
            except (TypeError, ValueError):
                return []

        return entries
