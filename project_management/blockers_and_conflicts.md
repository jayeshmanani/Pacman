# Blockers, Technical Hurdles & Conflict Resolution

This document records the major technical obstacles, architectural dilemmas,
and team decision conflicts encountered during the development of the 42 Pac-Man
project, along with the collaborative resolutions reached.

---

## 1. Technical Blockers & Hurdles

### Blocker 1: Monolithic App File Coupling & Testability
- **Phase & Issue:** Phase 4 (PK-60)
- **Problem:** As gameplay rules, player movement, life loss, and scoring were
  implemented, `pacman/app.py` grew to 446 lines. It combined Pygame display
  initialization, event dispatching, game loop timing, and game state logic in
  a single file. Unit testing game mechanics required mocking Pygame displays,
  making tests slow and brittle.
- **Investigation:** Both team members reviewed the codebase and recognized that
  adding 4 autonomous ghost AIs in Phase 5 would exacerbate this coupling.
- **Resolution:** Halted feature delivery for 1 day to perform a behavior-preserving
  architectural refactor. Split `pacman/app.py` into focused components under
  `pacman/application/` (`context.py`, `runtime.py`, `gameplay_loop.py`), while
  retaining `pacman/app.py` as a lightweight facade. Domain rules were moved to
  `pacman/gameplay/` with zero Pygame dependencies.
- **Outcome:** 100% of game mechanics became testable headlessly; automated test
  suite runtime dropped to <2 seconds.

---

### Blocker 2: External Maze Generator `42` Marker Topology
- **Phase & Issue:** Phase 3 (PK-41) & Phase 7 (PK-94)
- **Problem:** The assigned external `mazegenerator` package embeds a fixed
  blocked-cell pattern spelling `42` in the center of the maze. In early
  iterations, pellet generators placed pacgums inside these blocked cells,
  making levels impossible to finish. Furthermore, with default seed `42`, the
  generated corridor network visually merged into the lower wall of the digit.
- **Investigation:** Reverse-engineered the grid output from the closed wheel
  without modifying the package source (satisfying Chapter V.4).
- **Resolution:**
  1. Updated `pacman.maze.grid` to detect and label `BLOCKED_42` cells explicitly.
  2. Guarded pellet and ghost spawn placement to skip blocked pattern tiles.
  3. Evaluated seed variations and selected seed `43` as default in `config.json`:
     it preserves the authentic `42` pattern while generating clean, open
     corridors around both digits.
- **Outcome:** Clean visual aesthetics and 100% reachable pellets on Level 1.

---

### Blocker 3: Floating-Point Timer Residual Drift in 50k-Tick Soak Runs
- **Phase & Issue:** Phase 7 (PK-92, BUG-01)
- **Problem:** During marathon endurance testing of 50,000 continuous frames,
  repeated floating-point subtractions ($t \leftarrow t - \Delta t$) produced
  minute residual values ($\approx 10^{-14}\text{s}$) rather than reaching exact
  `0.0`. Eaten ghosts remained stuck in `RESPAWNING` state, and `PowerState`
  flagged power as active for phantom frames.
- **Investigation:** Jayesh traced the issue in the headless simulation harness
  (`SoakSimulationHarness`). Standard equality checks (`time == 0.0`) failed,
  while `time > 0.0` remained True due to IEEE-754 precision limits.
- **Resolution:** Added an explicit epsilon threshold snap ($\epsilon \le 10^{-9}\text{s}$)
  in `PowerState.update()`, `Ghost.update()`, and `GameSession.update_level_timer()`.
- **Outcome:** Timers snap cleanly to `0.0`. Soak tests pass 50,000 ticks with
  zero timer drift.

---

### Blocker 4: Russian Cyrillic Keyboard Input (`ЦФЫВ`) for WASD
- **Phase & Issue:** Phase 7 (PK-94)
- **Problem:** During manual evaluation testing on machines with Cyrillic
  keyboard layouts active, Pygame emitted unicode characters `Ц`, `Ф`, `Ы`, `В`
  instead of `w`, `a`, `s`, `d`, leaving the player unable to navigate without
  arrow keys.
- **Investigation:** Pygame's `event.key` maps to physical scancodes, but
  character-based event checks failed when an alternate keyboard layout was
  active.
- **Resolution:** Added explicit translation for Russian characters (`Ц`, `Ф`,
  `Ы`, `В`) and physical key scancode fallbacks in `runtime.py`.
- **Outcome:** Seamless control responsiveness across multiple international
  keyboard layouts.

---

## 2. Team Decision Conflicts & Resolutions

### Conflict 1: Scope Boundary for Phase 4 (Domain Rules vs. Visual Integration)
- **Context:** At the end of Phase 4 (PK-60), Mariia proposed integrating the
  full Pygame rendering loop to visually verify movement and pellet collection.
  Jayesh argued that rendering should remain minimal until the core ghost AI
  (Phase 5) was completed, keeping the domain rule tests independent.
- **Discussion:** The team reviewed the architecture guidelines in
  `project_management/README.md` ("Keep domain rules independent from pygame so
  they can be tested without opening a window").
- **Agreed Resolution:** The placeholder game view in Pygame was retained for
  Phase 4, and visual rendering was deferred to Phase 6. In return, the team
  committed to building a rich vector sprite rendering system and full HUD
  during Phase 6.
- **Impact:** Enabled rapid, crash-free implementation of Phase 5 ghost AI.

---

### Conflict 2: Pacgum Placement Rule (Corridor Filling vs. Config Key)
- **Context:** Chapter VI.1 mandates pacgums in "most corridors", whereas
  Chapter V.2 suggests a `pacgum` config key (e.g. `42`). A conflict arose
  during live configuration testing (PK-91) when overriding `pacgum: 15` did
  not reduce the pellet count because the generator defaulted to filling every
  corridor tile.
- **Discussion:** Evaluators during defense might test custom `config.json` files
  with specific `pacgum` values to test boundary conditions.
- **Agreed Resolution:** Implemented **Dual-Mode Pacgum Generation** (ADR-07):
  if `pacgum` is explicitly specified as an integer, exactly that many pellets
  are distributed uniformly; if omitted or null, corridors are filled.
- **Impact:** Full compliance with both gameplay requirements and defense-time
  reconfiguration tests.
