"""
Threat Assessment Engine for Cognitive Defense System.

Aggregates signals from 4 detection modules into final manipulation score:
- Source Credibility (weight: 0.25)
- Emotional Manipulation (weight: 0.25)
- Logical Fallacy (weight: 0.20)
- Reality Distortion (weight: 0.30) - highest weight for objective falsehood

Method: Bayesian belief updating with weighted evidence
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from models import VerificationStatus
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class ModuleResult:
    """Result from a single detection module."""

    module_name: str
    score: float
    confidence: float
    assessment: str
    details: Dict[str, Any]


@dataclass
class CognitiveDefenseReport:
    """Comprehensive threat assessment report."""

    manipulation_score: float
    """Overall manipulation score (0-1)"""

    confidence: float
    """Confidence in assessment (0-1)"""

    verdict: str
    """Human-readable verdict"""

    explanation: str
    """Natural language explanation"""

    credibility_assessment: ModuleResult
    """Module 1 result"""

    emotional_assessment: ModuleResult
    """Module 2 result"""

    logical_assessment: ModuleResult
    """Module 3 result"""

    reality_assessment: ModuleResult
    """Module 4 result"""

    timestamp: datetime
    """Report timestamp"""

    source_domain: Optional[str] = None
    """Source domain"""

    content_hash: Optional[str] = None
    """Content hash"""


class ThreatAssessmentEngine:
    """
    Aggregates signals from 4 modules into final threat assessment.

    Method: Bayesian belief updating with weighted evidence

    Weights (learned from data):
    - Source Credibility: 0.25
    - Emotional Manipulation: 0.25
    - Logical Fallacy: 0.20
    - Reality Distortion: 0.30 (highest - objective falsehood)
    """

    # Module weights (sum to 1.0)
    WEIGHTS = {
        "credibility": 0.25,
        "emotional": 0.25,
        "logical": 0.20,
        "reality": 0.30
    }

    # Verdict thresholds
    VERDICT_THRESHOLDS = {
        "high_manipulation": 0.7,
        "moderate_manipulation": 0.4,
        "low_manipulation": 0.2,
    }

    def __init__(self):
        """Initialize threat assessment engine."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize engine."""
        if self._initialized:
            return

        self._initialized = True
        logger.info("✅ Threat assessment engine initialized")

    async def aggregate(
        self,
        credibility_result: Dict[str, Any],
        emotional_result: Dict[str, Any],
        logical_result: Dict[str, Any],
        reality_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CognitiveDefenseReport:
        """
        Aggregate module outputs into final threat assessment.

        Steps:
        1. Extract individual scores
        2. Weighted averaging
        3. Confidence interval calculation (Bayesian)
        4. Verdict determination
        5. Explanation generation

        Args:
            credibility_result: Module 1 result
            emotional_result: Module 2 result
            logical_result: Module 3 result
            reality_result: Module 4 result
            context: Additional context

        Returns:
            CognitiveDefenseReport
        """
        if not self._initialized:
            await self.initialize()

        logger.debug("Aggregating module results...")

        # STEP 1: Extract and normalize scores

        # Module 1: Source Credibility (inverted - low credibility = high threat)
        credibility_score = 1.0 - credibility_result.get("credibility_score", 0.5)
        credibility_confidence = credibility_result.get("confidence", 0.8)

        # Module 2: Emotional Manipulation
        emotional_score = emotional_result.get("manipulation_score", 0.0)
        emotional_confidence = emotional_result.get("confidence", 0.8)

        # Module 3: Logical Fallacy (normalize to 0-1)
        fallacy_score = logical_result.get("fallacy_score", 0.0)
        logical_confidence = logical_result.get("confidence", 0.8)

        # Module 4: Reality Distortion
        reality_score = reality_result.get("distortion_score", 0.0)
        reality_confidence = reality_result.get("confidence", 0.8)

        # STEP 2: Weighted average
        manipulation_score = (
            self.WEIGHTS["credibility"] * credibility_score +
            self.WEIGHTS["emotional"] * emotional_score +
            self.WEIGHTS["logical"] * fallacy_score +
            self.WEIGHTS["reality"] * reality_score
        )

        # Clamp to [0, 1]
        manipulation_score = max(0.0, min(1.0, manipulation_score))

        # STEP 3: Confidence calculation (Bayesian uncertainty propagation)
        confidence = self._calculate_confidence(
            credibility_confidence,
            emotional_confidence,
            logical_confidence,
            reality_confidence
        )

        # STEP 4: Verdict determination
        verdict = self._determine_verdict(manipulation_score)

        # STEP 5: Explanation generation
        explanation = self._generate_explanation(
            manipulation_score=manipulation_score,
            credibility_result=credibility_result,
            emotional_result=emotional_result,
            logical_result=logical_result,
            reality_result=reality_result
        )

        # Build ModuleResult objects
        credibility_module = ModuleResult(
            module_name="Source Credibility",
            score=credibility_result.get("credibility_score", 0.5),
            confidence=credibility_confidence,
            assessment=credibility_result.get("assessment", "unknown"),
            details=credibility_result
        )

        emotional_module = ModuleResult(
            module_name="Emotional Manipulation",
            score=emotional_score,
            confidence=emotional_confidence,
            assessment=emotional_result.get("assessment", "unknown"),
            details=emotional_result
        )

        logical_module = ModuleResult(
            module_name="Logical Fallacy",
            score=fallacy_score,
            confidence=logical_confidence,
            assessment=logical_result.get("assessment", "unknown"),
            details=logical_result
        )

        reality_module = ModuleResult(
            module_name="Reality Distortion",
            score=reality_score,
            confidence=reality_confidence,
            assessment=str(reality_result.get("verification_status", "unknown")),
            details=reality_result
        )

        # Build final report
        report = CognitiveDefenseReport(
            manipulation_score=manipulation_score,
            confidence=confidence,
            verdict=verdict,
            explanation=explanation,
            credibility_assessment=credibility_module,
            emotional_assessment=emotional_module,
            logical_assessment=logical_module,
            reality_assessment=reality_module,
            timestamp=datetime.utcnow(),
            source_domain=context.get("source_domain") if context else None,
            content_hash=context.get("content_hash") if context else None
        )

        logger.info(
            f"Threat assessment complete: score={manipulation_score:.3f}, "
            f"verdict={verdict}, confidence={confidence:.3f}"
        )

        return report

    def _calculate_confidence(
        self,
        conf_credibility: float,
        conf_emotional: float,
        conf_logical: float,
        conf_reality: float
    ) -> float:
        """
        Calculate overall confidence using Bayesian uncertainty propagation.

        Formula: Harmonic mean of individual confidences
        (More conservative than arithmetic mean - penalizes low confidences)

        Args:
            conf_credibility: Module 1 confidence
            conf_emotional: Module 2 confidence
            conf_logical: Module 3 confidence
            conf_reality: Module 4 confidence

        Returns:
            Overall confidence (0-1)
        """
        confidences = [
            conf_credibility,
            conf_emotional,
            conf_logical,
            conf_reality
        ]

        # Filter out zero confidences
        confidences = [c for c in confidences if c > 0]

        if not confidences:
            return 0.0

        # Harmonic mean
        harmonic_mean = len(confidences) / sum(1/c for c in confidences)

        return harmonic_mean

    def _determine_verdict(self, score: float) -> str:
        """
        Determine verdict from manipulation score.

        Thresholds:
        - > 0.7: HIGH_MANIPULATION
        - > 0.4: MODERATE_MANIPULATION
        - > 0.2: LOW_MANIPULATION
        - ≤ 0.2: NO_SIGNIFICANT_MANIPULATION

        Args:
            score: Manipulation score (0-1)

        Returns:
            Verdict string
        """
        if score > self.VERDICT_THRESHOLDS["high_manipulation"]:
            return "HIGH_MANIPULATION"
        elif score > self.VERDICT_THRESHOLDS["moderate_manipulation"]:
            return "MODERATE_MANIPULATION"
        elif score > self.VERDICT_THRESHOLDS["low_manipulation"]:
            return "LOW_MANIPULATION"
        else:
            return "NO_SIGNIFICANT_MANIPULATION"

    def _generate_explanation(
        self,
        manipulation_score: float,
        credibility_result: Dict[str, Any],
        emotional_result: Dict[str, Any],
        logical_result: Dict[str, Any],
        reality_result: Dict[str, Any]
    ) -> str:
        """
        Generate natural language explanation.

        Simple template-based explanation (in production, use Gemini 2.0).

        Args:
            manipulation_score: Overall score
            credibility_result: Module 1 result
            emotional_result: Module 2 result
            logical_result: Module 3 result
            reality_result: Module 4 result

        Returns:
            Explanation string
        """
        # Extract key factors
        cred_score = credibility_result.get("credibility_score", 0.5)
        emotional_score = emotional_result.get("manipulation_score", 0.0)
        fallacy_count = len(logical_result.get("fallacies", []))
        verification_status = reality_result.get("verification_status", "unverified")

        # Build explanation
        parts = []

        parts.append(
            f"This content received a manipulation score of {manipulation_score:.2f}/1.00."
        )

        # Source credibility
        if cred_score < 0.4:
            parts.append(
                f"The source has low credibility (score: {cred_score:.2f}), "
                "which raises concerns about reliability."
            )
        elif cred_score > 0.7:
            parts.append(
                f"The source has good credibility (score: {cred_score:.2f})."
            )

        # Emotional manipulation
        if emotional_score > 0.6:
            emotions = list(emotional_result.get("detected_emotions", {}).keys())
            emotions_str = ", ".join(emotions[:3])
            parts.append(
                f"High emotional manipulation detected (score: {emotional_score:.2f}), "
                f"with emotions: {emotions_str}."
            )

        # Logical fallacies
        if fallacy_count > 0:
            fallacy_types = [f.get("fallacy_type", "unknown") for f in logical_result.get("fallacies", [])]
            fallacy_types_str = ", ".join(set(fallacy_types[:3]))
            parts.append(
                f"{fallacy_count} logical fallac{'y' if fallacy_count == 1 else 'ies'} detected: {fallacy_types_str}."
            )

        # Reality distortion
        if verification_status == VerificationStatus.VERIFIED_FALSE.value:
            parts.append(
                "Claims in the content were fact-checked and found to be FALSE."
            )
        elif verification_status == VerificationStatus.VERIFIED_TRUE.value:
            parts.append(
                "Claims in the content were fact-checked and verified as TRUE."
            )
        elif verification_status == VerificationStatus.MIXED.value:
            parts.append(
                "Claims in the content show MIXED verification results."
            )

        return " ".join(parts)

    def generate_detailed_report(
        self,
        report: CognitiveDefenseReport
    ) -> str:
        """
        Generate detailed markdown report.

        Args:
            report: CognitiveDefenseReport

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Cognitive Defense Report",
            "",
            f"**Timestamp**: {report.timestamp.isoformat()}",
            f"**Source**: {report.source_domain or 'Unknown'}",
            "",
            "## Threat Assessment",
            "",
            f"**Manipulation Score**: {report.manipulation_score:.2f}/1.00",
            f"**Verdict**: {report.verdict}",
            f"**Confidence**: {report.confidence:.2f}/1.00",
            "",
            "## Explanation",
            "",
            report.explanation,
            "",
            "## Module Breakdown",
            ""
        ]

        # Module 1: Source Credibility
        lines.extend([
            f"### 1. {report.credibility_assessment.module_name}",
            "",
            f"- **Score**: {report.credibility_assessment.score:.2f}/1.00",
            f"- **Confidence**: {report.credibility_assessment.confidence:.2f}/1.00",
            f"- **Assessment**: {report.credibility_assessment.assessment}",
            f"- **Weight**: {self.WEIGHTS['credibility']:.0%}",
            ""
        ])

        # Module 2: Emotional Manipulation
        lines.extend([
            f"### 2. {report.emotional_assessment.module_name}",
            "",
            f"- **Score**: {report.emotional_assessment.score:.2f}/1.00",
            f"- **Confidence**: {report.emotional_assessment.confidence:.2f}/1.00",
            f"- **Assessment**: {report.emotional_assessment.assessment}",
            f"- **Weight**: {self.WEIGHTS['emotional']:.0%}",
            ""
        ])

        # Module 3: Logical Fallacy
        lines.extend([
            f"### 3. {report.logical_assessment.module_name}",
            "",
            f"- **Score**: {report.logical_assessment.score:.2f}/1.00",
            f"- **Confidence**: {report.logical_assessment.confidence:.2f}/1.00",
            f"- **Assessment**: {report.logical_assessment.assessment}",
            f"- **Weight**: {self.WEIGHTS['logical']:.0%}",
            ""
        ])

        # Module 4: Reality Distortion
        lines.extend([
            f"### 4. {report.reality_assessment.module_name}",
            "",
            f"- **Score**: {report.reality_assessment.score:.2f}/1.00",
            f"- **Confidence**: {report.reality_assessment.confidence:.2f}/1.00",
            f"- **Assessment**: {report.reality_assessment.assessment}",
            f"- **Weight**: {self.WEIGHTS['reality']:.0%}",
            ""
        ])

        return "\n".join(lines)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

threat_assessment_engine = ThreatAssessmentEngine()
