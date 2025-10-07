"""Tests for CytokineAggregator - Cytokine Processing

FASE 3 SPRINT 2: Test suite for cytokine aggregation, filtering, temperature impact,
and escalation logic extracted from lymphnode.py.

Test Structure:
- TestCytokineAggregatorLifecycle (5 tests)
- TestValidationAndParsing (6 tests)
- TestAreaFiltering (4 tests)
- TestCytokineProcessing (8 tests)
- TestTemperatureImpact (4 tests)
- TestStatistics (3 tests)

Total: 30 tests

NO MOCK, NO PLACEHOLDER, NO TODO - Production ready.
DOUTRINA VERTICE compliant: Quality-first, production-ready code.

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict

from coordination.cytokine_aggregator import (
    CytokineAggregator,
    CytokineType,
    EventType,
    ProcessingResult,
)
from pydantic import ValidationError


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def aggregator():
    """Create a CytokineAggregator with default settings."""
    return CytokineAggregator(
        area="network-zone-1",
        nivel="regional",
        escalation_priority_threshold=9,
    )


@pytest.fixture
def global_aggregator():
    """Create a global-level CytokineAggregator."""
    return CytokineAggregator(
        area="global",
        nivel="global",
        escalation_priority_threshold=9,
    )


@pytest.fixture
def valid_cytokine():
    """Create a valid cytokine message."""
    return {
        "tipo": "IL6",
        "emissor_id": "agent-001",
        "prioridade": 7,
        "timestamp": datetime.now().isoformat(),
        "area_alvo": "network-zone-1",
        "payload": {
            "evento": "ameaca_detectada",
            "alvo": {"id": "threat-123", "ip": "192.168.1.100"},
            "is_threat": True,
        },
    }


@pytest.fixture
def pro_inflammatory_cytokine():
    """Create a pro-inflammatory cytokine (IL1)."""
    return {
        "tipo": "IL1",
        "emissor_id": "agent-002",
        "prioridade": 8,
        "timestamp": datetime.now().isoformat(),
        "area_alvo": "network-zone-1",
        "payload": {"evento": "ameaca_detectada", "threat_id": "malware-x"},
    }


@pytest.fixture
def anti_inflammatory_cytokine():
    """Create an anti-inflammatory cytokine (IL10)."""
    return {
        "tipo": "IL10",
        "emissor_id": "agent-003",
        "prioridade": 5,
        "timestamp": datetime.now().isoformat(),
        "area_alvo": "network-zone-1",
        "payload": {"evento": "neutralizacao_sucesso", "threat_id": "malware-x"},
    }


@pytest.fixture
def high_priority_cytokine():
    """Create a high-priority cytokine (for escalation)."""
    return {
        "tipo": "TNF",
        "emissor_id": "agent-004",
        "prioridade": 10,  # Above escalation threshold
        "timestamp": datetime.now().isoformat(),
        "area_alvo": "network-zone-1",
        "payload": {
            "evento": "ameaca_detectada",
            "threat_id": "apt-threat",
            "is_threat": True,
        },
    }


# =============================================================================
# TEST LIFECYCLE
# =============================================================================


class TestCytokineAggregatorLifecycle:
    """Test CytokineAggregator initialization and configuration."""

    def test_initialization_default(self):
        """Test default initialization."""
        aggregator = CytokineAggregator()
        assert aggregator.area == "default"
        assert aggregator.nivel == "local"
        assert aggregator.escalation_priority_threshold == 9

    def test_initialization_custom(self):
        """Test custom initialization."""
        aggregator = CytokineAggregator(
            area="network-zone-2",
            nivel="regional",
            escalation_priority_threshold=8,
        )
        assert aggregator.area == "network-zone-2"
        assert aggregator.nivel == "regional"
        assert aggregator.escalation_priority_threshold == 8

    def test_initial_stats(self, aggregator):
        """Test initial statistics are zero."""
        stats = aggregator.get_stats()
        assert stats["total_processed"] == 0
        assert stats["total_threats"] == 0
        assert stats["total_neutralizations"] == 0
        assert stats["total_escalated"] == 0
        assert stats["total_validation_errors"] == 0

    def test_reset_stats(self, aggregator):
        """Test stats can be reset."""
        # Manually increment stats
        aggregator._total_processed = 10
        aggregator._total_threats = 5

        aggregator.reset_stats()

        stats = aggregator.get_stats()
        assert stats["total_processed"] == 0
        assert stats["total_threats"] == 0

    def test_repr(self, aggregator):
        """Test string representation."""
        repr_str = repr(aggregator)
        assert "CytokineAggregator" in repr_str
        assert "network-zone-1" in repr_str
        assert "regional" in repr_str


# =============================================================================
# TEST VALIDATION AND PARSING
# =============================================================================


class TestValidationAndParsing:
    """Test cytokine validation and parsing."""

    @pytest.mark.asyncio
    async def test_validate_and_parse_valid(self, aggregator, valid_cytokine):
        """Test validation succeeds for valid cytokine."""
        result = await aggregator.validate_and_parse(valid_cytokine)
        assert result is not None
        assert result["tipo"] == "IL6"
        assert result["emissor_id"] == "agent-001"

    @pytest.mark.asyncio
    async def test_validate_and_parse_invalid_missing_tipo(self, aggregator):
        """Test validation fails for cytokine missing 'tipo'."""
        invalid = {
            "emissor_id": "agent-001",
            "prioridade": 5,
            "timestamp": datetime.now().isoformat(),
        }
        result = await aggregator.validate_and_parse(invalid)
        assert result is None

        stats = aggregator.get_stats()
        assert stats["total_validation_errors"] == 1

    @pytest.mark.asyncio
    async def test_validate_and_parse_invalid_missing_emissor(self, aggregator):
        """Test validation fails for cytokine missing 'emissor_id'."""
        invalid = {
            "tipo": "IL6",
            "prioridade": 5,
            "timestamp": datetime.now().isoformat(),
        }
        result = await aggregator.validate_and_parse(invalid)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_and_parse_invalid_prioridade(self, aggregator):
        """Test validation fails for invalid prioridade (out of range)."""
        invalid = {
            "tipo": "IL6",
            "emissor_id": "agent-001",
            "prioridade": 15,  # Must be 0-10
            "timestamp": datetime.now().isoformat(),
        }
        result = await aggregator.validate_and_parse(invalid)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_and_parse_invalid_timestamp(self, aggregator):
        """Test validation fails for invalid timestamp format."""
        invalid = {
            "tipo": "IL6",
            "emissor_id": "agent-001",
            "prioridade": 5,
            "timestamp": "not-a-timestamp",
        }
        result = await aggregator.validate_and_parse(invalid)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_and_parse_tracks_errors(self, aggregator):
        """Test validation errors are tracked in stats."""
        invalid1 = {"tipo": "IL6"}  # Missing required fields
        invalid2 = {"emissor_id": "agent-001"}  # Missing tipo

        await aggregator.validate_and_parse(invalid1)
        await aggregator.validate_and_parse(invalid2)

        stats = aggregator.get_stats()
        assert stats["total_validation_errors"] == 2


# =============================================================================
# TEST AREA FILTERING
# =============================================================================


class TestAreaFiltering:
    """Test area-based cytokine filtering."""

    @pytest.mark.asyncio
    async def test_should_process_for_area_matching(self, aggregator, valid_cytokine):
        """Test regional aggregator processes cytokines from its area."""
        assert aggregator.area == "network-zone-1"
        assert valid_cytokine["area_alvo"] == "network-zone-1"

        should_process = await aggregator.should_process_for_area(valid_cytokine)
        assert should_process is True

    @pytest.mark.asyncio
    async def test_should_process_for_area_non_matching(self, aggregator):
        """Test regional aggregator skips cytokines from other areas."""
        other_area_cytokine = {
            "tipo": "IL6",
            "emissor_id": "agent-001",
            "area_alvo": "network-zone-2",  # Different area
        }

        should_process = await aggregator.should_process_for_area(other_area_cytokine)
        assert should_process is False

    @pytest.mark.asyncio
    async def test_should_process_for_area_global_processes_all(
        self, global_aggregator, valid_cytokine
    ):
        """Test global aggregator processes cytokines from all areas."""
        assert global_aggregator.nivel == "global"

        # Different area, but global processes all
        valid_cytokine["area_alvo"] = "network-zone-999"

        should_process = await global_aggregator.should_process_for_area(valid_cytokine)
        assert should_process is True

    @pytest.mark.asyncio
    async def test_should_process_for_area_missing_area(self, aggregator):
        """Test handling of cytokine with missing area_alvo."""
        no_area_cytokine = {
            "tipo": "IL6",
            "emissor_id": "agent-001",
            # No area_alvo field
        }

        should_process = await aggregator.should_process_for_area(no_area_cytokine)
        # Should not process (area_alvo=None != "network-zone-1")
        assert should_process is False


# =============================================================================
# TEST CYTOKINE PROCESSING
# =============================================================================


class TestCytokineProcessing:
    """Test cytokine processing logic."""

    @pytest.mark.asyncio
    async def test_process_cytokine_threat_detected(
        self, aggregator, valid_cytokine
    ):
        """Test processing cytokine with threat detection."""
        result = await aggregator.process_cytokine(valid_cytokine)

        assert isinstance(result, ProcessingResult)
        assert result.threat_detected is True
        assert result.threat_id == "threat-123"
        assert result.neutralization is False
        assert result.metadata["tipo"] == "IL6"
        assert result.metadata["prioridade"] == 7

        stats = aggregator.get_stats()
        assert stats["total_processed"] == 1
        assert stats["total_threats"] == 1

    @pytest.mark.asyncio
    async def test_process_cytokine_neutralization(
        self, aggregator, anti_inflammatory_cytokine
    ):
        """Test processing cytokine with neutralization event."""
        result = await aggregator.process_cytokine(anti_inflammatory_cytokine)

        assert result.threat_detected is False
        assert result.neutralization is True
        assert result.metadata["evento"] == "neutralizacao_sucesso"

        stats = aggregator.get_stats()
        assert stats["total_neutralizations"] == 1

    @pytest.mark.asyncio
    async def test_process_cytokine_nk_cytotoxicity(self, aggregator):
        """Test processing NK cytotoxicity event (neutralization)."""
        nk_cytokine = {
            "tipo": "TNF",
            "emissor_id": "nk-agent-001",
            "prioridade": 8,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {"evento": "nk_cytotoxicity", "target": "infected-cell"},
        }

        result = await aggregator.process_cytokine(nk_cytokine)

        assert result.neutralization is True
        assert result.threat_detected is False

    @pytest.mark.asyncio
    async def test_process_cytokine_neutrophil_net(self, aggregator):
        """Test processing neutrophil NET formation (neutralization)."""
        net_cytokine = {
            "tipo": "IL8",
            "emissor_id": "neutrophil-001",
            "prioridade": 7,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {"evento": "neutrophil_net_formation", "target": "bacteria"},
        }

        result = await aggregator.process_cytokine(net_cytokine)

        assert result.neutralization is True

    @pytest.mark.asyncio
    async def test_process_cytokine_escalation(
        self, aggregator, high_priority_cytokine
    ):
        """Test processing cytokine that triggers escalation."""
        assert aggregator.escalation_priority_threshold == 9
        assert high_priority_cytokine["prioridade"] == 10

        result = await aggregator.process_cytokine(high_priority_cytokine)

        assert result.should_escalate is True

        stats = aggregator.get_stats()
        assert stats["total_escalated"] == 1

    @pytest.mark.asyncio
    async def test_process_cytokine_no_escalation_low_priority(
        self, aggregator, valid_cytokine
    ):
        """Test processing cytokine that does NOT trigger escalation."""
        assert valid_cytokine["prioridade"] == 7  # Below threshold

        result = await aggregator.process_cytokine(valid_cytokine)

        assert result.should_escalate is False

        stats = aggregator.get_stats()
        assert stats["total_escalated"] == 0

    @pytest.mark.asyncio
    async def test_process_cytokine_threat_id_extraction(self, aggregator):
        """Test threat ID extraction from various payload locations."""
        # Test extraction from payload.alvo.id
        cytokine1 = {
            "tipo": "IL6",
            "emissor_id": "agent-001",
            "prioridade": 7,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {
                "evento": "ameaca_detectada",
                "alvo": {"id": "threat-from-alvo"},
            },
        }
        result1 = await aggregator.process_cytokine(cytokine1)
        assert result1.threat_id == "threat-from-alvo"

        # Test extraction from payload.host_id
        cytokine2 = {
            "tipo": "IL6",
            "emissor_id": "agent-002",
            "prioridade": 7,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {"evento": "ameaca_detectada", "host_id": "threat-from-host-id"},
        }
        result2 = await aggregator.process_cytokine(cytokine2)
        assert result2.threat_id == "threat-from-host-id"

        # Test extraction from payload.threat_id
        cytokine3 = {
            "tipo": "IL6",
            "emissor_id": "agent-003",
            "prioridade": 7,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {
                "evento": "ameaca_detectada",
                "threat_id": "threat-from-threat-id",
            },
        }
        result3 = await aggregator.process_cytokine(cytokine3)
        assert result3.threat_id == "threat-from-threat-id"

    @pytest.mark.asyncio
    async def test_process_cytokine_increments_stats(self, aggregator, valid_cytokine):
        """Test processing multiple cytokines increments stats correctly."""
        await aggregator.process_cytokine(valid_cytokine)
        await aggregator.process_cytokine(valid_cytokine)
        await aggregator.process_cytokine(valid_cytokine)

        stats = aggregator.get_stats()
        assert stats["total_processed"] == 3
        assert stats["total_threats"] == 3


# =============================================================================
# TEST TEMPERATURE IMPACT
# =============================================================================


class TestTemperatureImpact:
    """Test temperature impact calculation."""

    @pytest.mark.asyncio
    async def test_temperature_impact_pro_inflammatory(
        self, aggregator, pro_inflammatory_cytokine
    ):
        """Test pro-inflammatory cytokine increases temperature."""
        result = await aggregator.process_cytokine(pro_inflammatory_cytokine)

        assert result.temperature_delta == CytokineAggregator.TEMPERATURE_INCREASE
        assert result.temperature_delta == 0.2

    @pytest.mark.asyncio
    async def test_temperature_impact_anti_inflammatory(
        self, aggregator, anti_inflammatory_cytokine
    ):
        """Test anti-inflammatory cytokine decreases temperature."""
        result = await aggregator.process_cytokine(anti_inflammatory_cytokine)

        assert result.temperature_delta == CytokineAggregator.TEMPERATURE_DECREASE
        assert result.temperature_delta == -0.1

    @pytest.mark.asyncio
    async def test_temperature_impact_all_pro_inflammatory(self, aggregator):
        """Test all pro-inflammatory cytokines increase temperature."""
        pro_types = ["IL1", "IL6", "IL8", "TNF"]

        for cytokine_type in pro_types:
            cytokine = {
                "tipo": cytokine_type,
                "emissor_id": "agent-test",
                "prioridade": 5,
                "timestamp": datetime.now().isoformat(),
                "area_alvo": "network-zone-1",
                "payload": {},
            }

            result = await aggregator.process_cytokine(cytokine)
            assert result.temperature_delta == 0.2, f"{cytokine_type} should increase temp"

    @pytest.mark.asyncio
    async def test_temperature_impact_unknown_cytokine(self, aggregator):
        """Test unknown cytokine type has neutral temperature impact."""
        unknown_cytokine = {
            "tipo": "UNKNOWN_CYTOKINE",
            "emissor_id": "agent-test",
            "prioridade": 5,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {},
        }

        result = await aggregator.process_cytokine(unknown_cytokine)
        assert result.temperature_delta == 0.0


# =============================================================================
# TEST STATISTICS
# =============================================================================


class TestStatistics:
    """Test statistics collection and reporting."""

    @pytest.mark.asyncio
    async def test_stats_threat_rate(self, aggregator, valid_cytokine):
        """Test threat rate calculation in stats."""
        # Process 3 threats out of 5 cytokines
        await aggregator.process_cytokine(valid_cytokine)  # Threat
        await aggregator.process_cytokine(valid_cytokine)  # Threat
        await aggregator.process_cytokine(valid_cytokine)  # Threat

        neutral_cytokine = {
            "tipo": "IL10",
            "emissor_id": "agent-neutral",
            "prioridade": 3,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {},
        }
        await aggregator.process_cytokine(neutral_cytokine)  # Not a threat
        await aggregator.process_cytokine(neutral_cytokine)  # Not a threat

        stats = aggregator.get_stats()
        assert stats["total_processed"] == 5
        assert stats["total_threats"] == 3
        assert stats["threat_rate"] == 0.6  # 3/5

    @pytest.mark.asyncio
    async def test_stats_escalation_rate(self, aggregator, high_priority_cytokine):
        """Test escalation rate calculation in stats."""
        low_priority = {
            "tipo": "IL10",
            "emissor_id": "agent-low",
            "prioridade": 3,
            "timestamp": datetime.now().isoformat(),
            "area_alvo": "network-zone-1",
            "payload": {},
        }

        # Process 2 high priority (escalate) + 3 low priority (no escalate)
        await aggregator.process_cytokine(high_priority_cytokine)  # Escalate
        await aggregator.process_cytokine(high_priority_cytokine)  # Escalate
        await aggregator.process_cytokine(low_priority)  # No escalate
        await aggregator.process_cytokine(low_priority)  # No escalate
        await aggregator.process_cytokine(low_priority)  # No escalate

        stats = aggregator.get_stats()
        assert stats["total_processed"] == 5
        assert stats["total_escalated"] == 2
        assert stats["escalation_rate"] == 0.4  # 2/5

    @pytest.mark.asyncio
    async def test_stats_all_fields(self, aggregator):
        """Test all stats fields are present and correct."""
        stats = aggregator.get_stats()

        # Check all expected fields exist
        assert "area" in stats
        assert "nivel" in stats
        assert "escalation_threshold" in stats
        assert "total_processed" in stats
        assert "total_threats" in stats
        assert "total_neutralizations" in stats
        assert "total_escalated" in stats
        assert "total_validation_errors" in stats
        assert "threat_rate" in stats
        assert "escalation_rate" in stats

        # Check initial values
        assert stats["area"] == "network-zone-1"
        assert stats["nivel"] == "regional"
        assert stats["escalation_threshold"] == 9
        assert stats["threat_rate"] == 0.0  # No processing yet
        assert stats["escalation_rate"] == 0.0
