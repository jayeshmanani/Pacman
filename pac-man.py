#!/usr/bin/env python3
"""Launch the Pacman graphical application."""

from pathlib import Path
import sys

from pacman.app import run_app
from pacman.infrastructure.config import (
    GameConfig,
    load_commented_json,
    parse_game_config,
)


def main() -> None:
    """Run the Pacman application."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>", file=sys.stderr)
        sys.exit(1)
    config_path = Path(sys.argv[1])
    if config_path.suffix.lower() != ".json":
        print(
            f"Error: '{config_path}' must be a .json file.", file=sys.stderr
        )
        sys.exit(1)
    if not config_path.exists():
        print(
            f"Error: Config file '{config_path}' not found.", file=sys.stderr
        )
        sys.exit(1)

    game_config = GameConfig()
    try:
        data = load_commented_json(config_path)
        game_config = parse_game_config(data)
    except Exception as err:
        print(
            f"Warning: Failed to parse '{config_path}' ({err}). "
            "Using default settings.",
            file=sys.stderr,
        )

    try:
        run_app(config=game_config)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
