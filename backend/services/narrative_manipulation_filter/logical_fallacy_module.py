"""
Logical Fallacy Identification Module (Module 3) for Cognitive Defense System.

Orchestrates:
- Transformer-based argument mining (claims, premises)
- Multi-class fallacy classification (21 fallacy types)
- Dung's Abstract Argumentation Framework analysis
- Seriema Graph persistence and graph analytics
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from argument_miner import argument_miner
from argumentation_framework import (
    build_framework_from_arguments,
)
from config import get_settings
from fallacy_classifier import fallacy_classifier
from models import Argument, ArgumentStructureAnalysis, Fallacy, LogicalFallacyResult
from seriema_graph_client import seriema_graph_client
from utils import hash_text

logger = logging.getLogger(__name__)

settings = get_settings()


class LogicalFallacyModule:
    """
    Module 3: Logical Fallacy Identification.

    Multi-stage analysis pipeline:
    1. Argument Mining (BERT token classification)
    2. Fallacy Detection (ML + pattern matching)
    3. Argumentation Framework Analysis (Dung's AF)
    4. Graph Analytics (Neo4j/Seriema Graph)
    """

    def __init__(self):
        """Initialize Module 3."""
        self._models_initialized = False
        self._graph_initialized = False

    async def initialize(self, initialize_graph: bool = True) -> None:
        """
        Initialize ML models and graph client.

        Args:
            initialize_graph: Initialize Seriema Graph client
        """
        if self._models_initialized:
            logger.warning("Logical fallacy models already initialized")
            return

        try:
            logger.info("🚀 Initializing logical fallacy detection models...")

            # Initialize models in parallel
            await asyncio.gather(argument_miner.initialize(), fallacy_classifier.initialize())

            self._models_initialized = True

            # Initialize graph client
            if initialize_graph:
                await seriema_graph_client.initialize()
                self._graph_initialized = True

            logger.info("✅ Logical fallacy detection models initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize models: {e}", exc_info=True)
            raise

    async def detect_logical_fallacies(
        self,
        text: str,
        persist_to_graph: bool = False,
        framework_id: Optional[str] = None,
    ) -> LogicalFallacyResult:
        """
        Comprehensive logical fallacy detection.

        Args:
            text: Input text
            persist_to_graph: Store framework in Neo4j
            framework_id: Custom framework ID (defaults to hash of text)

        Returns:
            LogicalFallacyResult
        """
        if not self._models_initialized:
            logger.warning("Models not initialized, initializing now...")
            await self.initialize(initialize_graph=persist_to_graph)

        # ========== STAGE 1: ARGUMENT MINING ==========

        arguments = argument_miner.extract_arguments(text=text, min_confidence=0.6, use_cache=True)

        logger.info(f"Extracted {len(arguments)} arguments from text")

        if not arguments:
            # No arguments detected
            return LogicalFallacyResult(
                fallacy_score=0.0,
                arguments=[],
                fallacies=[],
                argumentation_coherence=1.0,
                winning_arguments=[],
                structure_analysis=ArgumentStructureAnalysis(
                    total_arguments=0,
                    major_claims=0,
                    claims=0,
                    premises=0,
                    supported_claims=0,
                    unsupported_claims=0,
                    avg_premises_per_claim=0.0,
                    structure_quality=0.0,
                ),
            )

        # ========== STAGE 2: FALLACY CLASSIFICATION ==========

        fallacies = []

        for argument in arguments:
            # Hybrid detection (ML + patterns)
            detected_fallacies = fallacy_classifier.analyze_argument_for_fallacies(
                argument=argument, use_ml=True, use_patterns=True
            )
            fallacies.extend(detected_fallacies)

        logger.info(f"Detected {len(fallacies)} fallacies")

        # ========== STAGE 3: ARGUMENTATION FRAMEWORK ANALYSIS ==========

        framework = build_framework_from_arguments(arguments=arguments, fallacies=fallacies)

        # Calculate coherence
        coherence = framework.calculate_coherence()

        # Get winning arguments (grounded extension)
        winning_arguments = framework.get_winning_arguments()

        # Get argument structure analysis
        structure_analysis = argument_miner.get_argument_structure(arguments)

        # Detect circular reasoning patterns
        circular_patterns = argument_miner.detect_circular_reasoning(arguments)

        logger.info(
            f"Argumentation analysis: coherence={coherence:.3f}, "
            f"winning_args={len(winning_arguments)}, "
            f"circular_patterns={len(circular_patterns)}"
        )

        # ========== STAGE 4: GRAPH PERSISTENCE (OPTIONAL) ==========

        graph_metadata = {}

        if persist_to_graph and self._graph_initialized:
            if framework_id is None:
                framework_id = hash_text(text)

            metadata = {
                "text_hash": hash_text(text),
                "text_length": len(text),
                "num_fallacies": len(fallacies),
                "timestamp": datetime.utcnow().isoformat(),
            }

            success = await seriema_graph_client.store_framework(
                framework=framework, framework_id=framework_id, metadata=metadata
            )

            if success:
                # Get graph analytics
                centrality = await seriema_graph_client.get_argument_centrality(
                    framework_id=framework_id, algorithm="degree"
                )

                graph_stats = await seriema_graph_client.get_framework_statistics(framework_id=framework_id)

                graph_metadata = {
                    "framework_id": framework_id,
                    "centrality": centrality,
                    "statistics": graph_stats,
                }

                logger.info(f"Persisted framework to Seriema Graph: {framework_id}")

        # ========== AGGREGATION: CALCULATE FALLACY SCORE ==========

        fallacy_score = self._calculate_fallacy_score(
            arguments=arguments,
            fallacies=fallacies,
            coherence=coherence,
            structure_analysis=structure_analysis,
            circular_patterns=circular_patterns,
        )

        # ========== BUILD RESULT ==========

        result = LogicalFallacyResult(
            fallacy_score=fallacy_score,
            arguments=arguments,
            fallacies=fallacies,
            argumentation_coherence=coherence,
            winning_arguments=winning_arguments,
            structure_analysis=ArgumentStructureAnalysis(**structure_analysis),
            circular_reasoning_detected=len(circular_patterns) > 0,
            graph_metadata=graph_metadata if graph_metadata else None,
        )

        logger.info(
            f"Logical fallacy detection complete: score={fallacy_score:.3f}, "
            f"fallacies={len(fallacies)}, coherence={coherence:.3f}"
        )

        return result

    def _calculate_fallacy_score(
        self,
        arguments: List[Argument],
        fallacies: List[Fallacy],
        coherence: float,
        structure_analysis: Dict[str, Any],
        circular_patterns: List[Any],
    ) -> float:
        """
        Calculate overall logical fallacy score.

        Factors:
        - Fallacy density (40%): Number of fallacies / number of arguments
        - Fallacy severity (30%): Average severity of detected fallacies
        - Argumentation coherence (20%): Inverse of coherence (low coherence = high score)
        - Structure quality (10%): Inverse of structure quality

        Args:
            arguments: Extracted arguments
            fallacies: Detected fallacies
            coherence: Argumentation coherence (0-1)
            structure_analysis: Structure quality analysis
            circular_patterns: Circular reasoning patterns

        Returns:
            Fallacy score (0-1)
        """

        if not arguments:
            return 0.0

        # 1. Fallacy density (40%)
        fallacy_density = len(fallacies) / len(arguments)
        fallacy_density_score = min(1.0, fallacy_density)  # Cap at 1.0

        # 2. Fallacy severity (30%)
        if fallacies:
            avg_severity = sum(f.severity for f in fallacies) / len(fallacies)
            severity_score = avg_severity
        else:
            severity_score = 0.0

        # 3. Argumentation coherence (20%) - inverted (low coherence = high score)
        coherence_score = 1.0 - coherence

        # 4. Structure quality (10%) - inverted
        structure_quality = structure_analysis.get("structure_quality", 0.5)
        structure_score = 1.0 - structure_quality

        # Weighted combination
        base_score = (
            fallacy_density_score * 0.40 + severity_score * 0.30 + coherence_score * 0.20 + structure_score * 0.10
        )

        # Boosters for severe cases
        boosters = 0.0

        # High-severity fallacies (Straw Man, Circular Reasoning)
        critical_fallacies = [f for f in fallacies if f.severity > 0.8]
        if len(critical_fallacies) >= 2:
            boosters += 0.15

        # Circular reasoning detected
        if len(circular_patterns) > 0:
            boosters += 0.10

        # Many unsupported claims
        unsupported_ratio = structure_analysis.get("unsupported_claims", 0) / max(
            1, structure_analysis.get("claims", 1)
        )
        if unsupported_ratio > 0.7:
            boosters += 0.10

        # Very low coherence
        if coherence < 0.3:
            boosters += 0.15

        final_score = min(1.0, base_score + boosters)

        return final_score

    async def analyze_argument_graph(self, framework_id: str) -> Dict[str, Any]:
        """
        Perform graph analytics on persisted framework.

        Args:
            framework_id: Framework identifier

        Returns:
            Graph analysis results
        """
        if not self._graph_initialized:
            raise RuntimeError("Graph client not initialized")

        # Retrieve framework
        framework = await seriema_graph_client.retrieve_framework(framework_id)

        if not framework:
            raise ValueError(f"Framework not found: {framework_id}")

        # Centrality analysis
        pagerank = await seriema_graph_client.get_argument_centrality(framework_id=framework_id, algorithm="pagerank")

        degree = await seriema_graph_client.get_argument_centrality(framework_id=framework_id, algorithm="degree")

        # Circular arguments
        cycles = await seriema_graph_client.detect_circular_arguments(framework_id=framework_id)

        # Statistics
        stats = await seriema_graph_client.get_framework_statistics(framework_id=framework_id)

        # Top central arguments
        top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]

        top_degree = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "framework_id": framework_id,
            "statistics": stats,
            "centrality": {"pagerank": dict(top_pagerank), "degree": dict(top_degree)},
            "circular_arguments": cycles,
            "coherence": framework.calculate_coherence(),
            "grounded_extension": framework.get_winning_arguments(),
        }

    def get_fallacy_explanation(self, fallacy: Fallacy) -> Dict[str, str]:
        """
        Get detailed explanation for a fallacy.

        Args:
            fallacy: Fallacy object

        Returns:
            Explanation dict
        """
        return {
            "type": fallacy.fallacy_type.value,
            "description": fallacy.description,
            "evidence": fallacy.evidence,
            "counter_argument": fallacy.counter_argument,
            "severity": f"{fallacy.severity:.2f}",
            "recommendation": self._get_fallacy_recommendation(fallacy),
        }

    @staticmethod
    def _get_fallacy_recommendation(fallacy: Fallacy) -> str:
        """Get recommendation for handling fallacy."""
        if fallacy.severity >= 0.8:
            return "CRITICAL: This argument should be flagged or rejected due to severe logical fallacy."
        elif fallacy.severity >= 0.6:
            return "HIGH: Alert users to this fallacy and provide counter-argument."
        elif fallacy.severity >= 0.4:
            return "MEDIUM: Flag for review and inform users of logical weakness."
        else:
            return "LOW: Monitor but allow, minor logical issue detected."

    def generate_fallacy_report(self, result: LogicalFallacyResult) -> str:
        """
        Generate human-readable fallacy report.

        Args:
            result: LogicalFallacyResult

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Logical Fallacy Analysis Report",
            "",
            f"**Overall Fallacy Score**: {result.fallacy_score:.2f}/1.00",
            f"**Argumentation Coherence**: {result.argumentation_coherence:.2f}/1.00",
            "",
            "## Argument Structure",
            "",
            f"- **Total Arguments**: {result.structure_analysis.total_arguments}",
            f"- **Major Claims**: {result.structure_analysis.major_claims}",
            f"- **Claims**: {result.structure_analysis.claims}",
            f"- **Premises**: {result.structure_analysis.premises}",
            f"- **Supported Claims**: {result.structure_analysis.supported_claims}",
            f"- **Unsupported Claims**: {result.structure_analysis.unsupported_claims}",
            f"- **Avg Premises per Claim**: {result.structure_analysis.avg_premises_per_claim:.2f}",
            f"- **Structure Quality**: {result.structure_analysis.structure_quality:.2f}/1.00",
            "",
            "## Detected Fallacies",
            "",
        ]

        if not result.fallacies:
            lines.append("✅ No logical fallacies detected.")
        else:
            for i, fallacy in enumerate(result.fallacies, 1):
                lines.extend(
                    [
                        f"### {i}. {fallacy.fallacy_type.value.upper()}",
                        "",
                        f"**Severity**: {fallacy.severity:.2f}/1.00",
                        f"**Description**: {fallacy.description}",
                        f'**Evidence**: "{fallacy.evidence[:100]}..."',
                        f"**Counter-Argument**: {fallacy.counter_argument}",
                        "",
                    ]
                )

        if result.circular_reasoning_detected:
            lines.extend(
                [
                    "## ⚠️ Circular Reasoning Detected",
                    "",
                    "The text contains circular reasoning patterns where premises ",
                    "refer back to their own conclusions.",
                    "",
                ]
            )

        lines.extend(
            [
                "## Winning Arguments",
                "",
                f"Arguments in grounded extension: {len(result.winning_arguments)}",
                "",
            ]
        )

        if result.graph_metadata:
            lines.extend(
                [
                    "## Graph Analytics",
                    "",
                    f"**Framework ID**: {result.graph_metadata.get('framework_id', 'N/A')}",
                    f"**Graph Statistics**: {result.graph_metadata.get('statistics', {})}",
                    "",
                ]
            )

        return "\n".join(lines)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

logical_fallacy_module = LogicalFallacyModule()
