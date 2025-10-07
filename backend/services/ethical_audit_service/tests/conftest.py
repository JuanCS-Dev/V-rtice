"""Shared test fixtures and configuration for Ethical Audit Service tests.

This module provides reusable fixtures following PAGANI Standard:
- Mock external dependencies (PostgreSQL via asyncpg, Auth JWT)
- Provide test data factories
- DO NOT mock internal business logic
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from auth import TokenData, UserRole
from models import (
    ComplianceResult,
    DecisionType,
    EthicalDecisionLog,
    FinalDecision,
    OverrideReason,
    OperatorRole,
    Regulation,
    RiskLevel,
    UrgencyLevel,
)


# ============================================================================
# MOCK DATABASE FIXTURES
# ============================================================================


class MockAsyncPGConnection:
    """Mock asyncpg connection for testing."""

    def __init__(self):
        self._data_store = {
            "ethical_decisions": [],
            "human_overrides": [],
            "compliance_logs": [],
        }
        self._query_results = {}

    async def execute(self, query: str, *args):
        """Mock execute for schema initialization."""
        return "CREATE"

    async def fetchval(self, query: str, *args):
        """Mock fetchval for single value queries."""
        # Handle COUNT queries
        if "COUNT(*)" in query:
            if "ethical_decisions" in query:
                return len(self._data_store["ethical_decisions"])
            elif "human_overrides" in query:
                return len(self._data_store["human_overrides"])
            elif "compliance_logs" in query:
                return len(self._data_store["compliance_logs"])

        # Handle MAX queries
        if "MAX(timestamp)" in query:
            if self._data_store["ethical_decisions"]:
                return self._data_store["ethical_decisions"][-1].get("timestamp")
            return None

        # Handle INSERT RETURNING
        if "INSERT INTO" in query and "RETURNING" in query:
            new_id = args[0] if args else uuid.uuid4()
            return new_id

        # Default: return from query results
        return self._query_results.get(query)

    async def fetch(self, query: str, *args):
        """Mock fetch for multiple row queries."""
        if "ethical_decisions" in query:
            return self._data_store["ethical_decisions"]
        elif "human_overrides" in query:
            return len(self._data_store["human_overrides"])
        elif "compliance_logs" in query:
            return self._data_store["compliance_logs"]
        return []

    async def fetchrow(self, query: str, *args):
        """Mock fetchrow for single row queries."""
        if self._data_store["ethical_decisions"]:
            return self._data_store["ethical_decisions"][0]
        return None

    def set_query_result(self, query: str, result: Any):
        """Set result for a specific query."""
        self._query_results[query] = result

    def add_decision(self, decision: Dict[str, Any]):
        """Add decision to mock store."""
        self._data_store["ethical_decisions"].append(decision)

    def add_override(self, override: Dict[str, Any]):
        """Add override to mock store."""
        self._data_store["human_overrides"].append(override)

    def add_compliance_log(self, log: Dict[str, Any]):
        """Add compliance log to mock store."""
        self._data_store["compliance_logs"].append(log)


class MockAsyncPGPool:
    """Mock asyncpg pool for testing."""

    def __init__(self):
        self.connection = MockAsyncPGConnection()
        self._size = 10

    def acquire(self):
        """Mock acquire context manager."""
        return self

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def close(self):
        """Mock close."""
        pass

    def get_size(self):
        """Mock get_size."""
        return self._size


@pytest_asyncio.fixture
async def mock_db_pool():
    """Provides a mock asyncpg pool for testing."""
    return MockAsyncPGPool()


@pytest_asyncio.fixture
async def mock_db(mock_db_pool):
    """Provides a mock EthicalAuditDatabase instance."""
    from database import EthicalAuditDatabase

    db = EthicalAuditDatabase()
    db.pool = mock_db_pool
    return db


# ============================================================================
# MOCK AUTH FIXTURES
# ============================================================================


def create_mock_user(
    user_id: str = "test_user",
    username: str = "test_username",
    roles: List[str] = None,
) -> TokenData:
    """Create a mock authenticated user for testing.

    Args:
        user_id: User identifier
        username: Username
        roles: List of role strings

    Returns:
        TokenData instance
    """
    return TokenData(
        user_id=user_id,
        username=username,
        roles=roles or [UserRole.SOC_OPERATOR.value],
    )


@pytest.fixture
def mock_soc_user():
    """Mock SOC operator user."""
    return create_mock_user(roles=[UserRole.SOC_OPERATOR.value])


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    return create_mock_user(roles=[UserRole.ADMIN.value])


@pytest.fixture
def mock_auditor_user():
    """Mock auditor user."""
    return create_mock_user(roles=[UserRole.AUDITOR.value])


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def client(mock_db):
    """Provides an async HTTP client with mocked database.

    This fixture overrides the database dependency and auth dependencies
    to allow testing without PostgreSQL or JWT tokens.
    """
    import api

    # Override database in api module
    original_db = api.db
    api.db = mock_db

    # Create client (use localhost to pass TrustedHostMiddleware)
    transport = ASGITransport(app=api.app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac

    # Cleanup
    api.db = original_db


@pytest_asyncio.fixture
async def authenticated_client(mock_db, mock_soc_user):
    """Provides an authenticated HTTP client with SOC user role."""
    import api

    # Override database in api module
    original_db = api.db
    api.db = mock_db

    # Override auth dependency
    api.app.dependency_overrides[api.get_current_user] = lambda: mock_soc_user

    transport = ASGITransport(app=api.app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac

    # Cleanup
    api.app.dependency_overrides.clear()
    api.db = original_db


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================


@pytest.fixture
def create_test_decision_log():
    """Factory fixture for creating test EthicalDecisionLog instances."""

    def _create(
        decision_type: DecisionType = DecisionType.OFFENSIVE_ACTION,
        final_decision: FinalDecision = FinalDecision.APPROVED,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        **kwargs
    ) -> EthicalDecisionLog:
        """Create a test EthicalDecisionLog instance.

        Args:
            decision_type: Type of decision
            final_decision: Final decision outcome
            risk_level: Risk level
            **kwargs: Additional fields to override

        Returns:
            EthicalDecisionLog instance
        """
        defaults = {
            "id": uuid.uuid4(),
            "timestamp": datetime.utcnow(),
            "decision_type": decision_type,
            "action_description": "Test offensive action for security assessment",
            "system_component": "test_component",
            "input_context": {"target": "test_target", "severity": "high"},
            "final_decision": final_decision,
            "final_confidence": 0.85,
            "decision_explanation": "Decision approved based on ethical framework consensus",
            "total_latency_ms": 250,
            "risk_level": risk_level,
            "automated": True,
        }
        defaults.update(kwargs)
        return EthicalDecisionLog(**defaults)

    return _create


@pytest.fixture
def create_test_override_request():
    """Factory fixture for creating test HumanOverrideRequest payloads."""

    def _create(
        decision_id: uuid.UUID = None,
        operator_role: str = OperatorRole.SOC_ANALYST.value,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test HumanOverrideRequest payload.

        Args:
            decision_id: Decision ID to override
            operator_role: Role of operator (string value)
            **kwargs: Additional fields

        Returns:
            Dict with override request data
        """
        defaults = {
            "decision_id": str(decision_id or uuid.uuid4()),
            "operator_id": "test_operator",
            "operator_role": operator_role,
            "original_decision": FinalDecision.REJECTED.value,
            "override_decision": FinalDecision.APPROVED.value,
            "justification": "Override justified due to operational necessity and false positive assessment",
            "override_reason": OverrideReason.FALSE_POSITIVE.value,
            "urgency_level": UrgencyLevel.URGENT.value,
        }
        defaults.update(kwargs)
        return defaults

    return _create


@pytest.fixture
def create_test_compliance_request():
    """Factory fixture for creating test ComplianceCheckRequest payloads."""

    def _create(
        regulation: Regulation = Regulation.NIST_AI_RMF,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test ComplianceCheckRequest payload.

        Args:
            regulation: Regulation to check
            **kwargs: Additional fields

        Returns:
            Dict with compliance request data
        """
        defaults = {
            "regulation": regulation.value,
            "requirement_id": "NIST-AI-RMF-3.1",
            "check_type": "automated",
            "check_result": ComplianceResult.COMPLIANT.value,
            "evidence": {"test_coverage": "95%", "framework_agreement": "90%"},
            "findings": "All automated checks passed",
            "remediation_required": False,
        }
        defaults.update(kwargs)
        return defaults

    return _create
