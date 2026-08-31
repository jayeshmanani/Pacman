"""Unit tests for normal ghost chase targeting and direction selection."""

from pacman.gameplay.ghost import (
    Ghost,
    GhostIdentity,
    GhostState,
    calculate_ghost_target,
    select_chase_direction,
)
from pacman.maze.grid import MazeGrid, Tile
from pacman.gameplay.player import Direction
from pacman.maze.world import WorldMap


def create_test_world(grid_pattern: list[str]) -> WorldMap:
    """Create a WorldMap from a string grid pattern."""
    rows: list[tuple[Tile, ...]] = []
    first_corridor = (1, 1)
    last_corridor = (1, 1)

    for r_idx, line in enumerate(grid_pattern):
        row_tiles: list[Tile] = []
        for c_idx, char in enumerate(line):
            if char == "#":
                row_tiles.append(Tile.WALL)
            else:
                row_tiles.append(Tile.CORRIDOR)
                last_corridor = (c_idx, r_idx)
        rows.append(tuple(row_tiles))

    grid = MazeGrid(
        tiles=tuple(rows),
        entry=first_corridor,
        exit=last_corridor,
    )
    return WorldMap(maze=grid)


def test_calculate_ghost_target_blinky() -> None:
    """Verify Blinky directly targets Pacman's current tile."""
    target = calculate_ghost_target(
        identity=GhostIdentity.BLINKY,
        ghost_tile=(1, 1),
        player_tile=(5, 10),
        player_direction=Direction.RIGHT,
        home_spawn=(1, 1),
    )
    assert target == (5, 10)


def test_calculate_ghost_target_pinky() -> None:
    """Verify Pinky targets 4 tiles ahead in Pacman's facing direction."""
    target = calculate_ghost_target(
        identity=GhostIdentity.PINKY,
        ghost_tile=(1, 1),
        player_tile=(5, 10),
        player_direction=Direction.RIGHT,
        home_spawn=(1, 1),
    )
    # Right vector is (+1, 0), so (5 + 4, 10 + 0) = (9, 10)
    assert target == (9, 10)

    target_up = calculate_ghost_target(
        identity=GhostIdentity.PINKY,
        ghost_tile=(1, 1),
        player_tile=(5, 10),
        player_direction=Direction.UP,
        home_spawn=(1, 1),
    )
    # Up vector is (0, -1), so (5, 10 - 4) = (5, 6)
    assert target_up == (5, 6)


def test_calculate_ghost_target_inky() -> None:
    """Verify Inky targets vector doubled from Blinky through Pacman offset."""
    # Pacman at (5, 5) facing RIGHT, pivot = (5 + 2, 5) = (7, 5)
    # Blinky at (3, 5). Vector from Blinky to pivot = (7 - 3, 5 - 5) = (4, 0)
    # Target = pivot + (4, 0) = (11, 5)
    target = calculate_ghost_target(
        identity=GhostIdentity.INKY,
        ghost_tile=(1, 1),
        player_tile=(5, 5),
        player_direction=Direction.RIGHT,
        home_spawn=(1, 1),
        blinky_tile=(3, 5),
    )
    assert target == (11, 5)


def test_calculate_ghost_target_clyde() -> None:
    """Verify Clyde targets Pacman when far and home spawn when close."""
    home = (1, 1)
    # Far: Ghost at (1, 1), Pacman at (10, 10) -> distance squared > 64
    target_far = calculate_ghost_target(
        identity=GhostIdentity.CLYDE,
        ghost_tile=(1, 1),
        player_tile=(10, 10),
        player_direction=Direction.LEFT,
        home_spawn=home,
    )
    assert target_far == (10, 10)

    # Close: Ghost at (2, 2), Pacman at (3, 3) -> distance squared = 2 <= 64
    target_close = calculate_ghost_target(
        identity=GhostIdentity.CLYDE,
        ghost_tile=(2, 2),
        player_tile=(3, 3),
        player_direction=Direction.LEFT,
        home_spawn=home,
    )
    assert target_close == home


def test_select_chase_direction_minimizes_distance() -> None:
    """Verify direction choice selects neighbor tile closest to target."""
    # Current tile (2, 2), target (5, 2) [to the right]
    # Options: UP (2, 1), DOWN (2, 3), RIGHT (3, 2)
    # RIGHT is closest to (5, 2)
    chosen = select_chase_direction(
        current_tile=(2, 2),
        target_tile=(5, 2),
        legal_directions=[Direction.UP, Direction.DOWN, Direction.RIGHT],
    )
    assert chosen == Direction.RIGHT


def test_select_chase_direction_tiebreaker() -> None:
    """Verify tiebreaking priority order UP > LEFT > DOWN > RIGHT."""
    # Current tile (2, 2), target (3, 3)
    # UP -> (2, 1): dist_sq = (2-3)^2 + (1-3)^2 = 1 + 4 = 5
    # LEFT -> (1, 2): dist_sq = (1-3)^2 + (2-3)^2 = 4 + 1 = 5
    # Distance is equal (5 vs 5). Tiebreak order UP > LEFT chooses UP.
    chosen = select_chase_direction(
        current_tile=(2, 2),
        target_tile=(3, 3),
        legal_directions=[Direction.UP, Direction.LEFT],
    )
    assert chosen == Direction.UP


def test_ghost_chase_movement_integration() -> None:
    """Verify Blinky turns toward player at an intersection in a maze."""
    pattern = [
        "#######",
        "#.....#",
        "#.###.#",
        "#.....#",
        "#######",
    ]
    world = create_test_world(pattern)
    blinky = Ghost.from_spawn(GhostIdentity.BLINKY, spawn_tile=(1, 1))
    blinky.direction = Direction.RIGHT
    blinky.state = GhostState.NORMAL

    # At (3, 1) or (1, 1), when updating towards intersection, Blinky
    # targets the player position.
    # Player position = (1.5, 3.5)
    blinky.update(
        dt=0.1,
        world=world,
        base_speed=4.0,
        player_position=(1.5, 3.5),
        player_direction=Direction.RIGHT,
    )
    assert blinky.target_tile == (1, 3)
