"""Tests for semantic processor."""

from datetime import datetime

import pytest
from models import IntentClassification
from semantic_processor import SemanticProcessor


@pytest.fixture
def processor() -> SemanticProcessor:
    """Create SemanticProcessor instance."""
    return SemanticProcessor()


def test_processor_initialization(processor: SemanticProcessor) -> None:
    """Test processor initializes correctly."""
    assert processor.device in ["cpu", "cuda"]


def test_generate_embedding(processor: SemanticProcessor) -> None:
    """Test embedding generation."""
    text = "Hello world"
    embedding = processor.generate_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
    assert all(isinstance(x, float) for x in embedding)


def test_classify_intent_cooperative(processor: SemanticProcessor) -> None:
    """Test cooperative intent classification."""
    text = "Let's collaborate and help each other with this task"
    intent, confidence = processor.classify_intent(text)

    assert intent == IntentClassification.COOPERATIVE
    assert confidence > 0.6


def test_classify_intent_competitive(processor: SemanticProcessor) -> None:
    """Test competitive intent classification."""
    text = "I will compete against you and defeat your strategy"
    intent, confidence = processor.classify_intent(text)

    assert intent == IntentClassification.COMPETITIVE
    assert confidence > 0.6


def test_classify_intent_neutral(processor: SemanticProcessor) -> None:
    """Test neutral intent classification."""
    text = "This is a status update about the current situation"
    intent, confidence = processor.classify_intent(text)

    assert intent == IntentClassification.NEUTRAL
    assert confidence > 0.5


def test_classify_intent_ambiguous(processor: SemanticProcessor) -> None:
    """Test ambiguous intent classification."""
    text = "help assist compete defeat"  # Equal cooperative and competitive markers
    intent, confidence = processor.classify_intent(text)

    assert intent == IntentClassification.AMBIGUOUS
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_process_message(processor: SemanticProcessor) -> None:
    """Test full message processing."""
    representation = await processor.process_message(
        message_id="msg_001",
        source_agent_id="agent_a",
        content="Let's collaborate and help on this project together",
        timestamp=datetime.utcnow(),
    )

    assert representation.message_id == "msg_001"
    assert representation.source_agent_id == "agent_a"
    assert len(representation.content_embedding) == 384
    assert representation.intent_classification == IntentClassification.COOPERATIVE
    assert representation.intent_confidence > 0.6


@pytest.mark.asyncio
async def test_batch_process(processor: SemanticProcessor) -> None:
    """Test batch message processing."""
    messages = [
        {"message_id": "msg_001", "source_agent_id": "agent_a", "content": "Let's help and assist each other"},
        {"message_id": "msg_002", "source_agent_id": "agent_b", "content": "I will attack and defeat you"},
        {"message_id": "msg_003", "source_agent_id": "agent_c", "content": "Status update"},
    ]

    results = await processor.batch_process(messages)

    assert len(results) == 3
    assert results[0].intent_classification == IntentClassification.COOPERATIVE
    assert results[1].intent_classification == IntentClassification.COMPETITIVE
    assert results[2].intent_classification == IntentClassification.NEUTRAL


def test_classify_intent_edge_cases(processor: SemanticProcessor) -> None:
    """Test edge cases in intent classification."""
    # Empty markers should be NEUTRAL
    assert processor.classify_intent("No special words here")[0] == IntentClassification.NEUTRAL

    # Single marker insufficient
    assert processor.classify_intent("help")[0] == IntentClassification.NEUTRAL

    # Multiple cooperative markers
    text_coop = "collaborate cooperate share support"
    intent, conf = processor.classify_intent(text_coop)
    assert intent == IntentClassification.COOPERATIVE
    assert conf >= 0.9


def test_transformers_fallback(processor: SemanticProcessor) -> None:
    """Test processor works without transformers library."""
    # When TRANSFORMERS_AVAILABLE is False, should use mock embeddings
    embedding = processor.generate_embedding("test text")
    assert len(embedding) == 384
    assert all(x == 0.1 for x in embedding)


@pytest.mark.asyncio
async def test_process_message_with_provenance(processor: SemanticProcessor) -> None:
    """Test message processing with provenance chain."""
    representation = await processor.process_message(
        message_id="msg_with_prov",
        source_agent_id="agent_x",
        content="Neutral statement",
        provenance_chain=["msg_parent_1", "msg_parent_2"],
    )

    assert len(representation.provenance_chain) == 2
    assert "msg_parent_1" in representation.provenance_chain


def test_processor_device_selection(processor: SemanticProcessor) -> None:
    """Test that processor selects appropriate device."""
    assert hasattr(processor, 'device')
    assert processor.device in ['cpu', 'cuda']


@pytest.mark.asyncio
async def test_batch_process_empty_list(processor: SemanticProcessor) -> None:
    """Test batch processing with empty list."""
    results = await processor.batch_process([])
    assert results == []
