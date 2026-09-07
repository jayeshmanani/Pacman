"""Procedural vector sprites for Pac-Man, ghosts, pellets, and bonuses."""

from typing import Final

from pacman.application.contracts import Color, Coordinate, DrawModule, Surface
from pacman.gameplay.ghost import GhostIdentity, GhostState
from pacman.gameplay.player import Direction


PACMAN_YELLOW: Final[Color] = (255, 238, 0)

GHOST_PALETTES: Final[dict[GhostIdentity, Color]] = {
    GhostIdentity.BLINKY: (255, 0, 0),
    GhostIdentity.PINKY: (255, 184, 255),
    GhostIdentity.INKY: (0, 255, 255),
    GhostIdentity.CLYDE: (255, 184, 82),
}

FRIGHTENED_BLUE: Final[Color] = (33, 33, 222)
FRIGHTENED_WHITE: Final[Color] = (255, 255, 255)
FRIGHTENED_FACE_ORANGE: Final[Color] = (255, 184, 82)
FRIGHTENED_FACE_RED: Final[Color] = (255, 0, 0)

EYE_WHITE: Final[Color] = (255, 255, 255)
PUPIL_BLUE: Final[Color] = (33, 33, 222)

PACGUM_COLOR: Final[Color] = (255, 183, 174)
SUPER_PACGUM_COLOR: Final[Color] = (255, 220, 200)

CHERRY_RED: Final[Color] = (215, 0, 0)
STEM_GREEN: Final[Color] = (34, 177, 76)


def draw_pacman(
    surface: Surface,
    draw: DrawModule,
    center: Coordinate,
    radius: float,
    direction: Direction = Direction.RIGHT,
    mouth_open: bool = True,
    background_color: Color = (0, 0, 0),
) -> None:
    """Draw Pac-Man with directional orientation and animated mouth wedge."""
    cx, cy = center
    draw.circle(surface, PACMAN_YELLOW, center, radius)

    if not mouth_open:
        return

    r = int(radius)
    spread = int(r * 0.55)

    if direction is Direction.LEFT:
        wedge = [center, (cx - r, cy - spread), (cx - r, cy + spread)]
    elif direction is Direction.UP:
        wedge = [center, (cx - spread, cy - r), (cx + spread, cy - r)]
    elif direction is Direction.DOWN:
        wedge = [center, (cx - spread, cy + r), (cx + spread, cy + r)]
    else:
        wedge = [center, (cx + r, cy - spread), (cx + r, cy + spread)]

    draw.polygon(surface, background_color, wedge)


def draw_ghost(
    surface: Surface,
    draw: DrawModule,
    center: Coordinate,
    radius: float,
    identity: GhostIdentity = GhostIdentity.BLINKY,
    state: GhostState = GhostState.NORMAL,
    direction: Direction = Direction.RIGHT,
    flash_white: bool = False,
    background_color: Color = (0, 0, 0),
) -> None:
    """Draw a ghost in normal, frightened, flashing, or eaten/eyes state."""
    cx, cy = center
    r = int(radius)

    if state not in (GhostState.EATEN, GhostState.RESPAWNING):
        if state is GhostState.FRIGHTENED:
            body_color = FRIGHTENED_WHITE if flash_white else FRIGHTENED_BLUE
        else:
            body_color = GHOST_PALETTES.get(identity, (255, 0, 0))

        head_center = (cx, cy - int(r * 0.2))
        draw.circle(surface, body_color, head_center, radius)

        rect_y = cy - int(r * 0.2)
        rect_h = int(r * 1.2)
        draw.rect(
            surface,
            body_color,
            (cx - r, rect_y, 2 * r, rect_h),
        )

        bottom_y = cy + r
        sw = max(1, int(r * 0.22))
        sh = max(1, int(r * 0.35))
        for scallop_cx in (cx - int(r * 0.55), cx, cx + int(r * 0.55)):
            scallop = [
                (scallop_cx - sw, bottom_y),
                (scallop_cx, bottom_y - sh),
                (scallop_cx + sw, bottom_y),
            ]
            draw.polygon(surface, background_color, scallop)

    if state is GhostState.FRIGHTENED:
        face_color = (
            FRIGHTENED_FACE_RED if flash_white else FRIGHTENED_FACE_ORANGE
        )
        eye_r = max(1.0, radius * 0.18)
        draw.circle(
            surface,
            face_color,
            (cx - int(r * 0.35), cy - int(r * 0.1)),
            eye_r,
        )
        draw.circle(
            surface,
            face_color,
            (cx + int(r * 0.35), cy - int(r * 0.1)),
            eye_r,
        )

        mouth_y = cy + int(r * 0.35)
        p1 = (cx - int(r * 0.45), mouth_y)
        p2 = (cx - int(r * 0.15), mouth_y - max(1, int(r * 0.1)))
        p3 = (cx + int(r * 0.15), mouth_y)
        p4 = (cx + int(r * 0.45), mouth_y - max(1, int(r * 0.1)))
        draw.line(surface, face_color, p1, p2, max(1, int(r * 0.1)))
        draw.line(surface, face_color, p2, p3, max(1, int(r * 0.1)))
        draw.line(surface, face_color, p3, p4, max(1, int(r * 0.1)))
    else:
        dx, dy = 0, 0
        offset = max(1, int(r * 0.22))
        if direction is Direction.UP:
            dy = -offset
        elif direction is Direction.DOWN:
            dy = offset
        elif direction is Direction.LEFT:
            dx = -offset
        else:
            dx = offset

        eye_radius = max(2.0, radius * 0.3)
        pupil_radius = max(1.0, radius * 0.16)
        eye_spacing = int(r * 0.36)
        eye_y = cy - int(r * 0.15)

        left_eye = (cx - eye_spacing + dx, eye_y + dy)
        right_eye = (cx + eye_spacing + dx, eye_y + dy)

        draw.circle(surface, EYE_WHITE, left_eye, eye_radius)
        draw.circle(surface, EYE_WHITE, right_eye, eye_radius)

        pupil_dx = int(dx * 0.5)
        pupil_dy = int(dy * 0.5)
        left_pupil = (left_eye[0] + pupil_dx, left_eye[1] + pupil_dy)
        right_pupil = (right_eye[0] + pupil_dx, right_eye[1] + pupil_dy)

        draw.circle(surface, PUPIL_BLUE, left_pupil, pupil_radius)
        draw.circle(surface, PUPIL_BLUE, right_pupil, pupil_radius)


def draw_pacgum(
    surface: Surface,
    draw: DrawModule,
    center: Coordinate,
    radius: float,
    color: Color = PACGUM_COLOR,
) -> None:
    """Draw a compact circular pacgum dot."""
    draw.circle(surface, color, center, max(1.5, radius))


def draw_super_pacgum(
    surface: Surface,
    draw: DrawModule,
    center: Coordinate,
    radius: float,
    pulse_ratio: float = 1.0,
    color: Color = SUPER_PACGUM_COLOR,
) -> None:
    """Draw a glowing, scaled super-pacgum pellet."""
    scaled_radius = max(2.0, radius * pulse_ratio)
    draw.circle(surface, color, center, scaled_radius)


def draw_bonus_fruit(
    surface: Surface,
    draw: DrawModule,
    center: Coordinate,
    radius: float,
) -> None:
    """Draw a retro double-cherry bonus item with stems and leaf."""
    cx, cy = center
    r = int(radius)
    cherry_radius = max(2.0, radius * 0.42)

    draw.circle(
        surface,
        CHERRY_RED,
        (cx - int(r * 0.35), cy + int(r * 0.25)),
        cherry_radius,
    )
    draw.circle(
        surface,
        CHERRY_RED,
        (cx + int(r * 0.35), cy + int(r * 0.38)),
        cherry_radius,
    )

    stem_apex = (cx + int(r * 0.1), cy - int(r * 0.55))
    stem_width = max(1, int(r * 0.12))
    draw.line(
        surface,
        STEM_GREEN,
        (cx - int(r * 0.35), cy + int(r * 0.1)),
        stem_apex,
        stem_width,
    )
    draw.line(
        surface,
        STEM_GREEN,
        (cx + int(r * 0.35), cy + int(r * 0.2)),
        stem_apex,
        stem_width,
    )

    leaf_poly = [
        stem_apex,
        (stem_apex[0] + int(r * 0.35), stem_apex[1] - int(r * 0.2)),
        (stem_apex[0] + int(r * 0.45), stem_apex[1] + int(r * 0.05)),
    ]
    draw.polygon(surface, STEM_GREEN, leaf_poly)
