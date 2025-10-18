"""
Verdict Calculator - Calculates wargaming verdicts from evidence.

Verdict Logic:
- SUCCESS: Exploit works before patch + fails after patch
- FAILURE: Exploit fails before patch (can't reproduce vulnerability)
- PARTIAL: Exploit works before + works after (patch doesn't fix)
- INCONCLUSIVE: Unexpected behavior or errors

Confidence Scoring:
- Based on exit code match, workflow success, execution time
- Adjusted by anomaly detection (timeouts, errors)
"""

import logging
from typing import List, Tuple

from pydantic import BaseModel, Field

from .evidence_collector import WargameEvidence

logger = logging.getLogger(__name__)


class VerdictScore(BaseModel):
    """Verdict with confidence score."""

    verdict: str  # "success", "failure", "partial", "inconclusive"
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)
    should_trigger_hitl: bool = False  # Whether to escalate to human review


class VerdictCalculator:
    """
    Calculates wargaming verdicts from evidence.

    Verdict Types:
    - SUCCESS: Patch fixes vulnerability (exploit before=1, after=0)
    - FAILURE: Can't reproduce vulnerability (exploit before≠1)
    - PARTIAL: Vulnerability persists after patch (exploit before=1, after=1)
    - INCONCLUSIVE: Unexpected behavior, errors, or timeouts

    Confidence Factors:
    - Exit code match (+30%)
    - Workflow completion (+20%)
    - No anomalies (+20%)
    - Execution time normal (+15%)
    - Steps completed (+15%)
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        hitl_threshold: float = 0.6,
    ):
        """
        Initialize verdict calculator.

        Args:
            confidence_threshold: Minimum confidence for auto-merge
            hitl_threshold: Confidence below this triggers HITL review
        """
        self.confidence_threshold = confidence_threshold
        self.hitl_threshold = hitl_threshold

        logger.info(
            f"VerdictCalculator initialized: "
            f"confidence_threshold={confidence_threshold}, "
            f"hitl_threshold={hitl_threshold}"
        )

    def calculate_verdict(self, evidence: WargameEvidence) -> VerdictScore:
        """
        Calculate verdict from evidence.

        Args:
            evidence: WargameEvidence bundle

        Returns:
            VerdictScore with verdict, confidence, reasoning
        """
        logger.info(
            f"Calculating verdict for {evidence.apv_code}: "
            f"exit_before={evidence.exploit_exit_before}, "
            f"exit_after={evidence.exploit_exit_after}"
        )

        # Determine base verdict from exit codes
        base_verdict = self._determine_base_verdict(
            exploit_exit_before=evidence.exploit_exit_before,
            exploit_exit_after=evidence.exploit_exit_after,
            expected_exit_before=evidence.expected_exit_before,
            expected_exit_after=evidence.expected_exit_after,
        )

        # Calculate confidence score
        confidence, reasoning = self._calculate_confidence(
            evidence, base_verdict
        )

        # Detect anomalies
        anomalies = self._detect_anomalies(evidence)

        # Adjust confidence based on anomalies
        adjusted_confidence = confidence
        if anomalies:
            penalty = min(0.3, len(anomalies) * 0.1)
            adjusted_confidence = max(0.0, confidence - penalty)
            reasoning.append(
                f"Confidence reduced by {penalty:.0%} due to {len(anomalies)} anomalies"
            )

        # Determine if HITL review needed
        should_trigger_hitl = self._should_trigger_hitl(
            base_verdict, adjusted_confidence, anomalies
        )

        verdict_score = VerdictScore(
            verdict=base_verdict,
            confidence=adjusted_confidence,
            reasoning=reasoning,
            anomalies=anomalies,
            should_trigger_hitl=should_trigger_hitl,
        )

        logger.info(
            f"Verdict calculated: {base_verdict} "
            f"(confidence={adjusted_confidence:.2%}, hitl={should_trigger_hitl})"
        )

        return verdict_score

    def _determine_base_verdict(
        self,
        exploit_exit_before: int,
        exploit_exit_after: int,
        expected_exit_before: int,
        expected_exit_after: int,
    ) -> str:
        """Determine base verdict from exit codes."""
        # Perfect match: SUCCESS
        if (
            exploit_exit_before == expected_exit_before
            and exploit_exit_after == expected_exit_after
        ):
            logger.debug("Base verdict: SUCCESS (perfect exit code match)")
            return "success"

        # Exploit works before but not after: PARTIAL
        if exploit_exit_before == expected_exit_before:
            if exploit_exit_after == exploit_exit_before:
                logger.debug("Base verdict: PARTIAL (exploit still works after patch)")
                return "partial"
            else:
                logger.debug(
                    "Base verdict: INCONCLUSIVE (exploit before works, after unexpected)"
                )
                return "inconclusive"

        # Can't reproduce exploit: FAILURE
        if exploit_exit_before != expected_exit_before:
            logger.debug("Base verdict: FAILURE (can't reproduce vulnerability)")
            return "failure"

        # Default: INCONCLUSIVE
        logger.debug("Base verdict: INCONCLUSIVE (unexpected behavior)")
        return "inconclusive"

    def _calculate_confidence(
        self, evidence: WargameEvidence, verdict: str
    ) -> Tuple[float, List[str]]:
        """Calculate confidence score with reasoning."""
        confidence = 0.0
        reasoning = []

        # Factor 1: Exit code match (30%)
        exit_code_match = (
            evidence.exploit_exit_before == evidence.expected_exit_before
            and evidence.exploit_exit_after == evidence.expected_exit_after
        )

        if exit_code_match:
            confidence += 0.30
            reasoning.append("✅ Exit codes match expected values (+30%)")
        else:
            reasoning.append("❌ Exit codes don't match expected values (+0%)")

        # Factor 2: Workflow completion (20%)
        workflow_completed = (
            evidence.workflow_evidence.status == "completed"
            and evidence.workflow_evidence.conclusion in ["success", "failure"]
        )

        if workflow_completed:
            confidence += 0.20
            reasoning.append("✅ Workflow completed successfully (+20%)")
        else:
            reasoning.append(
                f"⚠️ Workflow status: {evidence.workflow_evidence.status} (+0%)"
            )

        # Factor 3: Key steps executed (20%)
        key_steps = [
            "test_before",
            "test_after",
            "collect_evidence",
        ]

        executed_steps = sum(
            1
            for step in evidence.workflow_evidence.steps
            if any(key in step.step_name.lower() for key in key_steps)
        )

        if executed_steps >= len(key_steps):
            confidence += 0.20
            reasoning.append(f"✅ All {len(key_steps)} key steps executed (+20%)")
        else:
            partial_credit = (executed_steps / len(key_steps)) * 0.20
            confidence += partial_credit
            reasoning.append(
                f"⚠️ Only {executed_steps}/{len(key_steps)} key steps executed (+{partial_credit:.0%})"
            )

        # Factor 4: Execution time reasonable (15%)
        if evidence.workflow_evidence.duration_seconds:
            duration = evidence.workflow_evidence.duration_seconds
            # Reasonable if between 10s and 300s (5 minutes)
            if 10 <= duration <= 300:
                confidence += 0.15
                reasoning.append(
                    f"✅ Execution time reasonable ({duration:.0f}s) (+15%)"
                )
            else:
                reasoning.append(
                    f"⚠️ Execution time unusual ({duration:.0f}s) (+0%)"
                )
        else:
            reasoning.append("⚠️ Execution time unknown (+0%)")

        # Factor 5: Verdict consistency (15%)
        # SUCCESS should have completed workflow
        # FAILURE/PARTIAL/INCONCLUSIVE might have issues
        if verdict == "success" and workflow_completed:
            confidence += 0.15
            reasoning.append("✅ Verdict consistent with workflow state (+15%)")
        elif verdict in ["failure", "inconclusive"]:
            # Don't penalize for expected inconsistencies
            confidence += 0.10
            reasoning.append(
                "➖ Verdict indicates issues (no penalty) (+10%)"
            )
        else:
            reasoning.append("⚠️ Verdict/workflow state mismatch (+0%)")

        return confidence, reasoning

    def _detect_anomalies(self, evidence: WargameEvidence) -> List[str]:
        """Detect anomalies in evidence."""
        anomalies = []

        # Anomaly 1: Workflow cancelled or timed out
        if evidence.workflow_evidence.conclusion in ["cancelled", "timed_out"]:
            anomalies.append(
                f"Workflow {evidence.workflow_evidence.conclusion}"
            )

        # Anomaly 2: Very short execution (< 5 seconds)
        if evidence.workflow_evidence.duration_seconds:
            if evidence.workflow_evidence.duration_seconds < 5:
                anomalies.append(
                    f"Suspiciously short execution ({evidence.workflow_evidence.duration_seconds:.1f}s)"
                )

        # Anomaly 3: Exit codes are error codes (≥ 100)
        if evidence.exploit_exit_before >= 100 or evidence.exploit_exit_after >= 100:
            anomalies.append(
                f"Exit codes indicate errors (before={evidence.exploit_exit_before}, after={evidence.exploit_exit_after})"
            )

        # Anomaly 4: Missing key steps
        step_names = [
            step.step_name.lower() for step in evidence.workflow_evidence.steps
        ]
        if "test" not in " ".join(step_names):
            anomalies.append("Missing test steps")

        # Anomaly 5: No artifact data
        if not evidence.artifact_data:
            anomalies.append("No artifact data collected")

        return anomalies

    def _should_trigger_hitl(
        self, verdict: str, confidence: float, anomalies: List[str]
    ) -> bool:
        """Determine if HITL review should be triggered."""
        # Always trigger HITL for low confidence
        if confidence < self.hitl_threshold:
            logger.info(
                f"Triggering HITL: low confidence ({confidence:.2%} < {self.hitl_threshold:.2%})"
            )
            return True

        # Trigger HITL for PARTIAL verdicts (patch doesn't fix vulnerability)
        if verdict == "partial":
            logger.info("Triggering HITL: partial verdict (patch ineffective)")
            return True

        # Trigger HITL if multiple anomalies detected
        if len(anomalies) >= 3:
            logger.info(
                f"Triggering HITL: multiple anomalies ({len(anomalies)} detected)"
            )
            return True

        # Trigger HITL for FAILURE verdicts with moderate confidence
        # (can't reproduce vulnerability - might be false positive APV)
        if verdict == "failure" and confidence < 0.8:
            logger.info(
                f"Triggering HITL: failure verdict with moderate confidence ({confidence:.2%})"
            )
            return True

        logger.debug("No HITL trigger: verdict acceptable")
        return False

    def should_auto_merge(self, verdict_score: VerdictScore) -> bool:
        """
        Determine if PR should be auto-merged.

        Args:
            verdict_score: VerdictScore

        Returns:
            True if safe to auto-merge
        """
        # Must be SUCCESS verdict
        if verdict_score.verdict != "success":
            return False

        # Must have high confidence
        if verdict_score.confidence < self.confidence_threshold:
            return False

        # Must not have HITL trigger
        if verdict_score.should_trigger_hitl:
            return False

        # Must not have critical anomalies
        critical_keywords = ["cancelled", "timed_out", "error"]
        for anomaly in verdict_score.anomalies:
            if any(keyword in anomaly.lower() for keyword in critical_keywords):
                return False

        logger.info(
            f"Auto-merge approved: {verdict_score.verdict} "
            f"(confidence={verdict_score.confidence:.2%})"
        )
        return True
