"""Storage abstraction boundary for persistent data."""

from pathlib import Path


class HighscoreStorage:
    """Baseline storage interface for highscores."""

    def __init__(self, filename: str = "highscores.json") -> None:
        """Initialize storage with target filename."""
        self._path = Path(filename)

    @property
    def path(self) -> Path:
        """Return target file path."""
        return self._path
