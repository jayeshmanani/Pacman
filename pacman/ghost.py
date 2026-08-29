"""Ghost state model and state machine definitions."""

import random
from dataclasses import dataclass
from enum import Enum, auto

from pacman.maze_grid import TileCoordinate
from pacman.player import Direction
from pacman.spawns import GhostSpawns
from pacman.world import WorldMap, WorldPosition


class GhostState(Enum):
    """Explicit behavioral states for a ghost entity."""

    NORMAL = auto()
    FRIGHTENED = auto()
    EATEN = auto()
    RESPAWNING = auto()
    FROZEN = auto()


class GhostIdentity(Enum):
    """Arcade ghost identities with assigned corner spawns."""

    BLINKY = "Blinky"
    PINKY = "Pinky"
    INKY = "Inky"
    CLYDE = "Clyde"


@dataclass
class Ghost:
    """Represent an individual ghost entity and its state machine."""

    identity: GhostIdentity
    home_spawn: TileCoordinate
    position: WorldPosition
    direction: Direction = Direction.NONE
    state: GhostState = GhostState.NORMAL
    previous_state: GhostState | None = None
    target_tile: TileCoordinate | None = None
    frightened_timer: float = 0.0
    respawn_timer: float = 0.0
    speed_multiplier: float = 1.0

    @classmethod
    def from_spawn(
        cls,
        identity: GhostIdentity,
        spawn_tile: TileCoordinate,
        speed_multiplier: float = 1.0,
    ) -> "Ghost":
        """Create a ghost centered at its assigned spawn tile coordinate."""
        x, y = spawn_tile
        return cls(
            identity=identity,
            home_spawn=spawn_tile,
            position=(x + 0.5, y + 0.5),
            direction=Direction.NONE,
            state=GhostState.NORMAL,
            speed_multiplier=speed_multiplier,
        )

    def frighten(self, duration: float = 7.0) -> bool:
        """Transition ghost to FRIGHTENED state if currently eligible."""
        if duration < 0:
            raise ValueError("frightened duration cannot be negative")

        ineligible_states = (
            GhostState.FROZEN,
            GhostState.EATEN,
            GhostState.RESPAWNING,
        )
        if self.state in ineligible_states:
            return False

        self.state = GhostState.FRIGHTENED
        self.frightened_timer = float(duration)
        return True

    def eat(self) -> bool:
        """Transition frightened ghost to EATEN state when caught."""
        if self.state != GhostState.FRIGHTENED:
            return False

        self.state = GhostState.EATEN
        self.frightened_timer = 0.0
        return True

    def start_respawn(self, delay: float = 5.0) -> None:
        """Return ghost to home spawn and transition to RESPAWNING."""
        if delay < 0:
            raise ValueError("respawn delay cannot be negative")

        hx, hy = self.home_spawn
        self.position = (hx + 0.5, hy + 0.5)
        self.direction = Direction.NONE
        self.state = GhostState.RESPAWNING
        self.respawn_timer = float(delay)
        self.frightened_timer = 0.0

    def freeze(self) -> bool:
        """Freeze ghost movement and timers for cheat mode or pause."""
        if self.state == GhostState.FROZEN:
            return False

        self.previous_state = self.state
        self.state = GhostState.FROZEN
        return True

    def unfreeze(self) -> bool:
        """Restore ghost state prior to being frozen."""
        if self.state != GhostState.FROZEN:
            return False

        restored_state = (
            self.previous_state
            if self.previous_state is not None
            else GhostState.NORMAL
        )
        self.state = restored_state
        self.previous_state = None
        return True

    def update(
        self,
        dt: float,
        world: WorldMap | None = None,
        base_speed: float = 4.0,
        rng: random.Random | None = None,
        player_position: WorldPosition | None = None,
        player_direction: Direction = Direction.NONE,
        blinky_tile: TileCoordinate | None = None,
    ) -> None:
        """Advance ghost timers and perform movement if world is provided."""
        if dt <= 0 or self.state == GhostState.FROZEN:
            return

        if self.state == GhostState.FRIGHTENED:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0.0:
                self.frightened_timer = 0.0
                self.state = GhostState.NORMAL

        elif self.state == GhostState.RESPAWNING:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.respawn_timer = 0.0
                self.state = GhostState.NORMAL

        if world is not None and self.state != GhostState.RESPAWNING:
            self._move(
                dt,
                world,
                base_speed,
                rng,
                player_position,
                player_direction,
                blinky_tile,
            )

    def _move(
        self,
        dt: float,
        world: WorldMap,
        base_speed: float = 4.0,
        rng: random.Random | None = None,
        player_position: WorldPosition | None = None,
        player_direction: Direction = Direction.NONE,
        blinky_tile: TileCoordinate | None = None,
    ) -> None:
        """Advance ghost position along corridors and align to tile axes."""
        speed = base_speed * self.speed_multiplier
        if self.state == GhostState.FRIGHTENED:
            speed *= 0.5
        elif self.state == GhostState.EATEN:
            speed *= 1.5

        current_tile = world.world_to_tile(self.position)
        legal_dirs = get_legal_ghost_directions(
            tile=current_tile,
            current_direction=self.direction,
            world=world,
            allow_reversal=(self.state == GhostState.FRIGHTENED),
        )

        is_blocked = (
            self.direction == Direction.NONE
            or self.direction not in legal_dirs
        )
        is_intersection = len(legal_dirs) > 1

        if is_blocked or is_intersection:
            if legal_dirs and legal_dirs[0] != Direction.NONE:
                if rng is not None or self.state == GhostState.FRIGHTENED:
                    chooser = rng if rng is not None else random
                    self.direction = chooser.choice(legal_dirs)
                else:
                    target_player_pos = (
                        player_position
                        if player_position is not None
                        else self.position
                    )
                    player_tile = world.world_to_tile(target_player_pos)
                    target = calculate_ghost_target(
                        identity=self.identity,
                        ghost_tile=current_tile,
                        player_tile=player_tile,
                        player_direction=player_direction,
                        home_spawn=self.home_spawn,
                        blinky_tile=blinky_tile,
                    )
                    self.target_tile = target
                    self.direction = select_chase_direction(
                        current_tile=current_tile,
                        target_tile=target,
                        legal_directions=legal_dirs,
                    )

        if self.direction == Direction.NONE:
            return

        dx, dy = self.direction.vector
        new_x = self.position[0] + dx * speed * dt
        new_y = self.position[1] + dy * speed * dt

        if dx != 0:
            new_y = current_tile[1] + 0.5
        elif dy != 0:
            new_x = current_tile[0] + 0.5

        target_position = (new_x, new_y)

        if world.can_occupy(target_position, half_size=(0.35, 0.35)):
            self.position = target_position
        else:
            cx, cy = world.tile_center(current_tile)
            self.position = (cx, cy)
            self.direction = Direction.NONE


def calculate_ghost_target(
    identity: GhostIdentity,
    ghost_tile: TileCoordinate,
    player_tile: TileCoordinate,
    player_direction: Direction,
    home_spawn: TileCoordinate,
    blinky_tile: TileCoordinate | None = None,
) -> TileCoordinate:
    """Calculate target tile for a ghost during NORMAL chase state."""
    px, py = player_tile

    if identity == GhostIdentity.BLINKY:
        return (px, py)

    if identity == GhostIdentity.PINKY:
        p_dx, p_dy = player_direction.vector
        return (int(px + int(4 * p_dx)), int(py + int(4 * p_dy)))

    if identity == GhostIdentity.INKY:
        b_tile = blinky_tile if blinky_tile is not None else home_spawn
        p_dx, p_dy = player_direction.vector
        pivot_x = px + int(2 * p_dx)
        pivot_y = py + int(2 * p_dy)
        target_x = pivot_x + (pivot_x - b_tile[0])
        target_y = pivot_y + (pivot_y - b_tile[1])
        return (target_x, target_y)

    if identity == GhostIdentity.CLYDE:
        gx, gy = ghost_tile
        dist_sq = (gx - px) ** 2 + (gy - py) ** 2
        if dist_sq > 64:
            return (px, py)
        return home_spawn

    return (px, py)


def select_chase_direction(
    current_tile: TileCoordinate,
    target_tile: TileCoordinate,
    legal_directions: list[Direction],
) -> Direction:
    """Select direction minimizing distance squared to target."""
    if not legal_directions or legal_directions == [Direction.NONE]:
        return Direction.NONE

    if len(legal_directions) == 1:
        return legal_directions[0]

    priority = {
        Direction.UP: 0,
        Direction.LEFT: 1,
        Direction.DOWN: 2,
        Direction.RIGHT: 3,
    }

    best_direction = legal_directions[0]
    min_dist_sq = float("inf")

    tx, ty = target_tile
    cx, cy = current_tile

    for direction in legal_directions:
        if direction == Direction.NONE:
            continue
        dx, dy = direction.vector
        nx = cx + int(dx)
        ny = cy + int(dy)
        dist_sq = (nx - tx) ** 2 + (ny - ty) ** 2

        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            best_direction = direction
        elif dist_sq == min_dist_sq:
            if priority.get(direction, 99) < priority.get(best_direction, 99):
                best_direction = direction

    return best_direction


def select_frightened_direction(
    current_tile: TileCoordinate,
    player_tile: TileCoordinate,
    legal_directions: list[Direction],
    rng: random.Random | None = None,
) -> Direction:
    """Select direction maximizing distance squared from player.

    When frightened, the ghost evaluates each legal corridor direction and
    chooses the one that increases its distance from the player.
    Ties are resolved using standard directional priority
    (UP, LEFT, DOWN, RIGHT), or pseudo-random choice if an RNG
    instance is provided.
    """
    if not legal_directions or legal_directions == [Direction.NONE]:
        return Direction.NONE

    if len(legal_directions) == 1:
        return legal_directions[0]

    valid_directions = [d for d in legal_directions if d != Direction.NONE]
    if not valid_directions:
        return Direction.NONE

    px, py = player_tile
    cx, cy = current_tile

    scored_directions: list[tuple[float, Direction]] = []
    for direction in valid_directions:
        dx, dy = direction.vector
        nx = cx + int(dx)
        ny = cy + int(dy)
        dist_sq = float((nx - px) ** 2 + (ny - py) ** 2)
        scored_directions.append((dist_sq, direction))

    max_dist_sq = max(d[0] for d in scored_directions)
    best_candidates = [
        direction for dist, direction in scored_directions
        if dist == max_dist_sq
    ]

    if len(best_candidates) == 1:
        return best_candidates[0]

    if rng is not None:
        return rng.choice(best_candidates)

    priority = {
        Direction.UP: 0,
        Direction.LEFT: 1,
        Direction.DOWN: 2,
        Direction.RIGHT: 3,
    }
    return min(best_candidates, key=lambda d: priority.get(d, 99))


def get_legal_ghost_directions(
    tile: TileCoordinate,
    current_direction: Direction,
    world: WorldMap,
    allow_reversal: bool = False,
) -> list[Direction]:
    """Return valid corridor directions for a ghost at a given tile.

    Enforces wall avoidance and classic ghost movement rules:
    - Filters out non-corridor/wall tiles.
    - Prevents 180-degree reversals unless at a dead end or explicitly allowed.
    """
    tx, ty = tile
    cardinal_directions = (
        Direction.UP,
        Direction.DOWN,
        Direction.LEFT,
        Direction.RIGHT,
    )
    walkable_directions: list[Direction] = []

    for direction in cardinal_directions:
        dx, dy = direction.vector
        target_tile = (int(tx + dx), int(ty + dy))
        if world.is_walkable_tile(target_tile):
            walkable_directions.append(direction)

    if not walkable_directions:
        return [Direction.NONE]

    if not allow_reversal and current_direction != Direction.NONE:
        forward_options = [
            d for d in walkable_directions
            if not d.is_opposite(current_direction)
        ]
        if forward_options:
            return forward_options

    return walkable_directions


def create_ghost_group(
    spawns: GhostSpawns,
    speed_multiplier: float = 1.0,
) -> list[Ghost]:
    """Create all four ghosts at their assigned corner spawns."""
    return [
        Ghost.from_spawn(
            GhostIdentity.BLINKY,
            spawns.top_left,
            speed_multiplier,
        ),
        Ghost.from_spawn(
            GhostIdentity.PINKY,
            spawns.top_right,
            speed_multiplier,
        ),
        Ghost.from_spawn(
            GhostIdentity.INKY,
            spawns.bottom_left,
            speed_multiplier,
        ),
        Ghost.from_spawn(
            GhostIdentity.CLYDE,
            spawns.bottom_right,
            speed_multiplier,
        ),
    ]
