"""Coordinate completed-game name entry and highscore saving."""


from pacman.application.context import AppContext
from pacman.application.state import GameState, GameStateController


def handle_completed_game_input(
    key: int,
    character: str,
    backspace_key: int,
    submit_key: int,
    controller: GameStateController,
    context: AppContext,
) -> bool:
    """Handle one name-entry key for either completed-game state."""
    if controller.state not in (GameState.GAME_OVER, GameState.VICTORY):
        return False

    if key == backspace_key:
        context.player_name_input.backspace()
    elif key == submit_key:
        if context.save_completed_game_score():
            context.reset_session()
            controller.return_to_main_menu(context.session)
    elif character:
        context.player_name_input.add_character(character)

    return True
