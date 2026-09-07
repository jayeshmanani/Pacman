"""Dynamic viewport scaling and centering for maze rendering."""

from dataclasses import dataclass
from typing import Final

from pacman.application.contracts import Color, Coordinate, DrawModule, Surface
from pacman.maze.grid import MazeGrid, Tile


DEFAULT_WALL_COLOR: Final[Color] = (33, 33, 222)
DEFAULT_WALL_BORDER: Final[Color] = (82, 113, 255)


@dataclass(frozen=True)
class MazeViewport:
    """Viewport layout and scaling for rendering a maze on a window."""

    tile_size: int
    offset_x: int
    offset_y: int
    grid_width: int
    grid_height: int

    def tile_to_screen(self, col: int, row: int) -> Coordinate:
        """Return the top-left screen pixel coordinate for a tile."""
        return (
            self.offset_x + col * self.tile_size,
            self.offset_y + row * self.tile_size,
        )

    def tile_center(self, col: int, row: int) -> Coordinate:
        """Return the center screen pixel coordinate for a tile."""
        return (
            self.offset_x + int((col + 0.5) * self.tile_size),
            self.offset_y + int((row + 0.5) * self.tile_size),
        )

    def world_to_screen(self, x: float, y: float) -> Coordinate:
        """Return screen pixel coordinates for a continuous position."""
        return (
            self.offset_x + int(x * self.tile_size),
            self.offset_y + int(y * self.tile_size),
        )


def calculate_maze_viewport(
    window_width: int,
    window_height: int,
    grid_width: int,
    grid_height: int,
    hud_height: int = 40,
    margin: int = 12,
) -> MazeViewport:
    """Compute centered viewport layout and integer tile scaling."""
    if grid_width <= 0 or grid_height <= 0:
        return MazeViewport(
            tile_size=16,
            offset_x=margin,
            offset_y=hud_height + margin,
            grid_width=max(1, grid_width),
            grid_height=max(1, grid_height),
        )

    available_width = max(0, window_width - 2 * margin)
    available_height = max(0, window_height - hud_height - 2 * margin)

    tile_size = max(
        4,
        min(
            available_width // grid_width,
            available_height // grid_height,
        ),
    )

    maze_w = grid_width * tile_size
    maze_h = grid_height * tile_size

    offset_x = (window_width - maze_w) // 2
    offset_y = hud_height + ((window_height - hud_height - maze_h) // 2)

    return MazeViewport(
        tile_size=tile_size,
        offset_x=offset_x,
        offset_y=offset_y,
        grid_width=grid_width,
        grid_height=grid_height,
    )


def draw_maze_walls(
    surface: Surface,
    draw: DrawModule,
    maze: MazeGrid,
    viewport: MazeViewport,
    wall_color: Color = DEFAULT_WALL_COLOR,
    border_color: Color = DEFAULT_WALL_BORDER,
) -> None:
    """Render styled wall blocks for each non-corridor cell in the maze."""
    border_width = max(1, viewport.tile_size // 10)

    for row in range(maze.height):
        for col in range(maze.width):
            if maze.tile_at((col, row)) is Tile.WALL:
                top_left = viewport.tile_to_screen(col, row)
                rect = (
                    top_left[0],
                    top_left[1],
                    viewport.tile_size,
                    viewport.tile_size,
                )
                draw.rect(surface, wall_color, rect)
                draw.rect(surface, border_color, rect, width=border_width)
