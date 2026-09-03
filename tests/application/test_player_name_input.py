"""Tests for player-name input and highscore-entry validation."""


import pytest

from pacman.application.player_name_input import PlayerNameInput
from pacman.infrastructure.highscore import HighscoreEntry


def test_player_name_input_accepts_supported_characters() -> None:
    """Verify letters, numbers, and spaces form a player name."""
    player_name = PlayerNameInput()

    for character in "Pac Man 01":
        assert player_name.add_character(character)

    assert player_name.value == "Pac Man 01"
    assert player_name.error_message is None


@pytest.mark.parametrize("character", ["!", "_", "-", "ab", ""])
def test_player_name_input_rejects_unsupported_characters(
    character: str,
) -> None:
    """Verify invalid input is ignored and explained."""
    player_name = PlayerNameInput(value="Maria")

    assert not player_name.add_character(character)
    assert player_name.value == "Maria"
    assert player_name.error_message == (
        "Use letters, numbers, and spaces only"
    )


def test_player_name_input_enforces_ten_character_limit() -> None:
    """Verify input beyond ten characters is ignored and explained."""
    player_name = PlayerNameInput(value="Pac Man 01")

    assert not player_name.add_character("X")
    assert player_name.value == "Pac Man 01"
    assert player_name.error_message == (
        "Name can contain up to 10 characters"
    )


def test_player_name_input_backspace_removes_last_character() -> None:
    """Verify Backspace edits the current input safely."""
    player_name = PlayerNameInput(value="Maria", error_message="old error")

    player_name.backspace()

    assert player_name.value == "Mari"
    assert player_name.error_message is None


def test_player_name_input_backspace_handles_empty_value() -> None:
    """Verify Backspace is harmless before any name is entered."""
    player_name = PlayerNameInput()

    player_name.backspace()

    assert player_name.value == ""


@pytest.mark.parametrize("value", ["", "   "])
def test_player_name_input_requires_visible_name(value: str) -> None:
    """Verify an empty or whitespace-only name cannot create an entry."""
    player_name = PlayerNameInput(value=value)

    assert player_name.create_entry(score=500) is None
    assert player_name.error_message == "Enter a player name"


def test_player_name_input_creates_normalized_highscore_entry() -> None:
    """Verify valid input creates an entry using the final score."""
    player_name = PlayerNameInput(value=" Maria ")

    entry = player_name.create_entry(score=1250)

    assert entry == HighscoreEntry(name="Maria", score=1250)
    assert player_name.error_message is None


def test_player_name_input_reset_clears_previous_game_data() -> None:
    """Verify a completed entry cannot leak into the next game."""
    player_name = PlayerNameInput(value="Maria", error_message="old error")

    player_name.reset()

    assert player_name.value == ""
    assert player_name.error_message is None
