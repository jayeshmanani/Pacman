"""Power state model for super-pacgum frightened mode."""

from dataclasses import dataclass


@dataclass
class PowerState:
    """Track frightened/power mode state duration."""

    remaining_time: float = 0.0

    @property
    def is_active(self) -> bool:
        """Return True if power mode is currently active."""
        return self.remaining_time > 0.0

    def activate(self, duration: float = 7.0) -> None:
        """Activate or reset the power mode duration."""
        if duration < 0:
            raise ValueError("duration can not be negative")

        self.remaining_time = float(duration)

    def update(self, dt: float) -> None:
        """Advance the power mode timer by delta time in seconds."""
        if dt <= 0:
            return
        self.remaining_time = max(0.0, self.remaining_time - dt)
