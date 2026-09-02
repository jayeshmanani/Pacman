"""Deterministic and random level generation services."""


from dataclasses import dataclass, field
import random
from typing import Protocol

from pacman.infrastructure.config import GameConfig, LevelConfig
from pacman.maze.adapter import MazeAdapterError, MazeGeneratorAdapter
from pacman.maze.grid import MazeGrid
from pacman.gameplay.pacgums import PacgumField, place_pacgums
from pacman.maze.spawns import SpawnPositions, find_spawn_positions
from pacman.maze.world import WorldMap


class LevelGenerationError(RuntimeError):
    """Report a failure during level generation."""


@dataclass(frozen=True)
class LevelData:
    """Represent one generated playable level."""

    level_number: int
    maze: MazeGrid
    seed: int
    time_limit: int = 90
    spawns: SpawnPositions | None = None
    pellets: PacgumField | None = None
    world: WorldMap = field(init=False)

    def __post_init__(self) -> None:
        """Resolve spawn positions if not explicitly provided."""
        if self.spawns is None:
            object.__setattr__(self, "spawns", find_spawn_positions(self.maze))
        object.__setattr__(self, "world", WorldMap(self.maze))


@dataclass(frozen=True)
class LevelGenerationResult:
    """Return either a generated level or a user-facing error message."""

    level: LevelData | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Require exactly one success or failure value."""
        if (self.level is None) == (self.error_message is None):
            raise ValueError(
                "level generation result must contain a level or an error"
            )

    @property
    def succeeded(self) -> bool:
        """Return whether level generation completed successfully."""
        return self.level is not None


class _Rng(Protocol):
    """Describe the random number generator protocol."""

    def randint(self, a: int, b: int) -> int:
        """Return a random integer in range [a, b]."""


class LevelGenerator:
    """Generate reproducible initial level and random subsequent levels."""

    def __init__(
        self,
        config: GameConfig | None = None,
        adapter: MazeGeneratorAdapter | None = None,
        rng: _Rng | None = None,
    ) -> None:
        """Initialize level generator with configuration and adapter."""
        self._config = config or GameConfig()
        self._adapter = adapter or MazeGeneratorAdapter()
        self._rng: _Rng = rng if rng is not None else random.Random()

    @property
    def config(self) -> GameConfig:
        """Return the active game configuration."""
        return self._config

    def get_level_config(self, level_index: int) -> LevelConfig:
        """Return the level configuration for a given 0-indexed level."""
        if not self._config.levels:
            return LevelConfig()
        index = level_index % len(self._config.levels)
        return self._config.levels[index]

    def get_seed_for_level(
        self,
        level_index: int,
        explicit_seed: int | None = None,
    ) -> int:
        """Return deterministic seed for level 0 or random seed for later."""
        if explicit_seed is not None:
            return explicit_seed
        if level_index == 0:
            return self._config.seed
        return self._rng.randint(0, 2_147_483_647)

    def generate_level(
        self,
        level_index: int = 0,
        seed: int | None = None,
    ) -> LevelData:
        """Generate a level with deterministic or random seed."""
        if type(level_index) is not int:
            raise TypeError("level_index must be an integer")
        if level_index < 0:
            raise ValueError("level_index must be non-negative")

        level_config = self.get_level_config(level_index)
        resolved_seed = self.get_seed_for_level(level_index, seed)

        try:
            maze = self._adapter.generate(
                width=level_config.width,
                height=level_config.height,
                seed=resolved_seed,
                include_42=level_index == 0,
            )
        except MazeAdapterError as error:
            raise LevelGenerationError(
                f"Failed to generate level {level_index + 1}: {error}"
            ) from error
        except Exception as error:
            raise LevelGenerationError(
                f"Failed to generate level {level_index + 1} due to an "
                f"unexpected error: {error}"
            ) from error

        spawns = find_spawn_positions(maze)
        pellets = place_pacgums(maze, spawns)
        return LevelData(
            level_number=level_index + 1,
            maze=maze,
            seed=resolved_seed,
            time_limit=self._config.level_max_time,
            spawns=spawns,
            pellets=pellets,
        )

    def generate_level_safely(
        self,
        level_index: int = 0,
        seed: int | None = None,
    ) -> LevelGenerationResult:
        """Generate a level safely without raising exceptions."""
        try:
            level = self.generate_level(level_index=level_index, seed=seed)
            return LevelGenerationResult(level=level)
        except (LevelGenerationError, ValueError, TypeError) as error:
            return LevelGenerationResult(error_message=str(error))
        except Exception as error:
            return LevelGenerationResult(
                error_message=f"Level generation failed: {error}"
            )
