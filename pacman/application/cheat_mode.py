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
    invincibility_enabled: bool = False
    ghost_freeze_enabled: bool = False
    speed_boost_enabled: bool = False

    def toggle(self) -> bool:
        """Toggle cheat mode and return its new activation state."""
        self.enabled = not self.enabled
        if not self.enabled:
            self._clear_active_cheats()
        return self.enabled

    def toggle_invincibility(self) -> bool:
        """Toggle invincibility when cheat mode is available."""
        if not self.enabled:
            return False
        self.invincibility_enabled = not self.invincibility_enabled
        return self.invincibility_enabled

    def toggle_ghost_freeze(self) -> bool:
        """Toggle ghost freeze when cheat mode is available."""
        if not self.enabled:
            return False
        self.ghost_freeze_enabled = not self.ghost_freeze_enabled
        return self.ghost_freeze_enabled

    def toggle_speed_boost(self) -> bool:
        """Toggle player speed boost when cheat mode is available."""
        if not self.enabled:
            return False
        self.speed_boost_enabled = not self.speed_boost_enabled
        return self.speed_boost_enabled

    def reset(self) -> None:
        """Disable cheat mode for a clean gameplay session."""
        self.enabled = False
        self._clear_active_cheats()

    def _clear_active_cheats(self) -> None:
        """Clear individual effects when evaluation mode is disabled."""
        self.invincibility_enabled = False
        self.ghost_freeze_enabled = False
        self.speed_boost_enabled = False


def handle_cheat_key(
    key: int,
    controls: CheatControls,
    cheat_mode: CheatMode,
) -> bool:
    """Apply one supported cheat key and report whether it was handled."""
    if key == controls.toggle_key:
        cheat_mode.toggle()
        return True

    if not cheat_mode.enabled:
        return False

    if key == controls.invincibility_key:
        cheat_mode.toggle_invincibility()
        return True
    if key == controls.ghost_freeze_key:
        cheat_mode.toggle_ghost_freeze()
        return True
    return False
