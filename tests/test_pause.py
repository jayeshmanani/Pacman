"""Tests for pause and resume gameplay behaviour."""

from pacman.app import GameState, GameStateController, update_active_gameplay
from pacman.context import GameSession
from pacman.maze_grid import MazeGrid, Tile
from pacman.player import Direction, Player
from pacman.world import WorldMap
from tests.app_fakes import _FakePygame, state_controls


def _open_world() -> WorldMap:
    """Create a compact walkable world for movement tests."""
    wall = Tile.WALL
    corridor = Tile.CORRIDOR
    maze = MazeGrid(
        tiles=(
            (wall, wall, wall, wall),
            (wall, corridor, corridor, wall),
            (wall, wall, wall, wall),
        ),
        entry=(1, 1),
        exit=(2, 1),
    )
    return WorldMap(maze)


def test_gameplay_can_enter_paused_state() -> None:
    """Verify the pause key pauses active gameplay."""
    session = GameSession()
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_p, state_controls(), session)

    assert session.is_paused
    assert controller.state is GameState.PLAYING


def test_gameplay_can_resume_from_paused_state() -> None:
    """Verify pressing pause again resumes active gameplay."""
    session = GameSession(is_paused=True)
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_p, state_controls(), session)

    assert not session.is_paused
    assert controller.state is GameState.PLAYING


def test_player_movement_does_not_advance_while_paused() -> None:
    """Verify paused gameplay does not run player movement updates."""
    world = _open_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.RIGHT
    session = GameSession(remaining_level_time=10.0, is_paused=True)
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(
        session,
        controller,
        0.1,
        lambda dt: player.update(dt, world),
    )

    assert player.position == (1.5, 1.5)
    assert session.remaining_level_time == 10.0


def test_level_timer_does_not_decrease_while_paused() -> None:
    """Verify pause freezes the PK-56 level timer."""
    session = GameSession(remaining_level_time=8.0, is_paused=True)
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(session, controller, 2.0)

    assert session.remaining_level_time == 8.0
    assert controller.state is GameState.PLAYING


def test_collision_updates_do_not_progress_while_paused() -> None:
    """Verify paused gameplay does not run collision/update callbacks."""
    collision_checks = 0
    session = GameSession(remaining_level_time=8.0, is_paused=True)
    controller = GameStateController(GameState.PLAYING)

    def check_collision(dt: float) -> None:
        nonlocal collision_checks
        collision_checks += 1

    update_active_gameplay(session, controller, 1.0, check_collision)

    assert collision_checks == 0
    assert session.remaining_level_time == 8.0


def test_pause_preserves_player_and_session_state() -> None:
    """Verify pause does not reset gameplay state."""
    player = Player(position=(1.75, 1.5), direction=Direction.RIGHT)
    session = GameSession(
        score=300,
        lives=2,
        current_level=1,
        remaining_level_time=12.0,
        is_paused=True,
    )
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(
        session,
        controller,
        5.0,
        lambda dt: player.update(dt, _open_world()),
    )

    assert player.position == (1.75, 1.5)
    assert player.direction is Direction.RIGHT
    assert session.score == 300
    assert session.lives == 2
    assert session.current_level == 1
    assert session.remaining_level_time == 12.0
    assert session.is_paused


def test_updates_resume_after_leaving_pause() -> None:
    """Verify gameplay continues from the same state after resume."""
    world = _open_world()
    player = Player.from_spawn((1, 1))
    player.direction = Direction.RIGHT
    session = GameSession(remaining_level_time=10.0, is_paused=True)
    controller = GameStateController(GameState.PLAYING)

    update_active_gameplay(
        session,
        controller,
        5.0,
        lambda dt: player.update(dt, world),
    )
    session.resume_gameplay()
    update_active_gameplay(
        session,
        controller,
        0.1,
        lambda dt: player.update(dt, world),
    )

    assert player.position[0] > 1.5
    assert session.remaining_level_time == 9.9
    assert controller.state is GameState.PLAYING


def test_repeated_pause_resume_transitions_are_predictable() -> None:
    """Verify repeated toggles leave state consistent."""
    session = GameSession(score=25, lives=3, remaining_level_time=7.0)
    controller = GameStateController(GameState.PLAYING)

    controller.handle_key(_FakePygame.K_p, state_controls(), session)
    controller.handle_key(_FakePygame.K_p, state_controls(), session)
    controller.handle_key(_FakePygame.K_p, state_controls(), session)
    controller.handle_key(_FakePygame.K_p, state_controls(), session)

    assert not session.is_paused
    assert session.score == 25
    assert session.lives == 3
    assert session.remaining_level_time == 7.0
    assert controller.state is GameState.PLAYING
