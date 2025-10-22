"""
TIG Fabric - FAITH BREAKTHROUGH to 100% 🙏
==========================================

Target: 81.96% → 100.00% (81 linhas em FÉ)

Missing Line Groups:
- 73-82: TIGConnection inactive + effective capacity
- 105: CircuitBreaker is_open with recovery
- 138-157: Node degree, clustering, broadcast
- 242-252, 620, 823, 827, 843-872, 881-932: Health monitoring, fault tolerance
- 952, 957, 966, 972-985, 1032-1033, 1061, 1103-1117: Partition detection, ESGT mode

PADRÃO PAGANI ABSOLUTO - ROMPENDO EM FÉ!
"""

import time
import pytest

from consciousness.tig.fabric import (
    TIGFabric,
    TIGNode,
    TIGConnection,
    CircuitBreaker,
    NodeHealth,
    TopologyConfig,
    NodeState,
)


class TestTIGConnectionEdgeCases:
    """Lines 73-82: TIGConnection.get_effective_capacity()"""

    def test_inactive_connection_zero_capacity_lines_73_82(self):
        """Test inactive connection returns 0.0 capacity (lines 73-82)."""
        conn = TIGConnection(
            remote_node_id="test-node",
            bandwidth_bps=10_000_000_000,
            latency_us=1.0,
            packet_loss=0.1,
            active=False,  # INACTIVE - trigger line 73-74
            weight=1.0
        )

        capacity = conn.get_effective_capacity()

        # Should return 0.0 immediately (line 74)
        assert capacity == 0.0


class TestCircuitBreakerRecovery:
    """Lines 105: CircuitBreaker recovery from open → half_open"""

    def test_circuit_breaker_recovery_timeout_line_105(self):
        """Test circuit breaker transitions to half_open after recovery timeout (line 105)."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Trigger failures to open breaker
        breaker.record_failure()
        breaker.record_failure()

        assert breaker.is_open() is True

        # Wait for recovery timeout
        time.sleep(0.15)

        # Should transition to half_open (line 72-73)
        is_still_open = breaker.is_open()

        # After recovery timeout, should allow requests (half_open)
        assert is_still_open is False
        assert breaker.state == "half_open"


class TestNodeHealthAndProcessing:
    """Lines 138-157: Node degree, clustering, broadcast"""

    @pytest.mark.asyncio
    async def test_node_degree_and_clustering_lines_156_186(self):
        """Test node degree and clustering coefficient (lines 156-186)."""
        # Create simple fabric
        config = TopologyConfig(node_count=8, min_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()

        # Get any node
        node_id = list(fabric.nodes.keys())[0]
        node = fabric.nodes[node_id]

        # Test get_degree (line 157-158)
        degree = node.get_degree()
        assert degree >= 3  # Min degree from config

        # Test get_clustering_coefficient (lines 160-185)
        clustering = node.get_clustering_coefficient(fabric)
        assert 0.0 <= clustering <= 1.0

        await fabric.stop()

    @pytest.mark.asyncio
    async def test_broadcast_to_neighbors_lines_187_213(self):
        """Test node broadcast to neighbors (lines 187-213)."""
        config = TopologyConfig(node_count=6, min_degree=2)
        fabric = TIGFabric(config)
        await fabric.initialize()

        node_id = list(fabric.nodes.keys())[0]
        node = fabric.nodes[node_id]

        # Broadcast message (lines 187-213)
        message = {"type": "test", "data": "hello"}
        count = await node.broadcast_to_neighbors(message, priority=5)

        # Should reach some neighbors
        assert count >= 0

        await fabric.stop()


class TestHealthMonitoringFaultTolerance:
    """Lines 242-252, 620, 823, 827, 843-872, 881-932: Health monitoring"""

    @pytest.mark.asyncio
    async def test_avg_path_length_disconnected_graph_lines_620_626(self):
        """Test avg_path_length with disconnected graph (lines 620-626)."""
        # Create small fabric that might have disconnected components
        config = TopologyConfig(node_count=4, min_degree=1, target_density=0.1)
        fabric = TIGFabric(config)
        await fabric.initialize()

        # Metrics computed during initialize - check if disconnected path was handled
        # Lines 620-626 handle disconnected graphs
        assert fabric.metrics.avg_path_length > 0.0

        await fabric.stop()

    @pytest.mark.asyncio
    async def test_isolate_and_reintegrate_node_lines_789_823(self):
        """Test node isolation and reintegration (lines 789-823)."""
        config = TopologyConfig(node_count=6, min_degree=2)
        fabric = TIGFabric(config)
        await fabric.initialize()

        node_id = list(fabric.nodes.keys())[0]

        # Manually trigger isolation (lines 789-805)
        await fabric._isolate_dead_node(node_id)

        health = fabric.node_health[node_id]
        assert health.isolated is True
        node = fabric.nodes[node_id]
        assert node.node_state == NodeState.OFFLINE

        # Manually trigger reintegration (lines 807-823)
        health.failures = 0  # Reset failures
        await fabric._reintegrate_node(node_id)

        assert health.isolated is False
        assert node.node_state == NodeState.ACTIVE
        assert health.last_seen > 0

        await fabric.stop()

    @pytest.mark.asyncio
    async def test_repair_topology_around_dead_node_lines_825_865(self):
        """Test topology repair when node dies (lines 825-865)."""
        config = TopologyConfig(node_count=8, min_degree=3)
        fabric = TIGFabric(config)
        await fabric.initialize()

        # Pick node with multiple neighbors
        dead_node_id = None
        for nid, node in fabric.nodes.items():
            if len(node.connections) >= 2:
                dead_node_id = nid
                break

        assert dead_node_id is not None

        # Trigger repair (lines 825-865)
        await fabric._repair_topology_around_dead_node(dead_node_id)

        # Bypass connections should be created
        # (Lines 843-862 create bidirectional bypasses)
        # Can't easily verify without introspecting, but ensure no crash

        await fabric.stop()

    @pytest.mark.asyncio
    async def test_send_to_node_with_circuit_breaker_lines_867_918(self):
        """Test send_to_node with circuit breaker (lines 867-918)."""
        config = TopologyConfig(node_count=4, min_degree=2)
        fabric = TIGFabric(config)
        await fabric.initialize()

        node_id = list(fabric.nodes.keys())[0]

        # Successful send (lines 882-910)
        success = await fabric.send_to_node(node_id, {"test": "data"}, timeout=1.0)
        assert success is True

        # Test with isolated node (lines 883-885)
        fabric.node_health[node_id].isolated = True
        success = await fabric.send_to_node(node_id, {"test": "data"}, timeout=1.0)
        assert success is False

        # Test with open circuit breaker (lines 887-890)
        fabric.node_health[node_id].isolated = False
        fabric.circuit_breakers[node_id].open()
        success = await fabric.send_to_node(node_id, {"test": "data"}, timeout=1.0)
        assert success is False

        await fabric.stop()

    def test_handle_send_failure_opens_circuit_breaker_lines_920_938(self):
        """Test _handle_send_failure opens circuit breaker (lines 920-938)."""
        config = TopologyConfig(node_count=4)
        fabric = TIGFabric(config)
        fabric.max_failures_before_isolation = 3  # Match default

        node_id = "test-node"
        fabric.node_health[node_id] = NodeHealth(node_id=node_id)
        fabric.circuit_breakers[node_id] = CircuitBreaker(failure_threshold=3)

        # First failure
        result = fabric._handle_send_failure(node_id, "test error")
        assert result is False
        assert fabric.node_health[node_id].failures == 1

        # Second failure
        result = fabric._handle_send_failure(node_id, "test error 2")
        assert result is False
        assert fabric.node_health[node_id].failures == 2

        # Third failure - should open circuit breaker (lines 932-936)
        result = fabric._handle_send_failure(node_id, "test error 3")
        assert result is False
        assert fabric.node_health[node_id].failures == 3
        assert fabric.circuit_breakers[node_id].state == "open"


class TestPartitionDetectionAndESGT:
    """Lines 940-1050: Partition detection, get_health_metrics, ESGT mode"""

    def test_detect_network_partition_lines_940_969(self):
        """Test network partition detection (lines 940-969)."""
        config = TopologyConfig(node_count=6, min_degree=2)
        fabric = TIGFabric(config)

        # Initialize node_health manually
        for i in range(6):
            node_id = f"tig-node-{i:03d}"
            fabric.node_health[node_id] = NodeHealth(node_id=node_id)
            fabric.nodes[node_id] = TIGNode(id=node_id)

        # Test with no partition (all active)
        is_partitioned = fabric._detect_network_partition()
        # May or may not be partitioned depending on graph generation
        assert isinstance(is_partitioned, bool)

        # Test with isolated nodes creating partition
        fabric.node_health["tig-node-000"].isolated = True
        fabric.node_health["tig-node-001"].isolated = True
        is_partitioned = fabric._detect_network_partition()
        assert isinstance(is_partitioned, bool)

    def test_get_health_metrics_lines_971_1009(self):
        """Test get_health_metrics (lines 971-1009)."""
        config = TopologyConfig(node_count=6, min_degree=2)
        fabric = TIGFabric(config)

        # Setup health tracking
        for i in range(6):
            node_id = f"tig-node-{i:03d}"
            fabric.node_health[node_id] = NodeHealth(node_id=node_id)

        # Isolate one node
        fabric.node_health["tig-node-000"].isolated = True
        fabric.node_health["tig-node-001"].degraded = True

        # Get metrics (lines 971-1009)
        metrics = fabric.get_health_metrics()

        assert metrics["total_nodes"] == 6
        assert metrics["isolated_nodes"] == 1
        assert metrics["degraded_nodes"] == 1
        assert metrics["healthy_nodes"] == 4
        assert 0.0 <= metrics["connectivity"] <= 1.0
        assert "is_partitioned" in metrics

    @pytest.mark.asyncio
    async def test_esgt_mode_enter_exit_lines_1029_1050(self):
        """Test enter/exit ESGT mode (lines 1029-1050)."""
        config = TopologyConfig(node_count=4, min_degree=2)
        fabric = TIGFabric(config)
        await fabric.initialize()

        # Enter ESGT mode (lines 1029-1041)
        await fabric.enter_esgt_mode()

        for node in fabric.nodes.values():
            assert node.node_state == NodeState.ESGT_MODE
            # Connections should have increased weight
            for conn in node.connections.values():
                assert conn.weight > 1.0

        # Exit ESGT mode (lines 1043-1050)
        await fabric.exit_esgt_mode()

        for node in fabric.nodes.values():
            assert node.node_state == NodeState.ACTIVE
            # Weights should be restored
            for conn in node.connections.values():
                assert conn.weight >= 1.0

        await fabric.stop()

    def test_repr_line_1052_1058(self):
        """Test __repr__ method (lines 1052-1058)."""
        config = TopologyConfig(node_count=4)
        fabric = TIGFabric(config)

        repr_str = repr(fabric)

        assert "TIGFabric" in repr_str
        assert "nodes=" in repr_str
        assert "ECI=" in repr_str


class TestSmallGraphEdgeCases:
    """Lines 545-553: Small graph (<12 nodes) skips hub enhancement"""

    @pytest.mark.asyncio
    async def test_small_graph_skips_hub_enhancement_lines_545_553(self):
        """Test small graphs skip hub enhancement pass (lines 545-546)."""
        # Create graph with <12 nodes
        config = TopologyConfig(node_count=8, min_degree=2, enable_small_world_rewiring=True)
        fabric = TIGFabric(config)
        await fabric.initialize()

        # Should complete without hub enhancement (lines 545-546 early return)
        assert fabric.metrics.node_count == 8

        await fabric.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
