# Delivery History: Phases 0-9

This record describes what was actually delivered, how it was verified, and
where the implementation can be reviewed. Jira remains the task tracker and
the progressive planner remains the live planning view.

## Phase 0 - Align and Set Up

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Mariia | PK-7, PK-8 | Required Makefile commands; quality tools and initial test layout |
| Jayesh | PK-2, PK-21, PK-27, PK-28 | Initial repository documentation; `uv` dependency workflow; branch protection and Git hooks; project-management setup |

The team established a reproducible Python workflow:
* Used `uv` for dependencies.
* Created Make targets for installation, execution, cleanup, testing, and linting.
* Configured Git hooks for local quality checks.
* Jira and the progressive planner are used to choose work gradually instead of permanently splitting the project into two fixed roles.

## Phase 1 - Walking Skeleton

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Mariia | PK-12, PK-13, PK-14 | Pygame window and event loop; game-state controller; placeholder menu and game view |
| Jayesh | PK-11, PK-15, PK-16 | Command-line entry and configuration start; application boundaries; input-update-render cycle review |

The first end-to-end application path was created:
* The command-line entry point loads configuration.
* Pygame opens and shuts down safely.
* A state controller moves between the main menu, playing view, end screen, and back to the menu.
* `AppContext` keeps configuration, storage, session state, and level generation behind explicit application boundaries.

## Phase 2 - Config and Persistence

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Jayesh | PK-30, PK-31, PK-32, PK-33 | Configuration model and defaults; commented JSON parser; validation, fallback handling, and tests |
| Mariia | PK-34, PK-35, PK-36, PK-37, PK-38 | Highscore validation, loading, update, persistence, tests, and application integration |

* **Configuration:** Commented JSON configuration is parsed into validated public settings with safe defaults.
* **Highscores:** Entries validate names and non-negative scores. Storage handles missing, empty, corrupt, invalid, and unwritable files without crashing.
* **Data flow:** New results are ordered, trimmed to the best ten, persisted, loaded at startup, and displayed by the menu.

## Phase 3 - Maze Integration

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Shared | PK-40 | Maze-adapter contract |
| Mariia | PK-41, PK-42, PK-43, PK-46, PK-47 | Generator adapter; normalized grid; validation and errors; pellet placement; adapter and integration tests |
| Jayesh | PK-44, PK-45, PK-48 | Deterministic and random level generation; valid spawn positions; maze integration review |

* **Adapter:** The assigned A-Maze-ing dependency is isolated behind an adapter that uses `PERFECT=False`.
* **Grid Normalization:** Native generator output is normalized into one internal grid, validated, and converted into a `WorldMap`.
* **Level Service:** Provides a repeatable first level and random later levels, safe player and ghost spawns, normal pacgums, four corner-oriented super-pacgums, and clear user-facing errors.
* **Verification:** Fake-generator tests and a terminal preview verify the complete maze pipeline without coupling game rules to the package format.

## Phase 4 - Core Gameplay

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Mariia | PK-50, PK-55, PK-56, PK-57, PK-59 | Shared coordinates and collision queries; lives, death, respawn, game over; timer; pause; core rule tests |
| Jayesh | PK-51, PK-52, PK-53, PK-54, PK-58 | Player movement; turn buffering; normal and super-pacgum collection; scoring and power activation; level progression |
| Together | PK-60 | Review and test the complete player-only gameplay flow |

* **Core Mechanics:** Supplies a common tile/world coordinate model, wall-safe four-direction movement, and buffered turns.
* **Game Logic:** Handles one-time pellet collection, configurable scoring, power-state activation, lives and respawn rules, timeout behaviour, and pause/resume.
* **Progression & Testing:** Implements multi-level progression through victory. Unit and rule-level tests keep these systems independent from pygame rendering.

### Phase 4 Review - Scope Boundary Confirmed

PK-60 reviews the complete gameplay loop at the game-rule and service level, independently from rendering. The current pygame `run_app()` intentionally keeps its placeholder game view: connecting the generated world, entities, input, HUD, menus, and complete visual player journey belongs to Phase 6 - UI and Full Game Flow.

This separation is intentional rather than an integration defect. Phase 4 proves that movement, collision, collection, scoring, lives, timing, pause, and progression cooperate without depending on pygame. That stable rule layer can now support Phase 5 ghost behaviour. Phase 6 will add the application coordinator and rendering integration without moving game rules into UI code.

### Architecture Decision

During Phase 4, the project grew enough for `pacman/app.py` to reach 446 lines
and combine several responsibilities: application state, pygame contracts,
rendering, and runtime orchestration. The team decided to review the
architecture at this point instead of allowing later gameplay and UI work to
increase that coupling.

The application code was separated into focused modules under
`pacman/application`, while `pacman.app` remains a small public facade so
existing imports continue to work. Domain modules now depend directly on the
state component instead of the larger application facade. The flat test suite
was also grouped by application, gameplay, maze, persistence, and integration
responsibilities, with reusable fakes moved into `tests/support`.

This was a behaviour-preserving refactor: responsibilities and dependencies
changed, but the existing game behaviour and public interface did not. The
decision also established a shared rule for later phases: when a file grows
because it mixes different kinds of logic, the team reviews its architecture
and extracts coherent responsibilities before adding more features.

The review is supported by focused tests for:

* Movement and walls
* Turn buffering
* Pellet collection and scoring
* Lives and respawn
* Timeout, pause/resume
* Level progression, victory, and game over

## Current Status

This history covers delivered work through Phase 4. Future work remains in
Jira and the progressive planner and is added here only after its phase review.
The next planned stage is Phase 5 - Ghost Behaviour; complete pygame UI and
player-flow integration remain Phase 6 work.
