# Acceptance Test Plan & Traceability Matrix

This document defines the formal Acceptance Test Plan for the 42 Pac-Man project.
It maps every requirement from the subject specifications to concrete automated
tests, manual verification procedures, and quality gates.

---

## 1. Subject Requirements Traceability Matrix

| Subject Chapter | Requirement Specification | Verification Method | Associated Test Modules | Acceptance Status |
| :--- | :--- | :---: | :--- | :---: |
| **III.1** | Python 3.10+, flake8, PEP 257 docstrings | Automated CI | `make lint`, `make lint-strict` | **Passed** |
| **III.1** | Full `mypy --strict` typing | Automated CI | `make lint-strict` | **Passed** |
| **III.1** | Zero crashes & unhandled exceptions | Automated Suite | `test_boundary_failures.py`, `test_storage.py` | **Passed** |
| **III.2** | Required Makefile targets (`install`, `run`, `debug`, `clean`, `lint`, `lint-strict`, `test`) | Automated & CLI | `Makefile`, `tests/test_project_setup.py` | **Passed** |
| **V.1** | CLI invocation `python3 pac-man.py config.json` with single argument | Automated Unit | `tests/application/test_entry_point.py` | **Passed** |
| **V.2** | Commented JSON config (`#` and `//` comments) | Automated Unit | `tests/infrastructure/test_config.py` | **Passed** |
| **V.3** | Faulty config clamped to safe defaults without tracebacks | Automated Integration | `tests/integration/test_live_configuration.py` | **Passed** |
| **V.4** | Use assigned `mazegenerator` wheel as-is with `PERFECT=False` | Automated Unit | `tests/maze/test_maze_adapter.py` | **Passed** |
| **V.4** | Graceful handling of generator failures | Automated Integration | `tests/integration/test_boundary_failures.py` | **Passed** |
| **V.5** | Highscore validation: alphanumeric + space, max 10 chars | Automated Unit | `tests/infrastructure/test_highscore.py` | **Passed** |
| **V.5** | Persistent Top 10 highscores in JSON format | Automated Unit | `tests/infrastructure/test_storage.py` | **Passed** |
| **V.5** | Robustness to missing, empty, or corrupt highscore file | Automated Integration | `tests/integration/test_boundary_failures.py` | **Passed** |
| **VI.1** | Deterministic fixed seed Level 1; random later levels | Automated Unit | `tests/maze/test_level_generator.py` | **Passed** |
| **VI.1** | 4 super-pacgums in corners; 4 ghosts in corners; player in center | Automated Unit | `tests/maze/test_spawns.py` | **Passed** |
| **VI.2** | 4-directional player movement through corridors only | Automated Unit | `tests/gameplay/test_player.py` | **Passed** |
| **VI.2** | Buffered turns and wall-safe navigation | Automated Unit | `tests/gameplay/test_player.py` | **Passed** |
| **VI.2** | 3 lives starting; loss of life on ghost collision; respawn in center | Automated Unit | `tests/gameplay/test_lives.py` | **Passed** |
| **VI.3** | 4 ghosts with autonomous AI and distinct chase personalities | Automated Unit | `tests/gameplay/test_ghost_chase.py` | **Passed** |
| **VI.3** | Ghosts flee when edible; delayed corner respawn when eaten | Automated Unit | `tests/gameplay/test_ghost_frightened.py` | **Passed** |
| **VI.4** | Pacgums in corridors; super-pacgums trigger frightened mode | Automated Unit | `tests/gameplay/test_pacgums.py` | **Passed** |
| **VI.5** | Cheat Mode (F1): Invincibility (1), Skip (2), Freeze (3), Lives (4), Speed (5) | Automated Integration | `tests/integration/test_evaluation_cheat_flow.py` | **Passed** |
| **VI.6** | Non-decreasing score: dots (+10), power (+50), ghosts (+200, +400, +800, +1600) | Automated Unit | `tests/gameplay/test_ghost_collision.py` | **Passed** |
| **VI.7** | 10+ levels progression, timer countdown, level timeout handling | Automated Unit | `tests/gameplay/test_progression.py`, `test_level_timer.py` | **Passed** |
| **VI.7** | Pause / Resume state handling | Automated Unit | `tests/gameplay/test_pause.py` | **Passed** |
| **VI.8** | Graphical UI: Menu, HUD, Pause, Game Over, Victory | Automated Unit | `tests/application/rendering/`, `test_game_state.py` | **Passed** |
| **VII** | Project packaging and platform deployment (Itch.io / Steam) | Build & Clean Env | PK-100 to PK-103 | **Passed** |
| **VIII** | Dedicated `project_management/` directory with PM evidence | Repo Inspection | `project_management/` documentation suite | **Passed** |
| **IX** | README format, 42 header, controls, architecture, AI disclosure | Manual Inspection | `README.md` | **Passed** |

---

## 2. Automated Test Suite Distribution (466 Tests)

All 466 tests execute headlessly and pass without failures:

```
tests/
├── application/           (169 tests)
│   ├── rendering/         - Menu, game, completion screens, dispatcher, scaling
│   ├── test_cheat_*.py    - Cheat controller, HUD feedback, toggles
│   ├── test_context.py    - AppContext lifecycle, session resets
│   ├── test_game_state.py - State machine transitions
│   └── test_sprites.py    - Vector rendering geometry and calculations
├── gameplay/              (133 tests)
│   ├── test_player.py     - Physics, movement, buffered turns, tile alignment
│   ├── test_ghost_*.py    - Blinky, Pinky, Inky, Clyde targeting, fleeing, respawn
│   ├── test_pacgums.py    - Pellet grid, collection, scoring
│   ├── test_lives.py      - Life decrement, respawn positioning, game-over trigger
│   └── test_progression.py- Level advance, score carry-over, victory condition
├── infrastructure/        (44 tests)
│   ├── test_config.py     - Comment stripping, fallback clamping, invalid JSON
│   ├── test_highscore.py  - HighscoreEntry validation, sorting, top 10 truncation
│   └── test_storage.py    - Atomic writes, corruption recovery, file I/O safety
├── maze/                  (52 tests)
│   ├── test_maze_adapter.py - Wheel boundary, PERFECT=False, error recovery
│   ├── test_maze_grid.py    - Grid coordinates, flood-fill connectivity
│   └── test_spawns.py       - Safe corner spawns, center player placement
├── integration/           (66 tests)
    ├── test_full_game_flow.py      - Menu -> Play -> Win/Lose -> Name Entry -> Menu
    ├── test_lifecycle_cleanup.py   - Multi-cycle session resets, zero cheat leakage
    ├── test_live_configuration.py  - Live defense config overrides
    ├── test_soak_*.py              - 50,000 continuous ticks, floating-point drift
│   └── test_boundary_failures.py   - Corrupt files, missing wheel, zero tracebacks
└── project setup          (2 tests) - Required files, targets, and metadata
```

---

## 3. Manual Acceptance Testing Procedure (Evaluation Script)

Evaluators and peer reviewers can execute the following structured test path
during defense:

### Step 1: Quality Gate & Setup
```bash
make clean
make install
make lint-strict
make test
```
*Expected Result:* Clean virtual environment created, zero flake8/mypy errors,
466 tests passing.

### Step 2: Fault Tolerance Check
```bash
python3 pac-man.py non_existent_file.json
```
*Expected Result:* Emits a clear user-facing error and exits safely without
raising a Python traceback because the required configuration file is missing.

### Step 3: Main Menu & Highscores
- Launch the application: `make run`
- Navigate using Arrow keys or `W`/`S`.
- Open **Highscores**: Verify Top 10 list displays correctly. Press `Esc` to return.
- Open **Instructions**: Verify controls and rules are displayed. Press `Esc` to return.

### Step 4: Gameplay & Cheats Evaluation
- Start a game (`Enter` or `Space`).
- Move Pac-Man using Arrow keys or `WASD` (or Russian `ЦФЫВ`). Verify smooth
  corridor movement and wall collision.
- Press `P`: Verify the game pauses, ghosts stop moving, and the timer halts.
  Press `P` to resume.
- Press `F1`: Enable Cheat Mode. Verify the cheat control HUD appears.
- Press `1`: Toggle **Invincibility**. Walk into a ghost. Verify Pac-Man survives
  without losing a life.
- Press `3`: Toggle **Ghost Freeze**. Verify all 4 ghosts freeze in place.
- While freeze remains active, collect a super-pacgum. Verify all frozen ghosts
  become visibly frightened and can be eaten without resuming movement.
- Eat a ghost, then collect another super-pacgum while its eyes are waiting in
  the corner. Verify it remains inactive during respawn and returns frightened
  if the newer power timer is still active. Repeat with freeze enabled and
  verify the eyes remain visible and the respawn delay still completes.
- Press `4`: Add an extra life. Verify the HUD lives counter increments.
- Press `5`: Toggle **2x Speed**. Verify Pac-Man moves twice as fast. Toggle
  again to verify normal speed is restored. While boosted, buffer turns before
  several crossroads and walls; verify every legal turn remains available and
  Pac-Man never becomes stuck between tile centres.
- Press `2`: Skip level. Verify transition to Level 2 with preserved score and lives.
- Skip through to Level 10 using `2`, then skip once more to trigger **Victory**.

### Step 5: Name Entry & Persistence
- On the Victory / Game Over screen, type a valid name (e.g., `HERO 42`).
- Press `Enter`: Verify the score saves and returns to the Main Menu.
- Re-open **Highscores**: Verify `HERO 42` appears in the Top 10 list.
- Quit the game and re-launch: Verify the highscore persists across restarts.

---

## 4. PK-103 Clean-Machine Acceptance Record

**Date:** September 14, 2026

**Ownership:** Team

**Result:** Passed

The release was rebuilt with `make package`, extracted into a fresh temporary
directory outside the repository, and launched from the standalone executable
without the project virtual environment or source tree. The package contained
the executable, `config.json`, and `INSTRUCTIONS.txt`, and remained stable
during an isolated headless startup check.

The team then completed an interactive packaged-game review covering menu
navigation, player movement, cheats, super-pacgum behaviour, ghost eating and
respawn, scoring, level progression, completion/name entry, highscores, and
return to the main menu. Three acceptance defects were found, fixed, documented
in [`bug_triage.md`](bug_triage.md), and retested:

- **BUG-08:** 2x speed could skip the valid buffered-turn window.
- **BUG-09:** Frozen ghosts did not become visibly edible after a super-pacgum.
- **BUG-10:** Freeze could visually overwrite and indefinitely pause respawn;
  a newer power period was also lost while a ghost was inactive.

Final verification completed with 466 passing tests, flake8, strict mypy, a
successful package rebuild, and a repeated manual check of the corrected
standalone game.
