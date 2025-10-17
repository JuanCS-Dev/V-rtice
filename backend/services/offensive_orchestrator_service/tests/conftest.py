"""
Pytest configuration and shared fixtures for Offensive Orchestrator Service tests.

Provides:
- Mock database connections
- Mock LLM clients
- Test data generators
- Common test utilities
"""

import os
import asyncio
from typing import Generator, AsyncGenerator, Dict, Any
from uuid import uuid4, UUID
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.services.offensive_orchestrator_service.models import (
    Base,
    CampaignObjective,
    CampaignPlan,
    ActionType,
    RiskLevel,
    CampaignStatus,
    HOTLRequest,
)
from backend.services.offensive_orchestrator_service.config import (
    ServiceConfig,
    DatabaseConfig,
    VectorDBConfig,
    LLMConfig,
    HOTLConfig,
)


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["QDRANT_HOST"] = "localhost"
    os.environ["QDRANT_PORT"] = "6333"
    os.environ["GEMINI_API_KEY"] = "test_api_key"
    os.environ["HOTL_ENABLED"] = "true"


# ============================================================================
# Async Event Loop
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing."""
    from sqlalchemy import event, TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    import uuid

    # UUID support for SQLite
    class GUID(TypeDecorator):
        """Platform-independent GUID type. Uses PostgreSQL's UUID type, otherwise uses CHAR(32)."""
        impl = CHAR
        cache_ok = True

        def load_dialect_impl(self, dialect):
            if dialect.name == 'postgresql':
                return dialect.type_descriptor(PGUUID())
            else:
                return dialect.type_descriptor(CHAR(32))

        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            elif dialect.name == 'postgresql':
                return str(value)
            else:
                if not isinstance(value, uuid.UUID):
                    return "%.32x" % uuid.UUID(value).int
                else:
                    return "%.32x" % value.int

        def process_result_value(self, value, dialect):
            if value is None:
                return value
            else:
                if not isinstance(value, uuid.UUID):
                    value = uuid.UUID(value)
                return value

    # Replace PGUUID with GUID for SQLite testing
    original_columns = {}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PGUUID):
                original_columns[column] = column.type
                column.type = GUID()

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

    # Restore original types
    for column, original_type in original_columns.items():
        column.type = original_type


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create database session for testing."""
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db_manager(test_db_engine):
    """Create DatabaseManager configured for testing with in-memory database."""
    from memory.database import DatabaseManager

    # Create DatabaseManager instance without calling __init__
    db = DatabaseManager.__new__(DatabaseManager)
    db.engine = test_db_engine
    db.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )

    yield db

    # Cleanup
    db.engine.dispose()


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_database_config() -> DatabaseConfig:
    """Test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        user="test_user",
        password="test_password",
        database="test_db",
        pool_size=5,
    )


@pytest.fixture
def test_vector_db_config() -> VectorDBConfig:
    """Test vector database configuration."""
    return VectorDBConfig(
        host="localhost",
        port=6333,
        collection_name="test_campaigns",
        api_key=None,
    )


@pytest.fixture
def test_llm_config() -> LLMConfig:
    """Test LLM configuration."""
    return LLMConfig(
        api_key="test_api_key",
        model="gemini-1.5-pro",
        temperature=0.7,
        max_tokens=4096,
        timeout_seconds=60,
    )


@pytest.fixture
def test_hotl_config() -> HOTLConfig:
    """Test HOTL configuration."""
    return HOTLConfig(
        enabled=True,
        approval_timeout_seconds=300,
        auto_approve_low_risk=True,
        audit_log_path="/tmp/test_hotl_audit.log",
    )


@pytest.fixture
def test_config(
    test_database_config,
    test_vector_db_config,
    test_llm_config,
    test_hotl_config,
) -> ServiceConfig:
    """Test full configuration."""
    return ServiceConfig(
        host="localhost",
        port=8090,
        debug=True,
        log_level="DEBUG",
        database=test_database_config,
        vectordb=test_vector_db_config,
        llm=test_llm_config,
        hotl=test_hotl_config,
    )


# ============================================================================
# Test Data Generators
# ============================================================================

@pytest.fixture
def sample_campaign_id() -> UUID:
    """Generate sample campaign UUID."""
    return uuid4()


@pytest.fixture
def sample_campaign_objective() -> CampaignObjective:
    """Generate sample campaign objective."""
    return CampaignObjective(
        target="example.com",
        scope=["web", "api"],
        objectives=["identify_vulnerabilities", "test_authentication"],
        constraints={
            "time_limit": "4h",
            "no_dos": True,
            "stealth_level": "high",
        },
        priority=7,
        created_by="test_operator",
    )


@pytest.fixture
def sample_campaign_action() -> Dict[str, Any]:
    """Generate sample campaign action."""
    return {
        "action": "Port scan",
        "ttp": "T1046",
        "agent": "recon_agent",
        "estimated_duration_min": 30,
        "requires_hotl": False,
    }


@pytest.fixture
def sample_campaign_phase(sample_campaign_action) -> Dict[str, Any]:
    """Generate sample campaign phase."""
    return {
        "name": "Phase 1: Reconnaissance",
        "actions": [sample_campaign_action],
    }


@pytest.fixture
def sample_campaign_plan(
    sample_campaign_id,
    sample_campaign_phase,
) -> CampaignPlan:
    """Generate sample campaign plan."""
    return CampaignPlan(
        campaign_id=sample_campaign_id,
        target="example.com",
        phases=[sample_campaign_phase],
        ttps=["T1046", "T1590"],
        estimated_duration_minutes=120,
        risk_assessment=RiskLevel.MEDIUM,
        success_criteria=["Identify all services", "Map attack surface"],
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_hotl_request(sample_campaign_id) -> HOTLRequest:
    """Generate sample HOTL request."""
    return HOTLRequest(
        request_id=uuid4(),
        campaign_id=sample_campaign_id,
        action_type=ActionType.EXPLOITATION,
        description="Exploit SQL injection vulnerability",
        risk_level=RiskLevel.HIGH,
        context={
            "vulnerability": "SQLi",
            "target_url": "https://example.com/api/login",
            "severity": "critical",
        },
    )


# ============================================================================
# Mock Utilities
# ============================================================================

@pytest.fixture
def mock_llm_response() -> str:
    """Mock LLM response for campaign planning."""
    return """
    CAMPAIGN PLAN:

    Phase 1: Reconnaissance (1h)
    - Action: Port scan (nmap, LOW risk)
    - Action: Service enumeration (nmap, LOW risk)

    Phase 2: Exploitation (2h)
    - Action: Test SQL injection (sqlmap, HIGH risk, requires_approval)
    - Action: Test XSS vulnerabilities (custom, MEDIUM risk)

    Total Duration: 3h
    Risk Assessment: MEDIUM
    """


@pytest.fixture
def mock_embedding_vector() -> list[float]:
    """Mock embedding vector (1536 dimensions)."""
    return [0.1] * 1536


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_campaign_plan(
    campaign_id: UUID | None = None,
    target: str = "test.example.com",
    num_phases: int = 2,
) -> CampaignPlan:
    """
    Helper to create test campaign plan.

    Args:
        campaign_id: Optional campaign ID
        target: Target identifier
        num_phases: Number of phases to create

    Returns:
        CampaignPlan instance
    """
    phases = []
    for i in range(num_phases):
        phase = {
            "name": f"Phase {i+1}: Test",
            "actions": [
                {
                    "action": f"Test action {i+1}",
                    "ttp": "T1046",
                    "agent": "test_agent",
                    "estimated_duration_min": 30,
                    "requires_hotl": False,
                }
            ],
        }
        phases.append(phase)

    return CampaignPlan(
        campaign_id=campaign_id or uuid4(),
        target=target,
        phases=phases,
        ttps=["T1046"],
        estimated_duration_minutes=num_phases * 60,
        risk_assessment=RiskLevel.LOW,
        success_criteria=["test_objective"],
        created_at=datetime.utcnow(),
    )


# Export helper functions
__all__ = [
    "create_test_campaign_plan",
]
