"""Generate several complete levels for human visual inspection."""

from pacman.config import GameConfig, LevelConfig
from pacman.level_generator import LevelGenerator
from pacman.maze_preview import render_level_ascii

_PREVIEW_SEEDS = (42, 1337, 2026)


def main() -> None:
    """Print deterministic previews with a symbol legend and metadata."""
    print("Legend: # wall, . pacgum, O super-pacgum, P player, G ghost")
    config = GameConfig(
        seed=_PREVIEW_SEEDS[0],
        levels=[LevelConfig(width=15, height=15)],
    )
    generator = LevelGenerator(config=config)
    for level_index, seed in enumerate(_PREVIEW_SEEDS):
        level = generator.generate_level(level_index, seed=seed)
        print(
            f"\nLevel {level.level_number} | seed {seed} | internal grid "
            f"{level.maze.width}x{level.maze.height} | "
            f"entry {level.maze.entry} | exit {level.maze.exit}"
        )
        print(render_level_ascii(level))


if __name__ == "__main__":
    main()
