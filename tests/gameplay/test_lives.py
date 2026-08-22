"""Gameplay tests for lives, death, respawn, and game over."""

import pytest

from pacman.app import GameState, GameStateController
from pacman.context import GameSession
from pacman.lives import PlayerDeathOutcome, handle_normal_ghost_collision
from pacman.maze_grid import MazeGrid, Tile
from pacman.player import Direction, Player
from pacman.world import WorldMap


def _test_world() -> WorldMap:
    """Create a small world with a safe center spawn."""
    wall = Tile.WALL
    corridor = Tile.CORRIDOR
    maze = MazeGrid(
        tiles=(
            (wall, wall, wall),
            (wall, corridor, wall),
            (wall, wall, wall),
        ),
        entry=(1, 1),
        exit=(1, 1),
    )
    return WorldMap(maze)


def test_normal_collision_removes_one_life_and_respawns_player() -> None:
    """Verify a surviving player returns safely to the spawn center."""
    world = _test_world()
    session = GameSession(lives=3)
    player = Player(
        position=(4.5, 2.5),
        direction=Direction.LEFT,
        queued_direction=Direction.UP,
    )
    controller = GameStateController(GameState.PLAYING)

    outcome = handle_normal_ghost_collision(
        session,
        player,
        (1, 1),
        world,
        controller,
    )

    assert outcome is PlayerDeathOutcome.RESPAWNED
    assert session.lives == 2
    assert player.position == (1.5, 1.5)
    assert player.direction is Direction.NONE
    assert player.queued_direction is Direction.NONE
    assert controller.state is GameState.PLAYING


def test_last_life_ends_game_without_respawning() -> None:
    """Verify losing the final life moves the game to the end screen."""
    world = _test_world()
    session = GameSession(lives=1)
    player = Player(position=(4.5, 2.5), direction=Direction.RIGHT)
    controller = GameStateController(GameState.PLAYING)

    outcome = handle_normal_ghost_collision(
        session,
        player,
        (1, 1),
        world,
        controller,
    )

    assert outcome is PlayerDeathOutcome.GAME_OVER
    assert session.lives == 0
    assert player.position == (4.5, 2.5)
    assert controller.state is GameState.END_SCREEN


def test_lives_never_become_negative() -> None:
    """Verify repeated death handling cannot produce negative lives."""
    world = _test_world()
    session = GameSession(lives=0)
    player = Player.from_spawn((1, 1))
    controller = GameStateController(GameState.PLAYING)

    outcome = handle_normal_ghost_collision(
        session,
        player,
        (1, 1),
        world,
        controller,
    )

    assert outcome is PlayerDeathOutcome.GAME_OVER
    assert session.lives == 0
    assert controller.state is GameState.END_SCREEN


def test_respawn_rejects_wall_tile() -> None:
    """Verify an invalid spawn cannot place the player inside a wall."""
    world = _test_world()
    player = Player.from_spawn((1, 1))

    with pytest.raises(ValueError, match="walkable"):
        player.respawn((0, 0), world)
