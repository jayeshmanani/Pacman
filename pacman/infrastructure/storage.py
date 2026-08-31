"""Storage abstraction boundary for persistent data."""


import json
from pathlib import Path

from pacman.infrastructure.highscore import HighscoreEntry

_MAX_HIGHSCORES = 10


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

    def update(self, entry: HighscoreEntry) -> list[HighscoreEntry]:
        """Add, rank, limit, and persist a valid highscore entry."""
        current_entries = self.load()
        if not isinstance(entry, HighscoreEntry):
            return current_entries

        updated_entries = sorted(
            [*current_entries, entry],
            key=lambda saved_entry: saved_entry.score,
            reverse=True,
        )[:_MAX_HIGHSCORES]

        if not self._save(updated_entries):
            return current_entries
        return updated_entries

    def _save(self, entries: list[HighscoreEntry]) -> bool:
        """Atomically save entries and report whether it succeeded."""
        data = [
            {"name": entry.name, "score": entry.score}
            for entry in entries
        ]
        temporary_path = self._path.with_name(f".{self._path.name}.tmp")

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self._path)
        except OSError:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False

        return True
