*This project has been created as part of the 42 curriculum by jmanani, mlagutin.*

# Pacman

A modular Python implementation of Pac-Man developed as part of the 42
curriculum. The current codebase provides configuration and highscore services,
validated maze generation, level construction, pacgum placement, shared world
coordinates, collision queries, core gameplay mechanics including movement,
turn buffering, scoring, lives, timing, pause, and level progression, and an
automated test suite.

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/)
- Git

The assigned `mazegenerator` wheel is included in the repository.

## Installation and usage

```bash
make install
make run
```

The application uses `config.json` by default. The equivalent direct command
is:

```bash
uv run python pac_man.py config.json
```

## Current controls

The current pygame shell supports the application-state controls below:

| Key | Action |
| --- | --- |
| `Enter` / `Space` | Start the playing state or return from the end screen |
| `P` | Pause or resume the active session |
| `E` | Open the placeholder end screen |
| `Esc` | Return from the playing state to the main menu |
| Close window | Quit the application |

The gameplay layer already maps arrow-direction names and `W`, `A`, `S`, `D`
to Pac-Man movement. Live pygame movement input and the complete visual game
flow belong to Phase 6 and are not presented as working UI controls yet.

## Development commands

| Command | Purpose |
| --- | --- |
| `make install` | Install runtime and development dependencies |
| `make run` | Run the application with `config.json` |
| `make debug` | Run the application with the Python debugger |
| `make test` | Run the complete automated test suite |
| `make lint` | Run flake8 and mypy checks |
| `make lint-strict` | Run flake8 and mypy strict mode |
| `make preview-mazes` | Display three generated levels in the terminal |
| `make clean` | Remove Python and test caches |

`make preview-mazes` is a development verification tool, not the final game
interface. It displays walls (`#`), pacgums (`.`), super-pacgums (`O`), the
player spawn (`P`), and ghost spawns (`G`).

## Configuration

The JSON configuration supports:

- highscore storage filename;
- per-level maze width and height;
- initial lives and level time limit;
- first-level seed;
- scoring values for pacgums, super-pacgums, and ghosts.
- frightened-state duration after collecting a super-pacgum.
- ghost respawn delay after a frightened ghost is eaten.

Missing or invalid values use safe defaults, unknown keys are ignored, and
configuration errors are handled without a Python traceback.

## Maze and level generation

`MazeGeneratorAdapter` calls the assigned A-Maze-ing package with
`perfect=False` and converts its native wall bitmasks into one immutable
wall/corridor grid.

The generation flow validates dimensions, boundaries, shared walls, and the
entry-to-exit path. Unreachable corridor islands are normalized as walls, and
package failures are returned as clear application-level errors.

The first level uses a fixed seed and includes the package's central `42` wall
pattern. Later levels use random seeds without the fixed pattern. Generated
levels include valid player and ghost spawns, normal pacgums on reachable
corridors, and four super-pacgums near the maze corners.

## World coordinates and collisions

Gameplay geometry is resolution-independent:

- `TileCoordinate` represents an integer `(column, row)`;
- `WorldPosition` represents a floating-point `(x, y)`;
- one tile occupies one world unit;
- screen pixel scaling is kept outside gameplay calculations.

Each level exposes one `WorldMap` for tile/world conversion, walkability
queries, boundary checks, and axis-aligned wall collision queries.

## Highscores

Highscores are stored as JSON. Missing, empty, corrupted, or invalid files
fall back to an empty list. Player names are limited to ten alphanumeric or
space characters, and scores must be non-negative integers.

Entries are sorted by score, limited to the best ten results, and saved through
a guarded persistence layer.

## Architecture

| Module | Responsibility |
| --- | --- |
| `config.py` | Configuration parsing and defaults |
| `highscore.py`, `storage.py` | Highscore validation and persistence |
| `maze_adapter.py`, `maze_grid.py` | External package boundary and internal grid |
| `level_generator.py` | Reproducible level construction |
| `spawns.py`, `pacgums.py` | Spawn and pacgum placement |
| `world.py` | Shared coordinates, walkability, and collision queries |
| `player.py`, `lives.py`, `power_state.py`, `progression.py` | Core movement, life, power-state, and level-progression rules |
| `context.py` | Shared application services and active session data |
| `application/` | Application state, rendering, pygame contracts, and runtime orchestration |
| `app.py` | Stable public facade for the application package |

## Testing

The suite is grouped by application, gameplay, maze, persistence, and
integration responsibilities. Reusable fakes live in `tests/support`.
Integration tests use the real assigned maze-generator package where
appropriate.

```bash
make test
make lint
make lint-strict
```

## Project management

Project planning, task tracking, and sprint progression are managed using Jira
(issue keys prefix: `PK-`). Features are broken down into dedicated tickets,
developed on Jira-linked feature branches, validated by automated tests, and
merged into `main` through peer review.

Project management documentation, completed phase history, and shared
engineering rules are maintained in the
[project_management](project_management/) directory. Active sprint status and
planning remain in Jira and the progressive planner.

## Resources and AI usage

- [Python documentation](https://docs.python.org/3/)
- [Pygame documentation](https://www.pygame.org/docs/)
- [pytest documentation](https://docs.pytest.org/)
- [mypy documentation](https://mypy.readthedocs.io/)

AI tools supported test design, code review, and identifying edge cases. The
project authors reviewed the suggestions, inspected the changes, and ran the
validation suite.
