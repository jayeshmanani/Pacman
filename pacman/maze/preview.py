"""Render generated Pacman levels as compact text previews."""


from pacman.maze.level_generator import LevelData
from pacman.maze.grid import Coordinate, Tile


def render_level_ascii(level: LevelData) -> str:
    """Render walls, corridors, spawns, and pacgums for visual review."""
    if level.spawns is None or level.pellets is None:
        raise ValueError("level preview requires spawns and pacgums")

    markers: dict[Coordinate, str] = {
        position: "." for position in level.pellets.pacgums
    }
    markers.update({
        position: "O" for position in level.pellets.super_pacgums
    })
    markers.update({
        position: "G" for position in level.spawns.ghosts.as_tuple()
    })
    markers[level.spawns.player] = "P"

    rows: list[str] = []
    for y, row in enumerate(level.maze.tiles):
        rows.append("".join(
            "#" if tile is Tile.WALL else markers.get((x, y), " ")
            for x, tile in enumerate(row)
        ))
    return "\n".join(rows)
