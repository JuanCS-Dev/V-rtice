"""FASE 10: Cloud Coordinator Service - Core Logic

Centralized brain for distributed organism.
Coordinates multiple edge agents.

NO MOCKS - Production-ready cloud coordination.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any, Dict, List, Optional, Set
import uuid

logger = logging.getLogger(__name__)


class AgentHealth(Enum):
    """Edge agent health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class RegisteredAgent:
    """Registered edge agent."""

    agent_id: str
    tenant_id: str
    host: str
    registered_at: datetime
    last_heartbeat: datetime
    health: AgentHealth = AgentHealth.HEALTHY
    events_received: int = 0
    events_processed: int = 0
    avg_latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_alive(self, timeout_seconds: float = 60.0) -> bool:
        """Check if agent is alive."""
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < timeout_seconds


class EventAggregator:
    """Aggregates events from multiple edge agents."""

    def __init__(self, window_seconds: float = 60.0):
        """Initialize aggregator.

        Args:
            window_seconds: Aggregation window
        """
        self.window_seconds = window_seconds
        self.events_by_tenant: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.event_counts: Dict[str, int] = defaultdict(int)

    def add_event(self, tenant_id: str, event: Dict[str, Any]):
        """Add event to aggregator."""
        self.events_by_tenant[tenant_id].append(event)
        self.event_counts[tenant_id] += 1

        # Cleanup old events
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        self.events_by_tenant[tenant_id] = [
            e
            for e in self.events_by_tenant[tenant_id]
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregation statistics."""
        total_events = sum(self.event_counts.values())
        return {
            "total_events": total_events,
            "events_by_tenant": dict(self.event_counts),
            "active_tenants": len(self.events_by_tenant),
            "window_seconds": self.window_seconds,
        }


class LoadBalancer:
    """Load balances requests across edge agents."""

    def __init__(self):
        """Initialize load balancer."""
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.response_times: Dict[str, List[float]] = defaultdict(list)

    def select_agent(self, agents: List[RegisteredAgent]) -> Optional[RegisteredAgent]:
        """Select best agent using least connections."""
        if not agents:
            return None

        # Filter healthy agents
        healthy = [
            a for a in agents if a.health == AgentHealth.HEALTHY and a.is_alive()
        ]

        if not healthy:
            return None

        # Least connections
        return min(healthy, key=lambda a: self.request_counts.get(a.agent_id, 0))

    def record_request(self, agent_id: str, response_time: float):
        """Record request to agent."""
        self.request_counts[agent_id] += 1
        self.response_times[agent_id].append(response_time)

        # Keep only recent times
        if len(self.response_times[agent_id]) > 100:
            self.response_times[agent_id] = self.response_times[agent_id][-100:]


class CloudCoordinatorController:
    """Main cloud coordinator controller."""

    def __init__(self, heartbeat_timeout: float = 60.0):
        """Initialize cloud coordinator.

        Args:
            heartbeat_timeout: Agent heartbeat timeout
        """
        self.heartbeat_timeout = heartbeat_timeout
        self.agents: Dict[str, RegisteredAgent] = {}
        self.aggregator = EventAggregator()
        self.load_balancer = LoadBalancer()
        self.total_events = 0

        logger.info("Cloud coordinator initialized")

    def register_agent(
        self,
        agent_id: str,
        tenant_id: str,
        host: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RegisteredAgent:
        """Register edge agent."""
        agent = RegisteredAgent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            host=host,
            registered_at=datetime.now(),
            last_heartbeat=datetime.now(),
            metadata=metadata or {},
        )

        self.agents[agent_id] = agent
        logger.info(f"Registered agent {agent_id} for tenant {tenant_id}")

        return agent

    def heartbeat(self, agent_id: str) -> bool:
        """Record agent heartbeat."""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.now()
            self.agents[agent_id].health = AgentHealth.HEALTHY
            return True
        return False

    def ingest_events(self, agent_id: str, events: List[Dict[str, Any]]):
        """Ingest events from edge agent."""
        if agent_id not in self.agents:
            logger.warning(f"Unknown agent {agent_id}")
            return

        agent = self.agents[agent_id]

        for event in events:
            self.aggregator.add_event(agent.tenant_id, event)

        agent.events_received += len(events)
        self.total_events += len(events)

        logger.info(f"Ingested {len(events)} events from agent {agent_id}")

    def check_agent_health(self):
        """Check health of all agents."""
        for agent in self.agents.values():
            if not agent.is_alive(self.heartbeat_timeout):
                agent.health = AgentHealth.OFFLINE
                logger.warning(f"Agent {agent.agent_id} offline")

    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status."""
        return {
            "total_agents": len(self.agents),
            "healthy_agents": sum(
                1 for a in self.agents.values() if a.health == AgentHealth.HEALTHY
            ),
            "total_events": self.total_events,
            "aggregator_stats": self.aggregator.get_stats(),
            "timestamp": datetime.now().isoformat(),
        }
