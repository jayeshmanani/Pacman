"""Coordinate ghost movement, power state, and collision rules."""

from collections.abc import Iterable
from dataclasses import dataclass, field
import random

from pacman.application.state import GameStateController
from pacman.config import GameConfig
from pacman.context import GameSession
from pacman.ghost import Ghost, GhostIdentity, create_ghost_group
from pacman.ghost_collision import (
    GhostCollisionFrameResult,
    GhostCollisionGuard,
    find_colliding_ghosts,
    resolve_ghost_collisions,
)
from pacman.lives import PlayerDeathOutcome, handle_normal_ghost_collision
from pacman.maze_grid import TileCoordinate
from pacman.player import Direction, Player
from pacman.power_state import PowerState
from pacman.spawns import GhostSpawns
from pacman.world import WorldMap, WorldPosition


@dataclass(frozen=True)
class GhostGameplayCollisionResult:
    """Combine ghost collision effects with optional player death handling."""

    collision: GhostCollisionFrameResult
    player_death: PlayerDeathOutcome | None = None


@dataclass
class GhostGameplay:
    """Own and update the complete four-ghost gameplay system."""

    ghosts: list[Ghost]
    frightened_duration: float = 7.0
    points_per_ghost: int = 200
    respawn_delay: float = 5.0
    base_speed: float = 4.0
    power_state: PowerState = field(default_factory=PowerState)
    collision_guard: GhostCollisionGuard = field(
        default_factory=GhostCollisionGuard
    )
    rng: random.Random = field(default_factory=random.Random)

    @classmethod
    def create(
        cls,
        spawns: GhostSpawns,
        config: GameConfig,
        base_speed: float = 4.0,
    ) -> "GhostGameplay":
        """Create all four ghosts using shared gameplay configuration."""
        return cls(
            ghosts=create_ghost_group(spawns),
            frightened_duration=config.frightened_duration,
            points_per_ghost=config.points_per_ghost,
            respawn_delay=config.ghost_respawn_delay,
            base_speed=base_speed,
            rng=random.Random(config.seed),
        )

    def activate_frightened(self) -> None:
        """Start or reset frightened mode for every eligible ghost."""
        self.power_state.activate(self.frightened_duration, self.ghosts)

    def update(
        self,
        dt: float,
        world: WorldMap,
        player_position: WorldPosition,
        player_direction: Direction = Direction.NONE,
    ) -> None:
        """Advance shared timing and all four ghost behaviours once."""
        self.power_state.update(dt, self.ghosts)
        blinky_tile = self._blinky_tile(world)

        for ghost in self.ghosts:
            ghost.update(
                dt=dt,
                world=world,
                base_speed=self.base_speed,
                rng=self.rng,
                player_position=player_position,
                player_direction=player_direction,
                blinky_tile=blinky_tile,
            )

    def resolve_collisions(
        self,
        session: GameSession,
        colliding_ghosts: Iterable[Ghost],
    ) -> GhostCollisionFrameResult:
        """Resolve one frame of player contact using shared settings."""
        return resolve_ghost_collisions(
            session=session,
            ghosts=colliding_ghosts,
            power_state=self.power_state,
            points_per_ghost=self.points_per_ghost,
            respawn_delay=self.respawn_delay,
            guard=self.collision_guard,
        )

    def resolve_player_collisions(
        self,
        session: GameSession,
        player: Player,
    ) -> GhostCollisionFrameResult:
        """Detect and resolve every ghost touching the player this frame."""
        colliding_ghosts = find_colliding_ghosts(player, self.ghosts)
        return self.resolve_collisions(session, colliding_ghosts)

    def handle_player_collisions(
        self,
        session: GameSession,
        player: Player,
        player_spawn: TileCoordinate,
        world: WorldMap,
        state_controller: GameStateController,
    ) -> GhostGameplayCollisionResult:
        """Resolve ghost contact and apply one normal-ghost player death."""
        collision = self.resolve_player_collisions(session, player)
        if not collision.player_hit:
            return GhostGameplayCollisionResult(collision=collision)

        player_death = handle_normal_ghost_collision(
            session=session,
            player=player,
            spawn_tile=player_spawn,
            world=world,
            state_controller=state_controller,
        )
        return GhostGameplayCollisionResult(
            collision=collision,
            player_death=player_death,
        )

    def _blinky_tile(self, world: WorldMap) -> tuple[int, int] | None:
        """Return Blinky's current tile for Inky's chase calculation."""
        for ghost in self.ghosts:
            if ghost.identity is GhostIdentity.BLINKY:
                return world.world_to_tile(ghost.position)
        return None
