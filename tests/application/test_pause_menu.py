"""Application tests for pause-menu navigation behaviour."""

import pytest

from pacman.app import (
    PAUSE_MENU_OPTIONS,
    MenuControls,
    PauseMenu,
    PauseMenuAction,
    PauseMenuOption,
)

UP_KEY = 273
DOWN_KEY = 274
RETURN_KEY = 13
SPACE_KEY = 32


def menu_controls() -> MenuControls:
    """Create deterministic menu controls for tests."""
    return MenuControls(
        up_keys=frozenset({UP_KEY}),
        down_keys=frozenset({DOWN_KEY}),
        confirm_keys=frozenset({RETURN_KEY, SPACE_KEY}),
    )


def test_pause_menu_exposes_required_actions() -> None:
    """Verify the pause menu exposes Resume and Return to Main Menu."""
    assert PAUSE_MENU_OPTIONS == (
        PauseMenuOption("Resume", PauseMenuAction.RESUME),
        PauseMenuOption(
            "Return to Main Menu", PauseMenuAction.RETURN_TO_MAIN_MENU
        ),
    )


def test_pause_menu_starts_with_resume_selected() -> None:
    """Verify the default selection starts on Resume."""
    menu = PauseMenu()

    assert menu.selected_index == 0
    assert menu.selected_option.label == "Resume"
    assert menu.selected_option.action is PauseMenuAction.RESUME


def test_down_key_moves_to_return_to_main_menu() -> None:
    """Verify Down changes the selected option to Return to Main Menu."""
    menu = PauseMenu()

    action = menu.handle_key(DOWN_KEY, menu_controls())

    assert action is None
    assert menu.selected_index == 1
    assert menu.selected_option.label == "Return to Main Menu"
    assert menu.selected_option.action is PauseMenuAction.RETURN_TO_MAIN_MENU


def test_navigation_wraps_at_boundaries() -> None:
    """Verify wrapping when navigating past top and bottom options."""
    menu = PauseMenu()

    menu.handle_key(UP_KEY, menu_controls())
    assert menu.selected_index == 1

    menu.handle_key(DOWN_KEY, menu_controls())
    assert menu.selected_index == 0


@pytest.mark.parametrize("confirm_key", (RETURN_KEY, SPACE_KEY))
def test_confirm_activates_selected_pause_action(confirm_key: int) -> None:
    """Verify confirming triggers the active action."""
    menu = PauseMenu()

    assert menu.handle_key(confirm_key, menu_controls()) is (
        PauseMenuAction.RESUME
    )

    menu.handle_key(DOWN_KEY, menu_controls())
    assert menu.handle_key(confirm_key, menu_controls()) is (
        PauseMenuAction.RETURN_TO_MAIN_MENU
    )


def test_reset_selection_resets_to_first_option() -> None:
    """Verify reset_selection puts cursor back on Resume."""
    menu = PauseMenu()
    menu.handle_key(DOWN_KEY, menu_controls())
    assert menu.selected_index == 1

    menu.reset_selection()
    assert menu.selected_index == 0


def test_empty_options_raise_value_error() -> None:
    """Verify creating a pause menu with no options fails safely."""
    with pytest.raises(ValueError, match="at least one option"):
        PauseMenu(options=())
