"""Application tests for main-menu navigation behaviour."""

import pytest

from pacman.app import (
    MAIN_MENU_OPTIONS,
    MainMenu,
    MainMenuAction,
    MainMenuOption,
    MenuControls,
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


def test_main_menu_exposes_required_actions() -> None:
    """Verify the main menu exposes all PK-76 actions in order."""
    assert MAIN_MENU_OPTIONS == (
        MainMenuOption("Start Game", MainMenuAction.START_GAME),
        MainMenuOption("View Highscores", MainMenuAction.VIEW_HIGHSCORES),
        MainMenuOption("Instructions", MainMenuAction.INSTRUCTIONS),
        MainMenuOption("Exit", MainMenuAction.EXIT),
    )


def test_main_menu_starts_with_first_option_selected() -> None:
    """Verify the default selection starts on Start Game."""
    menu = MainMenu()

    assert menu.selected_index == 0
    assert menu.selected_option.label == "Start Game"
    assert menu.selected_option.action is MainMenuAction.START_GAME


def test_down_key_moves_to_next_menu_option() -> None:
    """Verify Down changes the selected option."""
    menu = MainMenu()

    action = menu.handle_key(DOWN_KEY, menu_controls())

    assert action is None
    assert menu.selected_index == 1
    assert menu.selected_option.action is MainMenuAction.VIEW_HIGHSCORES


def test_up_key_moves_to_previous_menu_option() -> None:
    """Verify Up changes the selected option."""
    menu = MainMenu()
    menu.handle_key(DOWN_KEY, menu_controls())

    action = menu.handle_key(UP_KEY, menu_controls())

    assert action is None
    assert menu.selected_index == 0
    assert menu.selected_option.action is MainMenuAction.START_GAME


def test_menu_navigation_wraps_at_boundaries() -> None:
    """Verify menu navigation wraps consistently at both ends."""
    menu = MainMenu()

    menu.handle_key(UP_KEY, menu_controls())
    assert menu.selected_index == 3
    assert menu.selected_option.action is MainMenuAction.EXIT

    menu.handle_key(DOWN_KEY, menu_controls())
    assert menu.selected_index == 0
    assert menu.selected_option.label == "Start Game"


@pytest.mark.parametrize(
    ("selected_index", "expected_action"),
    [
        (0, MainMenuAction.START_GAME),
        (1, MainMenuAction.VIEW_HIGHSCORES),
        (2, MainMenuAction.INSTRUCTIONS),
        (3, MainMenuAction.EXIT),
    ],
)
def test_confirm_activates_selected_menu_option(
    selected_index: int,
    expected_action: MainMenuAction,
) -> None:
    """Verify confirm returns the selected option action."""
    menu = MainMenu()
    for _ in range(selected_index):
        menu.handle_key(DOWN_KEY, menu_controls())

    assert menu.handle_key(RETURN_KEY, menu_controls()) is expected_action


def test_space_activates_selected_menu_option() -> None:
    """Verify Space remains a confirm key for menu activation."""
    menu = MainMenu()

    assert menu.handle_key(SPACE_KEY, menu_controls()) is (
        MainMenuAction.START_GAME
    )


def test_unrelated_key_does_not_change_selection_or_activate() -> None:
    """Verify unrelated keys do not affect menu state."""
    menu = MainMenu()

    action = menu.handle_key(999, menu_controls())

    assert action is None
    assert menu.selected_index == 0
    assert menu.selected_option.action is MainMenuAction.START_GAME


def test_repeated_menu_navigation_is_deterministic() -> None:
    """Verify repeated navigation produces a predictable selection."""
    menu = MainMenu()

    for key in (DOWN_KEY, DOWN_KEY, UP_KEY, DOWN_KEY, DOWN_KEY):
        menu.handle_key(key, menu_controls())

    assert menu.selected_index == 3
    assert menu.selected_option.action is MainMenuAction.EXIT


def test_main_menu_requires_options() -> None:
    """Verify a menu cannot be created without selectable options."""
    with pytest.raises(ValueError, match="at least one option"):
        MainMenu(())
