"""Power state model for super-pacgum frightened mode."""

from dataclasses import dataclass
from collections.abc import Iterable

from pacman.ghost import Ghost


@dataclass
class PowerState:
    """Track frightened/power mode state duration."""

    remaining_time: float = 0.0
    eaten_ghost_count: int = 0

    @property
    def is_active(self) -> bool:
        """Return True if power mode is currently active."""
        return self.remaining_time > 0.0

    def activate(
        self,
        duration: float = 7.0,
        ghosts: Iterable[Ghost] = (),
    ) -> None:
        """Activate power mode and frighten every eligible active ghost."""
        if duration < 0:
            raise ValueError("duration can not be negative")

        self.remaining_time = float(duration)
        self.eaten_ghost_count = 0
        if self.is_active:
            for ghost in ghosts:
                ghost.frighten(duration)
        else:
            self._recover_ghosts(ghosts)

    def update(self, dt: float, ghosts: Iterable[Ghost] = ()) -> bool:
        """Advance power mode and recover ghosts once when it expires."""
        if dt <= 0:
            return False

        was_active = self.is_active
        self.remaining_time = max(0.0, self.remaining_time - dt)
        expired = was_active and not self.is_active
        if expired:
            self._recover_ghosts(ghosts)
        return expired

    def claim_ghost_score(self, base_score: int) -> int:
        """Return the next doubling ghost score in this power period."""
        if base_score < 0:
            raise ValueError("ghost score cannot be negative")

        multiplier = 1 << self.eaten_ghost_count
        score = base_score * multiplier
        self.eaten_ghost_count += 1
        return score

    @staticmethod
    def _recover_ghosts(ghosts: Iterable[Ghost]) -> None:
        """Remove only current or saved frightened state from a group."""
        for ghost in ghosts:
            ghost.recover_from_frightened()
