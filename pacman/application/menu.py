"""Main-menu option model and keyboard navigation."""

from dataclasses import dataclass
from enum import Enum
from typing import Final, Generic, Protocol, TypeVar


class MainMenuAction(Enum):
    """Actions available from the main menu."""

    START_GAME = "start_game"
    VIEW_HIGHSCORES = "view_highscores"
    INSTRUCTIONS = "instructions"
    EXIT = "exit"


@dataclass(frozen=True)
class MainMenuOption:
    """Describe a selectable main-menu option."""

    label: str
    action: MainMenuAction


class PauseMenuAction(Enum):
    """Actions available from the pause menu."""

    RESUME = "resume"
    RETURN_TO_MAIN_MENU = "return_to_main_menu"


@dataclass(frozen=True)
class PauseMenuOption:
    """Describe a selectable pause-menu option."""

    label: str
    action: PauseMenuAction


@dataclass(frozen=True)
class MenuControls:
    """Keyboard controls for menu navigation."""

    up_keys: frozenset[int]
    down_keys: frozenset[int]
    confirm_keys: frozenset[int]


MAIN_MENU_OPTIONS: Final[tuple[MainMenuOption, ...]] = (
    MainMenuOption("Start Game", MainMenuAction.START_GAME),
    MainMenuOption("View Highscores", MainMenuAction.VIEW_HIGHSCORES),
    MainMenuOption("Instructions", MainMenuAction.INSTRUCTIONS),
    MainMenuOption("Exit", MainMenuAction.EXIT),
)

PAUSE_MENU_OPTIONS: Final[tuple[PauseMenuOption, ...]] = (
    PauseMenuOption("Resume", PauseMenuAction.RESUME),
    PauseMenuOption(
        "Return to Main Menu", PauseMenuAction.RETURN_TO_MAIN_MENU
    ),
)

ActionT = TypeVar("ActionT", covariant=True)


class MenuOption(Protocol[ActionT]):
    """Protocol for any menu option carrying a label and an action."""

    @property
    def label(self) -> str:
        """Return the display label for the option."""
        ...

    @property
    def action(self) -> ActionT:
        """Return the action triggered by this option."""
        ...


OptionT = TypeVar("OptionT", bound=MenuOption[object])


class BaseMenu(Generic[OptionT, ActionT]):
    """Generic base menu tracking selection and keyboard navigation."""

    def __init__(self, options: tuple[OptionT, ...]) -> None:
        """Initialize the menu with the first option selected."""
        if not options:
            raise ValueError("menu requires at least one option")
        self._options = options
        self._selected_index = 0

    @property
    def options(self) -> tuple[OptionT, ...]:
        """Return all available menu options."""
        return self._options

    @property
    def selected_index(self) -> int:
        """Return the currently selected menu option index."""
        return self._selected_index

    @property
    def selected_option(self) -> OptionT:
        """Return the currently selected menu option."""
        return self._options[self._selected_index]

    def reset_selection(self) -> None:
        """Reset the menu selection to the first option."""
        self._selected_index = 0

    def move_previous(self) -> None:
        """Move selection to the previous option, wrapping at the top."""
        self._selected_index = (
            self._selected_index - 1
        ) % len(self._options)

    def move_next(self) -> None:
        """Move selection to the next option, wrapping at the bottom."""
        self._selected_index = (
            self._selected_index + 1
        ) % len(self._options)

    def activate(self) -> ActionT:
        """Return the action for the currently selected option."""
        return self.selected_option.action  # type: ignore[return-value]

    def handle_key(
        self,
        key: int,
        controls: MenuControls,
    ) -> ActionT | None:
        """Apply menu navigation for a key and return an action if selected."""
        if key in controls.up_keys:
            self.move_previous()
            return None

        if key in controls.down_keys:
            self.move_next()
            return None

        if key in controls.confirm_keys:
            return self.activate()

        return None


class MainMenu(BaseMenu[MainMenuOption, MainMenuAction]):
    """Track main-menu selection and translate keys into menu actions."""

    def __init__(
        self,
        options: tuple[MainMenuOption, ...] = MAIN_MENU_OPTIONS,
    ) -> None:
        """Initialize the main menu with the first option selected."""
        super().__init__(options)


class PauseMenu(BaseMenu[PauseMenuOption, PauseMenuAction]):
    """Track pause-menu selection and translate keys into pause actions."""

    def __init__(
        self,
        options: tuple[PauseMenuOption, ...] = PAUSE_MENU_OPTIONS,
    ) -> None:
        """Initialize the pause menu with the first option selected."""
        super().__init__(options)
