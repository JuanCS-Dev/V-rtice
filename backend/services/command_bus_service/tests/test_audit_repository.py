"""Tests for Audit Repository."""

from uuid import uuid4

import pytest
from backend.services.command_bus_service.audit_repository import AuditLog, AuditRepository


@pytest.mark.asyncio
async def test_save_audit_log():
    """Test saving audit log."""
    repo = AuditRepository()
    command_id = uuid4()

    audit = AuditLog(
        command_id=command_id,
        layer="SOFTWARE",
        action="test_action",
        success=True,
        details={"key": "value"},
    )

    await repo.save(audit)

    assert repo.count() == 1


@pytest.mark.asyncio
async def test_get_by_command():
    """Test retrieving audit logs by command ID."""
    repo = AuditRepository()
    command_id = uuid4()

    audit1 = AuditLog(
        command_id=command_id,
        layer="SOFTWARE",
        action="action1",
        success=True,
    )
    audit2 = AuditLog(
        command_id=command_id,
        layer="NETWORK",
        action="action2",
        success=True,
    )
    audit3 = AuditLog(
        command_id=uuid4(),
        layer="SOFTWARE",
        action="action3",
        success=False,
    )

    await repo.save(audit1)
    await repo.save(audit2)
    await repo.save(audit3)

    logs = await repo.get_by_command(command_id)

    assert len(logs) == 2
    assert all(log.command_id == command_id for log in logs)


@pytest.mark.asyncio
async def test_get_all():
    """Test retrieving all audit logs."""
    repo = AuditRepository()

    audit1 = AuditLog(
        command_id=uuid4(),
        layer="SOFTWARE",
        action="action1",
        success=True,
    )
    audit2 = AuditLog(
        command_id=uuid4(),
        layer="NETWORK",
        action="action2",
        success=False,
    )

    await repo.save(audit1)
    await repo.save(audit2)

    logs = await repo.get_all()

    assert len(logs) == 2


def test_count():
    """Test audit log count."""
    repo = AuditRepository()

    assert repo.count() == 0


@pytest.mark.asyncio
async def test_count_after_saves():
    """Test audit log count after saves."""
    repo = AuditRepository()

    for i in range(5):
        audit = AuditLog(
            command_id=uuid4(),
            layer="SOFTWARE",
            action=f"action{i}",
            success=True,
        )
        await repo.save(audit)

    assert repo.count() == 5
