"""Connect input and one-frame updates to the existing gameplay rules."""

from dataclasses import dataclass

from pacman.application.context import AppContext
from pacman.application.state import GameStateController
from pacman.gameplay.pacgums import collect_pacgum
from pacman.gameplay.player import Direction
from pacman.gameplay.progression import (
    LevelCompletionOutcome,
    handle_level_completion,
)


@dataclass(frozen=True)
class GameplayControls:
    """Map pygame keys to the four player movement directions."""

    up_keys: frozenset[int]
    down_keys: frozenset[int]
    left_keys: frozenset[int]
    right_keys: frozenset[int]

    def direction_for_key(self, key: int) -> Direction | None:
        """Return the direction assigned to a key, when supported."""
        if key in self.up_keys:
            return Direction.UP
        if key in self.down_keys:
            return Direction.DOWN
        if key in self.left_keys:
            return Direction.LEFT
        if key in self.right_keys:
            return Direction.RIGHT
        return None


def queue_player_direction(
    key: int,
    controls: GameplayControls,
    context: AppContext,
) -> bool:
    """Queue one supported turn without coupling Player to pygame keys."""
    direction = controls.direction_for_key(key)
    if direction is None or context.player is None:
        return False
    context.player.queued_direction = direction
    return True


def update_gameplay_frame(
    context: AppContext,
    controller: GameStateController,
    dt: float,
) -> None:
    """Advance the complete live gameplay pipeline by one frame."""
    level = context.active_level
    player = context.player
    ghost_gameplay = context.ghost_gameplay
    if (
        level is None
        or level.spawns is None
        or player is None
        or ghost_gameplay is None
    ):
        return

    player.update(dt, level.world)
    if level.pellets is not None:
        context.session.score += collect_pacgum(
            player.position,
            level.pellets,
            points_per_pacgum=context.config.points_per_pacgum,
            points_per_super_pacgum=(
                context.config.points_per_super_pacgum
            ),
            power_state=ghost_gameplay.power_state,
            frightened_duration=context.config.frightened_duration,
            ghosts=ghost_gameplay.ghosts,
        )

    ghost_gameplay.set_ghosts_frozen(
        context.cheat_mode.enabled
        and context.cheat_mode.ghost_freeze_enabled
    )
    ghost_gameplay.update(
        dt,
        level.world,
        player.position,
        player.direction,
    )
    ghost_gameplay.handle_player_collisions(
        context.session,
        player,
        level.spawns.player,
        level.world,
        controller,
        player_invincible=(
            context.cheat_mode.enabled
            and context.cheat_mode.invincibility_enabled
        ),
    )
    if context.session.is_game_over:
        return

    if level.pellets is not None and level.pellets.is_complete:
        outcome, next_level = handle_level_completion(
            context.session,
            player,
            context.level_generator,
            controller,
        )
        if outcome is LevelCompletionOutcome.ADVANCED:
            if next_level is not None:
                context.activate_level(next_level, respawn_player=False)
