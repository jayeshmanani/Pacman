"""Cheat-mode activation state and keyboard control mapping."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CheatControls:
    """Map activation and individual cheat actions to keyboard keys."""

    toggle_key: int
    invincibility_key: int
    level_skip_key: int
    ghost_freeze_key: int
    extra_life_key: int
    speed_boost_key: int


@dataclass
class CheatMode:
    """Track whether evaluation cheats are currently available."""

    enabled: bool = False

    def toggle(self) -> bool:
        """Toggle cheat mode and return its new activation state."""
        self.enabled = not self.enabled
        return self.enabled

    def reset(self) -> None:
        """Disable cheat mode for a clean gameplay session."""
        self.enabled = False
