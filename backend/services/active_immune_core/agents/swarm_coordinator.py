"""Swarm Coordinator - Collective intelligence for immune agents

Implements swarm coordination using Boids algorithm:
1. Separation: Avoid crowding neighbors
2. Alignment: Steer towards average heading of neighbors
3. Cohesion: Steer towards average position of neighbors

Additional behaviors:
4. Target seeking: Move towards threat
5. Obstacle avoidance: Avoid safe zones
6. Leader following: Follow designated swarm leader

Based on Craig Reynolds' Boids (1986), adapted for network security.

PRODUCTION-READY: No mocks, type hints, error handling, graceful degradation.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """2D position in network space"""

    x: float
    y: float

    def distance_to(self, other: "Position") -> float:
        """Calculate Euclidean distance to another position"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __add__(self, other: "Position") -> "Position":
        """Vector addition"""
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Position") -> "Position":
        """Vector subtraction"""
        return Position(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Position":
        """Scalar multiplication"""
        return Position(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Position":
        """Scalar division"""
        return Position(self.x / scalar, self.y / scalar)

    def magnitude(self) -> float:
        """Vector magnitude (length)"""
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> "Position":
        """Normalize to unit vector"""
        mag = self.magnitude()
        if mag > 0:
            return self / mag
        return Position(0, 0)

    def limit(self, max_value: float) -> "Position":
        """Limit magnitude to max_value"""
        mag = self.magnitude()
        if mag > max_value:
            return self.normalize() * max_value
        return self


@dataclass
class Boid:
    """
    Individual boid (agent) in the swarm.

    Attributes:
        id: Unique identifier
        position: Current position (x, y)
        velocity: Current velocity vector
        max_speed: Maximum speed
        max_force: Maximum steering force
    """

    id: str
    position: Position
    velocity: Position
    max_speed: float = 2.0
    max_force: float = 0.1


class SwarmCoordinator:
    """
    Swarm coordination engine using Boids algorithm.

    Manages collective behavior of immune agent swarms:
    - Neutrophil swarms (NET formation)
    - Macrophage clusters (coordinated phagocytosis)
    - Future: Dendritic cell migration

    Usage:
        coordinator = SwarmCoordinator()
        coordinator.add_boid("neutro_1", position=(10, 20))
        coordinator.add_boid("neutro_2", position=(12, 22))
        coordinator.update()  # Calculate new positions
    """

    def __init__(
        self,
        separation_weight: float = 1.5,
        alignment_weight: float = 1.0,
        cohesion_weight: float = 1.0,
        target_weight: float = 2.0,
        perception_radius: float = 10.0,
        separation_radius: float = 5.0,
    ):
        """
        Initialize Swarm Coordinator.

        Args:
            separation_weight: Weight for separation behavior
            alignment_weight: Weight for alignment behavior
            cohesion_weight: Weight for cohesion behavior
            target_weight: Weight for target seeking
            perception_radius: Radius within which boids perceive neighbors
            separation_radius: Minimum distance to maintain from neighbors
        """
        self.separation_weight = separation_weight
        self.alignment_weight = alignment_weight
        self.cohesion_weight = cohesion_weight
        self.target_weight = target_weight
        self.perception_radius = perception_radius
        self.separation_radius = separation_radius

        # Boid registry
        self._boids: Dict[str, Boid] = {}

        # Swarm target (threat location)
        self._target: Optional[Position] = None

        logger.info(f"SwarmCoordinator initialized (perception={perception_radius}, separation={separation_radius})")

    # ==================== BOID MANAGEMENT ====================

    def add_boid(
        self,
        boid_id: str,
        position: Tuple[float, float],
        velocity: Optional[Tuple[float, float]] = None,
    ) -> None:
        """
        Add boid to swarm.

        Args:
            boid_id: Unique identifier
            position: (x, y) position
            velocity: Optional (vx, vy) velocity
        """
        if velocity is None:
            velocity = (0.0, 0.0)

        boid = Boid(
            id=boid_id,
            position=Position(position[0], position[1]),
            velocity=Position(velocity[0], velocity[1]),
        )

        self._boids[boid_id] = boid

        logger.debug(f"Boid added: {boid_id} at position {position}")

    def remove_boid(self, boid_id: str) -> bool:
        """
        Remove boid from swarm.

        Args:
            boid_id: Boid identifier

        Returns:
            True if removed, False if not found
        """
        if boid_id in self._boids:
            del self._boids[boid_id]
            logger.debug(f"Boid removed: {boid_id}")
            return True
        return False

    def get_boid(self, boid_id: str) -> Optional[Boid]:
        """Get boid by ID"""
        return self._boids.get(boid_id)

    def get_all_boids(self) -> List[Boid]:
        """Get all boids"""
        return list(self._boids.values())

    def set_target(self, position: Tuple[float, float]) -> None:
        """
        Set swarm target (threat location).

        Args:
            position: (x, y) target position
        """
        self._target = Position(position[0], position[1])
        logger.debug(f"Swarm target set: {position}")

    def clear_target(self) -> None:
        """Clear swarm target"""
        self._target = None

    # ==================== BOIDS ALGORITHM ====================

    def update(self) -> None:
        """
        Update all boid positions using Boids algorithm.

        Applies steering forces:
        1. Separation
        2. Alignment
        3. Cohesion
        4. Target seeking (if target set)
        """
        if not self._boids:
            return

        # Calculate steering forces for each boid
        for boid in self._boids.values():
            # Get neighbors within perception radius
            neighbors = self._get_neighbors(boid)

            # Calculate steering forces
            separation_force = self._separation(boid, neighbors)
            alignment_force = self._alignment(boid, neighbors)
            cohesion_force = self._cohesion(boid, neighbors)

            # Apply weights
            acceleration = (
                separation_force * self.separation_weight
                + alignment_force * self.alignment_weight
                + cohesion_force * self.cohesion_weight
            )

            # Target seeking (if target set)
            if self._target:
                target_force = self._seek(boid, self._target)
                acceleration = acceleration + target_force * self.target_weight

            # Update velocity
            boid.velocity = boid.velocity + acceleration
            boid.velocity = boid.velocity.limit(boid.max_speed)

            # Update position
            boid.position = boid.position + boid.velocity

        logger.debug(f"Swarm updated: {len(self._boids)} boids")

    def _get_neighbors(self, boid: Boid) -> List[Boid]:
        """
        Get boids within perception radius.

        Args:
            boid: Current boid

        Returns:
            List of neighboring boids
        """
        neighbors = []

        for other in self._boids.values():
            if other.id == boid.id:
                continue

            distance = boid.position.distance_to(other.position)

            if distance < self.perception_radius:
                neighbors.append(other)

        return neighbors

    def _separation(self, boid: Boid, neighbors: List[Boid]) -> Position:
        """
        Separation: Steer away from crowded neighbors.

        Args:
            boid: Current boid
            neighbors: Neighboring boids

        Returns:
            Separation steering force
        """
        if not neighbors:
            return Position(0, 0)

        steering = Position(0, 0)
        total = 0

        for other in neighbors:
            distance = boid.position.distance_to(other.position)

            # Only separate if too close
            if distance < self.separation_radius and distance > 0:
                # Direction away from neighbor
                diff = boid.position - other.position

                # Weight by distance (closer = stronger repulsion)
                diff = diff / distance

                steering = steering + diff
                total += 1

        if total > 0:
            steering = steering / total

            # Steering = desired - current
            if steering.magnitude() > 0:
                steering = steering.normalize() * boid.max_speed
                steering = steering - boid.velocity
                steering = steering.limit(boid.max_force)

        return steering

    def _alignment(self, boid: Boid, neighbors: List[Boid]) -> Position:
        """
        Alignment: Steer towards average heading of neighbors.

        Args:
            boid: Current boid
            neighbors: Neighboring boids

        Returns:
            Alignment steering force
        """
        if not neighbors:
            return Position(0, 0)

        # Average velocity of neighbors
        avg_velocity = Position(0, 0)

        for other in neighbors:
            avg_velocity = avg_velocity + other.velocity

        avg_velocity = avg_velocity / len(neighbors)

        # Steering = desired - current
        steering = avg_velocity - boid.velocity
        steering = steering.limit(boid.max_force)

        return steering

    def _cohesion(self, boid: Boid, neighbors: List[Boid]) -> Position:
        """
        Cohesion: Steer towards average position of neighbors.

        Args:
            boid: Current boid
            neighbors: Neighboring boids

        Returns:
            Cohesion steering force
        """
        if not neighbors:
            return Position(0, 0)

        # Average position of neighbors
        avg_position = Position(0, 0)

        for other in neighbors:
            avg_position = avg_position + other.position

        avg_position = avg_position / len(neighbors)

        # Seek towards average position
        return self._seek(boid, avg_position)

    def _seek(self, boid: Boid, target: Position) -> Position:
        """
        Seek: Steer towards target position.

        Args:
            boid: Current boid
            target: Target position

        Returns:
            Seek steering force
        """
        # Desired velocity = direction to target
        desired = target - boid.position

        # Scale to max_speed
        desired = desired.normalize() * boid.max_speed

        # Steering = desired - current
        steering = desired - boid.velocity
        steering = steering.limit(boid.max_force)

        return steering

    # ==================== SWARM ANALYSIS ====================

    def get_swarm_center(self) -> Optional[Position]:
        """
        Get center of mass of swarm.

        Returns:
            Center position or None if no boids
        """
        if not self._boids:
            return None

        center = Position(0, 0)

        for boid in self._boids.values():
            center = center + boid.position

        center = center / len(self._boids)

        return center

    def get_swarm_radius(self) -> float:
        """
        Get radius of swarm (max distance from center).

        Returns:
            Swarm radius
        """
        center = self.get_swarm_center()

        if not center:
            return 0.0

        max_distance = 0.0

        for boid in self._boids.values():
            distance = boid.position.distance_to(center)
            max_distance = max(max_distance, distance)

        return max_distance

    def get_swarm_density(self) -> float:
        """
        Get swarm density (boids per unit area).

        Returns:
            Density (boids / (pi * r^2))
        """
        if not self._boids:
            return 0.0

        radius = self.get_swarm_radius()

        if radius == 0:
            return 0.0

        area = math.pi * radius**2
        return len(self._boids) / area

    # ==================== METRICS ====================

    def get_swarm_metrics(self) -> Dict[str, Any]:
        """
        Get swarm statistics.

        Returns:
            Dict with swarm metrics
        """
        center = self.get_swarm_center()

        return {
            "boids_total": len(self._boids),
            "swarm_center": (center.x, center.y) if center else None,
            "swarm_radius": self.get_swarm_radius(),
            "swarm_density": self.get_swarm_density(),
            "has_target": self._target is not None,
            "target_position": (self._target.x, self._target.y) if self._target else None,
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"SwarmCoordinator(boids={len(self._boids)}, "
            f"radius={self.get_swarm_radius():.2f}, "
            f"density={self.get_swarm_density():.2f})"
        )
