"""FASE 10: Edge Agent Service - Core Logic

Edge sensor for distributed organism deployment.
Collects events locally and syncs to cloud brain.

NO MOCKS - Production-ready edge deployment.
"""

import asyncio
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import gzip
import hashlib
import json
import logging
import time
from typing import Any, Deque, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types collected by edge agent."""

    FILE_EVENT = "file_event"
    NETWORK_EVENT = "network_event"
    PROCESS_EVENT = "process_event"
    SYSTEM_LOG = "system_log"
    SECURITY_ALERT = "security_alert"
    METRIC = "metric"


class EdgeAgentStatus(Enum):
    """Edge agent operational status."""

    INITIALIZING = "initializing"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    BUFFERING = "buffering"


@dataclass
class Event:
    """Edge-collected event."""

    event_id: str
    event_type: EventType
    timestamp: datetime
    source_host: str
    tenant_id: str
    severity: float  # 0.0 - 1.0
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source_host": self.source_host,
            "tenant_id": self.tenant_id,
            "severity": self.severity,
            "data": self.data,
            "metadata": self.metadata,
        }


@dataclass
class EventBatch:
    """Batch of events for efficient transmission."""

    batch_id: str
    events: List[Event]
    created_at: datetime
    compressed: bool = False
    compression_ratio: float = 1.0

    def compress(self) -> bytes:
        """Compress batch using gzip."""
        # Serialize to JSON
        data = {
            "batch_id": self.batch_id,
            "created_at": self.created_at.isoformat(),
            "events": [e.to_dict() for e in self.events],
        }

        json_bytes = json.dumps(data).encode("utf-8")
        compressed = gzip.compress(json_bytes, compresslevel=6)

        self.compressed = True
        self.compression_ratio = len(json_bytes) / max(len(compressed), 1)

        return compressed

    def size_bytes(self) -> int:
        """Get batch size in bytes."""
        data = json.dumps([e.to_dict() for e in self.events]).encode("utf-8")
        return len(data)


class LocalBuffer:
    """Local event buffer with backpressure control.

    Implements ring buffer with overflow protection.
    """

    def __init__(self, max_size: int = 100000):
        """Initialize buffer.

        Args:
            max_size: Maximum events in buffer
        """
        self.max_size = max_size
        self.buffer: Deque[Event] = deque(maxlen=max_size)
        self.overflow_count = 0
        self.total_buffered = 0

    def push(self, event: Event) -> bool:
        """Add event to buffer.

        Args:
            event: Event to buffer

        Returns:
            True if buffered, False if overflow
        """
        if len(self.buffer) >= self.max_size:
            self.overflow_count += 1
            logger.warning(f"Buffer overflow, dropping event {event.event_id}")
            return False

        self.buffer.append(event)
        self.total_buffered += 1
        return True

    def pop_batch(self, batch_size: int) -> List[Event]:
        """Pop batch of events from buffer.

        Args:
            batch_size: Number of events to pop

        Returns:
            List of events
        """
        batch = []

        for _ in range(min(batch_size, len(self.buffer))):
            if self.buffer:
                batch.append(self.buffer.popleft())

        return batch

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            "current_size": len(self.buffer),
            "max_size": self.max_size,
            "utilization": len(self.buffer) / self.max_size,
            "overflow_count": self.overflow_count,
            "total_buffered": self.total_buffered,
        }


class BatchingStrategy:
    """Intelligent batching strategy for event transmission.

    Batches based on size, time, and priority.
    """

    def __init__(
        self,
        max_batch_size: int = 1000,
        max_batch_age_seconds: float = 5.0,
        max_batch_bytes: int = 1_000_000,  # 1MB
    ):
        """Initialize batching strategy.

        Args:
            max_batch_size: Maximum events per batch
            max_batch_age_seconds: Maximum batch age before flush
            max_batch_bytes: Maximum batch size in bytes
        """
        self.max_batch_size = max_batch_size
        self.max_batch_age_seconds = max_batch_age_seconds
        self.max_batch_bytes = max_batch_bytes

    def should_flush(
        self,
        current_batch: List[Event],
        batch_created_at: datetime,
        high_priority: bool = False,
    ) -> bool:
        """Determine if batch should be flushed.

        Args:
            current_batch: Current batch
            batch_created_at: When batch was created
            high_priority: True if high priority event present

        Returns:
            True if should flush
        """
        # High priority - flush immediately
        if high_priority:
            return True

        # Size limit
        if len(current_batch) >= self.max_batch_size:
            return True

        # Age limit
        age = (datetime.now() - batch_created_at).total_seconds()
        if age >= self.max_batch_age_seconds:
            return True

        # Byte size limit (estimate)
        estimated_bytes = len(
            json.dumps([e.to_dict() for e in current_batch]).encode("utf-8")
        )
        if estimated_bytes >= self.max_batch_bytes:
            return True

        return False


class HeartbeatManager:
    """Manages heartbeat with cloud coordinator.

    Detects connectivity issues and triggers failover.
    """

    def __init__(self, heartbeat_interval: float = 30.0, timeout: float = 10.0):
        """Initialize heartbeat manager.

        Args:
            heartbeat_interval: Seconds between heartbeats
            timeout: Heartbeat timeout
        """
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout
        self.last_heartbeat: Optional[datetime] = None
        self.last_ack: Optional[datetime] = None
        self.missed_heartbeats = 0
        self.is_connected = False

    def should_send_heartbeat(self) -> bool:
        """Check if should send heartbeat."""
        if self.last_heartbeat is None:
            return True

        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed >= self.heartbeat_interval

    def record_heartbeat_sent(self):
        """Record heartbeat sent."""
        self.last_heartbeat = datetime.now()

    def record_heartbeat_ack(self):
        """Record heartbeat acknowledgment."""
        self.last_ack = datetime.now()
        self.missed_heartbeats = 0
        self.is_connected = True

    def check_timeout(self) -> bool:
        """Check if connection timed out.

        Returns:
            True if timed out
        """
        if self.last_heartbeat is None:
            return False

        if self.last_ack is None:
            elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
            if elapsed > self.timeout:
                self.missed_heartbeats += 1
                self.is_connected = False
                return True
        else:
            elapsed = (datetime.now() - self.last_ack).total_seconds()
            if elapsed > self.heartbeat_interval + self.timeout:
                self.missed_heartbeats += 1
                self.is_connected = False
                return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """Get heartbeat status."""
        return {
            "is_connected": self.is_connected,
            "last_heartbeat": (
                self.last_heartbeat.isoformat() if self.last_heartbeat else None
            ),
            "last_ack": self.last_ack.isoformat() if self.last_ack else None,
            "missed_heartbeats": self.missed_heartbeats,
        }


class RetryLogic:
    """Exponential backoff retry logic.

    Handles transient failures with intelligent retry.
    """

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """Initialize retry logic.

        Args:
            max_retries: Maximum retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Exponential backoff base
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.attempt_count: Dict[str, int] = {}

    def get_delay(self, operation_id: str) -> float:
        """Get retry delay for operation.

        Args:
            operation_id: Operation identifier

        Returns:
            Delay in seconds
        """
        attempts = self.attempt_count.get(operation_id, 0)

        if attempts >= self.max_retries:
            return -1  # Max retries exceeded

        # Exponential backoff: base_delay * (exponential_base ^ attempts)
        delay = self.base_delay * (self.exponential_base**attempts)
        delay = min(delay, self.max_delay)

        return delay

    def record_attempt(self, operation_id: str):
        """Record retry attempt."""
        self.attempt_count[operation_id] = self.attempt_count.get(operation_id, 0) + 1

    def record_success(self, operation_id: str):
        """Record successful operation."""
        if operation_id in self.attempt_count:
            del self.attempt_count[operation_id]

    def should_retry(self, operation_id: str) -> bool:
        """Check if should retry operation."""
        attempts = self.attempt_count.get(operation_id, 0)
        return attempts < self.max_retries


class LocalMetrics:
    """Local metrics collection for edge agent."""

    def __init__(self):
        """Initialize metrics."""
        self.events_collected = 0
        self.events_sent = 0
        self.events_failed = 0
        self.bytes_sent = 0
        self.batches_sent = 0
        self.compression_ratios: List[float] = []
        self.send_latencies: List[float] = []
        self.start_time = datetime.now()

    def record_event_collected(self):
        """Record event collected."""
        self.events_collected += 1

    def record_batch_sent(
        self,
        event_count: int,
        bytes_sent: int,
        compression_ratio: float,
        latency: float,
    ):
        """Record batch sent."""
        self.events_sent += event_count
        self.bytes_sent += bytes_sent
        self.batches_sent += 1
        self.compression_ratios.append(compression_ratio)
        self.send_latencies.append(latency)

    def record_send_failure(self, event_count: int):
        """Record send failure."""
        self.events_failed += event_count

    def get_stats(self) -> Dict[str, Any]:
        """Get metrics statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()

        avg_compression = sum(self.compression_ratios) / max(
            len(self.compression_ratios), 1
        )
        avg_latency = sum(self.send_latencies) / max(len(self.send_latencies), 1)

        return {
            "uptime_seconds": uptime,
            "events_collected": self.events_collected,
            "events_sent": self.events_sent,
            "events_failed": self.events_failed,
            "events_per_second": self.events_collected / max(uptime, 1),
            "bytes_sent": self.bytes_sent,
            "batches_sent": self.batches_sent,
            "avg_compression_ratio": avg_compression,
            "avg_send_latency_ms": avg_latency * 1000,
            "success_rate": self.events_sent / max(self.events_collected, 1),
        }


class EdgeAgentController:
    """Main edge agent controller.

    Coordinates all edge agent components.
    """

    def __init__(
        self,
        agent_id: str,
        tenant_id: str,
        source_host: str,
        cloud_coordinator_url: str,
        buffer_size: int = 100000,
        batch_size: int = 1000,
        batch_age_seconds: float = 5.0,
    ):
        """Initialize edge agent.

        Args:
            agent_id: Unique agent identifier
            tenant_id: Tenant identifier
            source_host: Source hostname
            cloud_coordinator_url: Cloud coordinator URL
            buffer_size: Local buffer size
            batch_size: Max batch size
            batch_age_seconds: Max batch age
        """
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.source_host = source_host
        self.cloud_coordinator_url = cloud_coordinator_url

        # Components
        self.buffer = LocalBuffer(max_size=buffer_size)
        self.batching = BatchingStrategy(
            max_batch_size=batch_size, max_batch_age_seconds=batch_age_seconds
        )
        self.heartbeat = HeartbeatManager()
        self.retry = RetryLogic()
        self.metrics = LocalMetrics()

        # State
        self.status = EdgeAgentStatus.INITIALIZING
        self.current_batch: List[Event] = []
        self.batch_created_at: Optional[datetime] = None

        logger.info(f"Edge agent {agent_id} initialized for tenant {tenant_id}")

    def collect_event(
        self,
        event_type: EventType,
        severity: float,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Collect edge event.

        Args:
            event_type: Event type
            severity: Event severity (0.0 - 1.0)
            data: Event data
            metadata: Optional metadata

        Returns:
            Event ID
        """
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            source_host=self.source_host,
            tenant_id=self.tenant_id,
            severity=severity,
            data=data,
            metadata=metadata or {},
        )

        # Buffer event
        buffered = self.buffer.push(event)

        if buffered:
            self.metrics.record_event_collected()
            logger.debug(f"Collected event {event.event_id}")

        return event.event_id

    def process_buffer(self) -> List[EventBatch]:
        """Process buffer and create batches.

        Returns:
            List of batches ready to send
        """
        batches = []

        # Initialize batch if needed
        if self.batch_created_at is None:
            self.batch_created_at = datetime.now()

        # Check if should flush current batch
        high_priority = any(e.severity >= 0.8 for e in self.current_batch)

        if self.current_batch and self.batching.should_flush(
            self.current_batch, self.batch_created_at, high_priority
        ):
            # Create batch
            batch = EventBatch(
                batch_id=str(uuid.uuid4()),
                events=self.current_batch.copy(),
                created_at=self.batch_created_at,
            )

            batches.append(batch)

            # Reset current batch
            self.current_batch = []
            self.batch_created_at = datetime.now()

        # Fill current batch from buffer
        available_slots = self.batching.max_batch_size - len(self.current_batch)

        if available_slots > 0:
            new_events = self.buffer.pop_batch(available_slots)
            self.current_batch.extend(new_events)

        return batches

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        return {
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "source_host": self.source_host,
            "status": self.status.value,
            "cloud_coordinator_url": self.cloud_coordinator_url,
            "buffer": self.buffer.get_stats(),
            "heartbeat": self.heartbeat.get_status(),
            "metrics": self.metrics.get_stats(),
            "current_batch_size": len(self.current_batch),
        }
