"""Find valid walkable spawn positions for player and ghosts."""


from dataclasses import dataclass
import math

from pacman.maze.grid import Coordinate, MazeGrid


@dataclass(frozen=True)
class GhostSpawns:
    """Corner spawn positions for the four ghosts."""

    top_left: Coordinate
    top_right: Coordinate
    bottom_left: Coordinate
    bottom_right: Coordinate

    def as_tuple(
        self,
    ) -> tuple[Coordinate, Coordinate, Coordinate, Coordinate]:
        """Return the ghost spawn positions as an ordered 4-tuple."""
        return (
            self.top_left,
            self.top_right,
            self.bottom_left,
            self.bottom_right,
        )

    def as_list(self) -> list[Coordinate]:
        """Return the ghost spawn positions as a list."""
        return [
            self.top_left,
            self.top_right,
            self.bottom_left,
            self.bottom_right,
        ]


@dataclass(frozen=True)
class SpawnPositions:
    """Valid walkable spawn coordinates for player and four ghosts."""

    player: Coordinate
    ghosts: GhostSpawns


def find_closest_walkable_tile(
    maze: MazeGrid,
    target: tuple[float, float] | Coordinate,
) -> Coordinate:
    """Find the closest walkable corridor tile to the given target point."""
    target_x, target_y = target
    best_coordinate: Coordinate | None = None
    best_distance = float("inf")

    for y in range(maze.height):
        for x in range(maze.width):
            coord = (x, y)
            if not maze.is_corridor(coord):
                continue
            distance = math.hypot(x - target_x, y - target_y)
            if distance < best_distance:
                best_distance = distance
                best_coordinate = coord

    if best_coordinate is None:
        raise ValueError("Maze contains no walkable corridors.")

    return best_coordinate


def find_player_spawn(maze: MazeGrid) -> Coordinate:
    """Find a valid walkable spawn position for the player near the center."""
    center_x = (maze.width - 1) / 2.0
    center_y = (maze.height - 1) / 2.0
    return find_closest_walkable_tile(maze, (center_x, center_y))


def find_ghost_spawns(maze: MazeGrid) -> GhostSpawns:
    """Find valid walkable spawn positions for 4 ghosts in the corners."""
    max_x = float(maze.width - 1)
    max_y = float(maze.height - 1)

    top_left = find_closest_walkable_tile(maze, (0.0, 0.0))
    top_right = find_closest_walkable_tile(maze, (max_x, 0.0))
    bottom_left = find_closest_walkable_tile(maze, (0.0, max_y))
    bottom_right = find_closest_walkable_tile(maze, (max_x, max_y))

    return GhostSpawns(
        top_left=top_left,
        top_right=top_right,
        bottom_left=bottom_left,
        bottom_right=bottom_right,
    )


def find_spawn_positions(maze: MazeGrid) -> SpawnPositions:
    """Calculate valid walkable spawn positions for player and 4 ghosts."""
    player_spawn = find_player_spawn(maze)
    ghost_spawns = find_ghost_spawns(maze)
    return SpawnPositions(player=player_spawn, ghosts=ghost_spawns)
