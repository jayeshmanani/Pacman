"""Highscore data model and validation."""


from dataclasses import dataclass


@dataclass(frozen=True)
class HighscoreEntry:
    """Represent one validated player highscore entry."""

    name: str
    score: int

    def __post_init__(self) -> None:
        """Validate the player name and score."""
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if len(self.name) > 10:
            raise ValueError("name must be no longer than 10 characters")
        if not all(
            character.isalnum() or character == " "
            for character in self.name
        ):
            raise ValueError(
                "name must contain only letters, numbers, and spaces"
            )

        if type(self.score) is not int:
            raise TypeError("score must be an integer")
        if self.score < 0:
            raise ValueError("score must be non-negative")
