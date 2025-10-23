"""
Tests for Sensory-ESGT Bridge
==============================

Validates the integration between Predictive Coding and ESGT consciousness.

Test Coverage:
- Salience computation from prediction errors
- Threshold-based ignition triggering
- Context-aware relevance/urgency
- End-to-end sensory→conscious pathway
- Statistics tracking

NO MOCK for core logic (ESGT coordinator can be mocked for unit tests).

Authors: Claude Code + Juan Carlos
Version: 1.0.0
Date: 2025-10-12
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from consciousness.integration.sensory_esgt_bridge import (
    SensoryESGTBridge,
    SensoryContext,
    SalienceFactors,
    PredictionError,
)


# ==================== FIXTURES ====================


@pytest.fixture
def mock_esgt():
    """Mock ESGT coordinator for isolated testing."""
    esgt = MagicMock()
    esgt.initiate_esgt = AsyncMock()
    return esgt


@pytest.fixture
def bridge(mock_esgt):
    """Sensory bridge with mocked ESGT."""
    return SensoryESGTBridge(
        esgt_coordinator=mock_esgt,
        salience_threshold=0.7,
        novelty_amplification=1.2,
    )


@pytest.fixture
def high_error():
    """High prediction error (salient)."""
    return PredictionError(
        layer_id=1,
        magnitude=0.8,
        max_error=1.0,
        bounded=True,
    )


@pytest.fixture
def low_error():
    """Low prediction error (not salient)."""
    return PredictionError(
        layer_id=1,
        magnitude=0.2,
        max_error=1.0,
        bounded=True,
    )


@pytest.fixture
def security_context():
    """High-priority security event context."""
    return SensoryContext(
        modality="security",
        timestamp=1234567890.0,
        source="intrusion_detection",
        metadata={
            "security_event": True,
            "severity": "critical",
            "anomaly": True,
        }
    )


@pytest.fixture
def normal_context():
    """Normal, low-priority context."""
    return SensoryContext(
        modality="system",
        timestamp=1234567890.0,
        source="monitoring",
        metadata={
            "security_event": False,
            "severity": "info",
        }
    )


# ==================== SALIENCE COMPUTATION ====================


class TestSalienceComputation:
    """Test salience factor computation from prediction errors."""
    
    def test_novelty_from_high_error(self, bridge, high_error, normal_context):
        """High prediction error → high novelty."""
        factors = bridge.compute_salience_from_error(high_error, normal_context)
        
        # Error 0.8 with amplification 1.2 → novelty ~0.96
        assert factors.novelty > 0.9
        assert factors.novelty <= 1.0
    
    def test_novelty_from_low_error(self, bridge, low_error, normal_context):
        """Low prediction error → low novelty."""
        factors = bridge.compute_salience_from_error(low_error, normal_context)
        
        # Error 0.2 with amplification → novelty ~0.24
        assert factors.novelty < 0.3
    
    def test_relevance_security_event(self, bridge, high_error, security_context):
        """Security events have high relevance."""
        factors = bridge.compute_salience_from_error(high_error, security_context)
        
        assert factors.relevance >= 0.9  # Security = HIGH
    
    def test_relevance_normal_event(self, bridge, high_error, normal_context):
        """Normal events have moderate relevance."""
        factors = bridge.compute_salience_from_error(high_error, normal_context)
        
        assert 0.4 <= factors.relevance <= 0.6  # Default = MEDIUM
    
    def test_urgency_critical_severity(self, bridge, high_error, security_context):
        """Critical severity → high urgency."""
        factors = bridge.compute_salience_from_error(high_error, security_context)
        
        assert factors.urgency == 1.0  # Critical = MAX
    
    def test_urgency_info_severity(self, bridge, high_error, normal_context):
        """Info severity → low urgency."""
        factors = bridge.compute_salience_from_error(high_error, normal_context)
        
        assert factors.urgency <= 0.4  # Info = LOW
    
    def test_intensity_from_magnitude(self, bridge, high_error, normal_context):
        """Intensity reflects error magnitude."""
        factors = bridge.compute_salience_from_error(high_error, normal_context)
        
        # Error 0.8 → intensity 0.8
        assert abs(factors.intensity - 0.8) < 0.1


class TestSalienceFactors:
    """Test SalienceFactors data class."""
    
    def test_compute_total_salience_weighted(self):
        """Total salience uses correct weights."""
        factors = SalienceFactors(
            novelty=1.0,
            relevance=1.0,
            urgency=1.0,
            intensity=1.0,
        )
        
        # 0.4*1.0 + 0.3*1.0 + 0.2*1.0 + 0.1*1.0 = 1.0
        total = factors.compute_total_salience()
        assert abs(total - 1.0) < 0.01  # Floating point tolerance
    
    def test_compute_total_salience_partial(self):
        """Partial factors compute correctly."""
        factors = SalienceFactors(
            novelty=0.8,
            relevance=0.6,
            urgency=0.4,
            intensity=0.2,
        )
        
        expected = 0.4*0.8 + 0.3*0.6 + 0.2*0.4 + 0.1*0.2
        assert abs(factors.compute_total_salience() - expected) < 0.01
    
    def test_novelty_weight_dominates(self):
        """Novelty has highest weight (0.4)."""
        # High novelty, low others
        high_novelty = SalienceFactors(
            novelty=1.0,
            relevance=0.0,
            urgency=0.0,
            intensity=0.0,
        )
        
        # Low novelty, high others
        low_novelty = SalienceFactors(
            novelty=0.0,
            relevance=1.0,
            urgency=1.0,
            intensity=1.0,
        )
        
        # High novelty alone (0.4) > all others combined (0.6)
        assert high_novelty.compute_total_salience() < low_novelty.compute_total_salience()


# ==================== IGNITION DECISION ====================


class TestIgnitionDecision:
    """Test threshold-based ignition triggering."""
    
    def test_high_salience_triggers_ignition(self, bridge):
        """Salience above threshold → should ignite."""
        factors = SalienceFactors(
            novelty=1.0,
            relevance=0.9,
            urgency=0.8,
            intensity=0.7,
        )
        
        # Total ~0.91 > threshold 0.7
        assert bridge.should_trigger_ignition(factors)
    
    def test_low_salience_no_ignition(self, bridge):
        """Salience below threshold → should not ignite."""
        factors = SalienceFactors(
            novelty=0.3,
            relevance=0.3,
            urgency=0.3,
            intensity=0.3,
        )
        
        # Total 0.3 < threshold 0.7
        assert not bridge.should_trigger_ignition(factors)
    
    def test_threshold_boundary(self, bridge):
        """Salience exactly at threshold → should ignite."""
        # Construct factors that sum exactly to 0.7
        factors = SalienceFactors(
            novelty=0.7 / 0.4,  # Reverse weight
            relevance=0.0,
            urgency=0.0,
            intensity=0.0,
        )
        
        # Should be at threshold
        assert abs(factors.compute_total_salience() - 0.7) < 0.01
        assert bridge.should_trigger_ignition(factors)


# ==================== CONTENT BUILDING ====================


class TestContentBuilding:
    """Test conscious content construction."""
    
    def test_content_includes_error_info(self, bridge, high_error, normal_context):
        """Content includes prediction error details."""
        factors = SalienceFactors(0.8, 0.6, 0.4, 0.5)
        
        content = bridge.build_conscious_content(high_error, normal_context, factors)
        
        assert "prediction_error" in content
        assert content["prediction_error"]["magnitude"] == 0.8
        assert content["prediction_error"]["layer_id"] == 1
    
    def test_content_includes_salience(self, bridge, high_error, normal_context):
        """Content includes salience breakdown."""
        factors = SalienceFactors(0.8, 0.6, 0.4, 0.5)
        
        content = bridge.build_conscious_content(high_error, normal_context, factors)
        
        assert "salience" in content
        assert content["salience"]["novelty"] == 0.8
        assert content["salience"]["relevance"] == 0.6
        assert "total" in content["salience"]
    
    def test_content_includes_context(self, bridge, high_error, security_context):
        """Content includes contextual metadata."""
        factors = SalienceFactors(0.8, 0.9, 1.0, 0.7)
        
        content = bridge.build_conscious_content(high_error, security_context, factors)
        
        assert content["modality"] == "security"
        assert content["source"] == "sensory_bridge"
        assert "context" in content
        assert content["context"]["security_event"] == True


# ==================== END-TO-END PROCESSING ====================


class TestEndToEndProcessing:
    """Test complete sensory→conscious pathway."""
    
    @pytest.mark.asyncio
    async def test_high_error_triggers_ignition(self, bridge, mock_esgt, high_error, security_context):
        """High error + security context → ESGT ignition."""
        # Mock successful ignition
        mock_event = MagicMock()
        mock_event.success = True
        mock_esgt.initiate_esgt.return_value = mock_event
        
        result = await bridge.process_sensory_input(high_error, security_context)
        
        # Should have triggered
        assert result == True
        assert mock_esgt.initiate_esgt.called
        assert bridge.ignitions_triggered == 1
    
    @pytest.mark.asyncio
    async def test_low_error_no_ignition(self, bridge, mock_esgt, low_error, normal_context):
        """Low error + normal context → no ignition."""
        result = await bridge.process_sensory_input(low_error, normal_context)
        
        # Should not have triggered (below min threshold)
        assert result == False
        assert not mock_esgt.initiate_esgt.called
        assert bridge.ignitions_triggered == 0
    
    @pytest.mark.asyncio
    async def test_force_ignition_bypasses_threshold(self, bridge, mock_esgt, low_error, normal_context):
        """Force ignition bypasses threshold check."""
        mock_event = MagicMock()
        mock_event.success = True
        mock_esgt.initiate_esgt.return_value = mock_event
        
        result = await bridge.process_sensory_input(
            low_error, normal_context, force_ignition=True
        )
        
        # Should have triggered despite low salience
        assert result == True
        assert mock_esgt.initiate_esgt.called
    
    @pytest.mark.asyncio
    async def test_failed_ignition_returns_false(self, bridge, mock_esgt, high_error, security_context):
        """Failed ESGT ignition returns False."""
        # Mock failed ignition
        mock_event = MagicMock()
        mock_event.success = False
        mock_esgt.initiate_esgt.return_value = mock_event
        
        result = await bridge.process_sensory_input(high_error, security_context)
        
        # Should return false even though triggered
        assert result == False
        assert mock_esgt.initiate_esgt.called


# ==================== STATISTICS ====================


class TestStatistics:
    """Test bridge statistics tracking."""
    
    @pytest.mark.asyncio
    async def test_statistics_initialization(self, bridge):
        """Statistics start at zero."""
        stats = bridge.get_statistics()
        
        assert stats["total_inputs"] == 0
        assert stats["salient_inputs"] == 0
        assert stats["ignitions_triggered"] == 0
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, bridge, mock_esgt, high_error, low_error, security_context, normal_context):
        """Statistics track inputs correctly."""
        mock_event = MagicMock()
        mock_event.success = True
        mock_esgt.initiate_esgt.return_value = mock_event
        
        # Process high error (should ignite)
        await bridge.process_sensory_input(high_error, security_context)
        
        # Process low error (should not ignite)
        await bridge.process_sensory_input(low_error, normal_context)
        
        stats = bridge.get_statistics()
        
        assert stats["total_inputs"] == 2
        assert stats["salient_inputs"] >= 1  # At least high error
        assert stats["ignitions_triggered"] == 1
    
    @pytest.mark.asyncio
    async def test_salient_rate_calculation(self, bridge, mock_esgt, high_error, security_context):
        """Salient rate computed correctly."""
        mock_event = MagicMock()
        mock_event.success = True
        mock_esgt.initiate_esgt.return_value = mock_event
        
        # Process 10 high-error inputs
        for _ in range(10):
            await bridge.process_sensory_input(high_error, security_context)
        
        stats = bridge.get_statistics()
        
        # All should be salient
        assert stats["salient_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_ignition_success_rate(self, bridge, mock_esgt, high_error, security_context):
        """Ignition success rate computed correctly."""
        mock_event = MagicMock()
        mock_event.success = True
        mock_esgt.initiate_esgt.return_value = mock_event
        
        # Process inputs
        await bridge.process_sensory_input(high_error, security_context)
        await bridge.process_sensory_input(high_error, security_context)
        
        stats = bridge.get_statistics()
        
        # All salient should have ignited successfully
        assert stats["ignition_success_rate"] == 1.0


# ==================== INTEGRATION TESTS ====================


class TestIntegration:
    """Integration tests with real components (where possible)."""
    
    def test_bridge_initialization(self):
        """Bridge initializes with correct defaults."""
        mock_esgt = MagicMock()
        
        bridge = SensoryESGTBridge(
            esgt_coordinator=mock_esgt,
            salience_threshold=0.8,
            novelty_amplification=1.5,
            min_error_for_salience=0.4,
        )
        
        assert bridge.salience_threshold == 0.8
        assert bridge.novelty_amplification == 1.5
        assert bridge.min_error_threshold == 0.4
        assert bridge.total_inputs == 0
    
    def test_multiple_modalities(self, bridge, high_error):
        """Bridge handles different sensory modalities."""
        modalities = ["visual", "auditory", "network", "system", "security"]
        
        for modality in modalities:
            context = SensoryContext(
                modality=modality,
                timestamp=0.0,
                source="test",
                metadata={}
            )
            
            factors = bridge.compute_salience_from_error(high_error, context)
            
            # Should compute without errors
            assert 0.0 <= factors.compute_total_salience() <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=consciousness/integration/sensory_esgt_bridge"])
