"""
Tests for Deception Engine.

Tests honeytoken generation, decoy systems, trap documents, and breadcrumbs.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..deception_engine import (
    DeceptionEngine,
    DeceptionConfig,
    DeceptionType,
    TokenType,
    Honeytoken,
    DecoySystem,
    TrapDocument,
    BreadcrumbTrail,
    DeceptionEvent,
    HoneytokenGenerator
)


@pytest.fixture
def config():
    """Create test configuration."""
    return DeceptionConfig(
        honeytoken_types=[
            TokenType.API_KEY,
            TokenType.PASSWORD,
            TokenType.DATABASE_CRED
        ],
        honeytokens_per_type=3,
        token_rotation_days=7,
        max_decoy_systems=5,
        decoy_ports=[22, 80, 443],
        trap_document_types=["txt", "pdf", "json"],
        max_trap_documents=10,
        alert_threshold=1,
        tracking_enabled=True
    )


@pytest.fixture
def engine(config):
    """Create test deception engine."""
    return DeceptionEngine(config)


@pytest.fixture
def generator():
    """Create honeytoken generator."""
    return HoneytokenGenerator()


class TestDeceptionEngine:
    """Test suite for DeceptionEngine."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        await engine.initialize()

        assert len(engine.honeytokens) > 0
        assert len(engine.decoy_systems) > 0
        assert len(engine.trap_documents) > 0
        assert len(engine.breadcrumbs) > 0
        assert engine.triggers_count == 0

    @pytest.mark.asyncio
    async def test_honeytoken_generation(self, engine):
        """Test honeytoken generation."""
        await engine._generate_honeytokens()

        # Check correct number of tokens
        expected_count = len(engine.config.honeytoken_types) * engine.config.honeytokens_per_type
        assert len(engine.honeytokens) == expected_count

        # Check token types
        token_types = [token.token_type for token in engine.honeytokens.values()]
        for expected_type in engine.config.honeytoken_types:
            assert expected_type in token_types

        # Check token values are not empty
        for token in engine.honeytokens.values():
            assert token.token_value
            assert token.token_id
            assert token.created_at

    @pytest.mark.asyncio
    async def test_check_honeytoken_triggered(self, engine):
        """Test honeytoken trigger detection."""
        await engine.initialize()

        # Get a honeytoken value
        token = list(engine.honeytokens.values())[0]
        token_value = token.token_value

        # Check the token
        event = await engine.check_honeytoken(token_value, "192.168.1.100")

        assert event is not None
        assert event.deception_type == DeceptionType.HONEYTOKEN
        assert event.source_ip == "192.168.1.100"
        assert event.severity == "high"

        # Check token was marked as triggered
        assert token.triggered is True
        assert token.access_count == 1

        # Check event was logged
        assert len(engine.events) == 1
        assert engine.triggers_count == 1

    @pytest.mark.asyncio
    async def test_check_honeytoken_not_triggered(self, engine):
        """Test non-honeytoken doesn't trigger."""
        await engine.initialize()

        # Check a non-existent token
        event = await engine.check_honeytoken("not_a_honeytoken", "192.168.1.100")

        assert event is None
        assert engine.triggers_count == 0

    @pytest.mark.asyncio
    async def test_decoy_system_creation(self, engine):
        """Test decoy system creation."""
        await engine._create_decoy_systems()

        assert len(engine.decoy_systems) > 0

        for decoy in engine.decoy_systems.values():
            assert decoy.hostname
            assert decoy.ip_address
            assert len(decoy.services) > 0
            assert decoy.created_at

    @pytest.mark.asyncio
    async def test_check_decoy_interaction(self, engine):
        """Test decoy system interaction detection."""
        await engine.initialize()

        # Get a decoy system
        decoy = list(engine.decoy_systems.values())[0]

        # Check interaction with decoy
        event = await engine.check_decoy_interaction(
            decoy.ip_address,
            "10.0.0.50",
            "connection"
        )

        assert event is not None
        assert event.deception_type == DeceptionType.DECOY_SYSTEM
        assert event.source_ip == "10.0.0.50"
        assert event.action == "connection"

        # Check decoy was marked as triggered
        assert decoy.triggered is True
        assert decoy.interaction_count == 1

    @pytest.mark.asyncio
    async def test_trap_document_deployment(self, engine):
        """Test trap document deployment."""
        await engine._deploy_trap_documents()

        assert len(engine.trap_documents) > 0

        for trap in engine.trap_documents.values():
            assert trap.filename
            assert trap.document_type in engine.config.trap_document_types
            assert trap.tracking_token
            assert trap.content_hash
            assert len(trap.deployed_paths) > 0

    @pytest.mark.asyncio
    async def test_check_trap_document(self, engine):
        """Test trap document access detection."""
        await engine.initialize()

        # Get a trap document
        trap = list(engine.trap_documents.values())[0]

        # Check document access
        event = await engine.check_trap_document(
            trap.filename,
            "opened",
            "192.168.1.200",
            "user123"
        )

        assert event is not None
        assert event.deception_type == DeceptionType.TRAP_DOCUMENT
        assert event.source_ip == "192.168.1.200"
        assert event.source_user == "user123"
        assert event.action == "opened"
        assert event.severity == "high"

        # Check trap was marked as triggered
        assert trap.triggered is True
        assert len(trap.access_log) == 1

    @pytest.mark.asyncio
    async def test_check_trap_document_critical_action(self, engine):
        """Test trap document with critical action."""
        await engine.initialize()

        trap = list(engine.trap_documents.values())[0]

        # Check critical action
        event = await engine.check_trap_document(
            trap.filename,
            "copied",
            "192.168.1.200"
        )

        assert event.severity == "critical"

    @pytest.mark.asyncio
    async def test_breadcrumb_creation(self, engine):
        """Test breadcrumb trail creation."""
        await engine._create_breadcrumbs()

        assert len(engine.breadcrumbs) > 0

        for trail in engine.breadcrumbs.values():
            assert trail.trail_type
            assert trail.false_path
            assert trail.created_at
            assert trail.followed is False

    @pytest.mark.asyncio
    async def test_check_breadcrumb(self, engine):
        """Test breadcrumb following detection."""
        await engine.initialize()

        # Get a breadcrumb
        trail = list(engine.breadcrumbs.values())[0]

        # Check breadcrumb access
        event = await engine.check_breadcrumb(trail.false_path, "10.0.0.100")

        assert event is not None
        assert event.deception_type == DeceptionType.BREADCRUMB
        assert event.source_ip == "10.0.0.100"
        assert event.action == "followed"
        assert event.severity == "medium"

        # Check breadcrumb was marked as followed
        assert trail.followed is True
        assert trail.follow_count == 1

    @pytest.mark.asyncio
    async def test_get_deception_status(self, engine):
        """Test deception status reporting."""
        await engine.initialize()

        # Trigger some elements
        token = list(engine.honeytokens.values())[0]
        await engine.check_honeytoken(token.token_value, "192.168.1.100")

        status = await engine.get_deception_status()

        assert "honeytokens" in status
        assert status["honeytokens"]["total"] > 0
        assert status["honeytokens"]["triggered"] > 0
        assert "decoy_systems" in status
        assert "trap_documents" in status
        assert "breadcrumbs" in status
        assert status["total_triggers"] == 1
        assert len(status["recent_events"]) == 1

    @pytest.mark.asyncio
    async def test_honeytoken_rotation(self, engine):
        """Test honeytoken rotation."""
        await engine.initialize()

        # Get initial count
        initial_count = len(engine.honeytokens)

        # Make some tokens old
        for token in list(engine.honeytokens.values())[:2]:
            token.created_at = datetime.utcnow() - timedelta(days=10)

        # Rotate tokens
        rotated = await engine.rotate_honeytokens()

        assert rotated == 2
        assert len(engine.honeytokens) == initial_count

    @pytest.mark.asyncio
    async def test_honeytoken_rotation_skip_triggered(self, engine):
        """Test that triggered tokens are not rotated."""
        await engine.initialize()

        # Make a token old but triggered
        token = list(engine.honeytokens.values())[0]
        token.created_at = datetime.utcnow() - timedelta(days=10)
        token.triggered = True

        # Rotate tokens
        rotated = await engine.rotate_honeytokens()

        # Triggered token should not be rotated
        assert token.token_id in engine.honeytokens

    @pytest.mark.asyncio
    async def test_start_stop(self, engine):
        """Test engine start and stop."""
        await engine.start()
        assert engine._running is True
        assert len(engine.honeytokens) > 0

        await engine.stop()
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_get_metrics(self, engine):
        """Test metrics retrieval."""
        await engine.initialize()

        # Trigger some events
        token = list(engine.honeytokens.values())[0]
        await engine.check_honeytoken(token.token_value, "192.168.1.100")

        metrics = engine.get_metrics()

        assert metrics["running"] is False
        assert metrics["honeytokens"] > 0
        assert metrics["decoy_systems"] > 0
        assert metrics["trap_documents"] > 0
        assert metrics["breadcrumbs"] > 0
        assert metrics["total_triggers"] == 1
        assert metrics["events_logged"] == 1

    @pytest.mark.asyncio
    async def test_multiple_token_access(self, engine):
        """Test multiple accesses to same honeytoken."""
        await engine.initialize()

        token = list(engine.honeytokens.values())[0]

        # Access token multiple times
        for i in range(3):
            event = await engine.check_honeytoken(token.token_value, f"192.168.1.{i}")

        assert token.access_count == 3
        assert len(engine.events) == 3
        assert engine.triggers_count == 3

    def test_repr(self, engine):
        """Test string representation."""
        repr_str = repr(engine)
        assert "DeceptionEngine" in repr_str
        assert "running=" in repr_str
        assert "honeytokens=" in repr_str
        assert "triggers=" in repr_str


class TestHoneytokenGenerator:
    """Test suite for HoneytokenGenerator."""

    def test_generate_api_key(self, generator):
        """Test API key generation."""
        key = generator.generate_api_key()

        assert key
        assert "_" in key
        assert len(key) > 20

    def test_generate_password(self, generator):
        """Test password generation."""
        password = generator.generate_password()

        assert password
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%" for c in password)

    def test_generate_ssh_key(self, generator):
        """Test SSH key generation."""
        key = generator.generate_ssh_key()

        assert key
        assert "BEGIN" in key
        assert "PRIVATE KEY" in key
        assert "END" in key

    def test_generate_database_cred(self, generator):
        """Test database credential generation."""
        creds = generator.generate_database_cred()

        assert creds
        assert "host" in creds
        assert "port" in creds
        assert "username" in creds
        assert "password" in creds
        assert "database" in creds

    def test_generate_aws_key(self, generator):
        """Test AWS key generation."""
        creds = generator.generate_aws_key()

        assert creds
        assert "access_key_id" in creds
        assert "secret_access_key" in creds
        assert "region" in creds
        assert creds["access_key_id"].startswith("AKIA")

    def test_generate_jwt(self, generator):
        """Test JWT generation."""
        jwt = generator.generate_jwt()

        assert jwt
        assert jwt.count(".") == 2  # JWT has three parts
        parts = jwt.split(".")
        assert len(parts) == 3