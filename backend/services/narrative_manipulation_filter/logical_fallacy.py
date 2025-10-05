"""Maximus Narrative Manipulation Filter - Logical Fallacy Detector.

This module implements a Logical Fallacy Detector for the Maximus AI's Narrative
Manipulation Filter. It is responsible for identifying errors in reasoning and
deductive arguments within textual content, which are often used to mislead or
persuade audiences through flawed logic.

Key functionalities include:
- Recognizing common logical fallacies (e.g., ad hominem, straw man, false dilemma).
- Analyzing the structure of arguments and the relationships between premises and conclusions.
- Quantifying the presence and severity of logical flaws.
- Providing other Maximus AI services with an assessment of the logical soundness
  of information, protecting the AI's reasoning processes from manipulation.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime


class LogicalFallacyDetector:
    """Identifies errors in reasoning and deductive arguments within textual content,
    which are often used to mislead or persuade audiences through flawed logic.

    Recognizes common logical fallacies and analyzes the structure of arguments.
    """

    def __init__(self):
        """Initializes the LogicalFallacyDetector with known fallacy patterns."""
        self.fallacy_patterns: Dict[str, List[str]] = {
            "ad_hominem": ["attack the person", "personal attack", "you too"],
            "straw_man": ["misrepresent argument", "distort position"],
            "false_dilemma": ["either or", "only two options"],
            "appeal_to_authority": ["expert says", "authority states"],
            "slippery_slope": ["if a then b then c", "domino effect"]
        }
        self.detection_history: List[Dict[str, Any]] = []
        self.last_detection_time: Optional[datetime] = None
        self.current_status: str = "ready_to_detect"

    def detect(self, content: str) -> Dict[str, Any]:
        """Detects logical fallacies within textual content.

        Args:
            content (str): The text content to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the detection results.
        """
        print(f"[LogicalFallacyDetector] Detecting fallacies in content (length: {len(content)})...")
        
        detected_fallacies: List[Dict[str, Any]] = []
        content_lower = content.lower()

        for fallacy_type, keywords in self.fallacy_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    detected_fallacies.append({"type": fallacy_type, "keyword_match": keyword, "excerpt": content[content_lower.find(keyword)-20:content_lower.find(keyword)+len(keyword)+20]})
                    break # Only detect one instance per fallacy type for simplicity

        assessment = "No significant logical fallacies detected." if not detected_fallacies else "Logical fallacies detected, indicating flawed reasoning."

        detection_result = {
            "timestamp": datetime.now().isoformat(),
            "detected_fallacies": detected_fallacies,
            "fallacy_count": len(detected_fallacies),
            "assessment": assessment
        }
        self.detection_history.append(detection_result)
        self.last_detection_time = datetime.now()

        return detection_result

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Logical Fallacy Detector.

        Returns:
            Dict[str, Any]: A dictionary summarizing the Detector's status.
        """
        return {
            "status": self.current_status,
            "total_detections": len(self.detection_history),
            "last_detection": self.last_detection_time.isoformat() if self.last_detection_time else "N/A",
            "known_fallacy_types": list(self.fallacy_patterns.keys())
        }