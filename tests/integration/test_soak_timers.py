"""Long-duration timer stability, drift, and boundary soak tests for PK-92."""

import pytest

from pacman.application.context import AppContext, GameSession
from pacman.application.state import update_active_gameplay
from pacman.gameplay.ghost import GhostIdentity, GhostState
from pacman.gameplay.ghost_gameplay import GhostGameplay
from pacman.infrastructure.config import GameConfig, LevelConfig
from pacman.maze.spawns import GhostSpawns
from tests.support.soak_harness import SoakSimulationHarness


def _test_ghost_spawns() -> GhostSpawns:
    """Return corner coordinates for ghost gameplay tests."""
    return GhostSpawns(
        top_left=(1, 1),
        top_right=(5, 1),
        bottom_left=(1, 5),
        bottom_right=(5, 5),
    )


def test_accumulated_tick_precision_over_50k_frames() -> None:
    """Verify 50k ticks with jittered dt accumulate without numeric drift."""
    session = GameSession(remaining_level_time=2000.0)
    jittered_dts = [0.015, 0.016, 0.018, 0.017, 0.0166]
    dt_cycle_len = len(jittered_dts)

    expected_elapsed = sum(
        jittered_dts[i % dt_cycle_len] for i in range(50000)
    )

    for i in range(50000):
        dt = jittered_dts[i % dt_cycle_len]
        session.update_level_timer(dt)

    assert session.remaining_level_time == pytest.approx(
        2000.0 - expected_elapsed,
        rel=1e-7,
    )
    assert not session.level_timed_out


def test_power_pellet_chaining_and_frightened_timer_endurance() -> None:
    """Verify 20 chained power refreshes preserve precision and recovery."""
    spawns = _test_ghost_spawns()
    config = GameConfig(
        frightened_duration=7.0,
        ghost_respawn_delay=5.0,
        seed=42,
    )
    gameplay = GhostGameplay.create(spawns=spawns, config=config)

    # Refresh power mode 20 times every 2.0 seconds
    for cycle in range(20):
        gameplay.activate_frightened()
        assert gameplay.power_state.remaining_time == pytest.approx(7.0)
        assert gameplay.power_state.is_active

        for ghost in gameplay.ghosts:
            assert ghost.state is GhostState.FRIGHTENED
            assert ghost.frightened_timer == pytest.approx(7.0)

        # Advance 2.0 seconds (120 frames at 1/60s)
        for _ in range(120):
            dt = 2.0 / 120.0
            gameplay.power_state.update(dt, gameplay.ghosts)
            for ghost in gameplay.ghosts:
                ghost.update(dt=dt)

        assert gameplay.power_state.remaining_time == pytest.approx(5.0)

    # Let the remaining 5.0 seconds expire (300 frames)
    for _ in range(300):
        dt = 5.0 / 300.0
        gameplay.power_state.update(dt, gameplay.ghosts)
        for ghost in gameplay.ghosts:
            ghost.update(dt=dt)

    assert gameplay.power_state.remaining_time == 0.0
    assert not gameplay.power_state.is_active
    for ghost in gameplay.ghosts:
        assert ghost.state is GhostState.NORMAL
        assert ghost.frightened_timer == 0.0


def test_pause_resume_drift_endurance_over_10k_frames() -> None:
    """Verify 10,000 alternating frames introduce zero timer leakage."""
    config = GameConfig(
        level_max_time=300,
        levels=[LevelConfig(width=7, height=7)],
        seed=42,
    )
    context = AppContext(config=config)
    context.start_new_game()
    context.cheat_mode.enabled = True
    context.cheat_mode.invincibility_enabled = True
    harness = SoakSimulationHarness(context=context)

    expected_active_time = 0.0
    frame_dt = 1.0 / 60.0

    # 100 alternating blocks: 50 playing frames, 50 paused frames
    for _ in range(100):
        # 50 playing frames
        context.session.resume_gameplay()
        for _ in range(50):
            harness.tick(dt=frame_dt)
            expected_active_time += frame_dt

        # 50 paused frames
        context.session.pause_gameplay()
        for _ in range(50):
            # Advance frame through update_active_gameplay directly
            update_active_gameplay(
                session=context.session,
                state_controller=harness.controller,
                dt=frame_dt,
            )

    assert context.session.remaining_level_time == pytest.approx(
        300.0 - expected_active_time,
        rel=1e-7,
    )
    assert not context.session.level_timed_out


def test_exact_timeout_boundary_precision_and_non_retriggering() -> None:
    """Verify timer triggers timeout once at boundary and stays clamped."""
    session = GameSession(remaining_level_time=90.0)

    # Advance 89.98 seconds
    for _ in range(8998):
        assert not session.update_level_timer(0.01)
    assert session.remaining_level_time == pytest.approx(0.02)
    assert not session.level_timed_out

    # Advance 0.01s -> 0.01s remaining
    assert not session.update_level_timer(0.01)
    assert session.remaining_level_time == pytest.approx(0.01)
    assert not session.level_timed_out

    # Advance 0.01s -> Exact timeout trigger
    assert session.update_level_timer(0.01)
    assert session.remaining_level_time == 0.0
    assert session.level_timed_out

    # Subsequent 500 frames must never re-trigger timeout or become negative
    for _ in range(500):
        assert not session.update_level_timer(0.016)
        assert session.remaining_level_time == 0.0
        assert session.level_timed_out


def test_ghost_respawn_timer_precision_and_recovery() -> None:
    """Verify all 4 eaten ghosts count down and respawn at exact intervals."""
    spawns = _test_ghost_spawns()
    config = GameConfig(
        ghost_respawn_delay=4.0,
        seed=42,
    )
    gameplay = GhostGameplay.create(spawns=spawns, config=config)

    # Put all 4 ghosts into RESPAWNING state
    for ghost in gameplay.ghosts:
        ghost.start_respawn(delay=4.0)
        assert ghost.state is GhostState.RESPAWNING
        assert ghost.respawn_timer == pytest.approx(4.0)

    # Advance 3.5 seconds (210 ticks at 1/60s)
    dt = 3.5 / 210.0
    for _ in range(210):
        for ghost in gameplay.ghosts:
            ghost.update(dt=dt)

    for ghost in gameplay.ghosts:
        assert ghost.state is GhostState.RESPAWNING
        assert ghost.respawn_timer == pytest.approx(0.5)

    # Advance remaining 0.5 seconds (30 ticks)
    dt = 0.5 / 30.0
    for _ in range(30):
        for ghost in gameplay.ghosts:
            ghost.update(dt=dt)

    for ghost in gameplay.ghosts:
        assert ghost.state is GhostState.NORMAL
        assert ghost.respawn_timer == 0.0
        assert ghost.identity in (
            GhostIdentity.BLINKY,
            GhostIdentity.PINKY,
            GhostIdentity.INKY,
            GhostIdentity.CLYDE,
        )
