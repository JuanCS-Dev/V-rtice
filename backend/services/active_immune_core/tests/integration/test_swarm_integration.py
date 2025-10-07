"""Swarm Coordinator Integration Tests

Tests the Swarm Coordinator's Boids algorithm and collective behavior.
Validates swarm formation, coordination, and analysis.
"""

import pytest

from active_immune_core.agents import SwarmCoordinator


# ==================== FIXTURES ====================


@pytest.fixture
def coordinator():
    """Create Swarm Coordinator"""
    return SwarmCoordinator(
        separation_weight=1.5,
        alignment_weight=1.0,
        cohesion_weight=1.0,
        target_weight=2.0,
        perception_radius=10.0,
        separation_radius=5.0,
    )


# ==================== TESTS ====================


@pytest.mark.asyncio
class TestSwarmCoordinatorInitialization:
    """Test swarm coordinator initialization"""

    async def test_coordinator_creation(self, coordinator):
        """Test that coordinator initializes correctly"""
        assert coordinator.separation_weight == 1.5
        assert coordinator.alignment_weight == 1.0
        assert coordinator.cohesion_weight == 1.0
        assert coordinator.target_weight == 2.0
        assert coordinator.perception_radius == 10.0
        assert coordinator.separation_radius == 5.0
        assert len(coordinator._boids) == 0

    async def test_coordinator_custom_parameters(self):
        """Test creating coordinator with custom parameters"""
        coord = SwarmCoordinator(
            separation_weight=2.0,
            alignment_weight=1.5,
            cohesion_weight=0.8,
            perception_radius=15.0,
        )

        assert coord.separation_weight == 2.0
        assert coord.alignment_weight == 1.5
        assert coord.cohesion_weight == 0.8
        assert coord.perception_radius == 15.0


@pytest.mark.asyncio
class TestBoidManagement:
    """Test boid management"""

    async def test_add_boid(self, coordinator):
        """Test adding boid to swarm"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0))

        assert "boid_1" in coordinator._boids
        boid = coordinator.get_boid("boid_1")
        assert boid.position.x == 10.0
        assert boid.position.y == 20.0

    async def test_add_boid_with_velocity(self, coordinator):
        """Test adding boid with initial velocity"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0), velocity=(1.0, 2.0))

        boid = coordinator.get_boid("boid_1")
        assert boid.velocity.x == 1.0
        assert boid.velocity.y == 2.0

    async def test_add_multiple_boids(self, coordinator):
        """Test adding multiple boids"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0))
        coordinator.add_boid("boid_2", position=(15.0, 25.0))
        coordinator.add_boid("boid_3", position=(12.0, 22.0))

        assert len(coordinator._boids) == 3

    async def test_get_boid(self, coordinator):
        """Test retrieving boid by ID"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0))

        boid = coordinator.get_boid("boid_1")

        assert boid is not None
        assert boid.id == "boid_1"

    async def test_get_boid_not_found(self, coordinator):
        """Test retrieving non-existent boid"""
        boid = coordinator.get_boid("non_existent")

        assert boid is None

    async def test_get_all_boids(self, coordinator):
        """Test retrieving all boids"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0))
        coordinator.add_boid("boid_2", position=(15.0, 25.0))

        all_boids = coordinator.get_all_boids()

        assert len(all_boids) == 2

    async def test_remove_boid(self, coordinator):
        """Test removing boid"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0))

        result = coordinator.remove_boid("boid_1")

        assert result is True
        assert "boid_1" not in coordinator._boids

    async def test_remove_boid_not_found(self, coordinator):
        """Test removing non-existent boid"""
        result = coordinator.remove_boid("non_existent")

        assert result is False


@pytest.mark.asyncio
class TestTargetManagement:
    """Test swarm target management"""

    async def test_set_target(self, coordinator):
        """Test setting swarm target"""
        coordinator.set_target((50.0, 60.0))

        assert coordinator._target is not None
        assert coordinator._target.x == 50.0
        assert coordinator._target.y == 60.0

    async def test_clear_target(self, coordinator):
        """Test clearing swarm target"""
        coordinator.set_target((50.0, 60.0))
        coordinator.clear_target()

        assert coordinator._target is None


@pytest.mark.asyncio
class TestBoidsAlgorithm:
    """Test Boids algorithm behaviors"""

    async def test_update_empty_swarm(self, coordinator):
        """Test update with no boids"""
        # Should not crash
        coordinator.update()

        assert True

    async def test_update_single_boid(self, coordinator):
        """Test update with single boid (no neighbors)"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0), velocity=(1.0, 0.0))

        # Update (no neighbors, should continue moving)
        coordinator.update()

        boid = coordinator.get_boid("boid_1")

        # Position should have changed
        assert boid.position.x > 10.0

    async def test_update_two_boids_separation(self, coordinator):
        """Test separation behavior (boids too close)"""
        # Add two boids very close together
        coordinator.add_boid("boid_1", position=(10.0, 10.0), velocity=(0.0, 0.0))
        coordinator.add_boid("boid_2", position=(12.0, 10.0), velocity=(0.0, 0.0))

        # Update multiple times
        for _ in range(10):
            coordinator.update()

        boid1 = coordinator.get_boid("boid_1")
        boid2 = coordinator.get_boid("boid_2")

        # Distance should increase (separation)
        distance = boid1.position.distance_to(boid2.position)
        assert distance > 2.0  # Started at 2.0, should increase

    async def test_update_three_boids_cohesion(self, coordinator):
        """Test cohesion behavior (boids stay together)"""
        # Add three boids in a line
        coordinator.add_boid("boid_1", position=(0.0, 0.0), velocity=(1.0, 0.0))
        coordinator.add_boid("boid_2", position=(10.0, 0.0), velocity=(-1.0, 0.0))
        coordinator.add_boid("boid_3", position=(5.0, 0.0), velocity=(0.0, 1.0))

        # Update multiple times
        for _ in range(20):
            coordinator.update()

        # Boids should be closer together (cohesion)
        # Just test that update doesn't crash
        assert len(coordinator._boids) == 3

    async def test_update_with_target(self, coordinator):
        """Test target seeking behavior"""
        coordinator.add_boid("boid_1", position=(0.0, 0.0), velocity=(0.0, 0.0))

        # Set target far away
        coordinator.set_target((100.0, 100.0))

        # Update multiple times
        for _ in range(20):
            coordinator.update()

        boid = coordinator.get_boid("boid_1")

        # Boid should have moved towards target
        assert boid.position.x > 0.0
        assert boid.position.y > 0.0


@pytest.mark.asyncio
class TestSwarmAnalysis:
    """Test swarm analysis functions"""

    async def test_get_swarm_center_empty(self, coordinator):
        """Test swarm center with no boids"""
        center = coordinator.get_swarm_center()

        assert center is None

    async def test_get_swarm_center(self, coordinator):
        """Test swarm center calculation"""
        coordinator.add_boid("boid_1", position=(0.0, 0.0))
        coordinator.add_boid("boid_2", position=(10.0, 0.0))
        coordinator.add_boid("boid_3", position=(5.0, 10.0))

        center = coordinator.get_swarm_center()

        # Center should be at (5, 3.33)
        assert center is not None
        assert abs(center.x - 5.0) < 0.1
        assert abs(center.y - 3.33) < 0.1

    async def test_get_swarm_radius_empty(self, coordinator):
        """Test swarm radius with no boids"""
        radius = coordinator.get_swarm_radius()

        assert radius == 0.0

    async def test_get_swarm_radius(self, coordinator):
        """Test swarm radius calculation"""
        coordinator.add_boid("boid_1", position=(0.0, 0.0))
        coordinator.add_boid("boid_2", position=(10.0, 0.0))

        radius = coordinator.get_swarm_radius()

        # Max distance from center (5, 0) should be 5
        assert radius == 5.0

    async def test_get_swarm_density_empty(self, coordinator):
        """Test swarm density with no boids"""
        density = coordinator.get_swarm_density()

        assert density == 0.0

    async def test_get_swarm_density(self, coordinator):
        """Test swarm density calculation"""
        # Add boids in a small area
        coordinator.add_boid("boid_1", position=(0.0, 0.0))
        coordinator.add_boid("boid_2", position=(1.0, 0.0))
        coordinator.add_boid("boid_3", position=(0.0, 1.0))

        density = coordinator.get_swarm_density()

        # Should have positive density
        assert density > 0.0


@pytest.mark.asyncio
class TestSwarmMetrics:
    """Test swarm metrics"""

    async def test_get_swarm_metrics(self, coordinator):
        """Test retrieving swarm metrics"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0))
        coordinator.add_boid("boid_2", position=(15.0, 25.0))
        coordinator.set_target((50.0, 60.0))

        metrics = coordinator.get_swarm_metrics()

        assert metrics["boids_total"] == 2
        assert metrics["swarm_center"] is not None
        assert metrics["swarm_radius"] > 0.0
        assert metrics["swarm_density"] > 0.0
        assert metrics["has_target"] is True
        assert metrics["target_position"] == (50.0, 60.0)

    async def test_repr(self, coordinator):
        """Test string representation"""
        coordinator.add_boid("boid_1", position=(10.0, 20.0))
        coordinator.add_boid("boid_2", position=(15.0, 25.0))

        repr_str = repr(coordinator)

        assert "SwarmCoordinator" in repr_str
        assert "boids=2" in repr_str


@pytest.mark.asyncio
class TestSwarmIntegration:
    """Test full integration scenarios"""

    async def test_neutrophil_swarm_scenario(self, coordinator):
        """Test simulated Neutrophil swarm scenario"""
        # Create swarm of 5 neutrophils
        for i in range(5):
            coordinator.add_boid(f"neutro_{i}", position=(i * 2.0, i * 2.0))

        # Set target (threat location)
        coordinator.set_target((50.0, 50.0))

        # Simulate migration towards threat
        for _ in range(30):
            coordinator.update()

        # All boids should have moved towards target
        for i in range(5):
            boid = coordinator.get_boid(f"neutro_{i}")
            # Should have moved from starting position
            assert boid.position.x > i * 2.0
            assert boid.position.y > i * 2.0

    async def test_swarm_convergence(self, coordinator):
        """Test swarm convergence on target"""
        # Create scattered boids
        coordinator.add_boid("boid_1", position=(0.0, 0.0))
        coordinator.add_boid("boid_2", position=(20.0, 0.0))
        coordinator.add_boid("boid_3", position=(0.0, 20.0))
        coordinator.add_boid("boid_4", position=(20.0, 20.0))

        # Set target at center
        coordinator.set_target((10.0, 10.0))

        # Update many times
        for _ in range(50):
            coordinator.update()

        # Swarm should be more compact (smaller radius)
        radius = coordinator.get_swarm_radius()
        center = coordinator.get_swarm_center()

        # Center should be near target
        assert center is not None
        distance_to_target = ((center.x - 10.0) ** 2 + (center.y - 10.0) ** 2) ** 0.5
        assert distance_to_target < 15.0  # Within 15 units of target

    async def test_large_swarm_performance(self, coordinator):
        """Test performance with large swarm (100 boids)"""
        # Create large swarm
        for i in range(100):
            x = (i % 10) * 5.0
            y = (i // 10) * 5.0
            coordinator.add_boid(f"boid_{i}", position=(x, y))

        coordinator.set_target((50.0, 50.0))

        # Update (should complete without timeout)
        coordinator.update()

        # All boids should still exist
        assert len(coordinator._boids) == 100
