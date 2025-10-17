"""PatternDetector - Complete Test Suite for 100% Coverage

Tests for coordination/pattern_detector.py - Threat pattern recognition
extracted from LinfonodoDigital as part of FASE 3 Desacoplamento.

Coverage Target: ≥95% of pattern_detector.py
Test Strategy: Real execution with no mocks (except time when needed)
Quality Standard: Production-ready, NO MOCK, NO PLACEHOLDER, NO TODO

Test Categories:
----------------
1. Lifecycle (5 tests) - initialization, configuration
2. Persistent Threat Detection (8 tests) - threshold, confidence, edge cases
3. Coordinated Attack Detection (7 tests) - multi-threat scenarios
4. Pattern History (3 tests) - tracking, filtering, clearing
5. Statistics (2 tests) - metrics collection

Authors: Juan & Claude Code
Version: 1.0.0
Date: 2025-10-07
"""

from datetime import datetime, timedelta

import pytest

from active_immune_core.coordination.pattern_detector import (
    PatternDetector,
    PatternType,
)

# ==================== LIFECYCLE TESTS ====================


class TestPatternDetectorLifecycle:
    """Test PatternDetector initialization and configuration."""

    def test_pattern_detector_initialization(self):
        """Test PatternDetector initialization with all parameters."""
        # ACT: Create detector with custom parameters
        detector = PatternDetector(
            persistent_threshold=7,
            coordinated_threshold=15,
            time_window_sec=120.0,
        )

        # ASSERT: All parameters set correctly
        assert detector.persistent_threshold == 7
        assert detector.coordinated_threshold == 15
        assert detector.time_window_sec == 120.0
        assert len(detector._pattern_history) == 0
        assert detector._max_history_size == 1000

    def test_pattern_detector_default_parameters(self):
        """Test PatternDetector with default parameters."""
        # ACT: Create detector with defaults
        detector = PatternDetector()

        # ASSERT: Defaults applied
        assert detector.persistent_threshold == 5
        assert detector.coordinated_threshold == 10
        assert detector.time_window_sec == 60.0

    def test_pattern_detector_repr(self):
        """Test __repr__ method."""
        # ARRANGE: Create detector
        detector = PatternDetector(
            persistent_threshold=5,
            coordinated_threshold=10,
        )

        # ACT: Get string representation
        repr_str = repr(detector)

        # ASSERT: Contains key information
        assert "PatternDetector" in repr_str
        assert "persistent=5" in repr_str
        assert "coordinated=10" in repr_str
        assert "window=60.0s" in repr_str
        assert "history=0" in repr_str

    def test_pattern_detector_zero_threshold(self):
        """Test PatternDetector with zero threshold (edge case)."""
        # ACT: Create detector with zero thresholds
        detector = PatternDetector(
            persistent_threshold=0,
            coordinated_threshold=0,
        )

        # ASSERT: Zero values accepted
        assert detector.persistent_threshold == 0
        assert detector.coordinated_threshold == 0

    def test_pattern_detector_high_threshold(self):
        """Test PatternDetector with very high thresholds."""
        # ACT: Create detector with high thresholds
        detector = PatternDetector(
            persistent_threshold=1000,
            coordinated_threshold=500,
        )

        # ASSERT: High values accepted
        assert detector.persistent_threshold == 1000
        assert detector.coordinated_threshold == 500


# ==================== PERSISTENT THREAT DETECTION TESTS ====================


class TestPersistentThreatDetection:
    """Test persistent threat detection logic."""

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_single_threat(self):
        """Test detection of single persistent threat."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5)

        # Threat counts with one exceeding threshold
        threat_counts = {
            "malware_x": 7,
            "scan_y": 2,
        }

        # ACT: Detect patterns
        patterns = await detector.detect_persistent_threats(threat_counts)

        # ASSERT: One pattern detected
        assert len(patterns) == 1
        assert patterns[0].pattern_type == PatternType.PERSISTENT
        assert patterns[0].threat_ids == ["malware_x"]
        assert patterns[0].detection_count == 7
        assert patterns[0].confidence > 0.0

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_multiple(self):
        """Test detection of multiple persistent threats."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5)

        # Multiple threats exceeding threshold
        threat_counts = {
            "malware_a": 10,
            "malware_b": 8,
            "malware_c": 6,
            "scan_d": 2,
        }

        # ACT: Detect patterns
        patterns = await detector.detect_persistent_threats(threat_counts)

        # ASSERT: Three patterns detected
        assert len(patterns) == 3
        threat_ids = {p.threat_ids[0] for p in patterns}
        assert threat_ids == {"malware_a", "malware_b", "malware_c"}

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_none_detected(self):
        """Test when no threats exceed threshold."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5)

        # All threats below threshold
        threat_counts = {
            "scan_a": 1,
            "scan_b": 3,
            "scan_c": 4,
        }

        # ACT: Detect patterns
        patterns = await detector.detect_persistent_threats(threat_counts)

        # ASSERT: No patterns detected
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_exact_threshold(self):
        """Test detection at exact threshold boundary."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5)

        # Threat exactly at threshold
        threat_counts = {
            "malware_x": 5,
        }

        # ACT: Detect patterns
        patterns = await detector.detect_persistent_threats(threat_counts)

        # ASSERT: Pattern detected (threshold is inclusive: >=)
        assert len(patterns) == 1
        assert patterns[0].detection_count == 5

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_confidence_calculation(self):
        """Test confidence score calculation."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=10)

        # ACT: Test different counts
        patterns_low = await detector.detect_persistent_threats({"threat": 10})  # At threshold
        patterns_med = await detector.detect_persistent_threats({"threat": 15})  # Mid range
        patterns_high = await detector.detect_persistent_threats({"threat": 30})  # Above cap

        # ASSERT: Confidence increases with count
        assert patterns_low[0].confidence < patterns_med[0].confidence
        assert patterns_med[0].confidence < patterns_high[0].confidence
        # Confidence capped at 1.0
        assert patterns_high[0].confidence == 1.0
        # Low confidence should be 0.5 (10 / (10 * 2))
        assert patterns_low[0].confidence == 0.5

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_empty_input(self):
        """Test with empty threat counts."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5)

        # ACT: Detect with empty dict
        patterns = await detector.detect_persistent_threats({})

        # ASSERT: No patterns detected
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_metadata(self):
        """Test pattern metadata population."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5)

        # ACT: Detect pattern
        patterns = await detector.detect_persistent_threats({"malware_x": 8})

        # ASSERT: Metadata populated correctly
        pattern = patterns[0]
        assert "threat_id" in pattern.metadata
        assert pattern.metadata["threat_id"] == "malware_x"
        assert "threshold_exceeded_by" in pattern.metadata
        assert pattern.metadata["threshold_exceeded_by"] == 3  # 8 - 5

    @pytest.mark.asyncio
    async def test_detect_persistent_threats_history_tracking(self):
        """Test pattern is added to history."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5)

        # PRE-ASSERT: History empty
        assert len(detector._pattern_history) == 0

        # ACT: Detect pattern
        await detector.detect_persistent_threats({"malware_x": 7})

        # ASSERT: Pattern added to history
        assert len(detector._pattern_history) == 1
        assert detector._pattern_history[0].threat_ids == ["malware_x"]


# ==================== COORDINATED ATTACK DETECTION TESTS ====================


class TestCoordinatedAttackDetection:
    """Test coordinated attack detection logic."""

    @pytest.mark.asyncio
    async def test_detect_coordinated_attacks_single_attack(self):
        """Test detection of single coordinated attack."""
        # ARRANGE: Create detector
        detector = PatternDetector(coordinated_threshold=10)

        # Create 15 threat cytokines in last minute
        now = datetime.now()
        cytokines = []
        for i in range(15):
            cytokines.append(
                {
                    "timestamp": (now - timedelta(seconds=i)).isoformat(),
                    "payload": {"evento": "ameaca_detectada"},
                    "area_alvo": "network-zone-1",
                }
            )

        # ACT: Detect patterns
        patterns = await detector.detect_coordinated_attacks(cytokines)

        # ASSERT: One coordinated attack detected
        assert len(patterns) == 1
        assert patterns[0].pattern_type == PatternType.COORDINATED
        assert patterns[0].detection_count == 15
        assert patterns[0].confidence > 0.0

    @pytest.mark.asyncio
    async def test_detect_coordinated_attacks_none_detected(self):
        """Test when threat count is below threshold."""
        # ARRANGE: Create detector
        detector = PatternDetector(coordinated_threshold=10)

        # Create only 5 threat cytokines (below threshold)
        now = datetime.now()
        cytokines = []
        for i in range(5):
            cytokines.append(
                {
                    "timestamp": (now - timedelta(seconds=i)).isoformat(),
                    "payload": {"evento": "ameaca_detectada"},
                }
            )

        # ACT: Detect patterns
        patterns = await detector.detect_coordinated_attacks(cytokines)

        # ASSERT: No patterns detected
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_detect_coordinated_attacks_exact_threshold(self):
        """Test detection at exact threshold boundary."""
        # ARRANGE: Create detector
        detector = PatternDetector(coordinated_threshold=10)

        # Create exactly 10 threats
        now = datetime.now()
        cytokines = []
        for i in range(10):
            cytokines.append(
                {
                    "timestamp": (now - timedelta(seconds=i)).isoformat(),
                    "payload": {"evento": "ameaca_detectada"},
                }
            )

        # ACT: Detect patterns
        patterns = await detector.detect_coordinated_attacks(cytokines)

        # ASSERT: Pattern detected (threshold is inclusive: >=)
        assert len(patterns) == 1
        assert patterns[0].detection_count == 10

    @pytest.mark.asyncio
    async def test_detect_coordinated_attacks_old_cytokines_excluded(self):
        """Test that old cytokines are excluded from detection."""
        # ARRANGE: Create detector with 60s window
        detector = PatternDetector(coordinated_threshold=10, time_window_sec=60.0)

        now = datetime.now()
        cytokines = []

        # Add 5 recent threats (within 60s)
        for i in range(5):
            cytokines.append(
                {
                    "timestamp": (now - timedelta(seconds=i)).isoformat(),
                    "payload": {"evento": "ameaca_detectada"},
                }
            )

        # Add 10 old threats (older than 60s) - should be excluded
        for i in range(10):
            cytokines.append(
                {
                    "timestamp": (now - timedelta(seconds=120 + i)).isoformat(),
                    "payload": {"evento": "ameaca_detectada"},
                }
            )

        # ACT: Detect patterns
        patterns = await detector.detect_coordinated_attacks(cytokines)

        # ASSERT: No pattern detected (only 5 recent threats < threshold 10)
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_detect_coordinated_attacks_is_threat_flag(self):
        """Test detection using is_threat flag."""
        # ARRANGE: Create detector
        detector = PatternDetector(coordinated_threshold=10)

        # Create threats using is_threat flag instead of evento
        now = datetime.now()
        cytokines = []
        for i in range(12):
            cytokines.append(
                {
                    "timestamp": (now - timedelta(seconds=i)).isoformat(),
                    "payload": {"is_threat": True},
                }
            )

        # ACT: Detect patterns
        patterns = await detector.detect_coordinated_attacks(cytokines)

        # ASSERT: Pattern detected via is_threat flag
        assert len(patterns) == 1
        assert patterns[0].detection_count == 12

    @pytest.mark.asyncio
    async def test_detect_coordinated_attacks_confidence_calculation(self):
        """Test confidence score calculation."""
        # ARRANGE: Create detector
        detector = PatternDetector(coordinated_threshold=10)

        now = datetime.now()

        # Test with different threat counts
        cytokines_low = [
            {"timestamp": (now - timedelta(seconds=i)).isoformat(), "payload": {"evento": "ameaca_detectada"}}
            for i in range(10)
        ]
        cytokines_high = [
            {"timestamp": (now - timedelta(seconds=i)).isoformat(), "payload": {"evento": "ameaca_detectada"}}
            for i in range(30)
        ]

        # ACT: Detect patterns
        patterns_low = await detector.detect_coordinated_attacks(cytokines_low)
        patterns_high = await detector.detect_coordinated_attacks(cytokines_high)

        # ASSERT: Higher count = higher confidence
        assert patterns_low[0].confidence < patterns_high[0].confidence
        # Confidence capped at 1.0
        assert patterns_high[0].confidence == 1.0

    @pytest.mark.asyncio
    async def test_detect_coordinated_attacks_empty_input(self):
        """Test with empty cytokine list."""
        # ARRANGE: Create detector
        detector = PatternDetector(coordinated_threshold=10)

        # ACT: Detect with empty list
        patterns = await detector.detect_coordinated_attacks([])

        # ASSERT: No patterns detected
        assert len(patterns) == 0


# ==================== PATTERN HISTORY TESTS ====================


class TestPatternHistory:
    """Test pattern history tracking and retrieval."""

    @pytest.mark.asyncio
    async def test_get_pattern_history_all(self):
        """Test retrieving all pattern history."""
        # ARRANGE: Create detector and generate patterns
        detector = PatternDetector(persistent_threshold=5)

        # Detect 3 persistent threats
        await detector.detect_persistent_threats({"threat_a": 6})
        await detector.detect_persistent_threats({"threat_b": 7})
        await detector.detect_persistent_threats({"threat_c": 8})

        # ACT: Get all history
        history = detector.get_pattern_history()

        # ASSERT: All 3 patterns in history
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_pattern_history_filtered_by_type(self):
        """Test filtering history by pattern type."""
        # ARRANGE: Create detector
        detector = PatternDetector(persistent_threshold=5, coordinated_threshold=10)

        # Detect persistent threat
        await detector.detect_persistent_threats({"threat_a": 6})

        # Detect coordinated attack
        now = datetime.now()
        cytokines = [
            {"timestamp": (now - timedelta(seconds=i)).isoformat(), "payload": {"evento": "ameaca_detectada"}}
            for i in range(12)
        ]
        await detector.detect_coordinated_attacks(cytokines)

        # ACT: Get filtered history
        persistent_history = detector.get_pattern_history(pattern_type=PatternType.PERSISTENT)
        coordinated_history = detector.get_pattern_history(pattern_type=PatternType.COORDINATED)

        # ASSERT: Filters work correctly
        assert len(persistent_history) == 1
        assert len(coordinated_history) == 1
        assert persistent_history[0].pattern_type == PatternType.PERSISTENT
        assert coordinated_history[0].pattern_type == PatternType.COORDINATED

    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clearing pattern history."""
        # ARRANGE: Create detector with patterns
        detector = PatternDetector(persistent_threshold=5)
        await detector.detect_persistent_threats({"threat_a": 6})

        # PRE-ASSERT: History not empty
        assert len(detector._pattern_history) > 0

        # ACT: Clear history
        detector.clear_history()

        # ASSERT: History cleared
        assert len(detector._pattern_history) == 0


# ==================== STATISTICS TESTS ====================


class TestStatistics:
    """Test pattern detector statistics collection."""

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test get_stats method returns correct structure."""
        # ARRANGE: Create detector
        detector = PatternDetector(
            persistent_threshold=5,
            coordinated_threshold=10,
            time_window_sec=120.0,
        )

        # ACT: Get stats
        stats = detector.get_stats()

        # ASSERT: Stats structure correct
        assert "persistent_threshold" in stats
        assert stats["persistent_threshold"] == 5
        assert "coordinated_threshold" in stats
        assert stats["coordinated_threshold"] == 10
        assert "time_window_sec" in stats
        assert stats["time_window_sec"] == 120.0
        assert "total_patterns_detected" in stats
        assert "persistent_patterns" in stats
        assert "coordinated_patterns" in stats

    @pytest.mark.asyncio
    async def test_get_stats_with_patterns(self):
        """Test stats with detected patterns."""
        # ARRANGE: Create detector and detect patterns
        detector = PatternDetector(persistent_threshold=5, coordinated_threshold=10)

        # Detect 2 persistent threats
        await detector.detect_persistent_threats({"threat_a": 6, "threat_b": 7})

        # Detect 1 coordinated attack
        now = datetime.now()
        cytokines = [
            {"timestamp": (now - timedelta(seconds=i)).isoformat(), "payload": {"evento": "ameaca_detectada"}}
            for i in range(12)
        ]
        await detector.detect_coordinated_attacks(cytokines)

        # ACT: Get stats
        stats = detector.get_stats()

        # ASSERT: Counts correct
        assert stats["total_patterns_detected"] == 3  # 2 persistent + 1 coordinated
        assert stats["persistent_patterns"] == 2
        assert stats["coordinated_patterns"] == 1
