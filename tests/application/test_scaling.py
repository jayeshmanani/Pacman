"""Tests for dynamic viewport scaling and maze centering."""

import pytest

from pacman.application.scaling import (
    DEFAULT_WALL_BORDER,
    DEFAULT_WALL_COLOR,
    MazeViewport,
    calculate_maze_viewport,
    draw_maze_walls,
)
from pacman.maze.grid import MazeGrid, Tile
from tests.support.app_fakes import _FakeDrawModule, _FakeSurface


def test_calculate_maze_viewport_standard_21x21() -> None:
    """Verify 21x21 maze centers symmetrically in standard 520x496 window."""
    viewport = calculate_maze_viewport(
        window_width=520,
        window_height=496,
        grid_width=21,
        grid_height=21,
        hud_height=40,
        margin=12,
    )

    assert viewport.tile_size == 20
    assert viewport.offset_x == 50
    assert viewport.offset_y == 58
    assert viewport.grid_width == 21
    assert viewport.grid_height == 21

    # Equal left and right margins
    maze_right = viewport.offset_x + viewport.grid_width * viewport.tile_size
    right_margin = 520 - maze_right
    assert viewport.offset_x == right_margin

    # Equal top (below HUD) and bottom margins
    top_margin_below_hud = viewport.offset_y - 40
    maze_bottom = viewport.offset_y + viewport.grid_height * viewport.tile_size
    bottom_margin = 496 - maze_bottom
    assert top_margin_below_hud == bottom_margin


def test_calculate_maze_viewport_large_grid_31x31() -> None:
    """Verify large 31x31 maze fits inside window without clipping."""
    viewport = calculate_maze_viewport(
        window_width=520,
        window_height=496,
        grid_width=31,
        grid_height=31,
        hud_height=40,
        margin=12,
    )

    maze_right = viewport.offset_x + viewport.grid_width * viewport.tile_size
    maze_bottom = viewport.offset_y + viewport.grid_height * viewport.tile_size

    assert viewport.offset_x >= 12
    assert viewport.offset_y >= 52
    assert maze_right <= 520 - 12
    assert maze_bottom <= 496 - 12


def test_calculate_maze_viewport_non_square() -> None:
    """Verify rectangular maze scaling respects the limiting axis."""
    viewport = calculate_maze_viewport(
        window_width=600,
        window_height=400,
        grid_width=15,
        grid_height=25,
        hud_height=40,
        margin=10,
    )

    assert viewport.grid_width == 15
    assert viewport.grid_height == 25
    # Height is the limiting axis: (400 - 40 - 20) // 25 = 340 // 25 = 13
    assert viewport.tile_size == 13


@pytest.mark.parametrize(
    ("grid_w", "grid_h"),
    [
        (0, 0),
        (-5, 20),
        (20, -5),
    ],
)
def test_calculate_maze_viewport_invalid_dimensions_fallback(
    grid_w: int,
    grid_h: int,
) -> None:
    """Verify non-positive grid dimensions return a safe fallback layout."""
    viewport = calculate_maze_viewport(
        window_width=520,
        window_height=496,
        grid_width=grid_w,
        grid_height=grid_h,
    )

    assert viewport.tile_size >= 4
    assert viewport.offset_x >= 0
    assert viewport.offset_y >= 40


def test_viewport_coordinate_conversions() -> None:
    """Verify tile and continuous world coordinate translations."""
    viewport = MazeViewport(
        tile_size=20,
        offset_x=50,
        offset_y=60,
        grid_width=21,
        grid_height=21,
    )

    # Top-left of tile (2, 3)
    assert viewport.tile_to_screen(2, 3) == (90, 120)

    # Center of tile (2, 3)
    assert viewport.tile_center(2, 3) == (100, 130)

    # World position (2.5, 3.5)
    assert viewport.world_to_screen(2.5, 3.5) == (100, 130)


def test_draw_maze_walls() -> None:
    """Verify wall tiles render filled and bordered rectangles."""
    tiles = (
        (Tile.WALL, Tile.WALL, Tile.WALL),
        (Tile.WALL, Tile.CORRIDOR, Tile.WALL),
        (Tile.WALL, Tile.WALL, Tile.WALL),
    )
    maze = MazeGrid(tiles=tiles, entry=(1, 1), exit=(1, 1))
    viewport = MazeViewport(
        tile_size=20,
        offset_x=10,
        offset_y=10,
        grid_width=3,
        grid_height=3,
    )
    surface = _FakeSurface()
    draw = _FakeDrawModule()

    draw_maze_walls(surface, draw, maze, viewport)

    # 8 wall tiles, each drawn twice (fill + border)
    assert len(draw.rectangles) == 16

    wall_colors = [rect[0] for rect in draw.rectangles]
    assert wall_colors.count(DEFAULT_WALL_COLOR) == 8
    assert wall_colors.count(DEFAULT_WALL_BORDER) == 8
