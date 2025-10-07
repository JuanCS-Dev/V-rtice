"""
Executive Controller for Cognitive Defense System.

Prefrontal cortex-inspired orchestrator that integrates:
- Cognitive Control (attention allocation, adversarial filtering)
- Working Memory (context management)
- 4 Detection Modules (credibility, emotional, logical, reality)
- Threat Assessment (Bayesian aggregation)

Master pipeline for comprehensive manipulation detection.
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, Optional

from cognitive_control_layer import cognitive_control, ProcessingMode
from config import get_settings
from emotional_manipulation_module import emotional_manipulation_module
from logical_fallacy_module import logical_fallacy_module
from reality_distortion_module import ProcessingMode as RealityMode
from reality_distortion_module import (
    reality_distortion_module,
)
from source_credibility_module import source_credibility_module
from threat_assessment_engine import threat_assessment_engine
from utils import hash_text
from working_memory_system import working_memory

logger = logging.getLogger(__name__)

settings = get_settings()


class ExecutiveController:
    """
    Orchestrates the complete cognitive defense pipeline.

    Pipeline:
    1. Input sanitization (adversarial filtering)
    2. Mode determination (attention allocation)
    3. Context loading (working memory)
    4. Parallel module execution (4 modules)
    5. Result aggregation (Bayesian)
    6. Report generation and persistence
    """

    def __init__(self):
        """Initialize executive controller."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all subsystems."""
        if self._initialized:
            logger.warning("Executive controller already initialized")
            return

        try:
            logger.info("🚀 Initializing Cognitive Defense System...")

            # Initialize subsystems in parallel
            await asyncio.gather(
                cognitive_control.initialize(),
                working_memory.initialize(),
                source_credibility_module.initialize(),
                emotional_manipulation_module.initialize(),
                logical_fallacy_module.initialize(),
                reality_distortion_module.initialize(
                    enable_tier2=True, start_tier2_workers=False
                ),
                threat_assessment_engine.initialize(),
            )

            self._initialized = True
            logger.info("✅ Cognitive Defense System initialized")

        except Exception as e:
            logger.error(
                f"❌ Failed to initialize executive controller: {e}", exc_info=True
            )
            raise

    async def analyze(
        self,
        content: str,
        source_info: Optional[Dict[str, Any]] = None,
        mode: Optional[ProcessingMode] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive manipulation analysis.

        Args:
            content: Input content to analyze
            source_info: Source metadata (url, domain, author, etc.)
            mode: Override processing mode (None = auto-determine)

        Returns:
            Analysis report dict
        """
        if not self._initialized:
            await self.initialize()

        start_time = datetime.utcnow()

        source_info = source_info or {}
        content_hash = hash_text(content)

        logger.info(f"🔍 Analyzing content: {content_hash[:16]}...")

        # ========== STAGE 1: COGNITIVE CONTROL ==========

        # 1.1 Adversarial input filtering
        sanitized_content, is_adversarial = (
            await cognitive_control.filter_adversarial_input(content)
        )

        if is_adversarial:
            logger.warning("⚠️ Adversarial input detected and sanitized")

        # 1.2 Mode determination (if not provided)
        if mode is None:
            mode = await cognitive_control.determine_mode(
                sanitized_content, source_info
            )

        logger.info(f"Processing mode: {mode.value}")

        # Special handling for SKIP mode
        if mode == ProcessingMode.SKIP:
            return self._build_skip_report(content_hash, source_info)

        # ========== STAGE 2: CONTEXT LOADING ==========

        context = await working_memory.load_context(sanitized_content, source_info)

        logger.debug(
            f"Context loaded: reputation={context.source_reputation.score:.2f}, "
            f"history={len(context.recent_analyses)}"
        )

        # ========== STAGE 3: MODULE EXECUTION ==========

        # Map processing mode to reality distortion mode
        reality_mode_map = {
            ProcessingMode.FAST_TRACK: RealityMode.FAST_TRACK,
            ProcessingMode.STANDARD: RealityMode.STANDARD,
            ProcessingMode.DEEP_ANALYSIS: RealityMode.DEEP_ANALYSIS,
        }

        reality_mode = reality_mode_map.get(mode, RealityMode.STANDARD)

        # Execute 4 modules in parallel
        logger.debug("Executing 4 detection modules...")

        module_results = await asyncio.gather(
            # Module 1: Source Credibility
            source_credibility_module.analyze_source(
                url=source_info.get("url", ""),
                domain=source_info.get("domain", ""),
                author=source_info.get("author"),
                publisher=source_info.get("publisher"),
            ),
            # Module 2: Emotional Manipulation
            emotional_manipulation_module.detect_emotional_manipulation(
                text=sanitized_content, persist_to_db=True
            ),
            # Module 3: Logical Fallacy
            logical_fallacy_module.detect_logical_fallacies(
                text=sanitized_content,
                persist_to_graph=False,  # Skip graph for performance
            ),
            # Module 4: Reality Distortion
            reality_distortion_module.verify_content(
                text=sanitized_content,
                mode=reality_mode,
                tier2_timeout=None,  # Async Tier 2
            ),
            return_exceptions=True,
        )

        # Unpack results (handle exceptions)
        credibility_result = self._unwrap_result(
            module_results[0], "source_credibility"
        )
        emotional_result = self._unwrap_result(
            module_results[1], "emotional_manipulation"
        )
        logical_result = self._unwrap_result(module_results[2], "logical_fallacy")
        reality_result = self._unwrap_result(module_results[3], "reality_distortion")

        # ========== STAGE 4: THREAT ASSESSMENT (AGGREGATION) ==========

        report = await threat_assessment_engine.aggregate(
            credibility_result=credibility_result,
            emotional_result=emotional_result,
            logical_result=logical_result,
            reality_result=reality_result,
            context={
                "source_domain": context.source_domain,
                "content_hash": content_hash,
            },
        )

        # ========== STAGE 5: PERFORMANCE MONITORING ==========

        # Calculate latency
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # Model drift detection
        performance_report = {
            "manipulation_score": report.manipulation_score,
            "confidence": report.confidence,
            "latency_ms": latency_ms,
            "error": False,
        }

        await cognitive_control.detect_model_drift(performance_report)

        # ========== STAGE 6: PERSISTENCE ==========

        # Build full report for storage
        storage_report = {
            "content_hash": content_hash,
            "source_domain": context.source_domain,
            "manipulation_score": report.manipulation_score,
            "credibility_score": credibility_result.get("credibility_score", 0.5),
            "emotional_score": emotional_result.get("manipulation_score", 0.0),
            "fallacy_count": len(logical_result.get("fallacies", [])),
            "verification_result": str(
                reality_result.get("verification_status", "unverified")
            ),
            "confidence": report.confidence,
            "verdict": report.verdict,
            "explanation": report.explanation,
            "latency_ms": latency_ms,
            "processing_mode": mode.value,
            "content": sanitized_content,
            "arguments": logical_result.get("arguments", []),
            "fallacies": logical_result.get("fallacies", []),
            "timestamp": datetime.utcnow().isoformat(),
        }

        await working_memory.store_analysis(storage_report)

        # ========== STAGE 7: RESPONSE GENERATION ==========

        return self._build_response(
            report=report,
            content_hash=content_hash,
            source_domain=context.source_domain,
            latency_ms=latency_ms,
            mode=mode,
            is_adversarial=is_adversarial,
        )

    def _unwrap_result(self, result: Any, module_name: str) -> Dict[str, Any]:
        """
        Unwrap module result, handling exceptions.

        Args:
            result: Module result or exception
            module_name: Module identifier

        Returns:
            Result dict (or empty dict if exception)
        """
        if isinstance(result, Exception):
            logger.error(f"Module {module_name} failed: {result}", exc_info=True)
            return {"error": str(result), "module": module_name}

        return result

    def _build_skip_report(
        self, content_hash: str, source_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build report for skipped content."""
        return {
            "content_hash": content_hash,
            "source_domain": source_info.get("domain", "unknown"),
            "manipulation_score": 0.0,
            "verdict": "SKIPPED",
            "explanation": "Content classified as opinion/question with low check-worthiness. Analysis skipped.",
            "confidence": 1.0,
            "processing_mode": "skip",
            "latency_ms": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _build_response(
        self,
        report: Any,
        content_hash: str,
        source_domain: str,
        latency_ms: float,
        mode: ProcessingMode,
        is_adversarial: bool,
    ) -> Dict[str, Any]:
        """
        Build final API response.

        Args:
            report: CognitiveDefenseReport
            content_hash: Content hash
            source_domain: Source domain
            latency_ms: Processing latency
            mode: Processing mode
            is_adversarial: Whether adversarial input was detected

        Returns:
            Response dict
        """
        return {
            "content_hash": content_hash,
            "source_domain": source_domain,
            "manipulation_score": report.manipulation_score,
            "verdict": report.verdict,
            "explanation": report.explanation,
            "confidence": report.confidence,
            "module_scores": {
                "source_credibility": report.credibility_assessment.score,
                "emotional_manipulation": report.emotional_assessment.score,
                "logical_fallacy": report.logical_assessment.score,
                "reality_distortion": report.reality_assessment.score,
            },
            "module_confidences": {
                "source_credibility": report.credibility_assessment.confidence,
                "emotional_manipulation": report.emotional_assessment.confidence,
                "logical_fallacy": report.logical_assessment.confidence,
                "reality_distortion": report.reality_assessment.confidence,
            },
            "processing_mode": mode.value,
            "latency_ms": latency_ms,
            "adversarial_detected": is_adversarial,
            "timestamp": report.timestamp.isoformat(),
        }

    async def get_detailed_report(
        self, content: str, source_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get detailed markdown report.

        Args:
            content: Content to analyze
            source_info: Source metadata

        Returns:
            Markdown-formatted detailed report
        """
        # Run analysis
        result = await self.analyze(content, source_info)

        # Re-run aggregation to get full report object
        # (simplified - in production, cache the report)

        # For now, generate a simplified report
        lines = [
            "# Cognitive Defense Analysis Report",
            "",
            f"**Timestamp**: {result['timestamp']}",
            f"**Source**: {result['source_domain']}",
            f"**Processing Mode**: {result['processing_mode']}",
            f"**Latency**: {result['latency_ms']:.0f}ms",
            "",
            "## Threat Assessment",
            "",
            f"**Manipulation Score**: {result['manipulation_score']:.2f}/1.00",
            f"**Verdict**: {result['verdict']}",
            f"**Confidence**: {result['confidence']:.2f}/1.00",
            "",
            "## Explanation",
            "",
            result["explanation"],
            "",
            "## Module Scores",
            "",
            f"- **Source Credibility**: {result['module_scores']['source_credibility']:.2f}",
            f"- **Emotional Manipulation**: {result['module_scores']['emotional_manipulation']:.2f}",
            f"- **Logical Fallacy**: {result['module_scores']['logical_fallacy']:.2f}",
            f"- **Reality Distortion**: {result['module_scores']['reality_distortion']:.2f}",
            "",
        ]

        if result.get("adversarial_detected"):
            lines.extend(
                [
                    "## ⚠️ Security Alert",
                    "",
                    "Adversarial input patterns detected. Content has been sanitized.",
                    "",
                ]
            )

        return "\n".join(lines)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

executive_controller = ExecutiveController()
