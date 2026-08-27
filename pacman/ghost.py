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
