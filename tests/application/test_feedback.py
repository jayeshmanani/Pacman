"""Tests for visual feedback manager and state indicators."""

from pacman.application.feedback import (
    FeedbackManager,
    ScorePopup,
    is_frightened_flashing,
)
from tests.support.app_fakes import _FakeFont, _FakeSurface


def test_score_popup_update_and_drift() -> None:
    """Verify popup decreases remaining time and drifts upward."""
    popup = ScorePopup(
        text="+200",
        x=100.0,
        y=150.0,
        remaining_time=1.0,
        drift_speed=20.0,
    )

    is_alive = popup.update(0.5)

    assert is_alive
    assert popup.remaining_time == 0.5
    assert popup.y == 140.0

    is_alive_after_expiry = popup.update(0.6)
    assert not is_alive_after_expiry
    assert popup.remaining_time < 0


def test_feedback_manager_lifecycle_and_pruning() -> None:
    """Verify manager tracks, updates, and prunes expired score popups."""
    manager = FeedbackManager()
    manager.add_score(200, (50, 80), lifetime=1.0)
    manager.add_score(400, (100, 120), lifetime=0.5)

    assert len(manager.popups) == 2
    assert manager.popups[0].text == "+200"
    assert manager.popups[1].text == "+400"

    # Advance 0.6s -> the 0.5s popup should expire and be pruned
    manager.update(0.6)
    assert len(manager.popups) == 1
    assert manager.popups[0].text == "+200"

    # Advance another 0.5s -> remaining popup expires
    manager.update(0.5)
    assert len(manager.popups) == 0


def test_feedback_manager_draw_and_clear() -> None:
    """Verify manager renders popups and clears active list."""
    manager = FeedbackManager()
    manager.add_score(800, (120, 140))

    surface = _FakeSurface()
    font = _FakeFont(size=24)

    manager.draw(surface, font)

    assert "+800" in surface.rendered_texts
    assert len(surface.blit_destinations) == 1

    manager.clear()
    assert len(manager.popups) == 0


def test_is_frightened_flashing_thresholds() -> None:
    """Verify flashing only occurs when timer is below threshold."""
    # Above 2.0s threshold -> should not flash
    assert not is_frightened_flashing(remaining_time=5.0)
    assert not is_frightened_flashing(remaining_time=2.1)

    # Negative or zero time -> should not flash
    assert not is_frightened_flashing(remaining_time=0.0)
    assert not is_frightened_flashing(remaining_time=-1.0)

    # Below 2.0s threshold -> should alternate True/False based on cadence
    # At 4 Hz: 1.9s * 4 = 7 (odd -> True)
    assert is_frightened_flashing(remaining_time=1.9)
    # At 4 Hz: 1.6s * 4 = 6 (even -> False)
    assert not is_frightened_flashing(remaining_time=1.6)
