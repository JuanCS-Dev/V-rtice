"""
FASE A - Complete tests for consciousness/autobiographical_narrative.py
Target: 46.9% → 95%+ (17 missing lines)
Zero mocks - Padrão Pagani Absoluto
EM NOME DE JESUS!
"""

from datetime import datetime, timedelta
import pytest
from consciousness.autobiographical_narrative import AutobiographicalNarrative, NarrativeResult
from consciousness.episodic_memory import Episode


@pytest.fixture
def narrative_builder():
    """Create narrative builder."""
    return AutobiographicalNarrative()


@pytest.fixture
def sample_episodes():
    """Create sample episodes."""
    base_time = datetime(2025, 10, 22, 14, 0, 0)
    return [
        Episode(
            episode_id="ep1",
            timestamp=base_time,
            focus_target="task:coding",
            salience=0.9,
            confidence=0.85,
            narrative="Escrevendo código Python",
        ),
        Episode(
            episode_id="ep2",
            timestamp=base_time + timedelta(minutes=5),
            focus_target="task:coding",
            salience=0.8,
            confidence=0.9,
            narrative="Executando testes",
        ),
        Episode(
            episode_id="ep3",
            timestamp=base_time + timedelta(minutes=10),
            focus_target="task:debugging",
            salience=0.7,
            confidence=0.75,
            narrative="Corrigindo bugs",
        ),
    ]


class TestAutoGraphicalNarrativeInit:
    """Test initialization."""

    def test_init_creates_binder(self, narrative_builder):
        """Test that init creates temporal binder."""
        assert hasattr(narrative_builder, '_binder')
        assert narrative_builder._binder is not None


class TestBuildMethod:
    """Test build method."""

    def test_build_with_episodes(self, narrative_builder, sample_episodes):
        """Test building narrative from episodes."""
        result = narrative_builder.build(sample_episodes)

        assert isinstance(result, NarrativeResult)
        assert isinstance(result.narrative, str)
        assert len(result.narrative) > 0
        assert result.episode_count == 3

    def test_build_with_empty_episodes(self, narrative_builder):
        """Test building narrative with no episodes."""
        result = narrative_builder.build([])

        assert isinstance(result, NarrativeResult)
        assert result.narrative == "Não há episódios registrados para narrar."
        assert result.episode_count == 0
        assert result.coherence_score == 0.0

    def test_build_with_single_episode(self, narrative_builder, sample_episodes):
        """Test building narrative with single episode."""
        result = narrative_builder.build([sample_episodes[0]])

        assert isinstance(result, NarrativeResult)
        assert len(result.narrative) > 0
        assert result.episode_count == 1
        assert result.coherence_score >= 0.0

    def test_build_orders_episodes(self, narrative_builder):
        """Test that build orders episodes by timestamp."""
        base_time = datetime(2025, 10, 22, 14, 0, 0)
        unordered = [
            Episode(
                episode_id="ep3",
                timestamp=base_time + timedelta(minutes=10),
                focus_target="task:c",
                salience=0.7,
                confidence=0.7,
                narrative="C",
            ),
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:a",
                salience=0.9,
                confidence=0.9,
                narrative="A",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=5),
                focus_target="task:b",
                salience=0.8,
                confidence=0.8,
                narrative="B",
            ),
        ]

        result = narrative_builder.build(unordered)

        # Should contain episodes in order A, B, C
        assert "A" in result.narrative
        assert result.narrative.index("A") < result.narrative.index("B")
        assert result.narrative.index("B") < result.narrative.index("C")


class TestComputeCoherence:
    """Test _compute_coherence private method."""

    def test_compute_coherence_empty(self, narrative_builder):
        """Test coherence with empty episodes."""
        coherence = narrative_builder._compute_coherence([])
        assert coherence == 0.0

    def test_compute_coherence_single_episode(self, narrative_builder, sample_episodes):
        """Test coherence with single episode."""
        coherence = narrative_builder._compute_coherence([sample_episodes[0]])
        assert 0.0 <= coherence <= 1.0

    def test_compute_coherence_multiple_episodes(self, narrative_builder, sample_episodes):
        """Test coherence with multiple episodes."""
        coherence = narrative_builder._compute_coherence(sample_episodes)
        assert 0.0 <= coherence <= 1.0

    def test_compute_coherence_high_confidence(self, narrative_builder):
        """Test coherence is higher with high confidence episodes."""
        base_time = datetime(2025, 10, 22, 14, 0, 0)
        high_confidence = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:a",
                salience=0.9,
                confidence=0.95,
                narrative="High confidence",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=2),
                focus_target="task:a",
                salience=0.9,
                confidence=0.95,
                narrative="Also high",
            ),
        ]

        low_confidence = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:a",
                salience=0.9,
                confidence=0.2,
                narrative="Low confidence",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=2),
                focus_target="task:a",
                salience=0.9,
                confidence=0.2,
                narrative="Also low",
            ),
        ]

        high_coherence = narrative_builder._compute_coherence(high_confidence)
        low_coherence = narrative_builder._compute_coherence(low_confidence)

        assert high_coherence > low_coherence

    def test_compute_coherence_stable_focus(self, narrative_builder):
        """Test coherence is higher with stable focus."""
        base_time = datetime(2025, 10, 22, 14, 0, 0)
        stable = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:coding",
                salience=0.9,
                confidence=0.8,
                narrative="Coding",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=2),
                focus_target="task:testing",
                salience=0.9,
                confidence=0.8,
                narrative="Testing",
            ),
        ]

        unstable = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:coding",
                salience=0.9,
                confidence=0.8,
                narrative="Coding",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=2),
                focus_target="user:interrupt",
                salience=0.9,
                confidence=0.8,
                narrative="Interrupted",
            ),
        ]

        stable_coherence = narrative_builder._compute_coherence(stable)
        unstable_coherence = narrative_builder._compute_coherence(unstable)

        # Stable focus should have higher coherence
        assert stable_coherence >= unstable_coherence


class TestBuildText:
    """Test _build_text private method."""

    def test_build_text_empty(self, narrative_builder):
        """Test building text with no episodes."""
        text = narrative_builder._build_text([])
        assert text == "Não há episódios registrados para narrar."

    def test_build_text_single_episode(self, narrative_builder, sample_episodes):
        """Test building text with single episode."""
        text = narrative_builder._build_text([sample_episodes[0]])

        assert len(text) > 0
        assert "concentrei-me" in text or "focando" in text.lower()
        assert sample_episodes[0].focus_target in text
        assert sample_episodes[0].narrative in text

    def test_build_text_multiple_episodes(self, narrative_builder, sample_episodes):
        """Test building text with multiple episodes."""
        text = narrative_builder._build_text(sample_episodes)

        # Should contain all narratives
        for ep in sample_episodes:
            assert ep.narrative in text

    def test_build_text_format(self, narrative_builder):
        """Test that built text follows expected format."""
        base_time = datetime(2025, 10, 22, 14, 0, 0)
        episode = Episode(
            episode_id="ep1",
            timestamp=base_time,
            focus_target="task:test",
            salience=0.8,
            confidence=0.9,
            narrative="Teste",
        )

        text = narrative_builder._build_text([episode])

        # Should include timestamp, focus target, salience, and narrative
        assert "concentrei-me" in text or "2025-10-22" in text
        assert "task:test" in text or "test" in text
        assert "Teste" in text


class TestNarrativeResult:
    """Test NarrativeResult dataclass."""

    def test_narrative_result_creation(self):
        """Test creating narrative result."""
        result = NarrativeResult(
            narrative="Test narrative",
            coherence_score=0.85,
            episode_count=5,
        )

        assert result.narrative == "Test narrative"
        assert result.coherence_score == 0.85
        assert result.episode_count == 5

    def test_narrative_result_has_required_fields(self):
        """Test that NarrativeResult has required fields."""
        result = NarrativeResult(
            narrative="Test",
            coherence_score=0.5,
            episode_count=1,
        )

        assert hasattr(result, 'narrative')
        assert hasattr(result, 'coherence_score')
        assert hasattr(result, 'episode_count')


class TestIntegration:
    """Integration tests."""

    def test_full_narrative_workflow(self, narrative_builder, sample_episodes):
        """Test complete workflow from episodes to narrative."""
        result = narrative_builder.build(sample_episodes)

        # Verify result structure
        assert isinstance(result, NarrativeResult)
        assert result.episode_count == len(sample_episodes)
        assert 0.0 <= result.coherence_score <= 1.0
        assert len(result.narrative) > 0

        # Verify all episodes mentioned
        for ep in sample_episodes:
            assert ep.narrative in result.narrative

    def test_narrative_with_varying_confidence(self, narrative_builder):
        """Test narrative with varying confidence levels."""
        base_time = datetime(2025, 10, 22, 14, 0, 0)
        episodes = [
            Episode(
                episode_id=f"ep{i}",
                timestamp=base_time + timedelta(minutes=i * 5),
                focus_target=f"task:{i}",
                salience=0.8,
                confidence=0.3 + (i * 0.2),  # Varying confidence
                narrative=f"Episode {i}",
            )
            for i in range(4)
        ]

        result = narrative_builder.build(episodes)
        assert result.episode_count == 4
        assert 0.0 <= result.coherence_score <= 1.0
