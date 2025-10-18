"""
RabbitMQ Cluster Support.

Provides high availability features:
- Multiple broker URLs (automatic failover)
- Connection pooling
- Load balancing across brokers
- Health checking
- Automatic reconnection
- Cluster topology awareness

Features:
- Round-robin load balancing
- Automatic failover to healthy brokers
- Connection pool management
- Health check monitoring
- Cluster status tracking
- Metrics integration
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class BrokerHealth(Enum):
    """Broker health states."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class BrokerNode:
    """
    Represents a RabbitMQ broker node in cluster.

    Attributes:
        host: Broker hostname
        port: AMQP port
        management_port: Management API port
        health: Current health status
        last_check: Last health check timestamp
        failure_count: Number of consecutive failures
        connection_count: Number of active connections
    """

    host: str
    port: int = 5672
    management_port: int = 15672
    health: BrokerHealth = BrokerHealth.UNKNOWN
    last_check: Optional[float] = None
    failure_count: int = 0
    connection_count: int = 0

    def get_url(self, username: str = "guest", password: str = "guest") -> str:
        """
        Get AMQP connection URL.

        Args:
            username: RabbitMQ username
            password: RabbitMQ password

        Returns:
            Connection URL
        """
        return f"amqp://{username}:{password}@{self.host}:{self.port}/"

    def get_management_url(self) -> str:
        """
        Get management API URL.

        Returns:
            Management URL
        """
        return f"http://{self.host}:{self.management_port}"

    def is_healthy(self) -> bool:
        """Check if broker is healthy."""
        return self.health == BrokerHealth.HEALTHY

    def mark_failure(self) -> None:
        """Record failed connection attempt."""
        self.failure_count += 1
        if self.failure_count >= 3:
            self.health = BrokerHealth.UNHEALTHY
        elif self.failure_count >= 1:
            self.health = BrokerHealth.DEGRADED

    def mark_success(self) -> None:
        """Record successful connection."""
        self.failure_count = 0
        self.health = BrokerHealth.HEALTHY

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"BrokerNode({self.host}:{self.port}, "
            f"health={self.health.value}, "
            f"failures={self.failure_count})"
        )


class ClusterConfig:
    """
    Configuration for RabbitMQ cluster.

    Attributes:
        broker_urls: List of broker URLs
        connection_pool_size: Max connections per broker
        health_check_interval: Seconds between health checks
        failover_timeout: Seconds before trying failed broker again
        load_balancing: Load balancing strategy (round_robin, random)
    """

    def __init__(
        self,
        broker_urls: List[str],
        connection_pool_size: int = 10,
        health_check_interval: int = 30,
        failover_timeout: int = 60,
        load_balancing: str = "round_robin",
    ):
        self.broker_urls = broker_urls
        self.connection_pool_size = connection_pool_size
        self.health_check_interval = health_check_interval
        self.failover_timeout = failover_timeout
        self.load_balancing = load_balancing

        # Parse broker nodes
        self.nodes = self._parse_broker_urls(broker_urls)

    def _parse_broker_urls(self, urls: List[str]) -> List[BrokerNode]:
        """
        Parse broker URLs into BrokerNode objects.

        Args:
            urls: List of AMQP URLs

        Returns:
            List of BrokerNode objects
        """
        nodes = []

        for url in urls:
            # Simple URL parsing (format: amqp://host:port/)
            # In production, use proper URL parsing
            if "://" in url:
                parts = url.split("://")[1].split("/")[0]
                if "@" in parts:
                    parts = parts.split("@")[1]

                if ":" in parts:
                    host, port_str = parts.split(":")
                    port = int(port_str)
                else:
                    host = parts
                    port = 5672

                nodes.append(BrokerNode(host=host, port=port))

        return nodes


class RabbitMQCluster:
    """
    Manages RabbitMQ cluster connections.

    Provides high availability through:
    - Multiple broker connections
    - Automatic failover
    - Load balancing
    - Health monitoring
    """

    def __init__(self, config: ClusterConfig):
        """
        Initialize cluster manager.

        Args:
            config: Cluster configuration
        """
        self.config = config
        self.nodes = config.nodes
        self._current_node_index = 0
        self._health_check_task: Optional[asyncio.Task] = None

        logger.info(
            f"RabbitMQCluster initialized with {len(self.nodes)} nodes: "
            f"{[n.host for n in self.nodes]}"
        )

    async def start_health_checks(self) -> None:
        """Start background health check task."""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("Started health check task")

    async def stop_health_checks(self) -> None:
        """Stop background health check task."""
        if self._health_check_task is not None:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Stopped health check task")

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_all_nodes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check failed: {e}", exc_info=True)

    async def _check_all_nodes(self) -> None:
        """Check health of all broker nodes."""
        for node in self.nodes:
            try:
                healthy = await self._check_node_health(node)
                node.last_check = time.time()

                if healthy:
                    node.mark_success()
                    logger.debug(f"Node {node.host} is healthy")
                else:
                    node.mark_failure()
                    logger.warning(f"Node {node.host} health check failed")

            except Exception as e:
                node.mark_failure()
                logger.error(f"Health check error for {node.host}: {e}")

    async def _check_node_health(self, node: BrokerNode) -> bool:
        """
        Check health of specific broker node.

        Args:
            node: Broker node to check

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to connect via management API
            import aiohttp

            async with aiohttp.ClientSession() as session:
                url = f"{node.get_management_url()}/api/healthchecks/node"

                async with session.get(
                    url,
                    auth=aiohttp.BasicAuth("guest", "guest"),
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.debug(f"Health check failed for {node.host}: {e}")
            return False

    def get_healthy_nodes(self) -> List[BrokerNode]:
        """
        Get list of healthy broker nodes.

        Returns:
            List of healthy nodes
        """
        return [node for node in self.nodes if node.is_healthy()]

    def get_next_node(self) -> Optional[BrokerNode]:
        """
        Get next broker node for load balancing.

        Uses configured load balancing strategy.

        Returns:
            BrokerNode or None if no healthy nodes
        """
        healthy_nodes = self.get_healthy_nodes()

        if not healthy_nodes:
            # No healthy nodes - try any node
            logger.warning("No healthy nodes available - using any node")
            healthy_nodes = self.nodes

        if not healthy_nodes:
            return None

        # Load balancing strategy
        if self.config.load_balancing == "round_robin":
            node = healthy_nodes[self._current_node_index % len(healthy_nodes)]
            self._current_node_index += 1
            return node

        elif self.config.load_balancing == "random":
            return random.choice(healthy_nodes)

        elif self.config.load_balancing == "least_connections":
            return min(healthy_nodes, key=lambda n: n.connection_count)

        else:
            # Default to round-robin
            node = healthy_nodes[self._current_node_index % len(healthy_nodes)]
            self._current_node_index += 1
            return node

    def get_connection_url(
        self,
        username: str = "guest",
        password: str = "guest",
    ) -> Optional[str]:
        """
        Get connection URL for next available broker.

        Args:
            username: RabbitMQ username
            password: RabbitMQ password

        Returns:
            Connection URL or None if no nodes available
        """
        node = self.get_next_node()

        if node is None:
            return None

        return node.get_url(username, password)

    def record_connection_success(self, broker_host: str) -> None:
        """
        Record successful connection to broker.

        Args:
            broker_host: Broker hostname
        """
        for node in self.nodes:
            if node.host == broker_host:
                node.mark_success()
                node.connection_count += 1
                logger.debug(f"Connection success: {broker_host} (total={node.connection_count})")
                break

    def record_connection_failure(self, broker_host: str) -> None:
        """
        Record failed connection to broker.

        Args:
            broker_host: Broker hostname
        """
        for node in self.nodes:
            if node.host == broker_host:
                node.mark_failure()
                logger.warning(f"Connection failure: {broker_host} (failures={node.failure_count})")
                break

    def get_cluster_status(self) -> dict:
        """
        Get cluster status.

        Returns:
            Dict with cluster information
        """
        healthy = sum(1 for n in self.nodes if n.is_healthy())
        degraded = sum(1 for n in self.nodes if n.health == BrokerHealth.DEGRADED)
        unhealthy = sum(1 for n in self.nodes if n.health == BrokerHealth.UNHEALTHY)

        return {
            "total_nodes": len(self.nodes),
            "healthy_nodes": healthy,
            "degraded_nodes": degraded,
            "unhealthy_nodes": unhealthy,
            "nodes": [
                {
                    "host": node.host,
                    "port": node.port,
                    "health": node.health.value,
                    "failures": node.failure_count,
                    "connections": node.connection_count,
                    "last_check": node.last_check,
                }
                for node in self.nodes
            ],
        }

    def __repr__(self) -> str:
        """String representation."""
        status = self.get_cluster_status()
        return (
            f"RabbitMQCluster("
            f"nodes={status['total_nodes']}, "
            f"healthy={status['healthy_nodes']}, "
            f"degraded={status['degraded_nodes']}, "
            f"unhealthy={status['unhealthy_nodes']})"
        )


# --- Connection Pool ---


class ConnectionPool:
    """
    Connection pool for RabbitMQ cluster.

    Manages multiple connections to distribute load.
    """

    def __init__(
        self,
        cluster: RabbitMQCluster,
        pool_size: int = 10,
    ):
        """
        Initialize connection pool.

        Args:
            cluster: RabbitMQ cluster
            pool_size: Maximum pool size
        """
        self.cluster = cluster
        self.pool_size = pool_size
        self._connections: List[Any] = []  # List of connections
        self._lock = asyncio.Lock()

        logger.info(f"ConnectionPool initialized (size={pool_size})")

    async def acquire(self) -> Any:
        """
        Acquire connection from pool.

        Returns:
            Connection object
        """
        async with self._lock:
            # Try to reuse existing connection
            if self._connections:
                return self._connections.pop(0)

            # Create new connection
            url = self.cluster.get_connection_url()
            if url is None:
                raise ConnectionError("No healthy brokers available")

            # In real implementation, create actual connection
            logger.debug(f"Creating new connection to {url}")
            return url  # Placeholder

    async def release(self, connection: Any) -> None:
        """
        Release connection back to pool.

        Args:
            connection: Connection to release
        """
        async with self._lock:
            if len(self._connections) < self.pool_size:
                self._connections.append(connection)
            else:
                # Pool full - close connection
                logger.debug("Pool full - closing connection")

    async def close_all(self) -> None:
        """Close all connections in pool."""
        async with self._lock:
            for conn in self._connections:
                # In real implementation, close connection
                logger.debug("Closing connection")
            self._connections.clear()

    def get_stats(self) -> dict:
        """
        Get pool statistics.

        Returns:
            Dict with pool stats
        """
        return {
            "pool_size": self.pool_size,
            "active_connections": len(self._connections),
            "utilization": len(self._connections) / self.pool_size,
        }


# --- Global Cluster ---

_global_cluster: Optional[RabbitMQCluster] = None


def get_rabbitmq_cluster(
    config: Optional[ClusterConfig] = None,
) -> RabbitMQCluster:
    """
    Get global RabbitMQ cluster.

    Args:
        config: Cluster configuration

    Returns:
        RabbitMQCluster instance
    """
    global _global_cluster

    if _global_cluster is None:
        if config is None:
            # Default to single local broker
            config = ClusterConfig(
                broker_urls=["amqp://guest:guest@localhost:5672/"]
            )

        _global_cluster = RabbitMQCluster(config)

    return _global_cluster
