# Risk Analysis & Mitigation Register

This document records the risk analysis, severity scoring, mitigation strategies,
and residual risk tracking for the 42 Pac-Man project in compliance with Chapter
VIII of the subject.

---

## 1. Risk Evaluation Framework

Risks are evaluated by multiplying Likelihood and Impact:

| Likelihood / Impact | Low Impact | Medium Impact | High Impact |
| :--- | :---: | :---: | :---: |
| **High Likelihood** | Medium | High | **Critical** |
| **Medium Likelihood** | Low | Medium | High |
| **Low Likelihood** | Low | Low | Medium |

---

## 2. Risk Summary Matrix

| Risk ID | Title | Category | Initial Severity | Mitigation Status | Residual Severity | Owner |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **RISK-01** | External Maze Generator Failures | External Dependency | High | Mitigated (Adapter + Fallback) | Low | Mariia |
| **RISK-02** | Timer Drift in Long Play Sessions | Technical / Game Rules | High | Mitigated ($\epsilon \le 10^{-9}\text{s}$ Snap) | Low | Jayesh |
| **RISK-03** | Highscore File Corruption | Data / Persistence | High | Mitigated (Atomic File Write) | Low | Mariia |
| **RISK-04** | State Contamination Across Sessions | Architecture | High | Mitigated (Lifecycle Reset) | Low | Jayesh |
| **RISK-05** | Non-QWERTY Keyboard Incompatibility | User Experience | Medium | Mitigated (Cyrillic WASD Support)| Low | Mariia |
| **RISK-06** | Pygame Rendering / Rule Coupling | Architecture | High | Mitigated (`AppContext` Decoupling)| Low | Team |
| **RISK-07** | Packaging Failures on Clean Environments| Deployment | High | In Progress (Phase 8 Testing) | Medium | Jayesh |
| **RISK-08** | Ghost AI Corner Oscillation & Trapping | Gameplay AI | Medium | Mitigated (Reverse-Turn Prohibition)| Low | Jayesh |

---

## 3. Detailed Risk Records

### RISK-01: External Maze Generator Failures or Invalid Output
- **Category:** External Dependency
- **Context:** The project must use the assigned `mazegenerator` wheel as-is. The package may produce unsolvable mazes, raise unhandled exceptions on extreme sizes, or emit unexpected structures.
- **Impact:** High (Application crash or unplayable maze violates Chapter III and V.4).
- **Mitigations:**
  1. Wrapped all third-party generator calls in `MazeGeneratorAdapter` with comprehensive exception catching.
  2. Implemented flood-fill connectivity validation on generated grids.
  3. Added deterministic procedural fallback mazes in the event of upstream failure.
- **Status:** Closed / Verified by `test_maze_adapter.py` and `test_boundary_failures.py`.

---

### RISK-02: Floating-Point Timer Drift During Long Play
- **Category:** Technical / Game Rules
- **Context:** Running the game at variable framerates using delta-time subtractions ($t \leftarrow t - \Delta t$) can accumulate floating-point residual errors over thousands of frames.
- **Impact:** High (Phantom power pellet duration, delayed ghost respawn, desynchronized level timers).
- **Mitigations:**
  1. Implemented $\epsilon \le 10^{-9}\text{s}$ threshold snapping in `PowerState`, `Ghost`, and `GameSession`.
  2. Built automated 50,000-tick headless soak test harness (`test_soak_timers.py`).
- **Status:** Closed / Resolved in PK-92 (BUG-01).

---

### RISK-03: Highscore File Corruption on Abrupt Exit
- **Category:** Data / Persistence
- **Context:** If the application process terminates or encounters an I/O interrupt while writing `highscores.json`, the file could be truncated or corrupted.
- **Impact:** High (Loss of user data, potential JSON decode crash on next startup violating Chapter V.5).
- **Mitigations:**
  1. Implemented atomic disk writes: serialize data to a temporary file (`highscores.json.tmp`) and replace target atomically via `os.replace`.
  2. Wrapped loading in defensive JSON parsing; on unreadable or corrupt content, safely back up the bad file, log a warning, and initialize an empty table.
- **Status:** Closed / Verified by `test_storage.py` and `test_boundary_failures.py`.

---

### RISK-04: State Contamination Across Consecutive Sessions
- **Category:** Architecture / Session Lifecycle
- **Context:** If active cheats (e.g. 2x speed, invincibility) or game variables (remaining lives, score, pellet counts) persist after Game Over or returning to the main menu, subsequent games would be tainted.
- **Impact:** High (Evaluation failure; non-deterministic gameplay).
- **Mitigations:**
  1. Centralized session teardown inside `AppContext.reset_session()`.
  2. Explicitly invoke `cheat_mode.reset()` on all transitions back to the main menu.
  3. Added multi-cycle integration tests (`test_lifecycle_cleanup.py`) verifying 50 consecutive game cycles.
- **Status:** Closed / Resolved in PK-90 (BUG-03).

---

### RISK-05: Non-QWERTY Keyboard Incompatibility
- **Category:** User Experience / Evaluation
- **Context:** Evaluators using non-English keyboard layouts (e.g. Russian JCUKEN where WASD corresponds to `Ц`, `Ф`, `Ы`, `В`) would find the game unresponsive.
- **Impact:** Medium (Impaired evaluation experience during peer review).
- **Mitigations:**
  1. Added physical scancode fallback and direct character mapping for Cyrillic `ЦФЫВ` keys in `runtime.py`.
  2. Supported both Arrow keys and WASD/ЦФЫВ natively.
- **Status:** Closed / Verified in manual gameplay review (PK-94).

---

### RISK-06: Pygame Rendering and Domain Rule Coupling
- **Category:** Architecture / Code Quality
- **Context:** Mixing graphics code with game rules causes file bloat, prevents unit testing without an active display server, and violates PEP 257 / modularity principles.
- **Impact:** High (Unmaintainable code, slow test suite, brittle refactoring).
- **Mitigations:**
  1. Refactored domain rules out of `pacman/app.py` into `pacman/gameplay/` and `pacman/application/`.
  2. Rendering components strictly receive read-only state copies or properties.
  3. Verified by 456 headless automated tests passing in under 2 seconds.
- **Status:** Closed / Resolved in PK-60.

---

### RISK-07: Packaging Failures on Clean Environments
- **Category:** Deployment / Submission
- **Context:** Packaging the application into a standalone executable or release archive may fail due to hidden dynamic imports (Pygame SDL libraries, embedded wheel).
- **Impact:** High (Violates Chapter VII: project must be packaged and launchable on clean machines).
- **Mitigations:**
  1. Creating a reproducible packaging specification (PyInstaller / standalone bundle) in Phase 8 (P8-05).
  2. Testing on clean virtual environments and recording verification steps (P8-08).
- **Status:** In Progress / Active in Phase 8.

---

### RISK-08: Ghost AI Corner Oscillation & Trapping
- **Category:** Gameplay AI
- **Context:** Ghosts navigating grid intersections could reverse direction repeatedly or oscillate indefinitely if targeting rules allow immediate 180-degree turnarounds.
- **Impact:** Medium (Unauthentic arcade behavior, unchallenging gameplay).
- **Mitigations:**
  1. Enforced authentic arcade constraint: ghosts are prohibited from choosing the reverse of their current direction unless entering/exiting Frightened mode.
  2. Verified by deterministic AI navigation tests in `test_ghost_movement.py`.
- **Status:** Closed / Verified in Phase 5.
