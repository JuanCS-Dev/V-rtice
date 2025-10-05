"""
BERTimbau Emotion Classifier for Cognitive Defense System.

Fine-tuned BERT model for Portuguese emotion classification across 27 categories.
Based on GoEmotions dataset adapted for Portuguese via BERTimbau.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict
import asyncio
from functools import lru_cache

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer

from .models import EmotionProfile, EmotionCategory
from .cache_manager import cache_manager, CacheCategory
from .utils import hash_text
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class BERTimbauEmotionClassifier:
    """
    BERTimbau-based emotion classifier for Portuguese text.

    Classifies text into 27 emotion categories with arousal and valence scoring.
    """

    # Emotion to arousal/valence mapping (psychological research-based)
    EMOTION_AROUSAL_VALENCE = {
        EmotionCategory.ADMIRATION: (0.6, 0.8),
        EmotionCategory.AMUSEMENT: (0.7, 0.9),
        EmotionCategory.ANGER: (0.9, -0.7),
        EmotionCategory.ANNOYANCE: (0.6, -0.4),
        EmotionCategory.APPROVAL: (0.4, 0.6),
        EmotionCategory.CARING: (0.5, 0.7),
        EmotionCategory.CONFUSION: (0.5, -0.2),
        EmotionCategory.CURIOSITY: (0.6, 0.3),
        EmotionCategory.DESIRE: (0.7, 0.5),
        EmotionCategory.DISAPPOINTMENT: (0.4, -0.6),
        EmotionCategory.DISAPPROVAL: (0.5, -0.5),
        EmotionCategory.DISGUST: (0.7, -0.8),
        EmotionCategory.EMBARRASSMENT: (0.6, -0.5),
        EmotionCategory.EXCITEMENT: (0.9, 0.8),
        EmotionCategory.FEAR: (0.9, -0.6),
        EmotionCategory.GRATITUDE: (0.5, 0.8),
        EmotionCategory.GRIEF: (0.6, -0.8),
        EmotionCategory.JOY: (0.7, 0.9),
        EmotionCategory.LOVE: (0.6, 0.9),
        EmotionCategory.NERVOUSNESS: (0.7, -0.4),
        EmotionCategory.OPTIMISM: (0.5, 0.7),
        EmotionCategory.PRIDE: (0.6, 0.7),
        EmotionCategory.REALIZATION: (0.4, 0.2),
        EmotionCategory.RELIEF: (0.3, 0.6),
        EmotionCategory.REMORSE: (0.5, -0.6),
        EmotionCategory.SADNESS: (0.4, -0.7),
        EmotionCategory.SURPRISE: (0.8, 0.1),
        EmotionCategory.NEUTRAL: (0.1, 0.0),
    }

    def __init__(
        self,
        model_name: str = "neuralmind/bert-base-portuguese-cased",
        device: str = "cpu",
        use_quantization: bool = True
    ):
        """
        Initialize BERTimbau emotion classifier.

        Args:
            model_name: HuggingFace model identifier
            device: 'cpu' or 'cuda'
            use_quantization: Use INT8 quantization for speed
        """
        self.model_name = model_name
        self.device = device
        self.use_quantization = use_quantization

        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSequenceClassification] = None
        self.embedder: Optional[SentenceTransformer] = None

        self._initialized = False
        self._label_mapping = self._create_label_mapping()

    def _create_label_mapping(self) -> Dict[int, EmotionCategory]:
        """Create mapping from model output indices to EmotionCategory."""
        emotion_list = list(EmotionCategory)
        return {i: emotion_list[i] for i in range(len(emotion_list))}

    async def initialize(self) -> None:
        """
        Load model and tokenizer.

        Downloads and caches models on first run.
        """
        if self._initialized:
            logger.warning("BERTimbau already initialized")
            return

        try:
            logger.info(f"Loading BERTimbau emotion classifier: {self.model_name}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=True
            )

            # Load model
            # Note: In production, use a fine-tuned version for emotion classification
            # This is a placeholder using base BERTimbau
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=27,  # 27 emotions
                problem_type="multi_label_classification"
            )

            self.model.to(self.device)
            self.model.eval()

            # Quantization for faster inference
            if self.use_quantization and self.device == "cpu":
                self.model = torch.quantization.quantize_dynamic(
                    self.model,
                    {torch.nn.Linear},
                    dtype=torch.qint8
                )
                logger.info("✅ INT8 quantization applied")

            # Sentence embedder for semantic analysis
            self.embedder = SentenceTransformer(
                'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
            )

            self._initialized = True
            logger.info("✅ BERTimbau emotion classifier initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize BERTimbau: {e}", exc_info=True)
            raise

    @torch.no_grad()
    def classify_emotion(
        self,
        text: str,
        return_all_scores: bool = True,
        use_cache: bool = True
    ) -> EmotionProfile:
        """
        Classify emotion in text.

        Args:
            text: Input text
            return_all_scores: Return full probability distribution
            use_cache: Use cached results

        Returns:
            EmotionProfile with primary emotion and scores
        """
        if not self._initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        # Check cache
        if use_cache:
            cache_key = f"emotion:{hash_text(text)}"
            cached = asyncio.get_event_loop().run_until_complete(
                cache_manager.get(CacheCategory.MODEL_CACHE, cache_key)
            )
            if cached:
                return EmotionProfile(**cached)

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)

        # Forward pass
        outputs = self.model(**inputs)
        logits = outputs.logits

        # Convert to probabilities (sigmoid for multi-label)
        probs = torch.sigmoid(logits).cpu().numpy()[0]

        # Map to emotion categories
        emotion_scores = {
            self._label_mapping[i]: float(probs[i])
            for i in range(len(probs))
        }

        # Normalize to sum to 1.0 (convert multi-label to single-label distribution)
        total = sum(emotion_scores.values())
        if total > 0:
            emotion_scores = {
                k: v / total for k, v in emotion_scores.items()
            }

        # Primary emotion (highest probability)
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]

        # Calculate arousal and valence (weighted by emotion scores)
        arousal = sum(
            score * self.EMOTION_AROUSAL_VALENCE[emotion][0]
            for emotion, score in emotion_scores.items()
        )
        valence = sum(
            score * self.EMOTION_AROUSAL_VALENCE[emotion][1]
            for emotion, score in emotion_scores.items()
        )

        # Create profile
        profile = EmotionProfile(
            primary_emotion=primary_emotion,
            emotion_scores=emotion_scores,
            arousal=float(np.clip(arousal, 0.0, 1.0)),
            valence=float(np.clip(valence, -1.0, 1.0))
        )

        # Cache result
        if use_cache:
            cache_key = f"emotion:{hash_text(text)}"
            asyncio.get_event_loop().run_until_complete(
                cache_manager.set(
                    CacheCategory.MODEL_CACHE,
                    cache_key,
                    profile.model_dump(),
                    ttl_override=3600  # 1 hour
                )
            )

        return profile

    def batch_classify(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[EmotionProfile]:
        """
        Classify emotions in batch for efficiency.

        Args:
            texts: List of texts
            batch_size: Batch size for inference

        Returns:
            List of EmotionProfile
        """
        if not self._initialized:
            raise RuntimeError("Model not initialized")

        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Tokenize batch
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)

            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            # Process each result
            probs = torch.sigmoid(logits).cpu().numpy()

            for prob_dist in probs:
                emotion_scores = {
                    self._label_mapping[i]: float(prob_dist[i])
                    for i in range(len(prob_dist))
                }

                # Normalize
                total = sum(emotion_scores.values())
                if total > 0:
                    emotion_scores = {k: v / total for k, v in emotion_scores.items()}

                primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]

                arousal = sum(
                    score * self.EMOTION_AROUSAL_VALENCE[emotion][0]
                    for emotion, score in emotion_scores.items()
                )
                valence = sum(
                    score * self.EMOTION_AROUSAL_VALENCE[emotion][1]
                    for emotion, score in emotion_scores.items()
                )

                profile = EmotionProfile(
                    primary_emotion=primary_emotion,
                    emotion_scores=emotion_scores,
                    arousal=float(np.clip(arousal, 0.0, 1.0)),
                    valence=float(np.clip(valence, -1.0, 1.0))
                )

                results.append(profile)

        return results

    def detect_emotional_trajectory(
        self,
        text: str,
        window_size: int = 50
    ) -> List[Tuple[int, EmotionCategory]]:
        """
        Detect emotion changes over text.

        Args:
            text: Full text
            window_size: Character window size for sliding analysis

        Returns:
            List of (char_offset, emotion) tuples
        """
        trajectory = []

        # Sliding window
        for i in range(0, len(text), window_size // 2):  # 50% overlap
            segment = text[i:i + window_size]
            if len(segment) < 20:  # Skip very short segments
                continue

            profile = self.classify_emotion(segment, use_cache=False)
            trajectory.append((i, profile.primary_emotion))

        return trajectory

    def detect_emotional_manipulation_signals(
        self,
        profile: EmotionProfile
    ) -> Dict[str, float]:
        """
        Detect manipulation signals from emotion profile.

        Args:
            profile: EmotionProfile to analyze

        Returns:
            Dict of manipulation indicators
        """
        signals = {}

        # High arousal emotions (fear, anger, excitement)
        high_arousal_emotions = [
            EmotionCategory.FEAR,
            EmotionCategory.ANGER,
            EmotionCategory.EXCITEMENT,
            EmotionCategory.SURPRISE
        ]
        high_arousal_score = sum(
            profile.emotion_scores.get(emotion, 0.0)
            for emotion in high_arousal_emotions
        )
        signals["high_arousal"] = high_arousal_score

        # Negative emotions (anger, fear, disgust)
        negative_emotions = [
            EmotionCategory.ANGER,
            EmotionCategory.FEAR,
            EmotionCategory.DISGUST,
            EmotionCategory.GRIEF,
            EmotionCategory.SADNESS
        ]
        negative_score = sum(
            profile.emotion_scores.get(emotion, 0.0)
            for emotion in negative_emotions
        )
        signals["negative_emotion"] = negative_score

        # Fear + urgency
        fear_urgency = profile.emotion_scores.get(EmotionCategory.FEAR, 0.0)
        signals["fear_appeal"] = fear_urgency

        # Emotional polarization (very high arousal + extreme valence)
        polarization = profile.arousal * abs(profile.valence)
        signals["polarization"] = polarization

        # Emotional inconsistency (mixed high-arousal emotions)
        top_emotions = sorted(
            profile.emotion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        if len(top_emotions) >= 2:
            arousal_variance = np.var([
                self.EMOTION_AROUSAL_VALENCE[e[0]][0] for e in top_emotions
            ])
            signals["emotional_inconsistency"] = float(arousal_variance)

        return signals

    def calculate_manipulation_score(
        self,
        profile: EmotionProfile,
        signals: Dict[str, float]
    ) -> float:
        """
        Calculate overall emotional manipulation score.

        Args:
            profile: EmotionProfile
            signals: Manipulation signals

        Returns:
            Manipulation score (0-1)
        """
        # Weighted combination
        score = (
            signals.get("high_arousal", 0.0) * 0.3 +
            signals.get("negative_emotion", 0.0) * 0.25 +
            signals.get("fear_appeal", 0.0) * 0.25 +
            signals.get("polarization", 0.0) * 0.15 +
            signals.get("emotional_inconsistency", 0.0) * 0.05
        )

        return float(np.clip(score, 0.0, 1.0))


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

bertimbau_classifier = BERTimbauEmotionClassifier(
    device="cuda" if torch.cuda.is_available() else "cpu"
)
