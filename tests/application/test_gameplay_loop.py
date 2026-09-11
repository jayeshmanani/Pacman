"""Tests for live input and frame-level gameplay orchestration."""

from pacman.application.context import AppContext
from pacman.application.gameplay_loop import (
    GameplayControls,
    queue_player_direction,
    update_gameplay_frame,
)
from pacman.application.state import GameState, GameStateController
from pacman.gameplay.ghost import GhostState
from pacman.gameplay.player import Direction
from pacman.infrastructure.config import GameConfig, LevelConfig
from pacman.maze.level_generator import LevelGenerator
from tests.support.gameplay_fakes import FixedMazeAdapter


def _context(level_count: int = 2) -> AppContext:
    """Create a deterministic live-game context."""
    config = GameConfig(
        levels=[LevelConfig() for _ in range(level_count)],
        level_max_time=60,
    )
    context = AppContext(config=config)
    context.level_generator = LevelGenerator(
        config=config,
        adapter=FixedMazeAdapter(),
    )
    context.start_new_game()
    return context


def _controls() -> GameplayControls:
    """Create distinct input values for direction tests."""
    return GameplayControls(
        up_keys=frozenset({1, 11}),
        down_keys=frozenset({2, 12}),
        left_keys=frozenset({3, 13}),
        right_keys=frozenset({4, 14}),
    )


def _set_pellets(
    context: AppContext,
    pacgums: set[tuple[int, int]],
    super_pacgums: set[tuple[int, int]],
) -> None:
    """Replace the mutable contents of the active level pellet field."""
    assert context.active_level is not None
    assert context.active_level.pellets is not None
    context.active_level.pellets.pacgums.clear()
    context.active_level.pellets.pacgums.update(pacgums)
    context.active_level.pellets.super_pacgums.clear()
    context.active_level.pellets.super_pacgums.update(super_pacgums)


def test_direction_key_queues_player_turn() -> None:
    """Verify supported input reaches the active player model."""
    context = _context()
    assert context.player is not None

    assert queue_player_direction(14, _controls(), context)
    assert context.player.queued_direction is Direction.RIGHT
    assert not queue_player_direction(99, _controls(), context)


def test_wasd_physical_positions_work_with_russian_layout() -> None:
    """Verify localized ЦФЫВ characters map to movement directions."""
    context = _context()
    assert context.player is not None

    localized_inputs = (
        ("ц", Direction.UP),
        ("ы", Direction.DOWN),
        ("ф", Direction.LEFT),
        ("в", Direction.RIGHT),
    )
    for character, expected_direction in localized_inputs:
        assert queue_player_direction(
            999,
            _controls(),
            context,
            character,
        )
        assert context.player.queued_direction is expected_direction


def test_frame_moves_player_and_collects_pacgum() -> None:
    """Verify movement and collection execute in the live frame pipeline."""
    context = _context()
    controller = GameStateController(GameState.PLAYING)
    assert context.player is not None
    assert context.active_level is not None
    start_x, start_y = context.player.position
    target_tile = (int(start_x), int(start_y))
    _set_pellets(context, {target_tile, (0, 0)}, set())
    context.player.queued_direction = Direction.RIGHT

    update_gameplay_frame(context, controller, 0.05)

    assert context.player.position[0] > start_x
    assert context.player.position[1] == start_y
    assert context.session.score == context.config.points_per_pacgum


def test_frame_activates_frightened_ghosts_from_super_pacgum() -> None:
    """Verify a collected power pellet changes visible ghost states."""
    context = _context()
    controller = GameStateController(GameState.PLAYING)
    assert context.player is not None
    assert context.active_level is not None
    assert context.ghost_gameplay is not None
    player_tile = (
        int(context.player.position[0]),
        int(context.player.position[1]),
    )
    _set_pellets(context, {(0, 0)}, {player_tile})

    update_gameplay_frame(context, controller, 0.0)

    assert context.session.score == context.config.points_per_super_pacgum
    assert all(
        ghost.state is GhostState.FRIGHTENED
        for ghost in context.ghost_gameplay.ghosts
    )


def test_normal_ghost_collision_removes_life_and_respawns_player() -> None:
    """Verify collision consequences run inside the live frame pipeline."""
    context = _context()
    controller = GameStateController(GameState.PLAYING)
    assert context.player is not None
    assert context.active_level is not None
    assert context.ghost_gameplay is not None
    context.ghost_gameplay.ghosts[0].position = context.player.position
    starting_lives = context.session.lives

    update_gameplay_frame(context, controller, 0.0)

    assert context.session.lives == starting_lives - 1
    assert context.active_level.spawns is not None
    assert context.player.position == context.active_level.world.tile_center(
        context.active_level.spawns.player
    )
    assert all(
        ghost.position == context.active_level.world.tile_center(
            ghost.home_spawn
        )
        for ghost in context.ghost_gameplay.ghosts
    )
    assert all(
        ghost.state is GhostState.NORMAL
        for ghost in context.ghost_gameplay.ghosts
    )
    assert controller.state is GameState.PLAYING

    update_gameplay_frame(context, controller, 0.0)

    assert context.session.lives == starting_lives - 1


def test_last_pacgum_advances_to_a_fresh_visible_level() -> None:
    """Verify normal completion installs the next level and ghost group."""
    context = _context(level_count=2)
    controller = GameStateController(GameState.PLAYING)
    assert context.player is not None
    assert context.active_level is not None
    player_tile = (
        int(context.player.position[0]),
        int(context.player.position[1]),
    )
    previous_ghost_gameplay = context.ghost_gameplay
    _set_pellets(context, {player_tile}, set())

    update_gameplay_frame(context, controller, 0.0)

    assert context.session.current_level == 1
    assert context.active_level.level_number == 2
    assert context.ghost_gameplay is not previous_ghost_gameplay
    assert controller.state is GameState.PLAYING


def test_last_pacgum_on_final_level_triggers_victory() -> None:
    """Verify the complete live pipeline reaches the Victory state."""
    context = _context(level_count=1)
    controller = GameStateController(GameState.PLAYING)
    assert context.player is not None
    assert context.active_level is not None
    player_tile = (
        int(context.player.position[0]),
        int(context.player.position[1]),
    )
    _set_pellets(context, {player_tile}, set())

    update_gameplay_frame(context, controller, 0.0)

    assert context.session.is_victory
    assert controller.state is GameState.VICTORY
