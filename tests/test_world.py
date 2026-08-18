"""Tests for shared world coordinates and collision queries."""

import math
from typing import cast

import pytest

from pacman.level_generator import LevelData
from pacman.maze_grid import MazeGrid, Tile
from pacman.world import WorldMap, WorldPosition, WorldSize


def _world() -> WorldMap:
    """Create a small world with corridors surrounded by walls."""
    wall = Tile.WALL
    corridor = Tile.CORRIDOR
    maze = MazeGrid(
        tiles=(
            (wall, wall, wall, wall, wall),
            (wall, corridor, corridor, corridor, wall),
            (wall, corridor, wall, corridor, wall),
            (wall, corridor, corridor, corridor, wall),
            (wall, wall, wall, wall, wall),
        ),
        entry=(1, 1),
        exit=(3, 3),
    )
    return WorldMap(maze)


def test_tile_center_and_world_to_tile_use_one_world_unit_per_tile() -> None:
    """Verify tile/world conversion is stable and resolution-independent."""
    world = _world()

    assert world.tile_center((3, 2)) == (3.5, 2.5)
    assert world.world_to_tile((3.5, 2.5)) == (3, 2)
    assert world.world_to_tile((3.01, 2.99)) == (3, 2)


def test_tile_center_rejects_invalid_coordinates() -> None:
    """Verify callers cannot convert malformed or out-of-bounds tiles."""
    world = _world()

    with pytest.raises(ValueError, match="in-bounds integer"):
        world.tile_center((5, 2))
    with pytest.raises(ValueError, match="in-bounds integer"):
        world.tile_center(cast(tuple[int, int], (1.5, 2)))


def test_world_queries_distinguish_corridors_walls_and_boundaries() -> None:
    """Verify all systems receive the same safe walkability answers."""
    world = _world()

    assert world.contains_world((1.5, 1.5))
    assert world.is_walkable_tile((1, 1))
    assert world.is_walkable_world((1.5, 1.5))
    assert not world.is_walkable_tile((2, 2))
    assert not world.is_walkable_world((2.5, 2.5))
    assert not world.contains_world((-0.1, 1.5))
    assert not world.is_walkable_world((-0.1, 1.5))


def test_collision_detects_wall_overlap() -> None:
    """Verify an entity cannot overlap a neighboring wall tile."""
    world = _world()

    assert not world.collides_with_wall((1.5, 1.5), (0.4, 0.4))
    assert world.collides_with_wall((1.8, 2.5), (0.3, 0.3))
    assert not world.can_occupy((1.8, 2.5), (0.3, 0.3))


def test_touching_a_tile_boundary_is_not_an_overlap() -> None:
    """Verify exact contact does not count as entering the next tile."""
    world = _world()

    assert world.can_occupy((1.5, 1.5), (0.5, 0.5))


def test_outside_world_is_treated_as_solid() -> None:
    """Verify entities cannot move beyond the normalized maze boundary."""
    world = _world()

    assert world.collides_with_wall((-0.1, 1.5))
    assert world.collides_with_wall((4.8, 3.5), (0.3, 0.3))


@pytest.mark.parametrize(
    ("center", "half_size", "expected_message"),
    [
        ((math.inf, 1.0), (0.2, 0.2), "finite numbers"),
        ((1.5, 1.5), (-0.1, 0.2), "cannot be negative"),
    ],
)
def test_collision_rejects_invalid_geometry(
    center: WorldPosition,
    half_size: WorldSize,
    expected_message: str,
) -> None:
    """Verify invalid geometry fails clearly at the shared boundary."""
    with pytest.raises(ValueError, match=expected_message):
        _world().collides_with_wall(center, half_size)


def test_level_data_exposes_one_world_map_for_all_systems() -> None:
    """Verify generated level consumers share the same maze geometry."""
    world = _world()
    level = LevelData(level_number=1, maze=world.maze, seed=42)

    assert level.world == world
    assert level.world.maze is level.maze
    assert level.spawns is not None
    assert level.world.tile_center(level.spawns.player) == (2.5, 1.5)
