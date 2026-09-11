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
- Automated unit, integration, soak, and headless playtest verification.

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
uv run python pac-man.py config.json
```

Alternatively, after activating the project environment, use the exact
subject-compatible command:
```bash
source .venv/bin/activate
python3 pac-man.py config.json
```

### Controls

The current application supports the state controls below:

| Key | Action |
| --- | --- |
| `Enter` / `Space` | Start game from menu or confirm name on end screen |
| `P` | Pause or resume the active gameplay session |
| `Esc` | Return to main menu from playing, paused, or end screen |
| `W`, `A`, `S`, `D` / `Ц`, `Ф`, `Ы`, `В` / Arrows | Buffer directional turns for Pac-Man |
| Close window | Quit the application |

### Cheat Mode Controls

Cheat mode is intended for peer review and evaluation. Press `F1` during
gameplay to enable or disable it. When enabled, the game displays the complete
control map below the HUD so evaluation controls do not need to appear on the
regular player instructions screen.

| Key | Cheat action |
| --- | --- |
| `F1` | Enable or disable cheat mode |
| `1` | Toggle player invincibility |
| `2` | Skip the current level |
| `3` | Toggle ghost freeze |
| `4` | Add an extra life |
| `5` | Toggle the player speed boost |

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

### Key Schema and Fallbacks

The bundled `config.json` defines ten 14x14 native maze levels, a 90-second
limit, and fixed seed `43` for its repeatable first-level layout. The values
below are parser fallbacks used when settings are omitted or invalid.

| Key | Type | Fallback | Description |
| --- | --- | --- | --- |
| `highscore_filename` | string | `highscores.json` | Path to persistent highscore JSON file |
| `pacgum` | integer | omitted | Optional normal pacgum count; omit to fill all eligible corridors |
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
- **Deterministic vs. Random:** Level 1 uses the fixed seed from `config.json` (`43` in the bundled configuration) and preserves the package's central `42` blocked-cell marker; subsequent levels generate procedural mazes using random seeds without the marker.
- **Entity Spawns & Pellets:** Computes the central player spawn, four corner ghost spawns, four corner-oriented super-pacgums, and either fills reachable corridors with normal pacgums or uses an explicit configured normal pacgum count.

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
| `application/` | `state.py`, `context.py`, `runtime.py`, `gameplay_loop.py`, `rendering/` | State machine, live gameplay coordination, focused rendering components, Pygame event loop |
| `gameplay/` | `player.py`, `ghost.py`, `ghost_collision.py`, `ghost_gameplay.py`, `power_state.py`, `lives.py`, `progression.py` | Game rules, physics, AI pathfinding, collision resolution, lifecycle |
| `maze/` | `adapter.py`, `grid.py`, `level_generator.py`, `spawns.py`, `world.py` | External maze adaptation, grid normalization, level construction |
| `infrastructure/` | `config.py`, `highscore.py`, `storage.py` | Safe configuration parsing and robust JSON highscore persistence |

## Project Management

The project is developed using Jira (issue key prefix `PK-`) and GitHub pull requests following trunk-based development with peer reviews and continuous automated testing.

Detailed project management records, engineering decision logs, sprint ownership, and phase delivery histories are maintained in the [`project_management/`](project_management/) directory:
- [`phase_history.md`](project_management/phase_history.md): Delivery history and phase reviews through the completed Phase 7 gameplay review.
- [`bug_triage.md`](project_management/bug_triage.md): Acceptance defect triage register, reproduction evidence, severity classifications, and resolutions (PK-93).
- [`README.md`](project_management/README.md): Team workflow, branch protection rules, and shared engineering standards.

## Resources

### References
- [Python 3 Documentation](https://docs.python.org/3/)
- [Pygame Documentation](https://www.pygame.org/docs/)
- [The Pac-Man Dossier (Jamey Pittman)](https://pacman.holycow.com/) for authentic ghost targeting rules and timing algorithms.
- [pytest Documentation](https://docs.pytest.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)

### AI Usage Disclosure

AI was used as a collaborative learning and review tool to discuss the subject,
identify implementation risks, propose tests, and improve documentation. It
also supported analysis of gameplay edge cases, code reviews, static type
verification, and discussions about modular architecture.

Every accepted change was reviewed, discussed, and tested before it was
committed. The project authors remain responsible for understanding,
explaining, and maintaining all submitted code and documentation.
