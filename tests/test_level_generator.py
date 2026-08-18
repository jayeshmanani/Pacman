"""Tests for deterministic and random level generation."""

import random
from typing import cast

import pytest

from pacman.config import GameConfig, LevelConfig
from pacman.context import AppContext
from pacman.level_generator import (
    LevelData,
    LevelGenerationError,
    LevelGenerationResult,
    LevelGenerator,
)
from pacman.maze_adapter import MazeAdapterError, MazeGeneratorAdapter
from pacman.maze_grid import MazeGrid, Tile


class FakeMazeAdapter(MazeGeneratorAdapter):
    """Controllable fake adapter to inspect level generation requests."""

    def __init__(self, should_fail: bool = False) -> None:
        """Initialize fake adapter with optional failure mode."""
        super().__init__()
        self.calls: list[dict[str, object]] = []
        self._should_fail = should_fail

    def generate(
        self,
        width: int,
        height: int,
        seed: int = 0,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] = (-1, -1),
        include_42: bool = True,
    ) -> MazeGrid:
        """Record arguments and return a simple mock grid or fail."""
        self.calls.append({
            "width": width,
            "height": height,
            "seed": seed,
            "entry": entry,
            "exit": exit,
            "include_42": include_42,
        })
        if self._should_fail:
            raise MazeAdapterError("Fake maze generation failure")
        rows = tuple(
            tuple(Tile.CORRIDOR for _ in range(7))
            for _ in range(7)
        )
        return MazeGrid(tiles=rows, entry=(0, 0), exit=(6, 6))


def test_level_zero_uses_configured_fixed_seed() -> None:
    """Verify level 0 uses the configured deterministic seed."""
    config = GameConfig(
        seed=1337,
        levels=[LevelConfig(width=15, height=15)],
    )
    fake_adapter = FakeMazeAdapter()
    generator = LevelGenerator(config=config, adapter=fake_adapter)

    level = generator.generate_level(0)

    assert level.level_number == 1
    assert level.seed == 1337
    assert level.time_limit == 90
    assert level.spawns is not None
    assert level.spawns.player == (3, 3)
    assert level.pellets is not None
    assert fake_adapter.calls[0]["seed"] == 1337
    assert fake_adapter.calls[0]["width"] == 15
    assert fake_adapter.calls[0]["height"] == 15
    assert fake_adapter.calls[0]["include_42"] is True


def test_level_zero_is_deterministic_and_reproducible() -> None:
    """Verify generating level 0 multiple times uses the exact same seed."""
    config = GameConfig(seed=42)
    fake_adapter = FakeMazeAdapter()
    generator = LevelGenerator(config=config, adapter=fake_adapter)

    level_a = generator.generate_level(0)
    level_b = generator.generate_level(0)

    assert level_a.seed == level_b.seed == 42
    assert fake_adapter.calls[0]["seed"] == 42
    assert fake_adapter.calls[1]["seed"] == 42


def test_subsequent_levels_use_random_seeds() -> None:
    """Verify subsequent levels use random changing seeds."""
    config = GameConfig(seed=42)
    fake_adapter = FakeMazeAdapter()
    rng = random.Random(999)
    generator = LevelGenerator(config=config, adapter=fake_adapter, rng=rng)

    level_1 = generator.generate_level(1)
    level_2 = generator.generate_level(2)

    assert level_1.level_number == 2
    assert level_2.level_number == 3
    assert level_1.seed != 42
    assert level_2.seed != 42
    assert level_1.seed != level_2.seed
    assert fake_adapter.calls[0]["include_42"] is False
    assert fake_adapter.calls[1]["include_42"] is False


def test_level_dimensions_from_configured_levels_list() -> None:
    """Verify each level resolves dimensions from config.levels."""
    config = GameConfig(
        levels=[
            LevelConfig(width=10, height=10),
            LevelConfig(width=20, height=20),
        ],
        level_max_time=120,
    )
    fake_adapter = FakeMazeAdapter()
    generator = LevelGenerator(config=config, adapter=fake_adapter)

    generator.generate_level(0)
    generator.generate_level(1)
    generator.generate_level(2)  # wraps around to index 0

    assert fake_adapter.calls[0]["width"] == 10
    assert fake_adapter.calls[1]["width"] == 20
    assert fake_adapter.calls[2]["width"] == 10


def test_explicit_seed_override() -> None:
    """Verify passing an explicit seed overrides automatic seed selection."""
    config = GameConfig(seed=42)
    fake_adapter = FakeMazeAdapter()
    generator = LevelGenerator(config=config, adapter=fake_adapter)

    level = generator.generate_level(1, seed=777)

    assert level.seed == 777
    assert fake_adapter.calls[0]["seed"] == 777


def test_generate_level_rejects_invalid_indices() -> None:
    """Verify negative or non-integer level indices are rejected."""
    generator = LevelGenerator()

    with pytest.raises(ValueError, match="non-negative"):
        generator.generate_level(-1)

    with pytest.raises(TypeError, match="integer"):
        generator.generate_level(cast(int, "invalid"))


def test_generate_level_wraps_adapter_error() -> None:
    """Verify adapter failure raises LevelGenerationError with context."""
    fake_adapter = FakeMazeAdapter(should_fail=True)
    generator = LevelGenerator(adapter=fake_adapter)

    with pytest.raises(
        LevelGenerationError,
        match="Failed to generate level 1",
    ):
        generator.generate_level(0)


def test_generate_level_safely_success() -> None:
    """Verify safe level generation returns a successful result object."""
    fake_adapter = FakeMazeAdapter()
    generator = LevelGenerator(adapter=fake_adapter)

    result = generator.generate_level_safely(0)

    assert result.succeeded
    assert isinstance(result.level, LevelData)
    assert result.error_message is None


def test_generate_level_safely_handles_failure() -> None:
    """Verify safe level generation handles failures cleanly."""
    fake_adapter = FakeMazeAdapter(should_fail=True)
    generator = LevelGenerator(adapter=fake_adapter)

    result = generator.generate_level_safely(0)

    assert not result.succeeded
    assert result.level is None
    assert "Failed to generate level 1" in str(result.error_message)


def test_level_generation_result_requires_one_value() -> None:
    """Verify LevelGenerationResult validates its arguments."""
    with pytest.raises(ValueError, match="must contain"):
        LevelGenerationResult()


def test_context_initializes_level_generator() -> None:
    """Verify AppContext initializes level_generator with its config."""
    config = GameConfig(seed=555, level_max_time=75)
    context = AppContext(config=config)

    assert isinstance(context.level_generator, LevelGenerator)
    assert context.level_generator.config.seed == 555
    assert context.level_generator.config.level_max_time == 75
