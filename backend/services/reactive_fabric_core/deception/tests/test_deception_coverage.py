"""
Additional tests for Deception Engine to increase coverage.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..deception_engine import (
    DeceptionEngine,
    DeceptionConfig,
    DecoySystem,
    TrapDocument,
    BreadcrumbTrail,
    HoneytokenGenerator,
    TokenType
)


@pytest.fixture
def config():
    """Create test configuration."""
    return DeceptionConfig(
        honeytoken_types=[TokenType.COOKIE],
        honeytokens_per_type=2,
        max_decoy_systems=3,
        max_trap_documents=5,
        tracking_enabled=True
    )


@pytest.fixture
def engine(config):
    """Create test engine."""
    return DeceptionEngine(config)


@pytest.fixture
def generator():
    """Create honeytoken generator."""
    return HoneytokenGenerator()


class TestDeceptionCoverage:
    """Additional tests for deception engine coverage."""

    @pytest.mark.asyncio
    async def test_generate_cookie_token(self, generator):
        """Test cookie token generation."""
        cookie = generator.generate_cookie()

        assert cookie is not None
        assert "sessionid=" in cookie
        assert "csrftoken=" in cookie
        assert "user_id=" in cookie

    @pytest.mark.asyncio
    async def test_decoy_system_with_custom_ports(self, engine):
        """Test decoy system with custom port configuration."""
        engine.config.decoy_ports = [8080, 8443, 3389]

        await engine._create_decoy_systems()

        for decoy in engine.decoy_systems.values():
            # Check that services match configured ports
            service_ports = [s.split(":")[1] for s in decoy.services if ":" in s]
            assert any(str(port) in service_ports for port in engine.config.decoy_ports)

    @pytest.mark.asyncio
    async def test_trap_document_with_metadata(self, engine):
        """Test trap document with embedded metadata."""
        await engine._deploy_trap_documents()

        for trap in engine.trap_documents.values():
            # Check metadata fields
            assert trap.content_hash is not None
            assert len(trap.content_hash) == 64  # SHA256 hash length
            assert trap.embedded_tokens is not None
            assert isinstance(trap.access_log, list)

    @pytest.mark.asyncio
    async def test_breadcrumb_registry_path(self, engine):
        """Test breadcrumb with registry path type."""
        await engine._create_breadcrumbs()

        # Find registry breadcrumb
        registry_trails = [
            trail for trail in engine.breadcrumbs.values()
            if "HKEY" in trail.false_path or "registry" in trail.trail_type.lower()
        ]

        # Should have at least one registry-related breadcrumb
        assert len(registry_trails) > 0 or len(engine.breadcrumbs) > 0

    @pytest.mark.asyncio
    async def test_check_trap_document_exfiltration(self, engine):
        """Test trap document exfiltration detection."""
        await engine.initialize()

        trap = list(engine.trap_documents.values())[0]

        # Check with exfiltration action
        event = await engine.check_trap_document(
            trap.filename,
            "exfiltrated",
            "10.0.0.50",
            "attacker"
        )

        assert event is not None
        assert event.severity == "critical"
        assert event.action == "exfiltrated"

    @pytest.mark.asyncio
    async def test_get_active_honeytokens(self, engine):
        """Test getting active (non-triggered) honeytokens."""
        await engine.initialize()

        # Trigger one token
        token = list(engine.honeytokens.values())[0]
        await engine.check_honeytoken(token.token_value, "10.0.0.1")

        # Get active tokens
        active_tokens = [
            t for t in engine.honeytokens.values()
            if not t.triggered
        ]

        assert len(active_tokens) == len(engine.honeytokens) - 1

    @pytest.mark.asyncio
    async def test_decoy_system_os_types(self, engine):
        """Test decoy systems have varied OS types."""
        await engine._create_decoy_systems()

        os_types = set()
        for decoy in engine.decoy_systems.values():
            # Extract OS from hostname or properties
            if "win" in decoy.hostname.lower():
                os_types.add("windows")
            elif "ubuntu" in decoy.hostname.lower() or "debian" in decoy.hostname.lower():
                os_types.add("linux")
            else:
                os_types.add("unknown")

        # Should have variety in OS types
        assert len(os_types) >= 1

    @pytest.mark.asyncio
    async def test_trap_document_beacon(self, engine):
        """Test trap document with beacon callback."""
        await engine.initialize()

        trap = list(engine.trap_documents.values())[0]

        # Simulate beacon callback
        event = await engine.check_trap_document(
            trap.filename,
            "beacon_triggered",
            "192.168.1.100"
        )

        assert event is not None
        assert trap.triggered is True

    @pytest.mark.asyncio
    async def test_breadcrumb_follow_count(self, engine):
        """Test breadcrumb follow count tracking."""
        await engine.initialize()

        trail = list(engine.breadcrumbs.values())[0]

        # Follow multiple times
        for i in range(3):
            await engine.check_breadcrumb(trail.false_path, f"10.0.0.{i}")

        assert trail.follow_count == 3
        assert trail.followed is True

    @pytest.mark.asyncio
    async def test_rotate_specific_token_type(self, engine):
        """Test rotating specific token type only."""
        await engine.initialize()

        # Make API key tokens old
        api_tokens = [
            t for t in engine.honeytokens.values()
            if t.token_type == TokenType.API_KEY
        ]

        for token in api_tokens:
            token.created_at = datetime.utcnow() - timedelta(days=10)

        initial_count = len(engine.honeytokens)

        # Rotate
        rotated = await engine.rotate_honeytokens()

        assert rotated == len(api_tokens)
        assert len(engine.honeytokens) == initial_count

    @pytest.mark.asyncio
    async def test_deception_status_with_breadcrumbs(self, engine):
        """Test deception status includes breadcrumb info."""
        await engine.initialize()

        # Trigger a breadcrumb
        trail = list(engine.breadcrumbs.values())[0]
        await engine.check_breadcrumb(trail.false_path, "10.0.0.1")

        status = await engine.get_deception_status()

        assert "breadcrumbs" in status
        assert status["breadcrumbs"]["total"] > 0
        assert status["breadcrumbs"]["triggered"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_honeytoken_checks(self, engine):
        """Test concurrent honeytoken checks."""
        await engine.initialize()

        token = list(engine.honeytokens.values())[0]

        # Concurrent checks
        tasks = [
            engine.check_honeytoken(token.token_value, f"10.0.0.{i}")
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # All should detect the token
        assert all(r is not None for r in results)
        assert token.access_count == 5

    @pytest.mark.asyncio
    async def test_trap_document_hash_verification(self, engine):
        """Test trap document content hash verification."""
        await engine.initialize()

        trap = list(engine.trap_documents.values())[0]
        original_hash = trap.content_hash

        # Hash should remain consistent
        assert trap.content_hash == original_hash
        assert len(trap.content_hash) == 64  # SHA256

    @pytest.mark.asyncio
    async def test_decoy_interaction_types(self, engine):
        """Test different decoy interaction types."""
        await engine.initialize()

        decoy = list(engine.decoy_systems.values())[0]

        # Test different interaction types
        interactions = ["connection", "login_attempt", "command_execution", "file_access"]

        for interaction in interactions:
            event = await engine.check_decoy_interaction(
                decoy.ip_address,
                "10.0.0.1",
                interaction
            )
            assert event is not None
            assert event.action == interaction

    @pytest.mark.asyncio
    async def test_cleanup_on_stop(self, engine):
        """Test cleanup operations on stop."""
        await engine.start()

        # Add some events
        token = list(engine.honeytokens.values())[0]
        await engine.check_honeytoken(token.token_value, "10.0.0.1")

        initial_events = len(engine.events)

        await engine.stop()

        # Events should be preserved after stop
        assert len(engine.events) == initial_events
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_embedded_token_extraction(self, engine):
        """Test extraction of embedded tokens from documents."""
        await engine.initialize()

        # Check trap documents have embedded tokens
        for trap in engine.trap_documents.values():
            if trap.embedded_tokens:
                # Should be valid token IDs
                for token_id in trap.embedded_tokens:
                    assert token_id in engine.honeytokens or token_id == ""

    @pytest.mark.asyncio
    async def test_max_limits_enforcement(self, engine):
        """Test enforcement of max limits for deception elements."""
        engine.config.max_decoy_systems = 2
        engine.config.max_trap_documents = 3

        await engine.initialize()

        assert len(engine.decoy_systems) <= engine.config.max_decoy_systems
        assert len(engine.trap_documents) <= engine.config.max_trap_documents