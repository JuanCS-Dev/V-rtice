"""Semantic Processor - Camada 1 do Filtro de Narrativas.

Responsável por:
- Gerar embeddings de mensagens (sentence-transformers)
- Classificar intenção (COOPERATIVE, COMPETITIVE, NEUTRAL, AMBIGUOUS)
- Persistir representações semânticas no PostgreSQL
"""

from datetime import datetime
from typing import Any

try:
    import torch
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


from narrative_filter_service.config import settings
from narrative_filter_service.models import IntentClassification, SemanticRepresentation


class SemanticProcessor:
    """Processador semântico de mensagens de agentes."""

    def __init__(self) -> None:
        """Initialize semantic processor with embedding model."""
        if not TRANSFORMERS_AVAILABLE:
            self.model = None
            self.device = "cpu"
            return

        self.model = SentenceTransformer(settings.embedding_model)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            List of float values (384 dimensions for all-MiniLM-L6-v2)
        """
        if not TRANSFORMERS_AVAILABLE or self.model is None:
            # Fallback: uniform embedding for testing without ML dependencies
            return [0.1] * 384

        embedding = self.model.encode(text, convert_to_tensor=True, device=self.device)
        return list(embedding.cpu().tolist())

    def classify_intent(self, text: str) -> tuple[IntentClassification, float]:
        """Classify intent of message using heuristic rules.

        Args:
            text: Input message text

        Returns:
            Tuple of (IntentClassification, confidence_score)
        """
        text_lower = text.lower()

        # Cooperative markers
        cooperative_markers = ["help", "assist", "collaborate", "cooperate", "share", "together", "support", "alliance"]
        cooperative_score = sum(1 for marker in cooperative_markers if marker in text_lower)

        # Competitive markers
        competitive_markers = ["compete", "defeat", "oppose", "attack", "against", "challenge", "rival", "dominate"]
        competitive_score = sum(1 for marker in competitive_markers if marker in text_lower)

        # Determine classification
        if cooperative_score > competitive_score and cooperative_score >= 2:
            return IntentClassification.COOPERATIVE, min(0.6 + (cooperative_score * 0.1), 0.95)
        elif competitive_score > cooperative_score and competitive_score >= 2:
            return IntentClassification.COMPETITIVE, min(0.6 + (competitive_score * 0.1), 0.95)
        elif cooperative_score == competitive_score and cooperative_score > 0:
            return IntentClassification.AMBIGUOUS, 0.5 + (cooperative_score * 0.05)
        else:
            return IntentClassification.NEUTRAL, 0.7

    async def process_message(
        self,
        message_id: str,
        source_agent_id: str,
        content: str,
        timestamp: datetime | None = None,
        provenance_chain: list[str] | None = None,
    ) -> SemanticRepresentation:
        """Process a message and create semantic representation.

        Args:
            message_id: Unique message identifier
            source_agent_id: ID of source agent
            content: Message content
            timestamp: Message timestamp (default: now)
            provenance_chain: Chain of message provenance

        Returns:
            SemanticRepresentation object
        """
        # Generate embedding
        embedding = self.generate_embedding(content)

        # Classify intent
        intent, confidence = self.classify_intent(content)

        # Create representation
        return SemanticRepresentation(
            message_id=message_id,
            source_agent_id=source_agent_id,
            timestamp=timestamp or datetime.utcnow(),
            content_embedding=embedding,
            intent_classification=intent,
            intent_confidence=confidence,
            raw_content=content,
            provenance_chain=provenance_chain or [],
        )

    async def batch_process(self, messages: list[dict[str, Any]]) -> list[SemanticRepresentation]:
        """Process multiple messages in batch.

        Args:
            messages: List of message dicts with keys: message_id, source_agent_id, content

        Returns:
            List of SemanticRepresentation objects
        """
        results = []
        for msg in messages:
            rep = await self.process_message(
                message_id=msg["message_id"],
                source_agent_id=msg["source_agent_id"],
                content=msg["content"],
                timestamp=msg.get("timestamp"),
                provenance_chain=msg.get("provenance_chain"),
            )
            results.append(rep)
        return results
