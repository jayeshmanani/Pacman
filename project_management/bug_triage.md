# Defect Triage Register (PK-93 and PK-103)

This register records defects, regressions, and boundary anomalies discovered
during robustness testing (PK-89, PK-90), live configuration testing (PK-91),
long-play multi-level soak testing (PK-92), and clean-machine packaged-game
acceptance (PK-103). It documents reproduction steps, severity classification,
root-cause analysis, and final disposition in accordance with Chapter VIII of
the 42 Pacman subject.

---

## Triage Summary Matrix

| Bug ID | Title | Discovered In | Severity | Owner | Disposition | Resolution / Verification |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **BUG-01** | Floating-point timer residual drift | PK-92 | High | Jayesh | Fixed Immediately | Timer snapping ($\epsilon \le 10^{-9}\text{s}$) in `power_state.py`, `ghost.py`, `context.py` |
| **BUG-02** | Unhandled `ValueError` on direct invalid name input | PK-92 | Medium | Jayesh | Fixed Immediately | `try/except` fallback in `PlayerNameInput.create_entry()` |
| **BUG-03** | Active cheat state leakage across session resets | PK-90 | High | Jayesh | Fixed Immediately | Added `cheat_mode.reset()` in `AppContext.reset_session()` |
| **BUG-04** | Main menu cursor lingering on non-start option | PK-90 | Low | Mariia | Fixed Immediately | Explicit `reset_selection()` on return to menu |
| **BUG-05** | Configured `pacgum` count ignored by level generator | PK-91 | Medium | Mariia | Fixed Immediately | Dual-mode support (`pacgum_configured`) in `LevelGenerator` |
| **BUG-06** | Victory progression desynchronized from `levels` count | PK-91 | High | Mariia | Fixed Immediately | Dynamically bind `session.total_levels = len(config.levels)` |
| **BUG-07** | External maze package stdout warning on small mazes | PK-89/92 | Low | Team | Accepted | Upstream wheel behavior; harmless per Chapter V.4 |
| **BUG-08** | Speed boost could skip buffered turns | PK-103 | High | Team | Fixed Immediately | Collision-safe movement substeps and a boosted-crossroads regression test |
| **BUG-09** | Frozen ghosts ignored frightened mode | PK-103 | High | Team | Fixed Immediately | Freeze now preserves edible state, rendering, and collision behaviour |
| **BUG-10** | Respawned ghost missed a newer power mode | PK-103 | High | Team | Fixed Immediately | New frightened activation is deferred until the inactive ghost returns |

---

## Detailed Bug Reports

### BUG-01: Floating-Point Timer Residual Drift

- **Component:** `pacman.gameplay.power_state`, `pacman.gameplay.ghost`, `pacman.application.context`
- **Severity:** High (Game rule / timing accuracy)
- **Owner:** Jayesh
- **Status:** Fixed Immediately
- **Discovered In:** PK-92 Soak Testing

#### Description
When running continuous multi-frame simulations over hundreds or thousands of
frames, repeated floating-point delta-time subtractions ($t \leftarrow t - \Delta t$)
left minute residual values on the order of $\approx 10^{-14}\text{s}$ to
$10^{-15}\text{s}$ instead of cleanly reaching exact `0.0`.

#### Impact
1. `PowerState.remaining_time` evaluated to `1.98e-14`, keeping `is_active` (`remaining_time > 0.0`)
   `True` for phantom frames after super-pacgum expiration.
2. Eaten ghosts in `RESPAWNING` state retained a `respawn_timer` of `9.20e-15`,
   delaying their return to `NORMAL` state.
3. `GameSession.remaining_level_time` could retain microsecond residuals near
   boundary transitions.

#### Reproduction Steps
1. Create a `PowerState` instance with `remaining_time = 5.0`.
2. Advance 300 discrete frames with $dt = 5.0 / 300.0$.
3. Check `remaining_time == 0.0`.
4. *Observed:* `remaining_time == 1.9866e-14` ($> 0.0$).

#### Resolution
Added an $\epsilon \le 10^{-9}\text{s}$ threshold snap across all timing updates:
- `PowerState.update`: Snaps `self.remaining_time = 0.0` when $\le 10^{-9}\text{s}$.
- `Ghost.update`: Snaps `frightened_timer` and `respawn_timer` when $\le 10^{-9}\text{s}$.
- `GameSession.update_level_timer`: Snaps `remaining_level_time = 0.0` and triggers
  timeout when $\le 10^{-9}\text{s}$.

#### Verification
Covered in `tests/integration/test_soak_timers.py`:
- `test_power_pellet_chaining_and_frightened_timer_endurance`
- `test_ghost_respawn_timer_precision_and_recovery`
- `test_exact_timeout_boundary_precision_and_non_retriggering`

---

### BUG-02: Unhandled `ValueError` in Player Name Input

- **Component:** `pacman.application.player_name_input`
- **Severity:** Medium (Unhandled exception avoidance)
- **Owner:** Jayesh
- **Status:** Fixed Immediately
- **Discovered In:** PK-92 Lifecycle Soak Testing

#### Description
While keyboard input in the UI filters keystrokes via `add_character()`, direct
assignment to `PlayerNameInput.value` (or unescaped string injection) with
illegal symbols (e.g. `!`, `@`, `-`) caused `create_entry()` to throw an
unhandled `ValueError` from `HighscoreEntry.__post_init__`.

#### Impact
Violated Chapter III and Chapter V.1 requirements: *"Functions should handle
exceptions gracefully to avoid crashes... never with a Python traceback."*

#### Reproduction Steps
1. Set `player_name_input.value = "CHAMP!"`.
2. Invoke `player_name_input.create_entry(score=500)`.
3. *Observed:* Unhandled `ValueError: name must contain only letters, numbers, and spaces`.

#### Resolution
Hardened `PlayerNameInput.create_entry()` with a `try/except (ValueError, TypeError)`
guard. If validation fails, `self.error_message` is safely populated with the
validation reason and `None` is returned cleanly.

#### Verification
Covered in:
- `tests/application/test_player_name_input.py` (`test_player_name_input_create_entry_catches_invalid_name`)
- `tests/integration/test_soak_lifecycle.py` (`test_highscore_io_endurance_under_100_submissions`)

---

### BUG-03: Active Cheat State Leakage Across Session Reset

- **Component:** `pacman.application.context`
- **Severity:** High (State isolation / review integrity)
- **Owner:** Jayesh
- **Status:** Fixed Immediately
- **Discovered In:** PK-90 Lifecycle Audit

#### Description
When a player activated cheats during active gameplay (such as 2x speed boost
or invincibility) and then abandoned the game or returned to the main menu,
`AppContext.reset_session()` cleared session metrics but left cheat flags enabled.

#### Impact
A subsequent playthrough or new game launched from the main menu unexpectedly
inherited active speed multipliers and invincibility without pressing `F1`.

#### Reproduction Steps
1. Start game, press `F1` and `5` (speed boost).
2. Press `Esc` to return to Main Menu.
3. Start a fresh game from Main Menu.
4. *Observed:* Pac-Man retained 2x movement speed in standard play.

#### Resolution
Added an explicit `self.cheat_mode.reset()` inside `AppContext.reset_session()`.

#### Verification
Covered in `tests/integration/test_lifecycle_cleanup.py` and
`tests/integration/test_soak_lifecycle.py`.

---

### BUG-04: Main Menu Selection Lingering on Non-Start Option

- **Component:** `pacman.application.runtime`
- **Severity:** Low (UI usability)
- **Owner:** Team
- **Status:** Fixed Immediately
- **Discovered In:** PK-90 Lifecycle Audit

#### Description
If a user navigated down the Main Menu to "View Highscores" or "Instructions",
started a game, and then returned to the menu, the menu cursor remained on the
previously selected option instead of resetting to `Start Game`.

#### Impact
Subsequent `Enter` presses from the menu unexpectedly re-opened the instructions
or highscores screen rather than launching a new game session.

#### Reproduction Steps
1. In Main Menu, press `Down` to highlight "Instructions".
2. Return to Main Menu from gameplay or pause.
3. Press `Enter`.
4. *Observed:* Instructions opened instead of starting a game.

#### Resolution
Added an explicit `main_menu.reset_selection()` on all state transitions returning
to `GameState.MAIN_MENU`.

#### Verification
Covered in `tests/application/test_app_window.py` and
`tests/integration/test_lifecycle_cleanup.py`.

---

### BUG-05: Configured `pacgum` Count Ignored by Level Generator

- **Component:** `pacman.maze.level_generator`, `pacman.infrastructure.config`
- **Severity:** Medium (Configuration compliance)
- **Owner:** Team
- **Status:** Fixed Immediately
- **Discovered In:** PK-91 Live Config Testing

#### Description
The root `config.json` specifies `"pacgum": 42`, but `LevelGenerator` unconditionally
called `place_pacgums(maze, spawns)` without forwarding a target count, always
filling all eligible reachable corridors.

#### Impact
Evaluating reviewers modifying `"pacgum"` in `config.json` during defense saw
no change in pellet counts.

#### Reproduction Steps
1. Set `"pacgum": 5` in `config.json`.
2. Launch game and check corridor dots.
3. *Observed:* Corridors were completely full with 100+ pellets.

#### Resolution
Added `pacgum_configured: bool` to `GameConfig`. If `"pacgum"` is explicitly present
in JSON, `normal_count = config.pacgum` is passed to `place_pacgums`; if omitted,
it defaults to the full corridor filling mode.

#### Verification
Covered in `tests/integration/test_live_configuration.py`
(`test_configured_pacgum_count_limits_generated_normal_pacgums`).

---

### BUG-06: Victory Progression Desynchronized from `levels` Count

- **Component:** `pacman.application.context`, `pacman.gameplay.progression`
- **Severity:** High (Progression defect)
- **Owner:** Team
- **Status:** Fixed Immediately
- **Discovered In:** PK-91 Live Config Testing

#### Description
When evaluators altered `config.json` to define fewer levels (e.g. 2 levels for
quick testing), `GameSession.total_levels` remained at its default count, causing
the game to attempt generating level 3 instead of triggering Victory.

#### Impact
Reviewers could not verify game victory without playing through all 10 default levels.

#### Reproduction Steps
1. Set `"levels": [{"width": 21, "height": 21}, {"width": 21, "height": 21}]` in config.
2. Complete Level 2.
3. *Observed:* Game failed to transition to `GameState.VICTORY`.

#### Resolution
Updated `AppContext._configure_session()` to dynamically set:
`session.total_levels = len(self.config.levels)`.

#### Verification
Covered in `tests/integration/test_live_configuration.py`
(`test_configured_levels_define_session_total_level_count`) and
`tests/integration/test_soak_progression.py`.

---

### BUG-07: External Maze Package Stdout Warning on Small Mazes

- **Component:** External `mazegenerator` package boundary
- **Severity:** Low (Upstream informational notice)
- **Owner:** Team
- **Status:** Accepted (Third-Party Constraint)
- **Discovered In:** PK-89 / PK-92

#### Description
When generating mazes smaller than $21 \times 21$ cells with `include_42=True`, the
assigned external `mazegenerator` wheel prints an informational notice to stdout:
`MazeGenerator Warning: maze is too small to add '42' in it`.

#### Impact
Harmless warning string emitted during testing or small custom configurations.
Grid normalization and reachability validation are completely unaffected.

#### Triage Decision
**Accepted as external package constraint.**
Chapter V.4 of the subject states: *"You must use their package as-is, without
modifying it. Your loader must adapt to their interface, not the opposite."*
Because modifying upstream wheel source code is prohibited and the warning does
not cause runtime errors, this behavior is accepted.

---

### BUG-08: Speed Boost Could Skip Buffered Turns

- **Component:** `pacman.gameplay.player`
- **Severity:** High (Player movement / packaged-game playability)
- **Owner:** Mariia
- **Status:** Fixed Immediately
- **Discovered In:** PK-103 Clean-Machine Acceptance Testing

#### Description
With the 2x speed cheat enabled, one frame could move Pac-Man beyond the centre
of an intersection before the buffered perpendicular direction was checked.
Once offset from the corridor centre, wall collision correctly rejected the
turn from that invalid alignment. Pac-Man could then reach a wall and appear
stuck, with only the reverse direction available.

#### Reproduction Steps
1. Enable Cheat Mode with `F1`, then enable 2x speed with `5`.
2. Move toward a crossroads and buffer a perpendicular turn before reaching it.
3. Repeat near a corridor end or with a longer frame interval.
4. *Observed:* Pac-Man crossed the tile centre, did not turn, and could become
   limited to the opposite direction.

#### Root Cause
`Player.update()` applied the entire frame distance in one collision query. At
boosted speed, that distance was large enough to skip the valid turning window
inside the crossed tile.

#### Resolution
Split each frame's travel into collision-safe movement substeps. Buffered turns
are now retried throughout the frame, so an intersection cannot be skipped while
the existing wall checks, speed multiplier, and corner alignment remain intact.

#### Verification
Covered by `test_speed_multiplier_does_not_skip_buffered_crossroads_turn` in
`tests/gameplay/test_player.py`, together with the existing movement, wall
collision, cheat-action, evaluation-flow, and high-speed soak tests.

---

### BUG-09: Frozen Ghosts Ignored Frightened Mode

- **Component:** `pacman.gameplay.ghost`, `pacman.gameplay.ghost_collision`,
  `pacman.application.rendering.game`
- **Severity:** High (Power-mode rules / acceptance playability)
- **Owner:** Mariia
- **Status:** Fixed Immediately
- **Discovered In:** PK-103 Clean-Machine Acceptance Testing

#### Description
When ghost freeze was already active, collecting a super-pacgum left every
ghost stationary but did not make the ghosts visibly edible or allow Pac-Man
to eat them.

#### Root Cause
Movement freeze was represented by `GhostState.FROZEN`, and frightened
activation treated that state as ineligible. Rendering and collision handling
also inspected only the outer state, so they could not represent frightened
mode underneath the independent freeze effect.

#### Resolution
Frozen ghosts now preserve `FRIGHTENED` as their underlying state while their
outer `FROZEN` state continues to stop movement. The edible state is used by
rendering and collision resolution, and expiration still clears it safely.
Eaten and actively respawning ghosts remain collision-ineligible.

#### Verification
Focused tests cover activation during freeze, unchanged positions, frightened
rendering, edible collision and scoring, respawn, unfreezing, and timer expiry.

---

### BUG-10: Respawned Ghost Missed a Newer Power Mode

- **Component:** `pacman.gameplay.ghost`, `pacman.gameplay.ghost_gameplay`,
  `pacman.gameplay.power_state`
- **Severity:** High (Repeated power-mode activation / state transition)
- **Owner:** Mariia
- **Status:** Fixed Immediately
- **Discovered In:** PK-103 Clean-Machine Acceptance Testing

#### Description
If another super-pacgum was collected while an eaten ghost was waiting in its
corner, that ghost correctly remained inactive during respawn but returned as
a normal full-colour ghost even though the newer power period was still active.
With ghost freeze enabled, the respawning ghost could also be wrapped in
`FROZEN`, making the eyes appear as a full-colour stationary ghost and pausing
the respawn timer indefinitely.

#### Root Cause
Frightened activation ignored `RESPAWNING` completely, so the ghost had no way
to remember that a newer power period started while it was inactive. The freeze
transition also treated inactive `EATEN` and `RESPAWNING` states as ordinary
moving ghosts.

#### Resolution
A new frightened activation is now deferred for a respawning ghost without
interrupting its safe, eyes-only respawn state. When the delay finishes, the
ghost becomes frightened for the shared power timer's remaining duration. If
that timer expires first, the deferred state is cleared and the ghost returns
normally. Freeze now applies only to active normal or frightened ghosts; eaten
and respawning ghosts remain eyes-only and continue their safe return timer.
The respawn completion frame no longer applies a full frame of movement from
the corner.

#### Verification
Focused tests cover a second power activation during respawn, frightened return
with the remaining shared duration, expiry before return, and preservation of
the existing collision and score protections while the ghost is inactive. They
also verify that freeze cannot pause or visually overwrite respawn.
