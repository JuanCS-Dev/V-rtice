"""WebSocket Event Broadcaster - PRODUCTION-READY

Helper functions for broadcasting system events via WebSocket.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional

from .events import WSEvent, WSEventType
from .router import get_connection_manager

logger = logging.getLogger(__name__)


async def broadcast_agent_created(agent_data: Dict[str, Any]) -> int:
    """
    Broadcast agent created event.

    Args:
        agent_data: Agent data dictionary

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.AGENT_CREATED,
        data=agent_data,
        source="agent_service",
        room="agents",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="agents")


async def broadcast_agent_updated(agent_data: Dict[str, Any]) -> int:
    """
    Broadcast agent updated event.

    Args:
        agent_data: Agent data dictionary

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.AGENT_UPDATED,
        data=agent_data,
        source="agent_service",
        room="agents",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="agents")


async def broadcast_agent_deleted(agent_id: str) -> int:
    """
    Broadcast agent deleted event.

    Args:
        agent_id: Deleted agent identifier

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.AGENT_DELETED,
        data={"agent_id": agent_id},
        source="agent_service",
        room="agents",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="agents")


async def broadcast_agent_status_changed(
    agent_id: str, old_status: str, new_status: str
) -> int:
    """
    Broadcast agent status changed event.

    Args:
        agent_id: Agent identifier
        old_status: Previous status
        new_status: New status

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.AGENT_STATUS_CHANGED,
        data={
            "agent_id": agent_id,
            "old_status": old_status,
            "new_status": new_status,
        },
        source="agent_service",
        room="agents",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="agents")


async def broadcast_agent_action(
    agent_id: str, action: str, result: Dict[str, Any]
) -> int:
    """
    Broadcast agent action event.

    Args:
        agent_id: Agent identifier
        action: Action performed
        result: Action result

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.AGENT_ACTION,
        data={
            "agent_id": agent_id,
            "action": action,
            "result": result,
        },
        source="agent_service",
        room="agents",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="agents")


async def broadcast_task_created(task_data: Dict[str, Any]) -> int:
    """
    Broadcast task created event.

    Args:
        task_data: Task data dictionary

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.TASK_CREATED,
        data=task_data,
        source="coordination_service",
        room="tasks",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="tasks")


async def broadcast_task_status_changed(
    task_id: str, old_status: str, new_status: str
) -> int:
    """
    Broadcast task status changed event.

    Args:
        task_id: Task identifier
        old_status: Previous status
        new_status: New status

    Returns:
        Number of connections notified
    """
    # Map to appropriate event type
    event_type_map = {
        "assigned": WSEventType.TASK_ASSIGNED,
        "running": WSEventType.TASK_STARTED,
        "completed": WSEventType.TASK_COMPLETED,
        "failed": WSEventType.TASK_FAILED,
        "cancelled": WSEventType.TASK_CANCELLED,
    }

    event_type = event_type_map.get(new_status, WSEventType.TASK_CREATED)

    event = WSEvent(
        event_type=event_type,
        data={
            "task_id": task_id,
            "old_status": old_status,
            "new_status": new_status,
        },
        source="coordination_service",
        room="tasks",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="tasks")


async def broadcast_election_triggered() -> int:
    """
    Broadcast election triggered event.

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.ELECTION_TRIGGERED,
        data={"message": "Leader election triggered"},
        source="coordination_service",
        room="coordination",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="coordination")


async def broadcast_leader_elected(leader_id: str, election_term: int) -> int:
    """
    Broadcast leader elected event.

    Args:
        leader_id: Elected leader identifier
        election_term: Election term number

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.LEADER_ELECTED,
        data={
            "leader_id": leader_id,
            "election_term": election_term,
        },
        source="coordination_service",
        room="coordination",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="coordination")


async def broadcast_consensus_proposed(proposal_data: Dict[str, Any]) -> int:
    """
    Broadcast consensus proposal event.

    Args:
        proposal_data: Proposal data dictionary

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.CONSENSUS_PROPOSED,
        data=proposal_data,
        source="coordination_service",
        room="coordination",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="coordination")


async def broadcast_consensus_decided(
    proposal_id: str, decision: str, approval_rate: float
) -> int:
    """
    Broadcast consensus decision event.

    Args:
        proposal_id: Proposal identifier
        decision: Decision result (approved/rejected)
        approval_rate: Approval rate (0.0-1.0)

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.CONSENSUS_DECIDED,
        data={
            "proposal_id": proposal_id,
            "decision": decision,
            "approval_rate": approval_rate,
        },
        source="coordination_service",
        room="coordination",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="coordination")


async def broadcast_health_changed(health_status: str, details: Dict[str, Any]) -> int:
    """
    Broadcast health status changed event.

    Args:
        health_status: New health status
        details: Health check details

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.HEALTH_CHANGED,
        data={
            "status": health_status,
            "details": details,
        },
        source="health_service",
        room="system",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="system")


async def broadcast_metrics_updated(metrics_data: Dict[str, Any]) -> int:
    """
    Broadcast metrics updated event.

    Args:
        metrics_data: Metrics data dictionary

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.METRICS_UPDATED,
        data=metrics_data,
        source="metrics_service",
        room="system",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="system")


async def broadcast_alert_triggered(
    alert_level: str, message: str, details: Optional[Dict[str, Any]] = None
) -> int:
    """
    Broadcast alert triggered event.

    Args:
        alert_level: Alert level (info, warning, error, critical)
        message: Alert message
        details: Optional alert details

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=WSEventType.ALERT_TRIGGERED,
        data={
            "level": alert_level,
            "message": message,
            "details": details or {},
        },
        source="alert_service",
        room="system",
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room="system")


async def broadcast_custom_event(
    event_type: WSEventType,
    data: Dict[str, Any],
    room: Optional[str] = None,
    source: str = "custom",
) -> int:
    """
    Broadcast custom event.

    Args:
        event_type: Event type
        data: Event data
        room: Optional room to broadcast to
        source: Event source

    Returns:
        Number of connections notified
    """
    event = WSEvent(
        event_type=event_type,
        data=data,
        source=source,
        room=room,
    )

    manager = get_connection_manager()
    return await manager.broadcast(event, room=room)
