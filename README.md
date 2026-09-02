*This project has been created as part of the 42 curriculum by jmanani, mlagutin.*

# Pacman

## Description

A modular, object-oriented recreation of the classic arcade game Pac-Man developed in Python 3.10+ as part of the 42 curriculum. The project combines modern Python development practices (`uv`, strict typing with `mypy`, `flake8` compliance) with authentic arcade game logic, integrating an external maze generation package, autonomous ghost AI behaviors, persistent highscores, and a fault-tolerant configuration system.

The current implementation provides:
- Validated maze generation with reachable corridor normalization.
- Full player mechanics: four-directional grid movement, buffered turning, and wall collision.
- Pellet systems: normal pacgums and corner super-pacgums (power pellets).
- Complete four-ghost autonomous AI: distinct chase targeting for Blinky, Pinky, Inky, and Clyde; frightened fleeing; score chaining; delayed corner respawn; and frame contact protection.
- Session lifecycle: scoring, lives, level timers, pause/resume, and multi-level progression.
- Robust commented-JSON configuration parsing and persistent highscores.
- Automated testing with 245 test cases and headless playtest verification.

## Instructions

### Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/)
- Git

The assigned `mazegenerator` wheel is included in the repository.

### Installation and Execution

Install dependencies and configure git hooks:
```bash
make install
```

Run the application with default configuration (`config.json`):
```bash
make run
```

Direct CLI invocation:
```bash
uv run python pac_man.py config.json
```

### Controls

The current application supports the state controls below:

| Key | Action |
| --- | --- |
| `Enter` / `Space` | Start game from menu or return from end screen |
| `P` | Pause or resume the active gameplay session |
| `E` | Open the end screen |
| `Esc` | Return from playing state to main menu |
| `W`, `A`, `S`, `D` / Arrows | Buffer directional turns for Pac-Man |
| Close window | Quit the application |

### Development Commands

| Command | Purpose |
| --- | --- |
| `make install` | Install runtime and development dependencies |
| `make run` | Run the application with `config.json` |
| `make debug` | Run the application with Python's built-in debugger |
| `make test` | Execute the complete automated test suite |
| `make lint` | Run flake8 and standard mypy checks |
| `make lint-strict` | Run flake8 and mypy strict mode |
| `make preview-mazes` | Display three generated levels in terminal |
| `make clean` | Remove temporary cache files |

## Configuration

Configuration is loaded from a JSON file that supports comment lines (prefixed with `#`). If a key is missing or contains an invalid value, the system logs a descriptive message and falls back to safe defaults without crashing or outputting tracebacks. Unknown keys are safely ignored.

### Key Schema and Defaults

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `highscore_filename` | string | `highscores.json` | Path to persistent highscore JSON file |
| `lives` | integer | `3` | Starting lives for the player (minimum: 1) |
| `points_per_pacgum` | integer | `10` | Score awarded per normal pacgum (minimum: 0) |
| `points_per_super_pacgum` | integer | `50` | Score awarded per super-pacgum (minimum: 0) |
| `points_per_ghost` | integer | `200` | Base score awarded for eating a frightened ghost |
| `frightened_duration` | float | `7.0` | Duration (seconds) of ghost frightened mode |
| `ghost_respawn_delay` | float | `5.0` | Time (seconds) an eaten ghost spends respawning |
| `seed` | integer | `42` | Deterministic seed for Level 1 generation |
| `level_max_time` | integer | `90` | Time limit (seconds) allowed per level |
| `levels` | array | `[{"width": 21, "height": 21}]` | Per-level maze dimensions (minimum: 5x5) |

## Maze Generation

The game integrates an assigned external maze generation package (`mazegenerator`) without modifying its source code:

- **Adapter Pattern:** `MazeGeneratorAdapter` adapts the external package interface, setting `perfect=False` to create interconnected corridor loops essential for Pac-Man gameplay.
- **Grid Normalization:** Converts external wall bitmasks into an immutable 2D grid of walls and corridors, validating boundaries and entry/exit reachability.
- **Deterministic vs. Random:** Level 1 uses a fixed seed (`42`) and includes the central `42` wall logo; subsequent levels generate procedural mazes using random seeds.
- **Entity Spawns & Pellets:** Computes the central player spawn, four corner ghost spawns, four corner-oriented super-pacgums, and fills reachable corridors with normal pacgums.

## Highscores

The highscore subsystem provides persistent score tracking across game sessions:

- **Storage Format:** Stored as human-readable JSON (`highscores.json`).
- **Validation:** Player names are restricted to 1–10 alphanumeric characters and spaces; scores must be non-negative integers.
- **Capacity & Ordering:** Retains the top 10 highest scores sorted in descending order.
- **Fault Tolerance:** If the storage file is missing, empty, corrupt, or unwritable, the system logs a warning and falls back to an empty list without interrupting gameplay.
- **Design Rationale:** JSON was chosen for transparent inspection, ease of debugging, cross-platform portability, and straightforward serialization without external database dependencies.

## Implementation

The technical implementation is split into decoupled domain services:

### 1. Coordinates and Collisions
- Resolution-independent geometry: `TileCoordinate` (integer grid `col, row`) and `WorldPosition` (float `x, y`).
- `WorldMap` handles tile walkability queries, boundary checks, and axis-aligned collision queries.

### 2. Player Mechanics
- Directional movement with turn buffering (`next_direction`), enabling responsive corner turning.
- Continuous pellet collection with score updates and power pellet activation.

### 3. Ghost AI System
Each ghost identity implements authentic arcade targeting behavior:
- **Blinky (Red):** Direct target chase targeting Pac-Man's current tile.
- **Pinky (Pink):** Ambush targeting 4 tiles ahead of Pac-Man's facing direction.
- **Inky (Cyan):** Complex vector targeting using a pivot 2 tiles ahead of Pac-Man reflected across Blinky's position.
- **Clyde (Orange):** Proximity-based targeting: chases Pac-Man when farther than 8 tiles away; retreats to home corner when closer.
- **Frightened Mode:** Speed reduced by 50%; chooses legal directions maximizing distance from Pac-Man (with seeded pseudo-random tie breaking).
- **Arcade Score Chaining:** Consecutive ghosts eaten within a single power activation award doubling points ($200 \rightarrow 400 \rightarrow 800 \rightarrow 1600$).
- **Frame Collision Guard:** `GhostCollisionGuard` prevents multiple life losses during continuous overlap frames and resolves multi-ghost contacts deterministically.

### 4. Progression & Lifecycle
- `GameSession` tracks score, lives, current level, level timer, and pause states.
- Multi-level progression preserves player score and remaining lives across levels.

## General Software Architecture

The codebase follows a modular package architecture with strict boundaries:

```
pacman/
├── application/       # Application context, state transitions, Pygame contracts, runtime loop
├── gameplay/          # Player, ghosts, collisions, scoring, lives, power state, progression
├── maze/              # External generator adapter, grid normalization, spawns, world geometry
├── infrastructure/    # Commented JSON configuration, highscore models, file storage
└── app.py             # Public facade maintaining backward compatibility
```

| Package | Key Modules | Responsibility |
| --- | --- | --- |
| `application/` | `state.py`, `context.py`, `runtime.py`, `rendering.py` | State machine, session coordination, rendering dispatch, Pygame event loop |
| `gameplay/` | `player.py`, `ghost.py`, `ghost_collision.py`, `ghost_gameplay.py`, `power_state.py`, `lives.py`, `progression.py` | Game rules, physics, AI pathfinding, collision resolution, lifecycle |
| `maze/` | `adapter.py`, `grid.py`, `level_generator.py`, `spawns.py`, `world.py` | External maze adaptation, grid normalization, level construction |
| `infrastructure/` | `config.py`, `highscore.py`, `storage.py` | Safe configuration parsing and robust JSON highscore persistence |

## Project Management

The project is developed using Jira (issue key prefix `PK-`) and GitHub pull requests following trunk-based development with peer reviews and continuous automated testing.

Detailed project management records, engineering decision logs, sprint ownership, and phase delivery histories are maintained in the [`project_management/`](project_management/) directory:
- [`phase_history.md`](project_management/phase_history.md): Comprehensive delivery history and phase reviews for Phases 0 through 5.
- [`README.md`](project_management/README.md): Team workflow, branch protection rules, and shared engineering standards.

## Resources and AI Usage

### References
- [Python 3 Documentation](https://docs.python.org/3/)
- [Pygame Documentation](https://www.pygame.org/docs/)
- [The Pac-Man Dossier (Jamey Pittman)](https://pacman.holycow.com/) for authentic ghost targeting rules and timing algorithms.
- [pytest Documentation](https://docs.pytest.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)

### AI Usage
Artificial Intelligence tools were utilized throughout development to:
- Formulate automated test suites and identify tricky edge cases (e.g. multi-ghost collision in the same frame, timer boundary expirations).
- Support code reviews, static type verification, and architecture boundary refactoring.
- Draft documentation and verify compliance with PEP 257 docstring standards.

All AI-suggested code and documentation were systematically reviewed, refactored, and verified by the project authors through comprehensive test suites.
