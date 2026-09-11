"""Application context and domain boundary container."""


from dataclasses import dataclass, field
import math
from typing import TYPE_CHECKING

from pacman.infrastructure.config import GameConfig
from pacman.infrastructure.highscore import HighscoreEntry
from pacman.maze.level_generator import LevelData, LevelGenerator
from pacman.infrastructure.storage import HighscoreStorage
from pacman.application.player_name_input import PlayerNameInput
from pacman.application.cheat_mode import CheatMode
from pacman.gameplay.player import Player

if TYPE_CHECKING:
    from pacman.gameplay.ghost_gameplay import GhostGameplay


LIVE_PLAYER_SPEED = 7.0


@dataclass
class GameSession:
    """Track active gameplay session state baseline."""

    score: int = 0
    lives: int = 3
    current_level: int = 0
    remaining_level_time: float = 0.0
    level_timed_out: bool = False
    is_paused: bool = False
    is_victory: bool = False
    total_levels: int = 10

    @property
    def is_game_over(self) -> bool:
        """Return whether the player has no lives remaining."""
        return self.lives == 0 or self.level_timed_out

    @property
    def is_final_level(self) -> bool:
        """Return whether the current level is the final level."""
        return self.current_level >= (self.total_levels - 1)

    def trigger_victory(self) -> None:
        """Mark the active session as victorious."""
        self.is_victory = True

    def advance_level(self) -> int:
        """Advance to the next level while preserving score and lives."""
        self.current_level += 1
        self.level_timed_out = False
        self.is_paused = False
        return self.current_level

    def lose_life(self) -> int:
        """Remove one life without allowing the count to become negative."""
        self.lives = max(0, self.lives - 1)
        return self.lives

    def add_life(self) -> int:
        """Add one life and return the updated count."""
        self.lives += 1
        return self.lives

    def pause_gameplay(self) -> None:
        """Pause active gameplay updates."""
        self.is_paused = True

    def resume_gameplay(self) -> None:
        """Resume active gameplay updates."""
        self.is_paused = False

    def toggle_pause(self) -> bool:
        """Toggle paused gameplay and return the new paused state."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def start_level_timer(self, time_limit: float) -> None:
        """Initialize the timer for the active level."""
        if (
            type(time_limit) not in (int, float)
            or not math.isfinite(time_limit)
            or time_limit < 0
        ):
            raise ValueError(
                "level time limit must be a finite non-negative number"
            )
        self.remaining_level_time = float(time_limit)
        self.level_timed_out = False
        self.is_paused = False

    def update_level_timer(self, dt: float) -> bool:
        """Decrease the level timer and return True on first timeout."""
        if (
            self.level_timed_out
            or type(dt) not in (int, float)
            or not math.isfinite(dt)
            or dt <= 0
        ):
            return False

        if self.remaining_level_time <= dt:
            self.remaining_level_time = 0.0
            self.level_timed_out = True
            return True

        self.remaining_level_time -= dt
        if self.remaining_level_time <= 1e-9:
            self.remaining_level_time = 0.0
            self.level_timed_out = True
            return True
        return False


@dataclass
class AppContext:
    """Central application context defining domain boundaries."""

    config: GameConfig = field(default_factory=GameConfig)
    state_controller: object | None = None
    storage: HighscoreStorage = field(default_factory=HighscoreStorage)
    session: GameSession = field(default_factory=GameSession)
    player_name_input: PlayerNameInput = field(default_factory=PlayerNameInput)
    cheat_mode: CheatMode = field(default_factory=CheatMode)
    active_level: LevelData | None = field(default=None, init=False)
    player: Player | None = field(default=None, init=False)
    ghost_gameplay: "GhostGameplay | None" = field(default=None, init=False)
    level_generator: LevelGenerator = field(init=False)
    highscores: list[HighscoreEntry] = field(
        default_factory=list,
        init=False,
    )

    def __post_init__(self) -> None:
        """Apply configuration and load persisted application data."""
        if self.config.highscore_filename:
            self.storage = HighscoreStorage(self.config.highscore_filename)
        self.level_generator = LevelGenerator(config=self.config)
        self._configure_session(self.session)
        self.highscores = self.storage.load()

    def _configure_session(self, session: GameSession) -> GameSession:
        """Apply configured gameplay defaults to a session."""
        session.lives = self.config.lives
        session.total_levels = len(self.config.levels)
        session.start_level_timer(self.config.level_max_time)
        return session

    def start_new_game(self) -> GameSession:
        """Create a fresh configured gameplay session."""
        self.player_name_input.reset()
        session = self.reset_session()
        self.activate_level(self.level_generator.generate_level(0))
        return session

    def activate_level(
        self,
        level: LevelData,
        respawn_player: bool = True,
    ) -> None:
        """Install one generated level and its visible gameplay entities."""
        from pacman.gameplay.ghost_gameplay import GhostGameplay

        self.active_level = level
        if level.spawns is None:
            self.player = None
            self.ghost_gameplay = None
            return

        if self.player is None:
            self.player = Player.from_spawn(
                level.spawns.player,
                speed=LIVE_PLAYER_SPEED,
            )
        elif respawn_player:
            self.player.respawn(level.spawns.player, level.world)
        self.ghost_gameplay = GhostGameplay.create(
            level.spawns.ghosts,
            self.config,
        )

    def reset_session(self) -> GameSession:
        """Reset session defaults, preventing stale gameplay state."""
        self.session = self._configure_session(GameSession())
        self.cheat_mode.reset()
        self.active_level = None
        self.player = None
        self.ghost_gameplay = None
        return self.session

    def save_completed_game_score(self) -> bool:
        """Validate and persist the completed session score."""
        entry = self.player_name_input.create_entry(self.session.score)
        if entry is None:
            return False

        self.highscores = self.storage.update(entry)
        self.player_name_input.reset()
        return True
