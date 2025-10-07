"""Maximus Narrative Manipulation Filter - Emotional Manipulation Detector.

This module implements an Emotional Manipulation Detector for the Maximus AI's
Narrative Manipulation Filter. It is responsible for identifying linguistic
patterns, rhetorical devices, and psychological triggers within textual content
that are designed to evoke strong emotions and bypass rational thought.

Key functionalities include:
- Analyzing sentiment, tone, and emotional vocabulary.
- Detecting appeals to fear, anger, pity, or other strong emotions.
- Identifying loaded language, hyperbole, and other manipulative rhetorical techniques.
- Quantifying the presence and intensity of emotional manipulation.

This detector is crucial for protecting the AI's decision-making processes from
being swayed by emotionally charged but logically unsound information, ensuring
that its responses are based on objective analysis rather than subjective influence.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional


class EmotionalManipulationDetector:
    """Identifies linguistic patterns, rhetorical devices, and psychological triggers
    within textual content that are designed to evoke strong emotions and bypass
    rational thought.

    Analyzes sentiment, tone, emotional vocabulary, and detects appeals to fear,
    anger, pity, or other strong emotions.
    """

    def __init__(self):
        """Initializes the EmotionalManipulationDetector with emotional keywords."""
        self.emotional_keywords: Dict[str, List[str]] = {
            "fear": ["terror", "danger", "threat", "catastrophe", "panic"],
            "anger": ["outrage", "fury", "disgust", "unacceptable", "blame"],
            "pity": ["victim", "suffering", "tragedy", "helpless", "poor"],
            "hope": ["future", "opportunity", "progress", "solution", "dream"],
        }
        self.detection_history: List[Dict[str, Any]] = []
        self.last_detection_time: Optional[datetime] = None
        self.current_status: str = "ready_to_detect"

    def detect(self, content: str) -> Dict[str, Any]:
        """Detects emotional manipulation within textual content.

        Args:
            content (str): The text content to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the detection results.
        """
        print(
            f"[EmotionalManipulationDetector] Detecting emotional manipulation in content (length: {len(content)})..."
        )

        emotional_score = 0.0
        detected_emotions: Dict[str, int] = {
            emotion: 0 for emotion in self.emotional_keywords.keys()
        }
        indicators: List[str] = []
        assessment = "No significant emotional manipulation detected."

        content_lower = content.lower()

        for emotion, keywords in self.emotional_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    detected_emotions[emotion] += content_lower.count(keyword)
                    indicators.append(f"{emotion}_keyword_match:{keyword}")

        # Simple scoring based on keyword counts
        total_emotional_keywords = sum(detected_emotions.values())
        if total_emotional_keywords > 0:
            emotional_score = min(1.0, total_emotional_keywords / 10.0)  # Scale to 0-1

        if emotional_score > 0.6:
            assessment = "High likelihood of emotional manipulation."
        elif emotional_score > 0.3:
            assessment = "Moderate signs of emotional manipulation."

        detection_result = {
            "timestamp": datetime.now().isoformat(),
            "emotional_score": emotional_score,
            "detected_emotions": detected_emotions,
            "indicators": indicators,
            "assessment": assessment,
        }
        self.detection_history.append(detection_result)
        self.last_detection_time = datetime.now()

        return detection_result

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Emotional Manipulation Detector.

        Returns:
            Dict[str, Any]: A dictionary summarizing the Detector's status.
        """
        return {
            "status": self.current_status,
            "total_detections": len(self.detection_history),
            "last_detection": (
                self.last_detection_time.isoformat()
                if self.last_detection_time
                else "N/A"
            ),
            "known_emotional_categories": list(self.emotional_keywords.keys()),
        }
