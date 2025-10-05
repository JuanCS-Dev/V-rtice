"""
Argument Mining with Transformer-based Sequence Labeling for Cognitive Defense System.

Extracts argumentative components (claims, premises) using BERT-based
token classification following the TARGER framework.
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import asyncio

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

from .models import Argument, ArgumentRole
from .cache_manager import cache_manager, CacheCategory
from .utils import hash_text
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ArgumentMiner:
    """
    Transformer-based argument mining.

    Performs token-level classification to extract:
    - Major Claims (main thesis)
    - Claims (supporting/opposing statements)
    - Premises (evidence/reasoning)
    """

    # BIO tagging scheme
    TAG_MAPPING = {
        0: "O",  # Outside
        1: "B-MajorClaim",
        2: "I-MajorClaim",
        3: "B-Claim",
        4: "I-Claim",
        5: "B-Premise",
        6: "I-Premise",
    }

    ROLE_MAPPING = {
        "MajorClaim": ArgumentRole.MAJOR_CLAIM,
        "Claim": ArgumentRole.CLAIM,
        "Premise": ArgumentRole.PREMISE,
    }

    def __init__(
        self,
        model_name: str = "neuralmind/bert-base-portuguese-cased",
        device: str = "cpu"
    ):
        """
        Initialize argument miner.

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
            logger.warning("Argument miner already initialized")
            return

        try:
            logger.info(f"Loading argument miner: {self.model_name}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=True
            )

            # Load model for token classification
            # Note: In production, use fine-tuned model on argument mining dataset
            num_labels = len(self.TAG_MAPPING)
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_name,
                num_labels=num_labels
            )

            self.model.to(self.device)
            self.model.eval()

            # Quantization
            if self.device == "cpu":
                self.model = torch.quantization.quantize_dynamic(
                    self.model,
                    {torch.nn.Linear},
                    dtype=torch.qint8
                )

            self._initialized = True
            logger.info("✅ Argument miner initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize argument miner: {e}", exc_info=True)
            raise

    @torch.no_grad()
    def extract_arguments(
        self,
        text: str,
        min_confidence: float = 0.6,
        use_cache: bool = True
    ) -> List[Argument]:
        """
        Extract arguments from text.

        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
            use_cache: Use cached results

        Returns:
            List of Argument objects
        """
        if not self._initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        # Check cache
        if use_cache:
            cache_key = f"arguments:{hash_text(text)}"
            cached = asyncio.get_event_loop().run_until_complete(
                cache_manager.get(CacheCategory.MODEL_CACHE, cache_key)
            )
            if cached:
                return [Argument(**arg) for arg in cached]

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

        # Predictions
        predictions = np.argmax(logits, axis=-1)

        # Extract argument spans
        arguments = self._extract_argument_spans(
            text,
            predictions,
            offset_mapping,
            logits,
            min_confidence
        )

        # Link premises to claims
        arguments = self._link_premises_to_claims(arguments)

        # Cache result
        if use_cache:
            cache_key = f"arguments:{hash_text(text)}"
            asyncio.get_event_loop().run_until_complete(
                cache_manager.set(
                    CacheCategory.MODEL_CACHE,
                    cache_key,
                    [arg.model_dump() for arg in arguments],
                    ttl_override=3600
                )
            )

        return arguments

    def _extract_argument_spans(
        self,
        text: str,
        predictions: np.ndarray,
        offset_mapping: np.ndarray,
        logits: np.ndarray,
        min_confidence: float
    ) -> List[Argument]:
        """
        Extract argument spans from BIO predictions.

        Args:
            text: Original text
            predictions: Token predictions
            offset_mapping: Character offsets
            logits: Raw logits
            min_confidence: Minimum confidence

        Returns:
            List of Argument objects
        """
        arguments = []
        current_arg = None
        current_type = None

        for i, (pred, offset) in enumerate(zip(predictions, offset_mapping)):
            # Skip special tokens
            if offset[0] == offset[1]:
                continue

            tag = self.TAG_MAPPING.get(pred, "O")

            # Calculate confidence
            probs = torch.softmax(torch.tensor(logits[i]), dim=0).numpy()
            confidence = float(probs[pred])

            if confidence < min_confidence:
                if current_arg:
                    arguments.append(current_arg)
                    current_arg = None
                    current_type = None
                continue

            if tag == "O":
                if current_arg:
                    arguments.append(current_arg)
                    current_arg = None
                    current_type = None
                continue

            # Parse tag
            if tag.startswith("B-"):
                # Begin new argument
                if current_arg:
                    arguments.append(current_arg)

                arg_type = tag[2:]  # Remove B-
                role = self.ROLE_MAPPING[arg_type]

                start_char = int(offset[0])
                end_char = int(offset[1])

                current_arg = Argument(
                    text=text[start_char:end_char],
                    role=role,
                    start_char=start_char,
                    end_char=end_char,
                    confidence=confidence
                )
                current_type = arg_type

            elif tag.startswith("I-"):
                # Continue current argument
                arg_type = tag[2:]

                if current_arg and arg_type == current_type:
                    end_char = int(offset[1])
                    current_arg.end_char = end_char
                    current_arg.text = text[current_arg.start_char:end_char]
                    # Update confidence (average)
                    current_arg.confidence = (current_arg.confidence + confidence) / 2

        # Add final argument
        if current_arg:
            arguments.append(current_arg)

        return arguments

    def _link_premises_to_claims(
        self,
        arguments: List[Argument]
    ) -> List[Argument]:
        """
        Link premises to their supporting claims.

        Uses proximity heuristic: premises follow claims.

        Args:
            arguments: List of arguments

        Returns:
            Arguments with parent_id links
        """
        # Find all claims
        claims = [arg for arg in arguments if arg.role in [ArgumentRole.CLAIM, ArgumentRole.MAJOR_CLAIM]]

        # For each premise, find closest preceding claim
        for arg in arguments:
            if arg.role == ArgumentRole.PREMISE:
                # Find closest claim before this premise
                candidates = [
                    claim for claim in claims
                    if claim.end_char <= arg.start_char
                ]

                if candidates:
                    # Get closest (by end position)
                    closest = max(candidates, key=lambda c: c.end_char)
                    arg.parent_id = closest.id

        return arguments

    def get_argument_structure(
        self,
        arguments: List[Argument]
    ) -> Dict[str, any]:
        """
        Analyze argument structure.

        Args:
            arguments: List of arguments

        Returns:
            Structure analysis dict
        """
        major_claims = [a for a in arguments if a.role == ArgumentRole.MAJOR_CLAIM]
        claims = [a for a in arguments if a.role == ArgumentRole.CLAIM]
        premises = [a for a in arguments if a.role == ArgumentRole.PREMISE]

        # Count supported claims (have premises)
        supported_claims = sum(
            1 for claim in claims
            if any(p.parent_id == claim.id for p in premises)
        )

        # Average premises per claim
        avg_premises = len(premises) / len(claims) if claims else 0

        return {
            "total_arguments": len(arguments),
            "major_claims": len(major_claims),
            "claims": len(claims),
            "premises": len(premises),
            "supported_claims": supported_claims,
            "unsupported_claims": len(claims) - supported_claims,
            "avg_premises_per_claim": avg_premises,
            "structure_quality": self._assess_structure_quality(
                claims,
                premises,
                supported_claims
            )
        }

    @staticmethod
    def _assess_structure_quality(
        claims: List[Argument],
        premises: List[Argument],
        supported_claims: int
    ) -> float:
        """
        Assess quality of argument structure.

        Args:
            claims: Claim arguments
            premises: Premise arguments
            supported_claims: Number of supported claims

        Returns:
            Quality score (0-1)
        """
        if not claims:
            return 0.0

        # Factor 1: Proportion of supported claims
        support_ratio = supported_claims / len(claims) if claims else 0

        # Factor 2: Premise density
        premise_density = min(1.0, len(premises) / (len(claims) * 2))  # Ideal: 2 premises per claim

        # Factor 3: Confidence
        avg_confidence = sum(a.confidence for a in claims + premises) / (len(claims) + len(premises))

        quality = (support_ratio * 0.5 + premise_density * 0.3 + avg_confidence * 0.2)
        return quality

    def detect_circular_reasoning(
        self,
        arguments: List[Argument]
    ) -> List[Tuple[str, str]]:
        """
        Detect circular reasoning patterns.

        Args:
            arguments: List of arguments

        Returns:
            List of (claim_id, premise_id) tuples showing circularity
        """
        circular_patterns = []

        for premise in arguments:
            if premise.role != ArgumentRole.PREMISE or not premise.parent_id:
                continue

            # Check if premise text is very similar to its claim
            parent_claim = next(
                (a for a in arguments if a.id == premise.parent_id),
                None
            )

            if parent_claim:
                # Simple similarity check (production should use embeddings)
                claim_words = set(parent_claim.text.lower().split())
                premise_words = set(premise.text.lower().split())

                overlap = len(claim_words & premise_words)
                union = len(claim_words | premise_words)

                similarity = overlap / union if union > 0 else 0

                # High similarity indicates circularity
                if similarity > 0.7:
                    circular_patterns.append((parent_claim.id, premise.id))

        return circular_patterns

    def batch_extract(
        self,
        texts: List[str],
        batch_size: int = 16
    ) -> List[List[Argument]]:
        """
        Batch argument extraction.

        Args:
            texts: List of texts
            batch_size: Batch size

        Returns:
            List of argument lists
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
                arguments = self._extract_argument_spans(
                    text,
                    predictions,
                    offset_mapping,
                    logit,
                    min_confidence=0.6
                )
                arguments = self._link_premises_to_claims(arguments)
                results.append(arguments)

        return results


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

argument_miner = ArgumentMiner(
    device="cuda" if torch.cuda.is_available() else "cpu"
)
