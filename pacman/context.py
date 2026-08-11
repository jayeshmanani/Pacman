"""Application context and domain boundary container."""

from dataclasses import dataclass, field
from pacman.config import GameConfig
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

    def __post_init__(self) -> None:
        """Initialize storage boundary with configured highscore filename."""
        if self.config.highscore_filename:
            self.storage = HighscoreStorage(self.config.highscore_filename)
