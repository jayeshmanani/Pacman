"""Player-name input state for end-of-game highscore entry."""


from dataclasses import dataclass
from typing import Final

from pacman.infrastructure.highscore import HighscoreEntry


MAX_PLAYER_NAME_LENGTH: Final = 10


@dataclass
class PlayerNameInput:
    """Collect and validate one player name without depending on pygame."""

    value: str = ""
    error_message: str | None = None

    def add_character(self, character: str) -> bool:
        """Append one allowed character when the name has space for it."""
        if len(character) != 1 or not (
            character.isalnum() or character == " "
        ):
            self.error_message = "Use letters, numbers, and spaces only"
            return False

        if len(self.value) >= MAX_PLAYER_NAME_LENGTH:
            self.error_message = "Name can contain up to 10 characters"
            return False

        self.value += character
        self.error_message = None
        return True

    def backspace(self) -> None:
        """Remove the final entered character when one exists."""
        self.value = self.value[:-1]
        self.error_message = None

    def create_entry(self, score: int) -> HighscoreEntry | None:
        """Return a validated entry, or retain an actionable name error."""
        normalized_name = self.value.strip()
        if not normalized_name:
            self.error_message = "Enter a player name"
            return None

        self.error_message = None
        return HighscoreEntry(name=normalized_name, score=score)

    def reset(self) -> None:
        """Clear input and validation state for another completed game."""
        self.value = ""
        self.error_message = None
