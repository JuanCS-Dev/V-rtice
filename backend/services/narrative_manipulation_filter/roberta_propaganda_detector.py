"""
RoBERTa Propaganda Span Detector for Cognitive Defense System.

Detects 18 propaganda techniques from SemEval-2020 Task 11:
Fine-grained Propaganda Detection using token-level classification.
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import asyncio

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

from .models import PropagandaSpan, PropagandaTechnique
from .cache_manager import cache_manager, CacheCategory
from .utils import hash_text
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class RoBERTaPropagandaDetector:
    """
    RoBERTa-based propaganda technique detector.

    Performs token-level classification to identify propaganda spans
    across 18 techniques.
    """

    # Propaganda technique mapping (SemEval-2020 Task 11)
    TECHNIQUE_LABELS = {
        0: PropagandaTechnique.LOADED_LANGUAGE,
        1: PropagandaTechnique.NAME_CALLING,
        2: PropagandaTechnique.REPETITION,
        3: PropagandaTechnique.EXAGGERATION,
        4: PropagandaTechnique.DOUBT,
        5: PropagandaTechnique.APPEAL_TO_FEAR,
        6: PropagandaTechnique.FLAG_WAVING,
        7: PropagandaTechnique.CAUSAL_OVERSIMPLIFICATION,
        8: PropagandaTechnique.SLOGANS,
        9: PropagandaTechnique.APPEAL_TO_AUTHORITY,
        10: PropagandaTechnique.BLACK_WHITE_FALLACY,
        11: PropagandaTechnique.THOUGHT_TERMINATING_CLICHES,
        12: PropagandaTechnique.WHATABOUTISM,
        13: PropagandaTechnique.REDUCTIO_AD_HITLERUM,
        14: PropagandaTechnique.RED_HERRING,
        15: PropagandaTechnique.BANDWAGON,
        16: PropagandaTechnique.OBFUSCATION,
        17: PropagandaTechnique.STRAW_MAN,
    }

    def __init__(
        self,
        model_name: str = "xlm-roberta-base",
        device: str = "cpu"
    ):
        """
        Initialize RoBERTa propaganda detector.

        Args:
            model_name: HuggingFace model identifier
            device: 'cpu' or 'cuda'
        """
        self.model_name = model_name
        self.device = device

        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForTokenClassification] = None

        self._initialized = False

    async def initialize(self) -> None:
        """Load model and tokenizer."""
        if self._initialized:
            logger.warning("RoBERTa propaganda detector already initialized")
            return

        try:
            logger.info(f"Loading RoBERTa propaganda detector: {self.model_name}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=True
            )

            # Load model for token classification
            # Note: In production, use fine-tuned model on SemEval-2020 dataset
            num_labels = len(self.TECHNIQUE_LABELS) * 2 + 1  # B-/I- tags + O
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_name,
                num_labels=num_labels
            )

            self.model.to(self.device)
            self.model.eval()

            # Quantization for CPU
            if self.device == "cpu":
                self.model = torch.quantization.quantize_dynamic(
                    self.model,
                    {torch.nn.Linear},
                    dtype=torch.qint8
                )

            self._initialized = True
            logger.info("✅ RoBERTa propaganda detector initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize RoBERTa: {e}", exc_info=True)
            raise

    @torch.no_grad()
    def detect_propaganda_spans(
        self,
        text: str,
        min_confidence: float = 0.7,
        use_cache: bool = True
    ) -> List[PropagandaSpan]:
        """
        Detect propaganda technique spans in text.

        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
            use_cache: Use cached results

        Returns:
            List of PropagandaSpan
        """
        if not self._initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        # Check cache
        if use_cache:
            cache_key = f"propaganda:{hash_text(text)}"
            cached = asyncio.get_event_loop().run_until_complete(
                cache_manager.get(CacheCategory.MODEL_CACHE, cache_key)
            )
            if cached:
                return [PropagandaSpan(**span) for span in cached]

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
            return_offsets_mapping=True
        ).to(self.device)

        offset_mapping = inputs.pop("offset_mapping")[0].cpu().numpy()

        # Forward pass
        outputs = self.model(**inputs)
        logits = outputs.logits[0].cpu().numpy()

        # Convert to predictions (argmax)
        predictions = np.argmax(logits, axis=-1)

        # Convert to BIO tags
        spans = self._extract_spans_from_bio(
            text,
            predictions,
            offset_mapping,
            logits,
            min_confidence
        )

        # Cache result
        if use_cache:
            cache_key = f"propaganda:{hash_text(text)}"
            asyncio.get_event_loop().run_until_complete(
                cache_manager.set(
                    CacheCategory.MODEL_CACHE,
                    cache_key,
                    [span.model_dump() for span in spans],
                    ttl_override=3600
                )
            )

        return spans

    def _extract_spans_from_bio(
        self,
        text: str,
        predictions: np.ndarray,
        offset_mapping: np.ndarray,
        logits: np.ndarray,
        min_confidence: float
    ) -> List[PropagandaSpan]:
        """
        Extract propaganda spans from BIO predictions.

        Args:
            text: Original text
            predictions: Token-level predictions
            offset_mapping: Character offsets
            logits: Raw logits for confidence
            min_confidence: Minimum confidence

        Returns:
            List of PropagandaSpan
        """
        spans = []
        current_span = None
        current_technique = None

        for i, (pred, offset) in enumerate(zip(predictions, offset_mapping)):
            # Skip special tokens
            if offset[0] == offset[1]:
                continue

            # Get technique from prediction
            # BIO format: 0=O, 1-18=B-techniques, 19-36=I-techniques
            if pred == 0:  # O tag
                if current_span is not None:
                    # End current span
                    spans.append(current_span)
                    current_span = None
                    current_technique = None
                continue

            # Calculate confidence from logits
            probs = torch.softmax(torch.tensor(logits[i]), dim=0).numpy()
            confidence = float(probs[pred])

            if confidence < min_confidence:
                continue

            # Determine technique
            if 1 <= pred <= 18:  # B- tags
                technique_id = pred - 1
                technique = self.TECHNIQUE_LABELS.get(technique_id)

                # Start new span
                if current_span is not None:
                    spans.append(current_span)

                start_char = int(offset[0])
                end_char = int(offset[1])

                current_span = PropagandaSpan(
                    technique=technique,
                    text=text[start_char:end_char],
                    start_char=start_char,
                    end_char=end_char,
                    confidence=confidence
                )
                current_technique = technique

            elif 19 <= pred <= 36:  # I- tags
                technique_id = pred - 19
                technique = self.TECHNIQUE_LABELS.get(technique_id)

                # Continue current span
                if current_span and technique == current_technique:
                    end_char = int(offset[1])
                    current_span.end_char = end_char
                    current_span.text = text[current_span.start_char:end_char]
                    # Update confidence (average)
                    current_span.confidence = (current_span.confidence + confidence) / 2

        # Add final span
        if current_span is not None:
            spans.append(current_span)

        return spans

    def merge_overlapping_spans(
        self,
        spans: List[PropagandaSpan]
    ) -> List[PropagandaSpan]:
        """
        Merge overlapping propaganda spans.

        Args:
            spans: List of spans

        Returns:
            Merged spans
        """
        if not spans:
            return []

        # Sort by start position
        sorted_spans = sorted(spans, key=lambda x: x.start_char)

        merged = [sorted_spans[0]]

        for current in sorted_spans[1:]:
            prev = merged[-1]

            # Check overlap
            if current.start_char <= prev.end_char:
                # Merge if same technique
                if current.technique == prev.technique:
                    prev.end_char = max(prev.end_char, current.end_char)
                    prev.text = prev.text[:prev.end_char - prev.start_char]
                    prev.confidence = max(prev.confidence, current.confidence)
                else:
                    # Keep both if different techniques
                    merged.append(current)
            else:
                merged.append(current)

        return merged

    def calculate_propaganda_density(
        self,
        text: str,
        spans: List[PropagandaSpan]
    ) -> float:
        """
        Calculate propaganda density (% of text containing propaganda).

        Args:
            text: Original text
            spans: Detected propaganda spans

        Returns:
            Density ratio (0-1)
        """
        if not text or not spans:
            return 0.0

        total_propaganda_chars = sum(
            span.end_char - span.start_char
            for span in spans
        )

        density = total_propaganda_chars / len(text)
        return float(np.clip(density, 0.0, 1.0))

    def get_technique_distribution(
        self,
        spans: List[PropagandaSpan]
    ) -> Dict[PropagandaTechnique, int]:
        """
        Get distribution of propaganda techniques.

        Args:
            spans: Detected propaganda spans

        Returns:
            Dict mapping technique to count
        """
        distribution = {}
        for span in spans:
            distribution[span.technique] = distribution.get(span.technique, 0) + 1

        return distribution

    def detect_multi_technique_patterns(
        self,
        spans: List[PropagandaSpan]
    ) -> List[Dict[str, any]]:
        """
        Detect patterns of multiple techniques used together.

        Args:
            spans: Detected propaganda spans

        Returns:
            List of pattern dicts
        """
        patterns = []

        # Common combinations
        KNOWN_PATTERNS = {
            ("APPEAL_TO_FEAR", "FLAG_WAVING"): "fear_patriotism",
            ("NAME_CALLING", "LOADED_LANGUAGE"): "ad_hominem_amplification",
            ("EXAGGERATION", "CAUSAL_OVERSIMPLIFICATION"): "oversimplified_threat",
            ("APPEAL_TO_AUTHORITY", "BANDWAGON"): "social_proof_cascade",
        }

        # Check for co-occurrence within 100 chars
        for i, span1 in enumerate(spans):
            for span2 in spans[i+1:]:
                distance = span2.start_char - span1.end_char

                if 0 <= distance <= 100:  # Close proximity
                    technique_pair = tuple(sorted([
                        span1.technique.value,
                        span2.technique.value
                    ]))

                    pattern_name = KNOWN_PATTERNS.get(technique_pair)

                    if pattern_name:
                        patterns.append({
                            "pattern": pattern_name,
                            "techniques": [span1.technique.value, span2.technique.value],
                            "span1": span1,
                            "span2": span2,
                            "distance": distance
                        })

        return patterns

    def batch_detect(
        self,
        texts: List[str],
        batch_size: int = 16
    ) -> List[List[PropagandaSpan]]:
        """
        Batch propaganda detection for efficiency.

        Args:
            texts: List of texts
            batch_size: Batch size

        Returns:
            List of span lists
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Tokenize batch
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
                return_offsets_mapping=True
            ).to(self.device)

            offset_mappings = inputs.pop("offset_mapping").cpu().numpy()

            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits.cpu().numpy()

            # Process each text
            for text, logit, offset_mapping in zip(batch, logits, offset_mappings):
                predictions = np.argmax(logit, axis=-1)
                spans = self._extract_spans_from_bio(
                    text,
                    predictions,
                    offset_mapping,
                    logit,
                    min_confidence=0.7
                )
                results.append(spans)

        return results


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

roberta_detector = RoBERTaPropagandaDetector(
    device="cuda" if torch.cuda.is_available() else "cpu"
)
