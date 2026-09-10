"""Headless simulation harness and invariant validator for soak testing."""

from dataclasses import dataclass
import math

from pacman.application.context import AppContext, GameSession
from pacman.application.state import GameState, GameStateController
from pacman.gameplay.ghost import Ghost, GhostState
from pacman.gameplay.ghost_gameplay import GhostGameplay
from pacman.gameplay.pacgums import collect_pacgum
from pacman.gameplay.player import Direction, Player
from pacman.gameplay.progression import (
    LevelCompletionOutcome,
    handle_level_completion,
)
from pacman.maze.world import WorldMap


class SoakInvariantViolation(AssertionError):
    """Raised when an engine invariant is violated during soak simulation."""


@dataclass
class SoakInvariantChecker:
    """Validate game state invariants on every frame tick."""

    last_score: int = 0
    allow_score_reset_on_new_session: bool = True

    def check(
        self,
        session: GameSession,
        world: WorldMap | None = None,
        player: Player | None = None,
        ghosts: list[Ghost] | None = None,
        ghost_gameplay: GhostGameplay | None = None,
    ) -> None:
        """Assert that all invariant rules hold on the current state."""
        # 1. Session Invariants
        if session.lives < 0:
            raise SoakInvariantViolation(
                f"Negative lives detected: {session.lives}"
            )
        if session.score < 0:
            raise SoakInvariantViolation(
                f"Negative score detected: {session.score}"
            )
        if (
            not self.allow_score_reset_on_new_session
            and session.score < self.last_score
        ):
            raise SoakInvariantViolation(
                f"Score decreased from {self.last_score} to {session.score}"
            )
        self.last_score = session.score

        if not math.isfinite(session.remaining_level_time):
            raise SoakInvariantViolation(
                f"Non-finite remaining_level_time: "
                f"{session.remaining_level_time}"
            )
        if session.remaining_level_time < 0.0:
            raise SoakInvariantViolation(
                f"Negative remaining_level_time: "
                f"{session.remaining_level_time}"
            )

        # 2. Player Invariants
        if player is not None:
            px, py = player.position
            if not (math.isfinite(px) and math.isfinite(py)):
                raise SoakInvariantViolation(
                    f"Non-finite player position: {player.position}"
                )
            if world is not None:
                if not world.contains_world(player.position):
                    raise SoakInvariantViolation(
                        f"Player out of world bounds: {player.position}"
                    )
                tile = world.world_to_tile(player.position)
                if not world.maze.is_corridor(tile):
                    raise SoakInvariantViolation(
                        f"Player in non-corridor tile {tile}: "
                        f"{player.position}"
                    )

        # 3. Ghost Invariants
        if ghosts is not None:
            for ghost in ghosts:
                gx, gy = ghost.position
                if not (math.isfinite(gx) and math.isfinite(gy)):
                    raise SoakInvariantViolation(
                        f"Non-finite ghost {ghost.identity} position: "
                        f"{ghost.position}"
                    )
                if (
                    not math.isfinite(ghost.frightened_timer)
                    or ghost.frightened_timer < 0.0
                ):
                    raise SoakInvariantViolation(
                        f"Invalid frightened_timer on {ghost.identity}: "
                        f"{ghost.frightened_timer}"
                    )
                if (
                    not math.isfinite(ghost.respawn_timer)
                    or ghost.respawn_timer < 0.0
                ):
                    raise SoakInvariantViolation(
                        f"Invalid respawn_timer on {ghost.identity}: "
                        f"{ghost.respawn_timer}"
                    )
                if not isinstance(ghost.state, GhostState):
                    raise SoakInvariantViolation(
                        f"Invalid ghost state on {ghost.identity}: "
                        f"{ghost.state}"
                    )
                if world is not None:
                    if not world.contains_world(ghost.position):
                        raise SoakInvariantViolation(
                            f"Ghost {ghost.identity} out of bounds: "
                            f"{ghost.position}"
                        )
                    gtile = world.world_to_tile(ghost.position)
                    if not world.maze.is_corridor(gtile):
                        raise SoakInvariantViolation(
                            f"Ghost {ghost.identity} inside wall {gtile}: "
                            f"{ghost.position}"
                        )

        # 4. Power State Invariants
        if ghost_gameplay is not None:
            power = ghost_gameplay.power_state
            if (
                not math.isfinite(power.remaining_time)
                or power.remaining_time < 0.0
            ):
                raise SoakInvariantViolation(
                    f"Invalid power_state remaining_time: "
                    f"{power.remaining_time}"
                )
            if power.eaten_ghost_count < 0:
                raise SoakInvariantViolation(
                    f"Negative eaten_ghost_count: {power.eaten_ghost_count}"
                )


@dataclass
class SoakSimulationMetrics:
    """Record metrics captured during soak execution."""

    total_frames: int = 0
    total_simulated_time: float = 0.0
    total_pellets_collected: int = 0
    total_super_pellets_collected: int = 0
    total_ghosts_eaten: int = 0
    total_lives_lost: int = 0
    levels_completed: int = 0


class SoakSimulationHarness:
    """Headless driver for executing multi-frame gameplay simulations."""

    def __init__(
        self,
        context: AppContext,
        controller: GameStateController | None = None,
        invariant_checker: SoakInvariantChecker | None = None,
    ) -> None:
        """Initialize the harness with context, controller, and checker."""
        self.context = context
        self.controller = controller or GameStateController(GameState.PLAYING)
        self.checker = invariant_checker or SoakInvariantChecker()
        self.metrics = SoakSimulationMetrics()
        self.ghost_gameplay: GhostGameplay | None = None
        self._init_ghosts()

    def _init_ghosts(self) -> None:
        """Initialize or re-initialize ghost gameplay for the active level."""
        if (
            self.context.active_level is not None
            and self.context.active_level.spawns is not None
        ):
            self.ghost_gameplay = GhostGameplay.create(
                spawns=self.context.active_level.spawns.ghosts,
                config=self.context.config,
                base_speed=1.0,
            )

    def tick(
        self,
        dt: float = 1.0 / 60.0,
        player_turn: Direction | None = None,
        auto_collect: bool = True,
    ) -> None:
        """Advance simulation by one frame and verify state invariants."""
        session = self.context.session
        level = self.context.active_level
        player = self.context.player

        # Advance level timer if playing and unpaused
        if (
            self.controller.state is GameState.PLAYING
            and not session.is_paused
        ):
            timed_out = session.update_level_timer(dt)
            if timed_out:
                self.controller.end_game(session)

            if level is not None and player is not None:
                # Update player turn buffer
                if player_turn is not None:
                    player.queued_direction = player_turn

                # Move player
                player.update(dt, level.world)

                # Collect pacgums at player position
                if auto_collect and level.pellets is not None:
                    px, py = level.world.world_to_tile(player.position)
                    pellet_pos = (px, py)
                    is_super = pellet_pos in level.pellets.super_pacgums
                    was_normal = pellet_pos in level.pellets.pacgums

                    points = collect_pacgum(
                        player.position,
                        level.pellets,
                        points_per_pacgum=(
                            self.context.config.points_per_pacgum
                        ),
                        points_per_super_pacgum=(
                            self.context.config.points_per_super_pacgum
                        ),
                    )
                    if points > 0:
                        session.score += points
                        if was_normal:
                            self.metrics.total_pellets_collected += 1
                        if is_super:
                            self.metrics.total_super_pellets_collected += 1
                            if self.ghost_gameplay is not None:
                                self.ghost_gameplay.activate_frightened()

                # Update ghosts and handle collisions
                if (
                    self.ghost_gameplay is not None
                    and level.spawns is not None
                ):
                    if not self.context.cheat_mode.ghost_freeze_enabled:
                        self.ghost_gameplay.update(
                            dt=dt,
                            world=level.world,
                            player_position=player.position,
                            player_direction=player.direction,
                        )

                    collision_result = (
                        self.ghost_gameplay.handle_player_collisions(
                            session=session,
                            player=player,
                            player_spawn=level.spawns.player,
                            world=level.world,
                            state_controller=self.controller,
                            player_invincible=(
                                self.context.cheat_mode.invincibility_enabled
                            ),
                        )
                    )
                    if collision_result.collision.eaten_ghosts > 0:
                        self.metrics.total_ghosts_eaten += (
                            collision_result.collision.eaten_ghosts
                        )
                    if collision_result.collision.player_hit:
                        self.metrics.total_lives_lost += 1
                        if session.is_game_over:
                            self.controller.end_game(session)

        # Check invariants
        ghost_list = (
            self.ghost_gameplay.ghosts if self.ghost_gameplay else None
        )
        world = level.world if level is not None else None
        self.checker.check(
            session=session,
            world=world,
            player=player,
            ghosts=ghost_list,
            ghost_gameplay=self.ghost_gameplay,
        )

        self.metrics.total_frames += 1
        self.metrics.total_simulated_time += dt

    def step_n(
        self,
        frames: int,
        dt: float = 1.0 / 60.0,
        player_turn: Direction | None = None,
        auto_collect: bool = True,
    ) -> None:
        """Advance the simulation by N frames."""
        for _ in range(frames):
            self.tick(
                dt=dt,
                player_turn=player_turn,
                auto_collect=auto_collect,
            )

    def advance_to_next_level(self) -> LevelCompletionOutcome:
        """Progress to the next level when current level pellets are clear."""
        if self.context.player is None:
            raise RuntimeError("Cannot advance level without an active player")

        outcome, next_level = handle_level_completion(
            session=self.context.session,
            player=self.context.player,
            level_generator=self.context.level_generator,
            state_controller=self.controller,
        )
        if (
            outcome is LevelCompletionOutcome.ADVANCED
            and next_level is not None
        ):
            self.context.active_level = next_level
            self.metrics.levels_completed += 1
            self._init_ghosts()
        elif outcome is LevelCompletionOutcome.VICTORY:
            self.context.active_level = None
            self.metrics.levels_completed += 1
            self.ghost_gameplay = None
        return outcome
