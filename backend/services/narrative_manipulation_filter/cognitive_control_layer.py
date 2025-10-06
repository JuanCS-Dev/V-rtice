"""
Cognitive Control Layer for Cognitive Defense System.

Implements prefrontal cortex-inspired cognitive control:
- Attention allocation (check-worthiness scoring)
- Interference suppression (adversarial input filtering)
- Performance monitoring (model drift detection)
- Conflict resolution (multi-signal reconciliation)
"""

import logging
import re
import unicodedata
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from fact_check_aggregator import fact_check_aggregator
from cache_manager import cache_manager, CacheCategory
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ProcessingMode(Enum):
    """Processing mode based on check-worthiness and reputation."""

    SKIP = "skip"
    """Skip analysis (opinion, question, low priority)"""

    FAST_TRACK = "fast_track"
    """Fast track (known good source + no claims)"""

    STANDARD = "standard"
    """Standard processing (default)"""

    DEEP_ANALYSIS = "deep_analysis"
    """Deep analysis (known bad source OR high check-worthiness)"""


class CognitiveControlLayer:
    """
    Cognitive control system for attention and performance management.

    Functions:
    - Check-worthiness scoring (attention allocation)
    - Adversarial input filtering (interference suppression)
    - Model drift detection (performance monitoring)
    - Multi-signal conflict resolution
    """

    # Adversarial patterns (prompt injection attempts)
    ADVERSARIAL_PATTERNS = [
        r"ignore\s+(previous|all|prior)\s+(instructions?|prompts?|commands?)",
        r"disregard\s+(everything|all|previous)",
        r"forget\s+(your|the|all)\s+(instructions?|rules?|guidelines?)",
        r"new\s+(instructions?|system\s+message|prompt)",
        r"system\s*:\s*you\s+are",
        r"<\|endoftext\|>",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"###\s*(instruction|system|assistant)",
        r"act\s+as\s+(if|though)\s+you",
        r"pretend\s+(to\s+be|you\s+are)",
        r"roleplay\s+as",
    ]

    # Special tokens to remove
    SPECIAL_TOKENS = [
        r"<\|.*?\|>",
        r"<\|endoftext\|>",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
    ]

    # Performance thresholds
    CONFIDENCE_THRESHOLD = 0.7
    LATENCY_THRESHOLD_MS = 1000
    ERROR_RATE_THRESHOLD = 0.05  # 5%

    def __init__(self):
        """Initialize cognitive control layer."""
        self._initialized = False
        self._performance_history: list = []

    async def initialize(self) -> None:
        """Initialize control layer."""
        if self._initialized:
            return

        # Initialize check-worthiness scorer (via fact_check_aggregator)
        await fact_check_aggregator.initialize()

        self._initialized = True
        logger.info("✅ Cognitive control layer initialized")

    async def determine_mode(
        self,
        content: str,
        source_info: Dict[str, Any]
    ) -> ProcessingMode:
        """
        Determine optimal processing mode.

        Decision tree:
        - Known good source + no claims → FAST_TRACK
        - Known bad source OR high check-worthiness → DEEP_ANALYSIS
        - Otherwise → STANDARD

        Args:
            content: Input content
            source_info: Source metadata

        Returns:
            ProcessingMode
        """
        if not self._initialized:
            await self.initialize()

        # STEP 1: Check-worthiness scoring
        check_worthiness = await self._score_check_worthiness(content)

        # STEP 2: Source reputation quick check
        domain = self._extract_domain(source_info.get("url", ""))
        reputation = await self._get_cached_reputation(domain)

        # STEP 3: Content type detection (opinion vs factual)
        is_opinion = self._is_opinion_content(content)

        # DECISION LOGIC

        # Skip if opinion/question with low check-worthiness
        if is_opinion and check_worthiness < 0.3:
            logger.debug(f"Mode: SKIP (opinion, check_worthiness={check_worthiness:.3f})")
            return ProcessingMode.SKIP

        # Fast track if reputable source and low check-worthiness
        if reputation > 0.8 and check_worthiness < 0.3:
            logger.debug(f"Mode: FAST_TRACK (reputation={reputation:.3f})")
            return ProcessingMode.FAST_TRACK

        # Deep analysis if bad reputation or high check-worthiness
        if reputation < 0.3 or check_worthiness > 0.7:
            logger.debug(
                f"Mode: DEEP_ANALYSIS (reputation={reputation:.3f}, "
                f"check_worthiness={check_worthiness:.3f})"
            )
            return ProcessingMode.DEEP_ANALYSIS

        # Default: standard processing
        logger.debug(f"Mode: STANDARD (reputation={reputation:.3f})")
        return ProcessingMode.STANDARD

    async def _score_check_worthiness(self, content: str) -> float:
        """
        Score check-worthiness of content.

        Uses ClaimBuster API via fact_check_aggregator.

        Args:
            content: Input content

        Returns:
            Check-worthiness score (0-1)
        """
        try:
            result = await fact_check_aggregator.claimbuster_client.score_claim(
                text=content,
                use_cache=True
            )

            score = result.get("score", 0.5)
            return score

        except Exception as e:
            logger.warning(f"Check-worthiness scoring failed: {e}")
            return 0.5  # Neutral default

    async def _get_cached_reputation(self, domain: str) -> float:
        """
        Get cached source reputation.

        Args:
            domain: Source domain

        Returns:
            Reputation score (0-1)
        """
        cache_key = f"source_reputation:{domain}"

        cached = await cache_manager.get(CacheCategory.ANALYSIS, cache_key)

        if cached:
            return float(cached)

        # Default: neutral reputation for unknown sources
        return 0.5

    @staticmethod
    def _is_opinion_content(content: str) -> bool:
        """
        Detect if content is opinion/question vs factual.

        Heuristics:
        - Contains question marks
        - Uses first-person pronouns
        - Contains opinion keywords

        Args:
            content: Input content

        Returns:
            True if likely opinion
        """
        content_lower = content.lower()

        # Check for questions
        if "?" in content or any(q in content_lower for q in ["como", "quem", "quando", "onde", "por que", "o que"]):
            return True

        # Check for first-person pronouns (opinion indicators)
        first_person = ["eu acho", "na minha opinião", "acredito que", "penso que", "eu sinto", "me parece"]
        if any(phrase in content_lower for phrase in first_person):
            return True

        # Check for opinion keywords
        opinion_keywords = ["opinião", "acho", "acredito", "deveria", "poderia", "talvez"]
        if sum(1 for kw in opinion_keywords if kw in content_lower) >= 2:
            return True

        return False

    async def filter_adversarial_input(self, content: str) -> Tuple[str, bool]:
        """
        Detect and sanitize adversarial inputs (prompt injection attempts).

        Defenses:
        - Instruction phrase detection
        - Special character removal
        - Length limiting
        - Encoding normalization

        Args:
            content: Input content

        Returns:
            (sanitized_content, is_flagged)
        """
        flagged = False
        sanitized = content

        # STEP 1: Detect adversarial patterns
        for pattern in self.ADVERSARIAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Adversarial pattern detected: {pattern}")
                flagged = True

        # STEP 2: Remove special tokens
        for token_pattern in self.SPECIAL_TOKENS:
            sanitized = re.sub(token_pattern, "", sanitized, flags=re.IGNORECASE)

        # STEP 3: Normalize unicode
        sanitized = unicodedata.normalize("NFKC", sanitized)

        # STEP 4: Limit length
        max_length = settings.MAX_CONTENT_LENGTH

        if len(sanitized) > max_length:
            logger.warning(f"Content truncated: {len(sanitized)} → {max_length} chars")
            sanitized = sanitized[:max_length]
            flagged = True

        # STEP 5: Remove excessive newlines/whitespace
        sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
        sanitized = re.sub(r' {2,}', ' ', sanitized)

        if flagged:
            logger.warning("Adversarial input detected and sanitized")

        return sanitized, flagged

    async def detect_model_drift(
        self,
        report: Dict[str, Any]
    ) -> bool:
        """
        Monitor for model performance degradation.

        Signals:
        - Decreasing confidence scores
        - Increasing inference latency
        - Rising error rates

        Args:
            report: Analysis report with performance metrics

        Returns:
            True if drift detected
        """
        # Extract metrics from report
        confidence = report.get("confidence", 1.0)
        latency_ms = report.get("latency_ms", 0)
        had_error = report.get("error", False)

        # Store in performance history
        self._performance_history.append({
            "confidence": confidence,
            "latency_ms": latency_ms,
            "error": had_error,
            "timestamp": datetime.utcnow()
        })

        # Keep only last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._performance_history = [
            m for m in self._performance_history
            if m["timestamp"] > cutoff
        ]

        # Need minimum history for drift detection
        if len(self._performance_history) < 10:
            return False

        # Calculate recent metrics
        recent_metrics = self._performance_history[-100:]  # Last 100 analyses

        avg_confidence = np.mean([m["confidence"] for m in recent_metrics])
        avg_latency = np.mean([m["latency_ms"] for m in recent_metrics])
        error_rate = sum(1 for m in recent_metrics if m["error"]) / len(recent_metrics)

        # Check thresholds
        drift_detected = (
            avg_confidence < self.CONFIDENCE_THRESHOLD or
            avg_latency > self.LATENCY_THRESHOLD_MS or
            error_rate > self.ERROR_RATE_THRESHOLD
        )

        if drift_detected:
            logger.warning(
                f"Model drift detected: confidence={avg_confidence:.3f}, "
                f"latency={avg_latency:.0f}ms, error_rate={error_rate:.3f}"
            )

            # Alert (in production, trigger retraining pipeline)
            await self._send_drift_alert({
                "avg_confidence": avg_confidence,
                "avg_latency": avg_latency,
                "error_rate": error_rate,
                "sample_size": len(recent_metrics)
            })

        return drift_detected

    async def _send_drift_alert(self, metrics: Dict[str, Any]) -> None:
        """
        Send alert for model drift.

        In production, this would:
        - Log to monitoring system (Prometheus, Grafana)
        - Send notification (email, Slack)
        - Trigger retraining pipeline

        Args:
            metrics: Performance metrics
        """
        logger.error(f"🚨 MODEL DRIFT ALERT: {metrics}")

        # Cache alert to prevent spam
        alert_key = "model_drift_alert"

        await cache_manager.set(
            CacheCategory.ANALYSIS,
            alert_key,
            metrics
        )

    def reconcile_signals(
        self,
        signal_scores: Dict[str, float],
        signal_confidences: Dict[str, float]
    ) -> Tuple[float, float]:
        """
        Reconcile conflicting signals from multiple modules.

        Method: Confidence-weighted averaging

        Args:
            signal_scores: Dict of module scores {module_name: score}
            signal_confidences: Dict of confidences {module_name: confidence}

        Returns:
            (reconciled_score, reconciled_confidence)
        """
        if not signal_scores:
            return 0.0, 0.0

        # Confidence-weighted average
        weighted_sum = sum(
            signal_scores[module] * signal_confidences.get(module, 1.0)
            for module in signal_scores
        )

        total_weight = sum(
            signal_confidences.get(module, 1.0)
            for module in signal_scores
        )

        reconciled_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Confidence: harmonic mean of individual confidences
        confidences = list(signal_confidences.values())
        if confidences:
            reconciled_confidence = len(confidences) / sum(1/c for c in confidences if c > 0)
        else:
            reconciled_confidence = 0.0

        logger.debug(
            f"Signal reconciliation: score={reconciled_score:.3f}, "
            f"confidence={reconciled_confidence:.3f}"
        )

        return reconciled_score, reconciled_confidence

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return "unknown"

        url = url.replace("https://", "").replace("http://", "")
        domain = url.split("/")[0]
        domain = domain.replace("www.", "")

        return domain


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

cognitive_control = CognitiveControlLayer()
