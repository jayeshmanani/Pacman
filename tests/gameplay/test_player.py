"""Gameplay tests for movement, turn buffering, and wall collisions."""

from pacman.maze_grid import MazeGrid, Tile
from pacman.player import Direction, Player, direction_from_key
from pacman.world import WorldMap


def _create_test_world() -> WorldMap:
    """Create a small 3x3 test maze with corridors and walls."""
    wall = Tile.WALL
    corridor = Tile.CORRIDOR
    # Tile grid indexed by tiles[y][x]
    tiles = (
        (wall, wall, wall),              # y=0: (1, 0) is a WALL
        (corridor, corridor, corridor),  # y=1: (1, 1) is CORRIDOR
        (wall, corridor, wall),          # y=2: (1, 2) is CORRIDOR
    )
    maze = MazeGrid(tiles=tiles, entry=(1, 1), exit=(1, 1))
    return WorldMap(maze)


def test_player_spawns_at_tile_center() -> None:
    """Verify player spawns centered at tile coordinates."""
    player = Player.from_spawn((1, 1))
    assert player.position == (1.5, 1.5)
    assert player.direction == Direction.NONE


def test_player_moves_along_clear_corridor() -> None:
    """Verify player advances along active direction."""
    world = _create_test_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.RIGHT

    player.update(dt=0.1, world=world)

    # Position moves right: 1.5 + (1.0 * 5.0 * 0.1) = 2.0
    assert player.position[0] > 1.5
    assert player.position[1] == 1.5


def test_player_blocked_by_wall() -> None:
    """Verify player stops when moving into a wall."""
    world = _create_test_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.UP  # Tile (1, 0) is a WALL

    player.update(dt=0.1, world=world)

    # Movement blocked, stays at original position and resets direction
    assert player.position == (1.5, 1.5)
    assert player.direction == Direction.NONE


def test_player_turn_buffering() -> None:
    """Verify queued_direction turns player when path becomes clear."""
    world = _create_test_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.LEFT
    player.queued_direction = Direction.DOWN

    player.update(dt=0.05, world=world)

    # Turned DOWN because (1, 2) is a corridor
    assert player.direction == Direction.DOWN


def test_direction_from_key_mapping() -> None:
    """Verify WASD and Arrow keys map to correct directions."""
    assert direction_from_key("w") == Direction.UP
    assert direction_from_key("Up") == Direction.UP
    assert direction_from_key("s") == Direction.DOWN
    assert direction_from_key("Down") == Direction.DOWN
    assert direction_from_key("a") == Direction.LEFT
    assert direction_from_key("Left") == Direction.LEFT
    assert direction_from_key("d") == Direction.RIGHT
    assert direction_from_key("Right") == Direction.RIGHT
    assert direction_from_key("x") is None


def test_direction_helpers() -> None:
    """Verify is_opposite and is_perpendicular helper methods."""
    assert Direction.LEFT.is_opposite(Direction.RIGHT)
    assert Direction.UP.is_opposite(Direction.DOWN)
    assert not Direction.LEFT.is_opposite(Direction.UP)
    assert not Direction.NONE.is_opposite(Direction.RIGHT)
    assert Direction.LEFT.is_perpendicular(Direction.UP)
    assert Direction.LEFT.is_perpendicular(Direction.DOWN)
    assert Direction.RIGHT.is_perpendicular(Direction.UP)
    assert Direction.RIGHT.is_perpendicular(Direction.DOWN)
    assert Direction.UP.is_perpendicular(Direction.LEFT)
    assert Direction.UP.is_perpendicular(Direction.RIGHT)
    assert not Direction.LEFT.is_perpendicular(Direction.RIGHT)
    assert not Direction.NONE.is_perpendicular(Direction.UP)


def test_player_turn_buffering_clears_queued_direction() -> None:
    """Verify queued_direction is reset to NONE after executing a turn."""
    world = _create_test_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.LEFT
    player.queued_direction = Direction.DOWN
    player.update(dt=0.05, world=world)
    assert player.direction == Direction.DOWN
    assert player.queued_direction == Direction.NONE


def test_player_corner_snapping() -> None:
    """Verify perpendicular turns snap off-axis position to tile center."""
    world = _create_test_world()
    # Spawn at (1.5, 1.5) but slightly off-center on X at (1.52, 1.5)
    player = Player(position=(1.52, 1.5), direction=Direction.RIGHT)
    player.queued_direction = Direction.DOWN  # (1, 2) is a clear corridor
    player.update(dt=0.05, world=world)
    assert player.direction == Direction.DOWN
    # X coordinate snapped from 1.52 to tile center 1.5
    assert player.position[0] == 1.5
