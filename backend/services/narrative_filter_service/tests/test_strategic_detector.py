"""Tests for strategic pattern detector."""

from datetime import datetime, timedelta

import pytest

from models import IntentClassification, PatternType, SemanticRepresentation
from strategic_detector import StrategicPatternDetector


@pytest.fixture
def detector() -> StrategicPatternDetector:
    """Create detector instance."""
    return StrategicPatternDetector()


@pytest.fixture
def sample_interactions() -> list[SemanticRepresentation]:
    """Create sample interactions."""
    now = datetime.utcnow()
    return [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_a" if i % 2 == 0 else "agent_b",
            timestamp=now - timedelta(hours=i),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE,
            intent_confidence=0.9,
            raw_content=f"Message {i} mentioning agent_b" if i % 2 == 0 else f"Message {i} mentioning agent_a",
        )
        for i in range(10)
    ]


def test_detector_initialization(detector: StrategicPatternDetector) -> None:
    """Test detector initializes correctly."""
    assert detector.alliance_graph is not None
    assert len(detector.interaction_history) == 0


def test_detect_alliance_success(detector: StrategicPatternDetector, sample_interactions: list[SemanticRepresentation]) -> None:
    """Test alliance detection with sufficient cooperative interactions."""
    alliance = detector.detect_alliance("agent_a", "agent_b", sample_interactions)

    assert alliance is not None
    assert alliance.agent_a == "agent_a"
    assert alliance.agent_b == "agent_b"
    assert alliance.strength >= 0.75
    assert alliance.status == "ACTIVE"


def test_detect_alliance_insufficient_data(detector: StrategicPatternDetector) -> None:
    """Test alliance detection with insufficient interactions."""
    interactions = [
        SemanticRepresentation(
            message_id="msg_1",
            source_agent_id="agent_a",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE,
            intent_confidence=0.9,
            raw_content="test",
        )
    ]

    alliance = detector.detect_alliance("agent_a", "agent_b", interactions)
    assert alliance is None


def test_calculate_mutual_information(detector: StrategicPatternDetector) -> None:
    """Test mutual information calculation."""
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_a" if i < 5 else "agent_b",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE if i % 2 == 0 else IntentClassification.NEUTRAL,
            intent_confidence=0.8,
            raw_content="test",
        )
        for i in range(10)
    ]

    mi = detector.calculate_mutual_information("agent_a", "agent_b", interactions)
    assert 0.0 <= mi <= 1.0


def test_calculate_mutual_information_no_data(detector: StrategicPatternDetector) -> None:
    """Test mutual information with no data."""
    mi = detector.calculate_mutual_information("agent_a", "agent_b", [])
    assert mi == 0.0


def test_detect_deception_high_variation(detector: StrategicPatternDetector) -> None:
    """Test deception detection with high intent variation."""
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_suspicious",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification(["COOPERATIVE", "COMPETITIVE", "NEUTRAL", "AMBIGUOUS"][i % 4]),
            intent_confidence=0.5,  # Low confidence
            raw_content="test",
        )
        for i in range(8)
    ]

    score = detector.detect_deception("agent_suspicious", interactions)
    assert score > 0.5  # Should detect high deception


def test_detect_deception_consistent_agent(detector: StrategicPatternDetector) -> None:
    """Test deception detection with consistent agent."""
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_honest",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE,
            intent_confidence=0.95,
            raw_content="test",
        )
        for i in range(5)
    ]

    score = detector.detect_deception("agent_honest", interactions)
    assert score < 0.3  # Should be low deception


def test_detect_inconsistency(detector: StrategicPatternDetector) -> None:
    """Test inconsistency detection."""
    now = datetime.utcnow()
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_inconsistent",
            timestamp=now - timedelta(hours=i),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE if i < 3 else IntentClassification.COMPETITIVE,
            intent_confidence=0.8,
            raw_content="test",
        )
        for i in range(6)
    ]

    score = detector.detect_inconsistency("agent_inconsistent", interactions)
    assert score > 0.0  # Should detect some inconsistency


@pytest.mark.asyncio
async def test_detect_patterns(detector: StrategicPatternDetector, sample_interactions: list[SemanticRepresentation]) -> None:
    """Test comprehensive pattern detection."""
    patterns = await detector.detect_patterns(sample_interactions, time_window_hours=24)

    assert isinstance(patterns, list)
    # Should detect at least the alliance pattern
    alliance_patterns = [p for p in patterns if p.pattern_type == PatternType.ALLIANCE]
    assert len(alliance_patterns) >= 1


def test_get_alliance_clusters_empty(detector: StrategicPatternDetector) -> None:
    """Test alliance clusters with empty graph."""
    clusters = detector.get_alliance_clusters()
    assert clusters == []


def test_get_alliance_clusters_with_data(detector: StrategicPatternDetector, sample_interactions: list[SemanticRepresentation]) -> None:
    """Test alliance clusters after detecting alliances."""
    # Detect alliance to populate graph
    detector.detect_alliance("agent_a", "agent_b", sample_interactions)

    clusters = detector.get_alliance_clusters()
    assert len(clusters) > 0
    assert any("agent_a" in cluster and "agent_b" in cluster for cluster in clusters)


def test_detect_alliance_updates_graph(detector: StrategicPatternDetector, sample_interactions: list[SemanticRepresentation]) -> None:
    """Test that detect_alliance updates the graph correctly."""
    initial_edges = detector.alliance_graph.number_of_edges()

    alliance = detector.detect_alliance("agent_a", "agent_b", sample_interactions)

    assert alliance is not None
    assert detector.alliance_graph.number_of_edges() > initial_edges
    assert detector.alliance_graph.has_edge("agent_a", "agent_b")


def test_detect_alliance_below_threshold(detector: StrategicPatternDetector) -> None:
    """Test alliance detection when strength is below threshold."""
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_a" if i % 2 == 0 else "agent_b",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COMPETITIVE if i < 2 else IntentClassification.NEUTRAL,
            intent_confidence=0.8,
            raw_content="agent_b" if i % 2 == 0 else "agent_a",
        )
        for i in range(4)
    ]

    alliance = detector.detect_alliance("agent_a", "agent_b", interactions)
    assert alliance is None  # Strength below threshold


def test_detect_deception_insufficient_data(detector: StrategicPatternDetector) -> None:
    """Test deception with insufficient data."""
    interactions = [
        SemanticRepresentation(
            message_id="msg_1",
            source_agent_id="agent_x",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.NEUTRAL,
            intent_confidence=0.8,
            raw_content="test",
        )
    ]

    score = detector.detect_deception("agent_x", interactions)
    assert score == 0.0


def test_detect_inconsistency_insufficient_data(detector: StrategicPatternDetector) -> None:
    """Test inconsistency with insufficient data."""
    interactions = [
        SemanticRepresentation(
            message_id="msg_1",
            source_agent_id="agent_x",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.NEUTRAL,
            intent_confidence=0.8,
            raw_content="test",
        )
    ]

    score = detector.detect_inconsistency("agent_x", interactions)
    assert score == 0.0


def test_detect_inconsistency_only_cooperative(detector: StrategicPatternDetector) -> None:
    """Test inconsistency when all messages are cooperative."""
    now = datetime.utcnow()
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_consistent",
            timestamp=now - timedelta(hours=i),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE,
            intent_confidence=0.9,
            raw_content="test",
        )
        for i in range(5)
    ]

    score = detector.detect_inconsistency("agent_consistent", interactions)
    assert score == 0.0  # No competitive messages, so no inconsistency


def test_detect_alliance_graph_update_existing_edge(detector: StrategicPatternDetector, sample_interactions: list[SemanticRepresentation]) -> None:
    """Test updating existing edge in alliance graph - covers line 59."""
    # First detection creates edge
    detector.detect_alliance("agent_a", "agent_b", sample_interactions)

    # Second detection updates edge weight (line 59)
    alliance2 = detector.detect_alliance("agent_a", "agent_b", sample_interactions)

    assert alliance2 is not None
    assert detector.alliance_graph.has_edge("agent_a", "agent_b")
    weight = detector.alliance_graph["agent_a"]["agent_b"]["weight"]
    assert weight == alliance2.strength


@pytest.mark.asyncio
async def test_detect_patterns_with_deception(detector: StrategicPatternDetector) -> None:
    """Test pattern detection includes deception - covers lines 231-233."""
    now = datetime.utcnow()
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_deceptive",
            timestamp=now - timedelta(hours=i),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification(["COOPERATIVE", "COMPETITIVE", "NEUTRAL", "AMBIGUOUS"][i % 4]),
            intent_confidence=0.3,  # Low confidence
            raw_content="test",
        )
        for i in range(10)
    ]

    patterns = await detector.detect_patterns(interactions, time_window_hours=24)

    deception_patterns = [p for p in patterns if p.pattern_type == PatternType.DECEPTION]
    assert len(deception_patterns) >= 1  # Should detect deception


@pytest.mark.asyncio
async def test_detect_patterns_with_inconsistency(detector: StrategicPatternDetector) -> None:
    """Test pattern detection includes inconsistency - covers lines 247-249."""
    now = datetime.utcnow()
    interactions = [
        SemanticRepresentation(
            message_id=f"msg_{i}",
            source_agent_id="agent_inconsistent",
            timestamp=now - timedelta(hours=i),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE if i < 5 else IntentClassification.COMPETITIVE,
            intent_confidence=0.85,
            raw_content="test",
        )
        for i in range(10)
    ]

    patterns = await detector.detect_patterns(interactions, time_window_hours=24)

    inconsistency_patterns = [p for p in patterns if p.pattern_type == PatternType.INCONSISTENCY]
    assert len(inconsistency_patterns) >= 1  # Should detect inconsistency
