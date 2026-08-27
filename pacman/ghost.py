"""Ghost state model and state machine definitions."""

from dataclasses import dataclass
from enum import Enum, auto

from pacman.maze_grid import TileCoordinate
from pacman.player import Direction
from pacman.world import WorldPosition


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

    def update(self, dt: float) -> None:
        """Advance ghost timers and perform automatic state transitions."""
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
