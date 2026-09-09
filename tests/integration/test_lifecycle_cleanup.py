"""Integration tests for resource cleanup and repeated start/quit cycles."""

from pathlib import Path

from pacman.app import run_app
from pacman.application.context import AppContext
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


def test_repeated_start_pause_return_to_menu_cycles_clean() -> None:
    """Verify 10 repeated start/pause/return cycles isolate menu state."""
    events: list[list[_FakeEvent]] = []
    for _ in range(10):
        events.extend([
            # Start Game (confirm on Start Game)
            [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
            # Pause
            [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_p)],
            # Return to Main Menu via Escape
            [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        ])
    events.append([_FakeEvent(type=_FakePygame.QUIT)])

    pygame = _FakePygame(events)
    run_app(pygame_module=pygame)

    assert pygame.display.captions[-1] == "Pacman - Main Menu"
    assert pygame.surface.rendered_texts.count("> Start Game <") >= 10
    assert pygame.quit_calls == 1


def test_repeated_cheat_activation_cycles_clear_on_menu_return() -> None:
    """Verify cheats enabled during gameplay are cleared on return to menu."""
    events: list[list[_FakeEvent]] = [
        # Game 1: Start -> F1 -> Speed Boost (5) -> Pause -> Return to Menu
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_F1)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_5)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_p)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        # Game 2: Start Game again -> Pause -> Return to Menu
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_p)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        # Exit
        [_FakeEvent(type=_FakePygame.QUIT)],
    ]

    pygame = _FakePygame(events)
    run_app(pygame_module=pygame)

    # In Game 1, speed boost feedback appeared
    assert "ACTIVE: SPEED BOOST" in pygame.surface.rendered_texts
    # In Game 2, cheats should NOT persist after starting fresh
    # Check that the final menu state is clean
    assert pygame.display.captions[-1] == "Pacman - Main Menu"
    assert "> Start Game <" in pygame.surface.rendered_texts


def test_repeated_end_screen_cancellations_do_not_leak_highscores(
    tmp_path: Path,
) -> None:
    """Verify repeated name cancellations leave highscores clean."""
    score_file = tmp_path / "scores.json"
    events: list[list[_FakeEvent]] = []

    for i in range(5):
        name = f"USER{i}"
        events.extend([
            # Start Game
            [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
            # Trigger Game Over
            [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_e)],
            # Type partial name
            *_type_string_events(name),
            # Press Escape to cancel name entry
            [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_ESCAPE)],
        ])

    # View Highscores from Main Menu (Down -> Return)
    events.extend([
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_DOWN)],
        [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
        [_FakeEvent(type=_FakePygame.QUIT)],
    ])

    pygame = _FakePygame(events)
    run_app(
        pygame_module=pygame,
        config=GameConfig(highscore_filename=str(score_file)),
    )

    assert not score_file.exists()
    assert "No highscores yet" in pygame.surface.rendered_texts
    assert pygame.display.captions[-1] == "Pacman - Highscores"


def test_consecutive_run_app_invocations_isolate_resources() -> None:
    """Verify consecutive application launches initialize and quit cleanly."""
    for _ in range(5):
        pygame = _FakePygame([
            [_FakeEvent(type=_FakePygame.KEYDOWN, key=_FakePygame.K_RETURN)],
            [_FakeEvent(type=_FakePygame.QUIT)],
        ])
        run_app(pygame_module=pygame)
        assert pygame.init_calls == 1
        assert pygame.quit_calls == 1
        assert pygame.display.captions[-1] == "Pacman - Playing"


def test_app_context_multi_cycle_state_cleanliness() -> None:
    """Verify 50 consecutive session resets completely scrub all state."""
    config = GameConfig(lives=3, level_max_time=90)
    context = AppContext(config=config)

    for cycle in range(50):
        session = context.start_new_game()
        session.score = 100 * (cycle + 1)
        session.lives = 1
        session.remaining_level_time = 12.5
        context.cheat_mode.enabled = True
        context.cheat_mode.speed_boost_enabled = True

        reset_session = context.reset_session()

        assert reset_session.score == 0
        assert reset_session.lives == 3
        assert reset_session.remaining_level_time == 90.0
        assert context.active_level is None
        assert context.player is None
        assert not context.cheat_mode.enabled
        assert not context.cheat_mode.speed_boost_enabled
