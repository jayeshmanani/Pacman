"""End-to-end tests for complete maze and level generation."""

from typing import NoReturn

import pytest

from pacman.config import GameConfig, LevelConfig
from pacman.level_generator import LevelData, LevelGenerator
from pacman.maze_adapter import MazeGeneratorAdapter
from pacman.maze_preview import render_level_ascii


@pytest.mark.parametrize(
    ("level_index", "seed"),
    [(0, 42), (1, 1337), (2, 2026)],
)
def test_complete_real_maze_generation_flow(
    level_index: int,
    seed: int,
) -> None:
    """Verify normalization, spawns, and pacgums work together."""
    config = GameConfig(
        seed=seed,
        levels=[LevelConfig(width=9, height=7)],
    )

    result = LevelGenerator(config=config).generate_level_safely(
        level_index,
        seed=seed,
    )

    assert result.succeeded
    assert result.level is not None
    level = result.level
    assert level.maze.width == 19
    assert level.maze.height == 15
    assert level.spawns is not None
    assert level.pellets is not None

    spawn_positions = {
        level.spawns.player,
        *level.spawns.ghosts.as_tuple(),
    }
    pellet_positions = (
        level.pellets.pacgums | level.pellets.super_pacgums
    )
    eligible_corridors = {
        (x, y)
        for y in range(level.maze.height)
        for x in range(level.maze.width)
        if level.maze.is_corridor((x, y))
    } - spawn_positions
    assert len(spawn_positions) == 5
    assert len(level.pellets.super_pacgums) == 4
    assert pellet_positions == eligible_corridors
    assert pellet_positions.isdisjoint(spawn_positions)
    assert all(
        level.maze.is_corridor(position)
        for position in spawn_positions | pellet_positions
    )

    preview = render_level_ascii(level)
    assert len(preview.splitlines()) == level.maze.height
    assert all(
        len(row) == level.maze.width
        for row in preview.splitlines()
    )
    assert preview.count("P") == 1
    assert preview.count("G") == 4
    assert preview.count(".") == len(eligible_corridors) - 4
    assert preview.count("O") == 4

    for position in tuple(pellet_positions):
        level.pellets.consume(position)
    assert level.pellets.is_complete


def test_complete_flow_returns_clear_error_for_package_failure() -> None:
    """Verify an external failure produces a safe top-level result."""

    def failing_factory(**arguments: object) -> NoReturn:
        raise RuntimeError("simulated package failure")

    adapter = MazeGeneratorAdapter(failing_factory)
    result = LevelGenerator(adapter=adapter).generate_level_safely(0)

    assert not result.succeeded
    assert result.level is None
    assert result.error_message == (
        "Failed to generate level 1: "
        "The assigned package could not generate a maze."
    )


def test_preview_rejects_incomplete_level_data() -> None:
    """Verify visual inspection cannot silently omit required objects."""
    config = GameConfig(levels=[LevelConfig(width=5, height=5)])
    level = LevelGenerator(config=config).generate_level(0)
    incomplete_level = LevelData(
        level_number=level.level_number,
        maze=level.maze,
        seed=level.seed,
        spawns=level.spawns,
    )

    with pytest.raises(ValueError, match="requires spawns and pacgums"):
        render_level_ascii(incomplete_level)
