"""Integration tests for the complete four-ghost gameplay coordinator."""

from pacman.config import GameConfig
from pacman.context import GameSession
from pacman.ghost import GhostIdentity, GhostState
from pacman.ghost_gameplay import GhostGameplay
from pacman.player import Direction, Player
from pacman.spawns import GhostSpawns
from pacman.world import WorldMap
from tests.gameplay_fakes import FixedMazeAdapter


def _world() -> WorldMap:
    """Create a fixed open world for coordinated ghost updates."""
    return WorldMap(FixedMazeAdapter().generate(width=7, height=7))


def _spawns() -> GhostSpawns:
    """Return four distinct walkable spawn tiles."""
    return GhostSpawns(
        top_left=(1, 1),
        top_right=(5, 1),
        bottom_left=(1, 5),
        bottom_right=(5, 5),
    )


def test_four_ghosts_share_frightened_activation_and_recovery() -> None:
    """Verify one coordinator advances all identities and shared timing."""
    config = GameConfig(seed=42, frightened_duration=1.0)
    gameplay = GhostGameplay.create(_spawns(), config, base_speed=1.0)
    world = _world()

    assert [ghost.identity for ghost in gameplay.ghosts] == list(
        GhostIdentity
    )

    gameplay.activate_frightened()
    gameplay.update(
        dt=0.5,
        world=world,
        player_position=(3.5, 3.5),
        player_direction=Direction.RIGHT,
    )

    assert gameplay.power_state.remaining_time == 0.5
    assert all(
        ghost.state is GhostState.FRIGHTENED
        and ghost.frightened_timer == 0.5
        and world.can_occupy(ghost.position, half_size=(0.35, 0.35))
        for ghost in gameplay.ghosts
    )

    gameplay.update(
        dt=0.5,
        world=world,
        player_position=(3.5, 3.5),
        player_direction=Direction.RIGHT,
    )
    recovered_states: list[GhostState] = [
        ghost.state for ghost in gameplay.ghosts
    ]

    assert gameplay.power_state.remaining_time == 0.0
    assert recovered_states == [GhostState.NORMAL] * 4
    assert all(ghost.frightened_timer == 0.0 for ghost in gameplay.ghosts)


def test_coordinator_applies_collision_score_and_respawn_config() -> None:
    """Verify collision handling uses the coordinator's shared settings."""
    config = GameConfig(
        seed=7,
        points_per_ghost=250,
        frightened_duration=4.0,
        ghost_respawn_delay=1.25,
    )
    gameplay = GhostGameplay.create(_spawns(), config, base_speed=1.0)
    session = GameSession()
    collided_ghost = gameplay.ghosts[0]

    gameplay.activate_frightened()
    eaten = gameplay.resolve_collisions(session, (collided_ghost,))
    repeated = gameplay.resolve_collisions(session, (collided_ghost,))

    assert eaten.player_hit is False
    assert eaten.eaten_ghosts == 1
    assert eaten.score_gained == 250
    assert session.score == 250
    assert collided_ghost.state is GhostState.RESPAWNING
    assert collided_ghost.respawn_timer == 1.25
    assert repeated.player_hit is False
    assert repeated.eaten_ghosts == 0
    assert repeated.score_gained == 0

    gameplay.update(
        dt=1.25,
        world=_world(),
        player_position=(3.5, 3.5),
        player_direction=Direction.LEFT,
    )
    state_after_respawn: GhostState = collided_ghost.state

    assert state_after_respawn is GhostState.NORMAL
    assert collided_ghost.respawn_timer == 0.0


def test_all_four_ghosts_complete_position_based_collision_cycle() -> None:
    """Verify four real overlaps complete eating, respawn, and hit flow."""
    config = GameConfig(
        seed=42,
        points_per_ghost=200,
        frightened_duration=4.0,
        ghost_respawn_delay=1.0,
    )
    gameplay = GhostGameplay.create(_spawns(), config, base_speed=1.0)
    player = Player.from_spawn((3, 3))
    session = GameSession(lives=3)

    for ghost in gameplay.ghosts:
        ghost.position = player.position

    gameplay.activate_frightened()
    eaten = gameplay.resolve_player_collisions(session, player)
    repeated = gameplay.resolve_player_collisions(session, player)

    assert eaten.player_hit is False
    assert eaten.eaten_ghosts == 4
    assert eaten.score_gained == 3000
    assert session.score == 3000
    assert all(
        ghost.state is GhostState.RESPAWNING
        for ghost in gameplay.ghosts
    )
    assert repeated.player_hit is False
    assert repeated.eaten_ghosts == 0
    assert repeated.score_gained == 0

    gameplay.update(
        dt=1.0,
        world=_world(),
        player_position=player.position,
    )
    returned_states: list[GhostState] = [
        ghost.state for ghost in gameplay.ghosts
    ]
    player.position = gameplay.ghosts[0].position

    first_normal_contact = gameplay.resolve_player_collisions(
        session,
        player,
    )
    repeated_normal_contact = gameplay.resolve_player_collisions(
        session,
        player,
    )

    assert returned_states == [GhostState.NORMAL] * 4
    assert first_normal_contact.player_hit is True
    assert repeated_normal_contact.player_hit is False
    assert session.score == 3000
    assert session.lives == 3
