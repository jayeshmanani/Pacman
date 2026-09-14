# Architecture Decision Records (ADRs)

This document captures the key architectural, technical, and gameplay design
decisions made throughout the development of the 42 Pac-Man project. Each record
outlines the context, options considered, final decision, and consequences.

---

## Index of Decisions

- [ADR-01: Custom Comment-Tolerant JSON Parser](#adr-01-custom-comment-tolerant-json-parser)
- [ADR-02: Isolation of External Maze Generator Behind Adapter](#adr-02-isolation-of-external-maze-generator-behind-adapter)
- [ADR-03: Headless Game Rules Isolated from Pygame (`AppContext`)](#adr-03-headless-game-rules-isolated-from-pygame-appcontext)
- [ADR-04: Procedural Vector Sprites over Static Raster Assets](#adr-04-procedural-vector-sprites-over-static-raster-assets)
- [ADR-05: Floating-Point Epsilon Snapping for Timer Endurance](#adr-05-floating-point-epsilon-snapping-for-timer-endurance)
- [ADR-06: Selection of Deterministic Seed 43 with Preserved `42` Marker](#adr-06-selection-of-deterministic-seed-43-with-preserved-42-marker)
- [ADR-07: Dual-Mode Pacgum Generation](#adr-07-dual-mode-pacgum-generation)
- [ADR-08: Non-Mutating Cheat Multipliers and Session Reset Cleanup](#adr-08-non-mutating-cheat-multipliers-and-session-reset-cleanup)

---

## ADR-01: Custom Comment-Tolerant JSON Parser

- **Date:** 2026-08-11
- **Status:** Accepted (Implemented in PK-31, PK-32)
- **Deciders:** Jayesh, Mariia

### Context
Chapter V.2 requires configuration in JSON format with comment support (lines
starting with `#` and optional `//` comments). Standard Python `json.loads`
fails on any comment syntax. Introducing third-party packages (like `json5` or
`pyyaml`) would increase dependency footprint and violate the requirement to
use a strict JSON structure.

### Decision
Implement a lightweight pre-parser in `pacman.infrastructure.config` that:
1. Strips full-line and trailing comments beginning with `#` and `//` outside of
   quoted strings.
2. Hands the sanitized string to Python's standard `json.loads`.
3. Validates all keys and clamps out-of-bound values to safe defaults without
   raising unhandled exceptions.

### Consequences
- **Positive:** Zero external dependencies beyond standard library; robust
  protection against syntax errors; clean warning logs on faulty values.
- **Negative:** Inline `#` characters within string values must be handled
  carefully by regex/lexer logic.

---

## ADR-02: Isolation of External Maze Generator Behind Adapter

- **Date:** 2026-08-18
- **Status:** Accepted (Implemented in PK-40, PK-41)
- **Deciders:** Team (Mariia, Jayesh)

### Context
Chapter V.4 specifies that the assigned external `A-Maze-ing` package
(`mazegenerator` wheel) must be used as-is without modification, called with
`PERFECT=False` to produce loops and interconnected corridors suitable for
Pac-Man. Direct use of external generator dictionaries inside game logic would
tightly couple game rules to third-party data structures.

### Decision
Create an explicit adapter layer (`MazeGeneratorAdapter` in `pacman.maze.adapter`):
1. Wrap all external calls in defensive error handlers (catching `Exception`).
2. Translate native output into an internal immutable `MazeGrid` of `WALL`,
   `CORRIDOR`, and `BLOCKED_42` cells.
3. Provide fallback procedural layouts if the generator raises an error or
   produces disconnected topologies.

### Consequences
- **Positive:** Upstream changes or edge cases in `mazegenerator` cannot break
  gameplay logic; unit tests can use lightweight fakes without loading the wheel.
- **Negative:** Small translation overhead during level loading (negligible:
  <2ms per level).

---

## ADR-03: Headless Game Rules Isolated from Pygame (`AppContext`)

- **Date:** 2026-08-28 (Refined in PK-60 on 2026-09-01)
- **Status:** Accepted
- **Deciders:** Team (Jayesh, Mariia)

### Context
During Phase 4, `pacman/app.py` grew to over 440 lines, coupling Pygame display
surfaces, event loops, movement rules, pellet collection, and life counters.
Testing game mechanics required initializing Pygame windows or mocking display
modes.

### Decision
Strictly decouple gameplay rules from the rendering layer:
1. Domain state (`Player`, `Ghost`, `PacgumField`, `PowerState`, `GameSession`)
   has zero dependencies on `pygame`.
2. Movement and collision physics use pure mathematical coordinates.
3. An `AppContext` holds state and service references; `GameplayLoop` coordinates
   updates per frame; `rendering/` consumes state as read-only.

### Consequences
- **Positive:** 100% of game mechanics can be verified headlessly at thousands
  of frames per second in unit and soak tests; no UI windows required in CI.
- **Negative:** Requires coordinate-to-viewport translation components in the
  renderer.

---

## ADR-04: Procedural Vector Sprites over Static Raster Assets

- **Date:** 2026-09-06
- **Status:** Accepted (Implemented in PK-83)
- **Deciders:** Jayesh

### Context
Chapter IV and VI require a graphical UI. Using external PNG raster sprites
introduces risks of missing asset files, incorrect working directory paths,
blurry scaling artifacts when resizing windows, and dependency on external
image decoders.

### Decision
Implement procedural vector rendering routines using native `pygame.draw`
primitives (`pacman.application.rendering.sprites`):
1. Draw Pac-Man with dynamic mouth-angle animations (`arc` / `polygon`).
2. Draw ghosts (Blinky, Pinky, Inky, Clyde) with authentic curved heads, wavy
   tentacles, direction-aware pupils, and flashing frightened appearances.
3. Support seamless integer and fractional tile scaling to fit any viewport.

### Consequences
- **Positive:** Zero external asset files to lose or misplace; crisp rendering
  at all display resolutions; instantaneous startup.
- **Negative:** Creating complex arcade shapes required custom mathematical
  coordinate geometry.

---

## ADR-05: Floating-Point Epsilon Snapping for Timer Endurance

- **Date:** 2026-09-10
- **Status:** Accepted (Implemented in PK-92, BUG-01)
- **Deciders:** Jayesh, Mariia

### Context
During 50,000-tick soak testing, repeated frame delta subtractions
($t \leftarrow t - \Delta t$) left minute floating-point residual values
($\approx 10^{-14}\text{s}$ to $10^{-15}\text{s}$) rather than reaching exact
`0.0`. This caused `PowerState.is_active` (`remaining_time > 0.0`) to remain
`True` for spurious frames and delayed ghost respawns.

### Decision
Apply an $\epsilon \le 10^{-9}\text{s}$ snapping boundary:
- Whenever a timer decrements to $\le 10^{-9}\text{s}$, explicitly set it to
  `0.0`.
- Applied consistently in `PowerState.update()`, `Ghost.update()`, and
  `GameSession.update_level_timer()`.

### Consequences
- **Positive:** Prevents phantom power states, guarantees deterministic timeout
  transitions, passes 50,000-tick marathon tests without drift.
- **Negative:** Requires consistent adherence across all future timer
  implementations.

---

## ADR-06: Selection of Deterministic Seed 43 with Preserved `42` Marker

- **Date:** 2026-09-10
- **Status:** Accepted (Implemented in PK-94)
- **Deciders:** Team (Mariia, Jayesh)

### Context
Chapter VI.1 states that Level 1 must be generated with a fixed seed. The
external package embeds a blocked cell pattern spelling `42` in the maze grid.
With seed `42`, the generated corridors formed a lower dead-end loop that
visually merged into the digit `4`. Seed `43` produces an open, readable
corridor network while preserving the `42` blocked cell marker intact.

### Decision
Use seed `43` as the default fixed seed for Level 1 in `config.json`:
1. Retains full determinism for Level 1 evaluation.
2. Explicitly preserves the package's `42` marker in `Level 1` while preventing
   pellet placement inside the blocked number cells.
3. Retains random seed generation for Levels 2 through 10.

### Consequences
- **Positive:** Superior visual presentation and corridor flow during
  evaluations while honoring upstream package idiosyncrasies.
- **Negative:** Seed value is 43 instead of 42 (both satisfy the specification
  requirement for a fixed seed).

---

## ADR-07: Dual-Mode Pacgum Generation

- **Date:** 2026-09-09
- **Status:** Accepted (Implemented in PK-91, BUG-05)
- **Deciders:** Mariia

### Context
Chapter VI.1 requires pacgums in "most corridors", while Chapter V.2 suggests a
`pacgum` configuration key with an example value (e.g. `42`). A conflict arose:
should the game populate all valid corridors, or clamp to the exact configured
count?

### Decision
Implement dual-mode pellet placement in `LevelGenerator`:
1. If `pacgum` is explicitly configured in `config.json` with a positive integer,
   the level generator places exactly that many pellets uniformly across valid
   corridor tiles.
2. If `pacgum` is omitted or set to its default (`None`), the generator fills
   all eligible corridor tiles (excluding ghost houses and spawns).

### Consequences
- **Positive:** Satisfies both the general subject gameplay rule (dense
  corridor dots) and defense-time evaluation requirements (testing specific
  pellet counts).
- **Negative:** Generator logic must maintain two distribution paths.

---

## ADR-08: Non-Mutating Cheat Multipliers and Session Reset Cleanup

- **Date:** 2026-09-09
- **Status:** Accepted (Implemented in PK-90, BUG-03)
- **Deciders:** Jayesh

### Context
Cheat mode (F1) allows toggling 2x player speed. If the player speed attribute
on the `Player` class were permanently multiplied ($v \leftarrow v \times 2$),
repeated toggling or session resets could leave the player with permanently
elevated speed in the next game session.

### Decision
1. Implement speed boost as a transient multiplier evaluated on demand:
   `effective_speed = base_speed * (2.0 if cheat_speed else 1.0)`.
2. In `AppContext.reset_session()`, explicitly invoke `cheat_mode.reset()` so
   all cheat toggles (invincibility, freeze, speed) are deactivated whenever
   returning to the main menu or starting a new game.

### Consequences
- **Positive:** Zero state leakage across consecutive games; safe, non-destructive
  evaluation cheats.
- **Negative:** Frame movement logic must query the cheat multiplier through the
  coordinator.
