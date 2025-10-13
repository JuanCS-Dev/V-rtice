"""
Confirmation Engine - Orchestrates vulnerability confirmation.

Combines static and dynamic analysis results to produce a final confirmation score.
Implements false positive detection and adaptive thresholds.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .static_analyzer import StaticAnalyzer, StaticAnalysisResult
from .dynamic_analyzer import DynamicAnalyzer, DynamicAnalysisResult

logger = logging.getLogger(__name__)


class ConfirmationResult(BaseModel):
    """Final confirmation result combining all analyses."""

    apv_id: str
    cve_id: str
    confirmed: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    confirmation_method: str  # "static", "dynamic", "hybrid"

    # Component scores
    static_confidence: float = Field(ge=0.0, le=1.0)
    dynamic_confidence: float = Field(ge=0.0, le=1.0)

    # Analysis results
    static_result: Optional[StaticAnalysisResult] = None
    dynamic_result: Optional[DynamicAnalysisResult] = None

    # False positive detection
    false_positive_probability: float = Field(ge=0.0, le=1.0, default=0.0)
    false_positive_indicators: List[str] = Field(default_factory=list)

    # Metadata
    confirmation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_duration_seconds: float
    recommendation: str  # "patch", "investigate", "ignore"


class ConfirmationEngine:
    """
    Orchestrates vulnerability confirmation process.

    Features:
    - Multi-stage confirmation (static → dynamic)
    - Adaptive thresholds based on severity
    - False positive detection
    - Confidence score aggregation
    - Recommendation generation
    """

    # Confirmation thresholds by severity
    THRESHOLDS = {
        "critical": 0.6,  # Lower threshold for critical (err on safe side)
        "high": 0.7,
        "medium": 0.75,
        "low": 0.8,
    }

    def __init__(
        self,
        static_analyzer: StaticAnalyzer,
        dynamic_analyzer: Optional[DynamicAnalyzer] = None,
        enable_dynamic: bool = True,
    ):
        """
        Initialize confirmation engine.

        Args:
            static_analyzer: StaticAnalyzer instance
            dynamic_analyzer: Optional DynamicAnalyzer instance
            enable_dynamic: Enable dynamic analysis (slower but more accurate)
        """
        self.static_analyzer = static_analyzer
        self.dynamic_analyzer = dynamic_analyzer
        self.enable_dynamic = enable_dynamic

        logger.info(
            f"ConfirmationEngine initialized: dynamic={enable_dynamic}"
        )

    async def confirm_apv(
        self,
        apv_id: str,
        cve_id: str,
        severity: str,
        vulnerable_code_signature: Optional[str],
        vulnerable_code_type: Optional[str],
        affected_files: List[str],
        cwe_ids: List[str],
        dependency_name: str,
        dependency_version: str,
        dependency_ecosystem: str,
    ) -> ConfirmationResult:
        """
        Confirm vulnerability using multi-stage analysis.

        Args:
            apv_id: APV identifier
            cve_id: CVE identifier
            severity: Severity level (critical, high, medium, low)
            vulnerable_code_signature: Code pattern to search for
            vulnerable_code_type: Signature type
            affected_files: List of affected files
            cwe_ids: CWE identifiers
            dependency_name: Package name
            dependency_version: Package version
            dependency_ecosystem: Ecosystem

        Returns:
            ConfirmationResult with final verdict
        """
        import time
        start_time = time.time()

        logger.info(
            f"🔬 Starting confirmation for APV: {apv_id} ({cve_id}) - severity={severity}"
        )

        # Stage 1: Static Analysis (always run)
        static_result = self.static_analyzer.analyze_apv(
            apv_id=apv_id,
            cve_id=cve_id,
            vulnerable_code_signature=vulnerable_code_signature,
            vulnerable_code_type=vulnerable_code_type,
            affected_files=affected_files,
            cwe_ids=cwe_ids,
        )

        static_confidence = static_result.confidence_score
        logger.info(f"Static analysis: confidence={static_confidence:.2f}")

        # Stage 2: Dynamic Analysis (conditional)
        dynamic_result = None
        dynamic_confidence = 0.0

        # Run dynamic analysis if:
        # 1. Enabled globally
        # 2. Static analysis is inconclusive (0.4 < confidence < 0.85)
        # 3. Severity is high or critical
        should_run_dynamic = (
            self.enable_dynamic
            and self.dynamic_analyzer
            and (
                (0.4 < static_confidence < 0.85)
                or severity in ["critical", "high"]
            )
        )

        if should_run_dynamic:
            logger.info("Running dynamic analysis for additional confirmation...")
            dynamic_result = await self.dynamic_analyzer.analyze_apv(
                apv_id=apv_id,
                cve_id=cve_id,
                dependency_name=dependency_name,
                dependency_version=dependency_version,
                dependency_ecosystem=dependency_ecosystem,
                vulnerable_code_signature=vulnerable_code_signature,
                cwe_ids=cwe_ids,
            )
            dynamic_confidence = dynamic_result.confidence_score
            logger.info(f"Dynamic analysis: confidence={dynamic_confidence:.2f}")

        # Stage 3: Aggregate scores
        final_confidence = self._aggregate_confidence(
            static_confidence, dynamic_confidence, severity
        )

        # Stage 4: False positive detection
        false_positive_prob, fp_indicators = self._detect_false_positive(
            static_result, dynamic_result, severity
        )

        # Adjust confidence based on false positive probability
        adjusted_confidence = final_confidence * (1.0 - false_positive_prob)

        # Stage 5: Determine confirmation
        threshold = self.THRESHOLDS.get(severity.lower(), 0.7)
        confirmed = adjusted_confidence >= threshold

        # Stage 6: Generate recommendation
        recommendation = self._generate_recommendation(
            confirmed, adjusted_confidence, severity, false_positive_prob
        )

        # Determine confirmation method
        if dynamic_result:
            method = "hybrid"
        else:
            method = "static"

        duration = time.time() - start_time

        logger.info(
            f"✅ Confirmation complete: "
            f"confirmed={confirmed}, confidence={adjusted_confidence:.2f}, "
            f"method={method}, recommendation={recommendation}, "
            f"duration={duration:.1f}s"
        )

        return ConfirmationResult(
            apv_id=apv_id,
            cve_id=cve_id,
            confirmed=confirmed,
            confidence_score=adjusted_confidence,
            confirmation_method=method,
            static_confidence=static_confidence,
            dynamic_confidence=dynamic_confidence,
            static_result=static_result,
            dynamic_result=dynamic_result,
            false_positive_probability=false_positive_prob,
            false_positive_indicators=fp_indicators,
            total_duration_seconds=duration,
            recommendation=recommendation,
        )

    def _aggregate_confidence(
        self, static_conf: float, dynamic_conf: float, severity: str
    ) -> float:
        """
        Aggregate static and dynamic confidence scores.

        Strategy:
        - If only static: use static score
        - If both: weighted average (dynamic weighted higher for critical)
        - Critical vulnerabilities: 40% static, 60% dynamic
        - Other severities: 50% static, 50% dynamic

        Args:
            static_conf: Static analysis confidence
            dynamic_conf: Dynamic analysis confidence
            severity: Severity level

        Returns:
            Aggregated confidence score
        """
        if dynamic_conf == 0.0:
            # Only static analysis available
            return static_conf

        # Weighted average
        if severity.lower() == "critical":
            # Trust dynamic analysis more for critical
            return static_conf * 0.4 + dynamic_conf * 0.6
        else:
            # Equal weight for other severities
            return static_conf * 0.5 + dynamic_conf * 0.5

    def _detect_false_positive(
        self,
        static_result: StaticAnalysisResult,
        dynamic_result: Optional[DynamicAnalysisResult],
        severity: str,
    ) -> tuple[float, List[str]]:
        """
        Detect false positive probability.

        Indicators:
        - Static and dynamic disagree significantly
        - Low number of findings
        - Low severity findings only
        - Single tool detection (no corroboration)
        - High false positive rate for specific CWEs

        Args:
            static_result: Static analysis result
            dynamic_result: Optional dynamic analysis result
            severity: Severity level

        Returns:
            Tuple of (false_positive_probability, indicators)
        """
        fp_probability = 0.0
        indicators = []

        # Indicator 1: Static-Dynamic disagreement
        if dynamic_result:
            if static_result.confirmed and not dynamic_result.confirmed:
                fp_probability += 0.3
                indicators.append("Static confirmed but dynamic did not")
            elif (
                abs(static_result.confidence_score - dynamic_result.confidence_score)
                > 0.4
            ):
                fp_probability += 0.2
                indicators.append("Large confidence disagreement between static/dynamic")

        # Indicator 2: Low finding count
        if len(static_result.findings) <= 1:
            fp_probability += 0.15
            indicators.append("Single finding only")

        # Indicator 3: Low severity only
        if all(f.severity in ["low", "info"] for f in static_result.findings):
            fp_probability += 0.2
            indicators.append("All findings are low severity")

        # Indicator 4: Single tool detection
        if len(static_result.tools_used) == 1:
            fp_probability += 0.1
            indicators.append("Single tool detection (no corroboration)")

        # Indicator 5: High error rate
        if static_result.error_messages:
            fp_probability += 0.1
            indicators.append("Analysis errors occurred")

        # Cap at 0.9 (never 100% sure it's false positive)
        fp_probability = min(fp_probability, 0.9)

        return fp_probability, indicators

    def _generate_recommendation(
        self,
        confirmed: bool,
        confidence: float,
        severity: str,
        false_positive_prob: float,
    ) -> str:
        """
        Generate recommendation based on confirmation results.

        Args:
            confirmed: Whether vulnerability is confirmed
            confidence: Confidence score
            severity: Severity level
            false_positive_prob: False positive probability

        Returns:
            Recommendation string
        """
        if not confirmed:
            if confidence > 0.5:
                return "investigate"  # Borderline, needs manual review
            else:
                return "ignore"  # Low confidence, likely false positive

        # Confirmed vulnerability
        if false_positive_prob > 0.5:
            return "investigate"  # High FP probability, verify manually

        if severity in ["critical", "high"]:
            return "patch"  # High severity, patch immediately

        if confidence > 0.85:
            return "patch"  # High confidence, patch

        return "investigate"  # Medium confidence, review before patching

    def get_confirmation_stats(
        self, results: List[ConfirmationResult]
    ) -> Dict[str, any]:
        """
        Calculate statistics from confirmation results.

        Args:
            results: List of ConfirmationResult instances

        Returns:
            Dictionary with statistics
        """
        if not results:
            return {}

        confirmed_count = sum(1 for r in results if r.confirmed)
        false_positive_count = sum(1 for r in results if r.false_positive_probability > 0.5)

        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        avg_static_conf = sum(r.static_confidence for r in results) / len(results)

        dynamic_results = [r for r in results if r.dynamic_result]
        avg_dynamic_conf = (
            sum(r.dynamic_confidence for r in dynamic_results) / len(dynamic_results)
            if dynamic_results
            else 0.0
        )

        recommendations = {}
        for result in results:
            recommendations[result.recommendation] = (
                recommendations.get(result.recommendation, 0) + 1
            )

        return {
            "total_analyzed": len(results),
            "confirmed_count": confirmed_count,
            "false_positive_count": false_positive_count,
            "confirmation_rate": confirmed_count / len(results),
            "avg_confidence_score": avg_confidence,
            "avg_static_confidence": avg_static_conf,
            "avg_dynamic_confidence": avg_dynamic_conf,
            "dynamic_analysis_used": len(dynamic_results),
            "recommendations": recommendations,
        }
