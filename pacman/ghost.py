"""Ghost state model and state machine definitions."""

from dataclasses import dataclass
from enum import Enum, auto

from pacman.maze_grid import TileCoordinate
from pacman.player import Direction
from pacman.world import WorldMap, WorldPosition


class GhostState(Enum):
    """Explicit behavioral states for a ghost entity."""

    NORMAL = auto()
    FRIGHTENED = auto()
    EATEN = auto()
    RESPAWNING = auto()
    FROZEN = auto()


class GhostIdentity(Enum):
    """Arcade ghost identities with assigned corner spawns."""

    BLINKY = "Blinky"
    PINKY = "Pinky"
    INKY = "Inky"
    CLYDE = "Clyde"


@dataclass
class Ghost:
    """Represent an individual ghost entity and its state machine."""

    identity: GhostIdentity
    home_spawn: TileCoordinate
    position: WorldPosition
    direction: Direction = Direction.NONE
    state: GhostState = GhostState.NORMAL
    previous_state: GhostState | None = None
    target_tile: TileCoordinate | None = None
    frightened_timer: float = 0.0
    respawn_timer: float = 0.0
    speed_multiplier: float = 1.0

    @classmethod
    def from_spawn(
        cls,
        identity: GhostIdentity,
        spawn_tile: TileCoordinate,
        speed_multiplier: float = 1.0,
    ) -> "Ghost":
        """Create a ghost centered at its assigned spawn tile coordinate."""
        x, y = spawn_tile
        return cls(
            identity=identity,
            home_spawn=spawn_tile,
            position=(x + 0.5, y + 0.5),
            direction=Direction.NONE,
            state=GhostState.NORMAL,
            speed_multiplier=speed_multiplier,
        )

    def frighten(self, duration: float = 7.0) -> bool:
        """Transition ghost to FRIGHTENED state if currently eligible."""
        if duration < 0:
            raise ValueError("frightened duration cannot be negative")

        ineligible_states = (
            GhostState.FROZEN,
            GhostState.EATEN,
            GhostState.RESPAWNING,
        )
        if self.state in ineligible_states:
            return False

        self.state = GhostState.FRIGHTENED
        self.frightened_timer = float(duration)
        return True

    def eat(self) -> bool:
        """Transition frightened ghost to EATEN state when caught."""
        if self.state != GhostState.FRIGHTENED:
            return False

        self.state = GhostState.EATEN
        self.frightened_timer = 0.0
        return True

    def start_respawn(self, delay: float = 5.0) -> None:
        """Return ghost to home spawn and transition to RESPAWNING."""
        if delay < 0:
            raise ValueError("respawn delay cannot be negative")

        hx, hy = self.home_spawn
        self.position = (hx + 0.5, hy + 0.5)
        self.direction = Direction.NONE
        self.state = GhostState.RESPAWNING
        self.respawn_timer = float(delay)
        self.frightened_timer = 0.0

    def freeze(self) -> bool:
        """Freeze ghost movement and timers for cheat mode or pause."""
        if self.state == GhostState.FROZEN:
            return False

        self.previous_state = self.state
        self.state = GhostState.FROZEN
        return True

    def unfreeze(self) -> bool:
        """Restore ghost state prior to being frozen."""
        if self.state != GhostState.FROZEN:
            return False

        restored_state = (
            self.previous_state
            if self.previous_state is not None
            else GhostState.NORMAL
        )
        self.state = restored_state
        self.previous_state = None
        return True

    def update(
        self,
        dt: float,
        world: WorldMap | None = None,
        base_speed: float = 4.0,
    ) -> None:
        """Advance ghost timers and perform movement if world is provided."""
        if dt <= 0 or self.state == GhostState.FROZEN:
            return

        if self.state == GhostState.FRIGHTENED:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0.0:
                self.frightened_timer = 0.0
                self.state = GhostState.NORMAL

        elif self.state == GhostState.RESPAWNING:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.respawn_timer = 0.0
                self.state = GhostState.NORMAL

        if world is not None and self.state != GhostState.RESPAWNING:
            self._move(dt, world, base_speed)

    def _move(
        self,
        dt: float,
        world: WorldMap,
        base_speed: float = 4.0,
    ) -> None:
        """Advance ghost position along corridors and align to tile axes."""
        speed = base_speed * self.speed_multiplier
        if self.state == GhostState.FRIGHTENED:
            speed *= 0.5
        elif self.state == GhostState.EATEN:
            speed *= 1.5

        current_tile = world.world_to_tile(self.position)
        legal_dirs = get_legal_ghost_directions(
            tile=current_tile,
            current_direction=self.direction,
            world=world,
            allow_reversal=(self.state == GhostState.FRIGHTENED),
        )

        if (
            self.direction == Direction.NONE
            or self.direction not in legal_dirs
        ):
            if legal_dirs and legal_dirs[0] != Direction.NONE:
                self.direction = legal_dirs[0]

        if self.direction == Direction.NONE:
            return

        dx, dy = self.direction.vector
        new_x = self.position[0] + dx * speed * dt
        new_y = self.position[1] + dy * speed * dt

        if dx != 0:
            new_y = current_tile[1] + 0.5
        elif dy != 0:
            new_x = current_tile[0] + 0.5

        target_position = (new_x, new_y)

        if world.can_occupy(target_position, half_size=(0.35, 0.35)):
            self.position = target_position
        else:
            cx, cy = world.tile_center(current_tile)
            self.position = (cx, cy)
            self.direction = Direction.NONE


def get_legal_ghost_directions(
    tile: TileCoordinate,
    current_direction: Direction,
    world: WorldMap,
    allow_reversal: bool = False,
) -> list[Direction]:
    """Return valid corridor directions for a ghost at a given tile.

    Enforces wall avoidance and classic ghost movement rules:
    - Filters out non-corridor/wall tiles.
    - Prevents 180-degree reversals unless at a dead end or explicitly allowed.
    """
    tx, ty = tile
    cardinal_directions = (
        Direction.UP,
        Direction.DOWN,
        Direction.LEFT,
        Direction.RIGHT,
    )
    walkable_directions: list[Direction] = []

    for direction in cardinal_directions:
        dx, dy = direction.vector
        target_tile = (int(tx + dx), int(ty + dy))
        if world.is_walkable_tile(target_tile):
            walkable_directions.append(direction)

    if not walkable_directions:
        return [Direction.NONE]

    if not allow_reversal and current_direction != Direction.NONE:
        forward_options = [
            d for d in walkable_directions
            if not d.is_opposite(current_direction)
        ]
        if forward_options:
            return forward_options

    return walkable_directions
