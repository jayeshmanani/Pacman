"""Application context and domain boundary container."""

from dataclasses import dataclass, field

from pacman.config import GameConfig
from pacman.highscore import HighscoreEntry
from pacman.storage import HighscoreStorage


@dataclass
class GameSession:
    """Track active gameplay session state baseline."""

    score: int = 0
    lives: int = 3
    current_level: int = 0


@dataclass
class AppContext:
    """Central application context defining domain boundaries."""

    config: GameConfig = field(default_factory=GameConfig)
    state_controller: object | None = None
    storage: HighscoreStorage = field(default_factory=HighscoreStorage)
    session: GameSession = field(default_factory=GameSession)
    highscores: list[HighscoreEntry] = field(
        default_factory=list,
        init=False,
    )

    def __post_init__(self) -> None:
        """Apply configuration and load persisted application data."""
        if self.config.highscore_filename:
            self.storage = HighscoreStorage(self.config.highscore_filename)
        self.session.lives = self.config.lives
        self.highscores = self.storage.load()
