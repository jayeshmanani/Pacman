"""Ghost state model and state machine definitions."""

from enum import Enum, auto


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
