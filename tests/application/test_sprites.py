"""Tests for procedural vector sprite generation."""

import pytest

from pacman.application.contracts import Color
from pacman.application.sprites import (
    CHERRY_RED,
    EYE_WHITE,
    FRIGHTENED_BLUE,
    FRIGHTENED_FACE_ORANGE,
    FRIGHTENED_FACE_RED,
    FRIGHTENED_WHITE,
    GHOST_PALETTES,
    PACGUM_COLOR,
    PACMAN_YELLOW,
    PUPIL_BLUE,
    STEM_GREEN,
    SUPER_PACGUM_COLOR,
    draw_bonus_fruit,
    draw_ghost,
    draw_pacgum,
    draw_pacman,
    draw_super_pacgum,
)
from pacman.gameplay.ghost import GhostIdentity, GhostState
from pacman.gameplay.player import Direction
from tests.support.app_fakes import _FakeDrawModule, _FakeSurface


@pytest.fixture
def draw_setup() -> tuple[_FakeSurface, _FakeDrawModule]:
    """Provide a fresh fake surface and fake draw module."""
    return _FakeSurface(), _FakeDrawModule()


def test_draw_pacman_closed_mouth(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
) -> None:
    """Verify closed-mouth Pac-Man renders as a single solid circle."""
    surface, draw = draw_setup
    center = (100, 100)
    radius = 16.0

    draw_pacman(surface, draw, center, radius, mouth_open=False)

    assert len(draw.circles) == 1
    assert draw.circles[0] == (PACMAN_YELLOW, center, radius, 0)
    assert len(draw.polygons) == 0


@pytest.mark.parametrize(
    ("direction", "expected_wedge_x_offset"),
    [
        (Direction.RIGHT, 16),
        (Direction.LEFT, -16),
        (Direction.NONE, 16),
    ],
)
def test_draw_pacman_horizontal_mouth_wedge(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
    direction: Direction,
    expected_wedge_x_offset: int,
) -> None:
    """Verify open-mouth Pac-Man cuts out a directional wedge."""
    surface, draw = draw_setup
    center = (100, 100)
    radius = 16.0

    draw_pacman(
        surface,
        draw,
        center,
        radius,
        direction=direction,
        mouth_open=True,
    )

    assert len(draw.circles) == 1
    assert len(draw.polygons) == 1
    _, wedge_points, _ = draw.polygons[0]
    assert wedge_points[0] == center
    assert wedge_points[1][0] == center[0] + expected_wedge_x_offset
    assert wedge_points[2][0] == center[0] + expected_wedge_x_offset


@pytest.mark.parametrize(
    ("direction", "expected_wedge_y_offset"),
    [
        (Direction.UP, -16),
        (Direction.DOWN, 16),
    ],
)
def test_draw_pacman_vertical_mouth_wedge(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
    direction: Direction,
    expected_wedge_y_offset: int,
) -> None:
    """Verify open-mouth vertical cuts point up and down."""
    surface, draw = draw_setup
    center = (100, 100)
    radius = 16.0

    draw_pacman(
        surface,
        draw,
        center,
        radius,
        direction=direction,
        mouth_open=True,
    )

    assert len(draw.polygons) == 1
    _, wedge_points, _ = draw.polygons[0]
    assert wedge_points[0] == center
    assert wedge_points[1][1] == center[1] + expected_wedge_y_offset
    assert wedge_points[2][1] == center[1] + expected_wedge_y_offset


@pytest.mark.parametrize("identity", list(GhostIdentity))
def test_draw_ghost_normal_body_color(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
    identity: GhostIdentity,
) -> None:
    """Verify each ghost renders with its authentic identity palette."""
    surface, draw = draw_setup
    center = (100, 100)
    radius = 16.0

    draw_ghost(surface, draw, center, radius, identity=identity)

    expected_color: Color = GHOST_PALETTES[identity]
    head_circle = draw.circles[0]
    assert head_circle[0] == expected_color
    torso_rect = draw.rectangles[0]
    assert torso_rect[0] == expected_color
    # 3 skirt scallops cutouts
    assert len(draw.polygons) == 3


def test_draw_ghost_frightened_blue(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
) -> None:
    """Verify frightened ghosts draw navy body, orange eyes, and mouth."""
    surface, draw = draw_setup
    center = (100, 100)
    radius = 16.0

    draw_ghost(
        surface,
        draw,
        center,
        radius,
        state=GhostState.FRIGHTENED,
        flash_white=False,
    )

    head_circle = draw.circles[0]
    assert head_circle[0] == FRIGHTENED_BLUE
    # Two orange eye dots
    assert draw.circles[1][0] == FRIGHTENED_FACE_ORANGE
    assert draw.circles[2][0] == FRIGHTENED_FACE_ORANGE
    # 3 mouth lines
    assert len(draw.lines) == 3
    for line in draw.lines:
        assert line[0] == FRIGHTENED_FACE_ORANGE


def test_draw_ghost_frightened_flashing_white(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
) -> None:
    """Verify flashing frightened ghosts draw white body and red face."""
    surface, draw = draw_setup
    center = (100, 100)
    radius = 16.0

    draw_ghost(
        surface,
        draw,
        center,
        radius,
        state=GhostState.FRIGHTENED,
        flash_white=True,
    )

    head_circle = draw.circles[0]
    assert head_circle[0] == FRIGHTENED_WHITE
    assert draw.circles[1][0] == FRIGHTENED_FACE_RED
    assert draw.circles[2][0] == FRIGHTENED_FACE_RED
    for line in draw.lines:
        assert line[0] == FRIGHTENED_FACE_RED


@pytest.mark.parametrize(
    "state",
    [GhostState.EATEN, GhostState.RESPAWNING],
)
def test_draw_ghost_eaten_only_renders_eyes(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
    state: GhostState,
) -> None:
    """Verify eaten/respawning ghosts omit body and draw eyes only."""
    surface, draw = draw_setup
    center = (100, 100)
    radius = 16.0

    draw_ghost(
        surface,
        draw,
        center,
        radius,
        state=state,
        direction=Direction.LEFT,
    )

    # No torso rectangle, no skirt polygons
    assert len(draw.rectangles) == 0
    assert len(draw.polygons) == 0
    # Only eye whites (2) and pupils (2)
    assert len(draw.circles) == 4
    assert draw.circles[0][0] == EYE_WHITE
    assert draw.circles[1][0] == EYE_WHITE
    assert draw.circles[2][0] == PUPIL_BLUE
    assert draw.circles[3][0] == PUPIL_BLUE


def test_draw_pacgum(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
) -> None:
    """Verify pacgum renders as a single centered pellet."""
    surface, draw = draw_setup
    center = (50, 50)
    radius = 3.0

    draw_pacgum(surface, draw, center, radius)

    assert len(draw.circles) == 1
    assert draw.circles[0] == (PACGUM_COLOR, center, radius, 0)


def test_draw_super_pacgum_scaling(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
) -> None:
    """Verify super-pacgum radius scales with the pulse ratio."""
    surface, draw = draw_setup
    center = (50, 50)
    base_radius = 6.0
    pulse_ratio = 1.25

    draw_super_pacgum(
        surface,
        draw,
        center,
        base_radius,
        pulse_ratio=pulse_ratio,
    )

    assert len(draw.circles) == 1
    assert draw.circles[0] == (
        SUPER_PACGUM_COLOR,
        center,
        base_radius * pulse_ratio,
        0,
    )


def test_draw_bonus_fruit(
    draw_setup: tuple[_FakeSurface, _FakeDrawModule],
) -> None:
    """Verify bonus fruit renders two cherries, stems, and leaf."""
    surface, draw = draw_setup
    center = (200, 200)
    radius = 16.0

    draw_bonus_fruit(surface, draw, center, radius)

    # 2 cherries
    assert len(draw.circles) == 2
    assert draw.circles[0][0] == CHERRY_RED
    assert draw.circles[1][0] == CHERRY_RED
    # 2 stems
    assert len(draw.lines) == 2
    assert draw.lines[0][0] == STEM_GREEN
    assert draw.lines[1][0] == STEM_GREEN
    # 1 leaf
    assert len(draw.polygons) == 1
    assert draw.polygons[0][0] == STEM_GREEN
