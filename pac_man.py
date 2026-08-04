"""Launch the Pacman graphical application."""

import json
import sys
from pathlib import Path
from typing import Any, cast

from pacman.app import run_app
from pacman.config import GameConfig, parse_game_config


def load_commented_json(filepath: Path) -> dict[str, Any]:
    """Read a JSON file while ignoring lines starting with '#' comments."""
    clean_lines = []
    with filepath.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped.startswith("#"):
                clean_lines.append(line)
    result = cast(dict[str, Any], json.loads("".join(clean_lines)))
    return result


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

    _ = game_config
    run_app()


if __name__ == "__main__":
    main()
