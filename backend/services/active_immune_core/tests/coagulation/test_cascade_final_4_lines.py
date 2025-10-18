"""Test missing lines in cascade.py - Final 4 lines to 100% coverage

Target lines:
- 363, 364: _execute_primary with injected reflex_triage (simulation path)
- 425, 426: _execute_neutralization with injected response_engine (simulation path)

Author: MAXIMUS Team
Date: 2025-10-15
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from coagulation.cascade import CoagulationCascadeSystem
from coagulation.models import (
    EnrichedThreat,
    ThreatSeverity,
    ThreatSource,
    BlastRadius,
)


class TestCascadeFinal4Lines:
    """Test final 4 missing lines in cascade.py"""

    @pytest.mark.asyncio
    async def test_execute_primary_with_injected_rte_simulation_lines_363_364(self):
        """
        Test _execute_primary when reflex_triage IS injected but uses simulation.

        Lines 363-364:
        await asyncio.sleep(0.1)
        return ContainmentResult(...)

        This is the TODO simulation path when RTE is injected.
        """
        system = CoagulationCascadeSystem()

        # Inject a mock reflex_triage (NOT None)
        mock_rte = Mock()
        mock_response_engine = Mock()
        mock_zone = Mock()
        mock_traffic = Mock()
        mock_firewall = Mock()

        system.set_dependencies(
            reflex_triage=mock_rte,
            response_engine=mock_response_engine,
            zone_isolator=mock_zone,
            traffic_shaper=mock_traffic,
            firewall_controller=mock_firewall,
        )

        # Create threat
        threat = EnrichedThreat(
            threat_id="test_rte_injected",
            threat_type="intrusion",
            severity=ThreatSeverity.LOW,
            source=ThreatSource(
                ip="192.168.1.100",
                port=443,
            ),
            blast_radius=BlastRadius(
                affected_zones=["DMZ"],
                affected_hosts=[],
            ),
            detection_timestamp=datetime.utcnow(),
            targeted_ports=[],
            compromised_credentials=[],
            affected_hosts=[],
        )

        # Execute cascade - this will hit lines 363-364 (simulation with RTE injected)
        result = await system.initiate_cascade(threat)

        # Verify cascade completed
        assert result.status == "SUCCESS"
        assert result.state.primary_result is not None
        assert result.state.primary_result.status == "CONTAINED"

    @pytest.mark.asyncio
    async def test_execute_neutralization_with_injected_engine_simulation_lines_425_426(self):
        """
        Test _execute_neutralization when response_engine IS injected but uses simulation.

        Lines 425-426:
        await asyncio.sleep(0.5)
        return {"status": "neutralized", "method": "simulated", "threat_id": state.threat.threat_id}

        This is the TODO simulation path when response engine is injected.
        """
        system = CoagulationCascadeSystem()

        # Inject mock dependencies (NOT None)
        mock_rte = Mock()
        mock_response_engine = Mock()  # NOT None, so hits lines 425-426
        mock_zone = Mock()
        mock_traffic = Mock()
        mock_firewall = Mock()

        system.set_dependencies(
            reflex_triage=mock_rte,
            response_engine=mock_response_engine,
            zone_isolator=mock_zone,
            traffic_shaper=mock_traffic,
            firewall_controller=mock_firewall,
        )

        # Create threat
        threat = EnrichedThreat(
            threat_id="test_response_engine_injected",
            threat_type="intrusion",
            severity=ThreatSeverity.MEDIUM,
            source=ThreatSource(
                ip="10.0.1.50",
                port=22,
            ),
            blast_radius=BlastRadius(
                affected_zones=["APPLICATION"],
                affected_hosts=["app-server-1"],
            ),
            detection_timestamp=datetime.utcnow(),
            targeted_ports=[22],
            compromised_credentials=[],
            affected_hosts=["app-server-1"],
        )

        # Execute cascade - this will hit lines 425-426 (simulation with response_engine injected)
        result = await system.initiate_cascade(threat)

        # Verify cascade completed
        assert result.status == "SUCCESS"
        assert result.state.neutralization_result is not None
        assert result.state.neutralization_result["status"] == "neutralized"
        assert result.state.neutralization_result["method"] == "simulated"
        assert result.state.neutralization_result["threat_id"] == threat.threat_id
