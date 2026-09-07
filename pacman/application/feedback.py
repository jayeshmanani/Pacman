"""Visual feedback systems including floating score popups and state cues."""

from dataclasses import dataclass, field
from typing import Final

from pacman.application.contracts import Color, Coordinate, Font, Surface


POPUP_DEFAULT_COLOR: Final[Color] = (0, 255, 255)
DEFAULT_DRIFT_SPEED: Final[float] = 18.0


@dataclass
class ScorePopup:
    """Transient floating score text displaying awarded points."""

    text: str
    x: float
    y: float
    remaining_time: float = 1.0
    color: Color = POPUP_DEFAULT_COLOR
    drift_speed: float = DEFAULT_DRIFT_SPEED

    def update(self, dt: float) -> bool:
        """Advance time, drift up, and return whether popup remains active."""
        self.remaining_time -= dt
        self.y -= self.drift_speed * dt
        return self.remaining_time > 0


@dataclass
class FeedbackManager:
    """Manage active in-game floating score notifications."""

    popups: list[ScorePopup] = field(default_factory=list)

    def add_score(
        self,
        score: int,
        position: Coordinate,
        color: Color = POPUP_DEFAULT_COLOR,
        lifetime: float = 1.0,
    ) -> None:
        """Create a new floating score popup at the given screen coordinate."""
        px, py = position
        self.popups.append(
            ScorePopup(
                text=f"+{score}" if score > 0 else str(score),
                x=float(px),
                y=float(py),
                remaining_time=lifetime,
                color=color,
            )
        )

    def update(self, dt: float) -> None:
        """Update lifetimes and remove expired score popups."""
        self.popups = [popup for popup in self.popups if popup.update(dt)]

    def draw(self, surface: Surface, font: Font) -> None:
        """Render all active score popups to the surface."""
        for popup in self.popups:
            rendered = font.render(popup.text, True, popup.color)
            rect = rendered.get_rect(center=(int(popup.x), int(popup.y)))
            surface.blit(rendered, rect)

    def clear(self) -> None:
        """Remove all active popups."""
        self.popups.clear()


def is_frightened_flashing(
    remaining_time: float,
    threshold: float = 2.0,
    frequency_hz: float = 4.0,
) -> bool:
    """Return whether ghosts should flash white as frightened mode expires."""
    if remaining_time <= 0 or remaining_time > threshold:
        return False
    cycle = int(remaining_time * frequency_hz)
    return cycle % 2 == 1
