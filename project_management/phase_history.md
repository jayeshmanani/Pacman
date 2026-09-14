# Delivery History

This record describes what was actually delivered, how it was verified, and
where the implementation can be reviewed. Jira remains the task tracker and
the progressive planner remains the live planning view.

Ownership records the agreed responsibility for each work item rather than
the author of an individual commit. `Team` identifies collaboratively
discussed, reviewed, and delivered work even when one member created the
commit or pull request.

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
| Team | PK-40 | Maze-adapter contract |
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
| Team | PK-60 | Review and test the complete player-only gameplay flow |

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

## Phase 5 - Ghost Behaviour

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Team | PK-62 | Ghost state-model foundation |
| Jayesh | PK-63, PK-64, PK-65 | Autonomous movement, chase behaviour, and frightened movement |
| Mariia | PK-66, PK-67, PK-68, PK-69 | Frightened timer; edible ghost collision and respawn; state edge cases; deterministic tests |
| Team | PK-70 | Complete ghost-behaviour review and playtest |

* **Ghost Behaviour:** Blinky, Pinky, Inky, and Clyde use legal autonomous
  movement with identity-specific chase targets and frightened movement.
* **Power and Collisions:** Shared frightened timing, arcade score chaining,
  position-based collisions, delayed respawn, repeated-contact protection,
  and player life loss cooperate through one gameplay coordinator.
* **Verification:** Deterministic unit and integration scenarios cover the
  complete state lifecycle for all four ghosts. A headless playtest confirmed
  legal positions, consistent states, and a challenging but playable balance.
* **Architecture:** Production modules are grouped by application, gameplay,
  maze, and infrastructure responsibilities, with tests organized to mirror
  those boundaries.

## Phase 6 - UI and Full Game Flow

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Jayesh | PK-76, PK-79, PK-80, PK-81, PK-83 | Main menu navigation; in-game HUD; pause menu; Game Over and Victory screens; vector sprites, dynamic maze scaling, and feedback indicators |
| Mariia | PK-77, PK-78, PK-82 | Highscores screen; instructions screen; validated player name entry and highscore saving flow |
| Team | PK-84 | Complete menu-to-game-to-score flow review, end-screen cancellation, victory transition, and full-loop integration testing |

* **User Interface & Navigation:** Keyboard-driven main menu, structured instructions screen, ordered top-10 highscores display, and in-game HUD tracking score, lives, level, and timer.
* **Game Lifecycle Screens:** Distinct Game Over and Victory screens with contextual causes (out of lives, time expired, or all levels cleared) and validated name entry.
* **Flow Control & Cancellation:** Implemented clean Escape cancellation on end screens returning to the main menu without saving, and state-level victory transitions.
* **Visual Presentation:** Procedural vector sprites for player and ghost identities, dynamic maze viewport centering and integer tile scaling, wall rendering, and score popups.
* **Verification:** Dedicated end-to-end integration test suite (`test_full_game_flow.py`) covering the complete Lose journey, Win journey, cancellation flow, and consecutive playthrough session isolation with zero state leakage.

## Phase 7 - Evaluation Cheats, Robustness, and Gameplay Review

### Ownership

| Owner | Jira tasks | Delivered focus |
| --- | --- | --- |
| Mariia | PK-86, PK-87, PK-88 | Evaluation cheat mode activation; invincibility; ghost freeze; level skip; extra lives; reversible speed boost |
| Jayesh | PK-89, PK-90 | External boundary fault tolerance; error diagnostics; resource cleanup audit; session and cheat deactivation on exit; multi-cycle integration tests |
| Mariia | PK-91 | Live configuration testing; dual-mode pacgum placement; dynamic total levels progression scaling |
| Jayesh | PK-92 | Long-play and multi-level soak tests; headless simulation harness; floating-point timer drift fix; lifecycle & persistence endurance |
| Team | PK-93 | Defect triage register; bug classification, reproduction steps, root cause analysis, and disposition |
| Team | PK-94 | Cheat-assisted gameplay review; live rendering integration; evaluation-flow fixes and verification |

* **Evaluation Cheats:** Implemented F1 master cheat toggle, invincibility (1), level skip (2), ghost freeze (3), extra life (4), and reversible 2x player speed boost (5) with dedicated HUD indicators and non-mutating player speed multiplier.
* **Boundary Hardening:** Graceful recovery without tracebacks for external maze generation failures, faulty config parameters clamped to safe defaults, and diagnostic logging for corrupt highscore files.
* **Resource Cleanup & Lifecycle Audit (PK-90):**
  - Guaranteed full cheat deactivation (`cheat_mode.reset()`) whenever a game session is cleared or abandoned (`reset_session()`), preventing active cheat multipliers from lingering into menus.
  - Reset main menu cursor to `> Start Game <` on all transitions back to the main menu from gameplay, pause, or end screens, ensuring deterministic start/quit cycles.
  - Multi-cycle stress test suite (`test_lifecycle_cleanup.py`) verifying zero state leakage across repeated start/play/pause/return-to-menu iterations, cancelled highscore submissions, and consecutive application runs.
* **Live Configuration Testing (PK-91):**
  - Connected `pacgum` config key to support both explicit pellet counts and default corridor-filling modes.
  - Dynamically bound `total_levels` to configuration array length.
  - Dedicated 13-test integration suite (`test_live_configuration.py`) verifying defense-time live parameter adjustments.
* **Long-Play and Multi-Level Soak Testing (PK-92):**
  - Built headless simulation harness (`SoakSimulationHarness`) and frame invariant validator (`SoakInvariantChecker`).
  - Verified unbroken 10-level marathon playthrough from Level 1 through Level 10 to Victory with life and score retention across boundaries (`test_soak_progression.py`).
  - Resolved floating-point epsilon residual drift in `PowerState`, `Ghost`, and `GameSession` by snapping timer thresholds $\le 10^{-9}\text{s}$ to `0.0`. Verified 50,000 continuous ticks, 20-cycle power refreshes, and zero-leakage pause/resume cycles (`test_soak_timers.py`).
  - Hardened `PlayerNameInput.create_entry()` against unhandled exceptions on invalid characters; verified 50-cycle session resets, 100 consecutive highscore disk writes, and garbage-collected entity cleanup (`test_soak_lifecycle.py`).
* **Defect Triage Register (PK-93):**
  - Compiled and structured [`bug_triage.md`](bug_triage.md) recording 7 defects across the robustness audit, live config testing, and soak testing phases.
  - Classified each issue by severity (Critical, High, Medium, Low), documented reproduction steps and root-cause analysis, and recorded resolution and acceptance rationale in accordance with Chapter VIII.

### Cheat-Assisted Gameplay Review (PK-94)

PK-94 connected the previously tested game rules to the real Pygame flow and
used the completed cheat system to reach difficult evaluation states quickly.
The review covered movement, wall collision, pellet collection, frightened and
eaten ghosts, player death, respawn, timeout, pause, ten-level progression,
Victory, Game Over, and persistent highscore saving.

The PK-94 review also produced focused improvements:

* Split the growing rendering module and its tests into focused
  `pacman/application/rendering/` components.
* Rendered the generated maze, pellets, Pac-Man, and all four live ghost states
  using the shared viewport and world-coordinate model.
* Refined the 900x800 game view with narrow connected walls and larger,
  readable entity sprites.
* Preserved the assigned package's blocked-cell `42` marker explicitly in the
  internal grid while keeping it limited to the fixed first level. After
  visual review, the bundled fixed seed changed from `42` to `43`: both retain
  deterministic generation and the package marker, while seed `43` produces a
  cleaner surrounding topology without a lower wall visually joining the two
  digits.
* Balanced the bundled ten-level configuration around 29x29 normalized grids,
  a 90-second level timer, and a playable live movement speed. Normal pacgums
  remain in most eligible corridors as required by the subject.
* Added localized physical-key support so WASD remains usable when the Russian
  keyboard layout reports `ЦФЫВ` characters.
* Fixed repeated life loss after respawn by returning Pac-Man and all ghosts to
  their assigned spawn positions and resetting transient round state.

| Acceptance path | Result | Evidence |
| --- | --- | --- |
| Movement and wall collision | Passed | Arrow, WASD/ЦФЫВ runtime checks and manual playtest |
| Pacgums, super-pacgums, score, frightened ghosts | Passed | Gameplay pipeline tests and manual cheat-assisted playtest |
| Player death, one-life loss, and safe group respawn | Passed | Multi-frame regression test and manual collision check |
| Pause, timer, timeout, Game Over | Passed | Rule tests and natural timeout integration journey |
| Ten levels and Victory | Passed | Soak progression plus F1/2 evaluation journey |
| Name entry and persistent Top 10 highscores | Passed | End-to-end save/display tests and manual review |

At the completion of PK-94, 456 automated tests pass together with `flake8`
and strict `mypy` checks. The manual application review confirmed the same
paths in the real Pygame window.

## Current Status

Phase 7 is complete through PK-94: the implemented gameplay was exercised in
the real Pygame application, difficult states were reached with cheats, and
the defects found during that review were corrected and retested. This marks
the end of the gameplay-review phase.

## Phase 8 - Documentation, Packaging, and Release

### Planned Ownership

| Owner | Work items | Planned focus |
| --- | --- | --- |
| Mariia | P8-01, P8-02, P8-03 | README; configuration and gameplay-system documentation; software architecture |
| Jayesh | P8-05, P8-06, P8-07, P8-09 | Reproducible packaging; packaged-game instructions; platform publishing; release rebuild |
| Team | P8-04 | Project timeline; progress evidence; decisions; risks; team organisation; blockers and conflicts |
| Team | P8-08, P8-10 | Clean-machine acceptance testing; joint documentation and release-evidence review |

Phase 8 is in progress. Completed outcomes and their verification evidence
will be recorded here as the corresponding work items are reviewed and
merged.
