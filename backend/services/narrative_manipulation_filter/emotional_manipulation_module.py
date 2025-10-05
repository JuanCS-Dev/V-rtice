"""
Emotional Manipulation Detection Module (Module 2) for Cognitive Defense System.

Orchestrates:
- BERTimbau 27-emotion classification
- RoBERTa propaganda span detection (18 techniques)
- Cialdini's 6 persuasion principles analysis
- Dark Triad personality markers
- Emotional trajectory tracking
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import asyncio

from .bertimbau_emotion_classifier import bertimbau_classifier
from .roberta_propaganda_detector import roberta_detector
from .cialdini_analyzer import cialdini_analyzer
from .dark_triad_detector import dark_triad_detector
from .models import (
    EmotionalManipulationResult,
    EmotionProfile,
    PropagandaSpan,
    CialdiniPrinciple,
    DarkTriadMarkers,
    EmotionCategory
)
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class EmotionalManipulationModule:
    """
    Module 2: Emotional Manipulation Detection.

    Multi-layer emotional analysis combining:
    1. Deep learning (BERTimbau, RoBERTa)
    2. Psychological pattern matching (Cialdini, Dark Triad)
    3. Temporal emotion tracking
    """

    def __init__(self):
        """Initialize Module 2."""
        self._models_initialized = False

    async def initialize(self) -> None:
        """Initialize ML models."""
        if self._models_initialized:
            logger.warning("Emotional manipulation models already initialized")
            return

        try:
            logger.info("🚀 Initializing emotional manipulation detection models...")

            # Initialize models in parallel
            await asyncio.gather(
                bertimbau_classifier.initialize(),
                roberta_detector.initialize()
            )

            self._models_initialized = True
            logger.info("✅ Emotional manipulation detection models initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize models: {e}", exc_info=True)
            raise

    async def detect_emotional_manipulation(
        self,
        text: str,
        analyze_trajectory: bool = True
    ) -> EmotionalManipulationResult:
        """
        Comprehensive emotional manipulation detection.

        Args:
            text: Input text
            analyze_trajectory: Enable temporal emotion analysis

        Returns:
            EmotionalManipulationResult
        """
        if not self._models_initialized:
            logger.warning("Models not initialized, initializing now...")
            await self.initialize()

        # ========== LAYER 1: EMOTION CLASSIFICATION (BERTimbau) ==========

        emotion_profile = bertimbau_classifier.classify_emotion(text)

        # Emotional trajectory
        emotional_trajectory = []
        if analyze_trajectory and len(text) > 200:
            trajectory_data = bertimbau_classifier.detect_emotional_trajectory(text)
            emotional_trajectory = trajectory_data

        # Manipulation signals from emotions
        emotion_signals = bertimbau_classifier.detect_emotional_manipulation_signals(
            emotion_profile
        )

        # ========== LAYER 2: PROPAGANDA DETECTION (RoBERTa) ==========

        propaganda_spans = roberta_detector.detect_propaganda_spans(text)

        # Merge overlapping spans
        propaganda_spans = roberta_detector.merge_overlapping_spans(propaganda_spans)

        # Calculate propaganda density
        propaganda_density = roberta_detector.calculate_propaganda_density(
            text,
            propaganda_spans
        )

        # Detect multi-technique patterns
        propaganda_patterns = roberta_detector.detect_multi_technique_patterns(
            propaganda_spans
        )

        # ========== LAYER 3: PERSUASION PRINCIPLES (Cialdini) ==========

        cialdini_principles = cialdini_analyzer.analyze_all_principles(text)

        # Get statistics
        cialdini_stats = cialdini_analyzer.get_principle_statistics(
            cialdini_principles
        )

        # ========== LAYER 4: DARK TRIAD MARKERS ==========

        dark_triad = dark_triad_detector.analyze_dark_triad(text)

        # Risk assessment
        dark_triad_risk = dark_triad_detector.assess_manipulation_risk(dark_triad)

        # ========== AGGREGATION: CALCULATE MANIPULATION SCORE ==========

        manipulation_score = self._calculate_manipulation_score(
            emotion_profile=emotion_profile,
            emotion_signals=emotion_signals,
            propaganda_density=propaganda_density,
            propaganda_spans=propaganda_spans,
            cialdini_principles=cialdini_principles,
            dark_triad=dark_triad
        )

        # ========== BUILD RESULT ==========

        result = EmotionalManipulationResult(
            manipulation_score=manipulation_score,
            emotion_profile=emotion_profile,
            propaganda_spans=propaganda_spans,
            cialdini_principles=cialdini_principles,
            dark_triad=dark_triad,
            emotional_trajectory=emotional_trajectory
        )

        logger.info(
            f"Emotional manipulation detected: score={manipulation_score:.3f}, "
            f"primary_emotion={emotion_profile.primary_emotion.value}, "
            f"propaganda_spans={len(propaganda_spans)}, "
            f"cialdini_detections={len(cialdini_principles)}, "
            f"dark_triad_agg={dark_triad.aggregate_score:.3f}"
        )

        return result

    def _calculate_manipulation_score(
        self,
        emotion_profile: EmotionProfile,
        emotion_signals: Dict[str, float],
        propaganda_density: float,
        propaganda_spans: List[PropagandaSpan],
        cialdini_principles: List[CialdiniPrinciple],
        dark_triad: DarkTriadMarkers
    ) -> float:
        """
        Calculate overall emotional manipulation score.

        Weighted combination of:
        - Emotion-based manipulation (25%)
        - Propaganda techniques (30%)
        - Persuasion principles (25%)
        - Dark Triad markers (20%)

        Args:
            emotion_profile: Emotion classification
            emotion_signals: Emotional manipulation signals
            propaganda_density: Propaganda text density
            propaganda_spans: Detected propaganda spans
            cialdini_principles: Detected Cialdini principles
            dark_triad: Dark Triad markers

        Returns:
            Manipulation score (0-1)
        """

        # 1. Emotion-based score (25%)
        emotion_score = bertimbau_classifier.calculate_manipulation_score(
            emotion_profile,
            emotion_signals
        )

        # 2. Propaganda score (30%)
        if propaganda_spans:
            # Average propaganda confidence
            propaganda_confidence = sum(
                span.confidence for span in propaganda_spans
            ) / len(propaganda_spans)

            # Combine density + confidence
            propaganda_score = (propaganda_density * 0.6 + propaganda_confidence * 0.4)
        else:
            propaganda_score = 0.0

        # 3. Persuasion principles score (25%)
        if cialdini_principles:
            # Average manipulation intent
            avg_manipulation_intent = sum(
                p.manipulation_intent for p in cialdini_principles
            ) / len(cialdini_principles)

            # Number of principles (diversity penalty)
            principle_diversity = min(1.0, len(set(p.principle for p in cialdini_principles)) / 6.0)

            cialdini_score = avg_manipulation_intent * 0.7 + principle_diversity * 0.3
        else:
            cialdini_score = 0.0

        # 4. Dark Triad score (20%)
        dark_triad_score = dark_triad.aggregate_score

        # Weighted combination
        final_score = (
            emotion_score * 0.25 +
            propaganda_score * 0.30 +
            cialdini_score * 0.25 +
            dark_triad_score * 0.20
        )

        # Boosters for severe cases
        boosters = 0.0

        # High arousal + negative valence = strong manipulation indicator
        if emotion_profile.arousal > 0.7 and emotion_profile.valence < -0.5:
            boosters += 0.15

        # Multiple propaganda techniques in short text
        if len(propaganda_spans) >= 3 and len(text) < 500:
            boosters += 0.10

        # Dark Triad + Cialdini combo (predatory manipulation)
        if dark_triad.aggregate_score > 0.6 and len(cialdini_principles) >= 2:
            boosters += 0.15

        final_score = min(1.0, final_score + boosters)

        return final_score

    def analyze_emotional_arc(
        self,
        trajectory: List[Tuple[int, EmotionCategory]]
    ) -> Dict[str, Any]:
        """
        Analyze emotional arc for manipulation patterns.

        Args:
            trajectory: List of (offset, emotion) tuples

        Returns:
            Arc analysis dict
        """
        if len(trajectory) < 3:
            return {
                "arc_type": "static",
                "volatility": 0.0,
                "manipulation_indicator": 0.0
            }

        # Extract emotion sequence
        emotions = [e for _, e in trajectory]

        # Detect emotion changes
        changes = sum(
            1 for i in range(len(emotions) - 1)
            if emotions[i] != emotions[i + 1]
        )

        volatility = changes / (len(emotions) - 1) if len(emotions) > 1 else 0

        # Common manipulation arcs
        arc_type = "unknown"
        manipulation_indicator = 0.0

        # Fear -> Scarcity arc (urgency manipulation)
        fear_indices = [i for i, (_, e) in enumerate(trajectory) if e == EmotionCategory.FEAR]
        if fear_indices and len(trajectory) > 0:
            # Check if fear is followed by urgency/excitement
            for idx in fear_indices:
                if idx < len(trajectory) - 1:
                    next_emotion = trajectory[idx + 1][1]
                    if next_emotion in [EmotionCategory.EXCITEMENT, EmotionCategory.DESIRE]:
                        arc_type = "fear_to_action"
                        manipulation_indicator = 0.8

        # Negative -> Positive swing (emotional whiplash)
        negative_emotions = {EmotionCategory.ANGER, EmotionCategory.FEAR, EmotionCategory.DISGUST, EmotionCategory.SADNESS}
        positive_emotions = {EmotionCategory.JOY, EmotionCategory.EXCITEMENT, EmotionCategory.OPTIMISM}

        for i in range(len(trajectory) - 1):
            curr_emotion = trajectory[i][1]
            next_emotion = trajectory[i + 1][1]

            if curr_emotion in negative_emotions and next_emotion in positive_emotions:
                arc_type = "emotional_whiplash"
                manipulation_indicator = max(manipulation_indicator, 0.7)

        return {
            "arc_type": arc_type,
            "volatility": volatility,
            "manipulation_indicator": manipulation_indicator,
            "total_changes": changes,
            "dominant_emotions": self._get_dominant_emotions(emotions)
        }

    @staticmethod
    def _get_dominant_emotions(
        emotions: List[EmotionCategory],
        top_k: int = 3
    ) -> List[Tuple[EmotionCategory, float]]:
        """Get top-K dominant emotions with frequencies."""
        from collections import Counter

        emotion_counts = Counter(emotions)
        total = len(emotions)

        dominant = [
            (emotion, count / total)
            for emotion, count in emotion_counts.most_common(top_k)
        ]

        return dominant


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

emotional_manipulation_module = EmotionalManipulationModule()
