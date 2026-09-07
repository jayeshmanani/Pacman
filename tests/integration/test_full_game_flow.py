"""End-to-end integration tests for complete menu-to-game-to-score flows."""

import json
from pathlib import Path

from pacman.app import run_app
from pacman.infrastructure.config import GameConfig
from tests.support.app_fakes import _FakeEvent, _FakePygame


def _type_string_events(text: str) -> list[list[_FakeEvent]]:
    """Generate fake Pygame keydown event batches for each character."""
    return [
        [_FakeEvent(
            type=_FakePygame.KEYDOWN,
            key=ord(character),
            unicode=character,
        )]
        for character in text
    ]


def test_full_lose_journey_from_menu_to_game_over_to_highscores(
    tmp_path: Path,
) -> None:
    """Verify complete Lose flow from main menu through highscore display."""
    score_file = tmp_path / "scores.json"
    name_events = _type_string_events("ALICE")
    events: list[list[_FakeEvent]] = [
        # Frame 1: Main Menu -> Start Game
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 2: Playing -> Game Over (via E)
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_e)],
        # Frames 3-7: Game Over -> Type "ALICE"
        *name_events,
        # Frame 8: Game Over -> Submit name
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 9: Main Menu -> Navigate down to View Highscores
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        # Frame 10: Main Menu -> Select View Highscores
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 11: Highscores Screen -> Return to Main Menu
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        # Frame 12: Main Menu -> Exit application
        [_FakeEvent(type=_FakePygame.QUIT)],
    ]
    pygame = _FakePygame(events)

    run_app(
        pygame_module=pygame,
        config=GameConfig(highscore_filename=str(score_file)),
    )

    assert "GAME OVER" in pygame.surface.rendered_texts
    assert "HIGHSCORES" in pygame.surface.rendered_texts
    assert "ALICE" in pygame.surface.rendered_texts

    saved = json.loads(score_file.read_text(encoding="utf-8"))
    assert saved == [{"name": "ALICE", "score": 0}]

    assert pygame.display.captions[-3:] == [
        "Pacman - Highscores",
        "Pacman - Main Menu",
        "Pacman - Main Menu",
    ]


def test_full_win_journey_from_menu_to_victory_to_highscores(
    tmp_path: Path,
) -> None:
    """Verify complete Win flow from main menu through highscore display."""
    score_file = tmp_path / "scores.json"
    name_events = _type_string_events("CHAMP")
    events: list[list[_FakeEvent]] = [
        # Frame 1: Main Menu -> Start Game
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 2: Playing -> Victory (via V)
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_v)],
        # Frames 3-7: Victory Screen -> Type "CHAMP"
        *name_events,
        # Frame 8: Victory Screen -> Submit name
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 9: Main Menu -> Navigate down to View Highscores
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        # Frame 10: Main Menu -> Select View Highscores
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 11: Highscores Screen -> Return to Main Menu
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        # Frame 12: Main Menu -> Exit application
        [_FakeEvent(type=_FakePygame.QUIT)],
    ]
    pygame = _FakePygame(events)

    run_app(
        pygame_module=pygame,
        config=GameConfig(highscore_filename=str(score_file)),
    )

    assert "VICTORY!" in pygame.surface.rendered_texts
    assert "HIGHSCORES" in pygame.surface.rendered_texts
    assert "CHAMP" in pygame.surface.rendered_texts

    saved = json.loads(score_file.read_text(encoding="utf-8"))
    assert saved == [{"name": "CHAMP", "score": 0}]

    assert pygame.display.captions[-3:] == [
        "Pacman - Highscores",
        "Pacman - Main Menu",
        "Pacman - Main Menu",
    ]


def test_end_screen_escape_cancels_without_persisting_score(
    tmp_path: Path,
) -> None:
    """Verify Escape on end screen returns to menu without saving highscore."""
    score_file = tmp_path / "scores.json"
    name_events = _type_string_events("GHOST")
    events: list[list[_FakeEvent]] = [
        # Frame 1: Main Menu -> Start Game
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 2: Playing -> Game Over
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_e)],
        # Frames 3-7: Game Over -> Type "GHOST"
        *name_events,
        # Frame 8: Game Over -> Press Escape to cancel
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        # Frame 9: Main Menu -> Navigate down to View Highscores
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        # Frame 10: Main Menu -> Select View Highscores
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Frame 11: Highscores Screen -> Return to Main Menu
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        # Frame 12: Main Menu -> Exit
        [_FakeEvent(type=_FakePygame.QUIT)],
    ]
    pygame = _FakePygame(events)

    run_app(
        pygame_module=pygame,
        config=GameConfig(highscore_filename=str(score_file)),
    )

    assert "No highscores yet" in pygame.surface.rendered_texts
    assert not score_file.exists()
    assert pygame.display.captions[-1] == "Pacman - Main Menu"


def test_consecutive_playthroughs_isolate_session_state(
    tmp_path: Path,
) -> None:
    """Verify playing consecutive games resets session data cleanly."""
    score_file = tmp_path / "scores.json"
    p1_events = _type_string_events("PONE")
    p2_events = _type_string_events("PTWO")

    events: list[list[_FakeEvent]] = [
        # Game 1: Start -> Lose -> Type PONE -> Save -> Menu
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_e)],
        *p1_events,
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Game 2: Start -> Win -> Type PTWO -> Save -> Menu
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_v)],
        *p2_events,
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        # Open Highscores to verify both entries
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ]
    pygame = _FakePygame(events)

    run_app(
        pygame_module=pygame,
        config=GameConfig(highscore_filename=str(score_file)),
    )

    saved = json.loads(score_file.read_text(encoding="utf-8"))
    saved_names = [entry["name"] for entry in saved]
    assert "PONE" in saved_names
    assert "PTWO" in saved_names
    assert len(saved) == 2
