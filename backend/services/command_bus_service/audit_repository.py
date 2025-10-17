"""Audit repository for C2L command execution logs."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class AuditLog(BaseModel):
    """Audit log entry."""

    audit_id: UUID = Field(default_factory=uuid4)
    command_id: UUID
    layer: str
    action: str
    success: bool
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditRepository:
    """Repository for audit logs (in-memory for now, DB in production)."""

    def __init__(self) -> None:
        """Initialize repository."""
        self.logs: list[AuditLog] = []

    async def save(self, audit: AuditLog) -> None:
        """Save audit log."""
        self.logs.append(audit)
        logger.debug("audit_saved", audit_id=str(audit.audit_id), command_id=str(audit.command_id))

    async def get_by_command(self, command_id: UUID) -> list[AuditLog]:
        """Get all audit logs for a command."""
        return [log for log in self.logs if log.command_id == command_id]

    async def get_all(self) -> list[AuditLog]:
        """Get all audit logs."""
        return self.logs

    def count(self) -> int:
        """Get total count of audit logs."""
        return len(self.logs)
