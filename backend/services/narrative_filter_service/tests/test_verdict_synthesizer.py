"""Tests for verdict synthesizer."""


import pytest

from models import PatternType, Severity, StrategicPattern, VerdictCategory, VerdictStatus
from verdict_synthesizer import VerdictSynthesizer


@pytest.fixture
def synthesizer() -> VerdictSynthesizer:
    """Create synthesizer instance."""
    return VerdictSynthesizer()


@pytest.fixture
def critical_deception_pattern() -> StrategicPattern:
    """Create critical deception pattern."""
    return StrategicPattern(
        pattern_type=PatternType.DECEPTION,
        agents_involved=["agent_malicious"],
        evidence_messages=["msg_1", "msg_2", "msg_3"],
        deception_score=0.95,
    )


@pytest.fixture
def high_alliance_pattern() -> StrategicPattern:
    """Create high-strength alliance pattern."""
    return StrategicPattern(
        pattern_type=PatternType.ALLIANCE,
        agents_involved=["agent_a", "agent_b"],
        evidence_messages=["msg_1", "msg_2"],
        mutual_information=0.85,
    )


@pytest.fixture
def medium_inconsistency_pattern() -> StrategicPattern:
    """Create medium inconsistency pattern."""
    return StrategicPattern(
        pattern_type=PatternType.INCONSISTENCY,
        agents_involved=["agent_inconsistent"],
        evidence_messages=["msg_1", "msg_2"],
        inconsistency_score=0.6,
    )


def test_synthesizer_initialization(synthesizer: VerdictSynthesizer) -> None:
    """Test synthesizer initializes correctly."""
    assert synthesizer.verdict_count == 0


def test_determine_severity_critical(synthesizer: VerdictSynthesizer, critical_deception_pattern: StrategicPattern) -> None:
    """Test critical severity determination."""
    severity = synthesizer.determine_severity(critical_deception_pattern)
    assert severity == Severity.CRITICAL


def test_determine_severity_high_deception(synthesizer: VerdictSynthesizer) -> None:
    """Test high severity for deception."""
    pattern = StrategicPattern(
        pattern_type=PatternType.DECEPTION,
        agents_involved=["agent_x"],
        evidence_messages=["msg_1"],
        deception_score=0.75,
    )
    severity = synthesizer.determine_severity(pattern)
    assert severity == Severity.HIGH


def test_determine_severity_high_alliance(synthesizer: VerdictSynthesizer, high_alliance_pattern: StrategicPattern) -> None:
    """Test high severity for strong alliance."""
    severity = synthesizer.determine_severity(high_alliance_pattern)
    assert severity == Severity.HIGH


def test_determine_severity_medium(synthesizer: VerdictSynthesizer, medium_inconsistency_pattern: StrategicPattern) -> None:
    """Test medium severity determination."""
    severity = synthesizer.determine_severity(medium_inconsistency_pattern)
    assert severity == Severity.MEDIUM


def test_determine_severity_low(synthesizer: VerdictSynthesizer) -> None:
    """Test low severity determination."""
    pattern = StrategicPattern(
        pattern_type=PatternType.ALLIANCE,
        agents_involved=["agent_a", "agent_b"],
        evidence_messages=["msg_1"],
        mutual_information=0.4,
    )
    severity = synthesizer.determine_severity(pattern)
    assert severity == Severity.LOW


def test_generate_title(synthesizer: VerdictSynthesizer, critical_deception_pattern: StrategicPattern) -> None:
    """Test title generation."""
    title = synthesizer.generate_title(critical_deception_pattern, Severity.CRITICAL)
    assert "CRITICAL" in title
    assert "Deception" in title
    assert "agent_malicious" in title


def test_generate_title_multiple_agents(synthesizer: VerdictSynthesizer) -> None:
    """Test title generation with many agents."""
    pattern = StrategicPattern(
        pattern_type=PatternType.COLLUSION,
        agents_involved=["agent_1", "agent_2", "agent_3", "agent_4"],
        evidence_messages=["msg_1"],
    )
    title = synthesizer.generate_title(pattern, Severity.HIGH)
    assert "+1 more" in title or "agent_1, agent_2, agent_3" in title


def test_recommend_action_critical_deception(synthesizer: VerdictSynthesizer, critical_deception_pattern: StrategicPattern) -> None:
    """Test action recommendation for critical deception."""
    action = synthesizer.recommend_action(critical_deception_pattern, Severity.CRITICAL)
    assert action == "ISOLATE"


def test_recommend_action_critical_inconsistency(synthesizer: VerdictSynthesizer) -> None:
    """Test action recommendation for critical inconsistency."""
    pattern = StrategicPattern(
        pattern_type=PatternType.INCONSISTENCY,
        agents_involved=["agent_x"],
        evidence_messages=["msg_1"],
        inconsistency_score=0.95,
    )
    action = synthesizer.recommend_action(pattern, Severity.CRITICAL)
    assert action == "SNAPSHOT_STATE"


def test_recommend_action_high_collusion(synthesizer: VerdictSynthesizer) -> None:
    """Test action recommendation for high collusion."""
    pattern = StrategicPattern(
        pattern_type=PatternType.COLLUSION,
        agents_involved=["agent_a", "agent_b"],
        evidence_messages=["msg_1"],
    )
    action = synthesizer.recommend_action(pattern, Severity.HIGH)
    assert action == "INJECT_CONSTRAINT"


def test_recommend_action_medium(synthesizer: VerdictSynthesizer, medium_inconsistency_pattern: StrategicPattern) -> None:
    """Test action recommendation for medium severity."""
    action = synthesizer.recommend_action(medium_inconsistency_pattern, Severity.MEDIUM)
    assert action == "MONITOR"


def test_map_pattern_to_category(synthesizer: VerdictSynthesizer) -> None:
    """Test pattern type to category mapping."""
    pattern_alliance = StrategicPattern(
        pattern_type=PatternType.ALLIANCE,
        agents_involved=["a", "b"],
        evidence_messages=["msg_1"],
    )
    assert synthesizer.map_pattern_to_category(pattern_alliance) == VerdictCategory.ALLIANCE

    pattern_deception = StrategicPattern(
        pattern_type=PatternType.DECEPTION,
        agents_involved=["a"],
        evidence_messages=["msg_1"],
    )
    assert synthesizer.map_pattern_to_category(pattern_deception) == VerdictCategory.DECEPTION


@pytest.mark.asyncio
async def test_synthesize_verdict(synthesizer: VerdictSynthesizer, critical_deception_pattern: StrategicPattern) -> None:
    """Test verdict synthesis."""
    verdict = await synthesizer.synthesize_verdict(critical_deception_pattern)

    assert verdict.category == VerdictCategory.DECEPTION
    assert verdict.severity == Severity.CRITICAL
    assert verdict.recommended_action == "ISOLATE"
    assert verdict.status == VerdictStatus.ACTIVE
    assert verdict.confidence >= 0.7
    assert len(verdict.evidence_chain) == 3
    assert verdict.color == "#DC2626"  # Critical red


@pytest.mark.asyncio
async def test_synthesize_verdict_alliance(synthesizer: VerdictSynthesizer, high_alliance_pattern: StrategicPattern) -> None:
    """Test verdict synthesis for alliance."""
    verdict = await synthesizer.synthesize_verdict(high_alliance_pattern)

    assert verdict.category == VerdictCategory.ALLIANCE
    assert verdict.severity == Severity.HIGH
    assert verdict.target == "agent_a-agent_b"
    assert len(verdict.agents_involved) == 2


@pytest.mark.asyncio
async def test_batch_synthesize(synthesizer: VerdictSynthesizer) -> None:
    """Test batch verdict synthesis."""
    patterns = [
        StrategicPattern(
            pattern_type=PatternType.DECEPTION,
            agents_involved=["agent_1"],
            evidence_messages=["msg_1"],
            deception_score=0.9,
        ),
        StrategicPattern(
            pattern_type=PatternType.ALLIANCE,
            agents_involved=["agent_2", "agent_3"],
            evidence_messages=["msg_2"],
            mutual_information=0.75,
        ),
    ]

    verdicts = await synthesizer.batch_synthesize(patterns)

    assert len(verdicts) == 2
    assert verdicts[0].category == VerdictCategory.DECEPTION
    assert verdicts[1].category == VerdictCategory.ALLIANCE


def test_get_verdict_stats(synthesizer: VerdictSynthesizer) -> None:
    """Test verdict statistics."""
    stats = synthesizer.get_verdict_stats()
    assert stats["total_verdicts"] == 0

    synthesizer.verdict_count = 5
    stats = synthesizer.get_verdict_stats()
    assert stats["total_verdicts"] == 5


def test_recommend_action_critical_other(synthesizer: VerdictSynthesizer) -> None:
    """Test action recommendation for critical severity with other pattern types - covers line 97."""
    pattern = StrategicPattern(
        pattern_type=PatternType.ALLIANCE,  # Not DECEPTION or INCONSISTENCY
        agents_involved=["agent_a", "agent_b"],
        evidence_messages=["msg_1"],
        mutual_information=0.95,
    )
    action = synthesizer.recommend_action(pattern, Severity.CRITICAL)
    assert action == "REVOKE_ACCESS"
