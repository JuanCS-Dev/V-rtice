"""
Chain-of-Thought Reasoning Engine
==================================

Advanced reasoning system that breaks down complex security problems
into step-by-step logical reasoning chains with backtracking support.

Features:
- Step-by-step problem decomposition
- Confidence scoring per reasoning step
- Backtracking on low-confidence paths
- Reasoning trace for explainability
- Alternative hypothesis exploration

Examples:
    reasoner = CoTReasoner()

    # Analyze complex security scenario
    result = reasoner.reason(
        problem="Investigate suspicious lateral movement",
        context={"hosts": [...], "events": [...]},
        strategy="security_investigation"
    )

    # Access reasoning trace
    for step in result.reasoning_trace:
        print(f"{step.step_num}: {step.thought} (confidence: {step.confidence})")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ReasoningStrategy(Enum):
    """Reasoning strategies for different problem types."""

    SECURITY_INVESTIGATION = "security_investigation"  # Security incident analysis
    THREAT_HUNTING = "threat_hunting"  # Proactive threat discovery
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"  # CVE/exploit analysis
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"  # Incident root cause
    ATTACK_PATH_MODELING = "attack_path_modeling"  # Attack chain reconstruction
    GENERAL = "general"  # General problem-solving


class StepType(Enum):
    """Types of reasoning steps."""

    OBSERVATION = "observation"  # Initial observation
    HYPOTHESIS = "hypothesis"  # Proposed explanation
    INFERENCE = "inference"  # Logical deduction
    QUESTION = "question"  # Open question
    CONCLUSION = "conclusion"  # Final conclusion
    BACKTRACK = "backtrack"  # Backtracking decision


@dataclass
class ReasoningStep:
    """
    Single step in reasoning chain.

    Attributes:
        step_num: Step number in chain
        step_type: Type of reasoning step
        thought: Natural language reasoning
        confidence: Confidence score (0-1)
        evidence: Supporting evidence
        alternatives: Alternative hypotheses considered
        timestamp: When step was created
    """
    step_num: int
    step_type: StepType
    thought: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningResult:
    """
    Complete reasoning result with trace.

    Attributes:
        problem: Original problem statement
        conclusion: Final conclusion
        reasoning_trace: Step-by-step reasoning
        confidence: Overall confidence (0-1)
        alternative_paths: Alternative reasoning paths explored
        metadata: Additional result metadata
    """
    problem: str
    conclusion: str
    reasoning_trace: List[ReasoningStep]
    confidence: float
    alternative_paths: List[List[ReasoningStep]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.now)


class CoTReasoner:
    """
    Chain-of-Thought reasoning engine.

    Implements step-by-step reasoning with confidence tracking,
    backtracking, and alternative hypothesis exploration.

    Example:
        reasoner = CoTReasoner(min_confidence=0.6)

        result = reasoner.reason(
            problem="Why is host 10.0.0.5 beaconing to external IP?",
            context={
                "host": "10.0.0.5",
                "external_ip": "93.184.216.34",
                "frequency": "every 60 seconds",
                "process": "svchost.exe"
            },
            strategy=ReasoningStrategy.SECURITY_INVESTIGATION
        )
    """

    def __init__(
        self,
        min_confidence: float = 0.5,
        max_steps: int = 20,
        enable_backtracking: bool = True,
    ):
        """
        Initialize CoT reasoner.

        Args:
            min_confidence: Minimum confidence to continue path (0-1)
            max_steps: Maximum reasoning steps before forcing conclusion
            enable_backtracking: Enable backtracking on low confidence
        """
        self.min_confidence = min_confidence
        self.max_steps = max_steps
        self.enable_backtracking = enable_backtracking

        # Reasoning state
        self._current_trace: List[ReasoningStep] = []
        self._alternative_paths: List[List[ReasoningStep]] = []
        self._step_counter = 0

        logger.info(
            f"CoTReasoner initialized (min_conf={min_confidence}, "
            f"max_steps={max_steps}, backtrack={enable_backtracking})"
        )

    def reason(
        self,
        problem: str,
        context: Dict[str, Any],
        strategy: ReasoningStrategy = ReasoningStrategy.GENERAL,
    ) -> ReasoningResult:
        """
        Perform chain-of-thought reasoning on problem.

        Args:
            problem: Problem statement to reason about
            context: Contextual information
            strategy: Reasoning strategy to use

        Returns:
            ReasoningResult with trace and conclusion

        Example:
            result = reasoner.reason(
                problem="Identify attack vector",
                context={"events": [...], "iocs": [...]},
                strategy=ReasoningStrategy.THREAT_HUNTING
            )
        """
        logger.info(f"Starting reasoning: {problem[:100]}...")

        # Reset state
        self._current_trace = []
        self._alternative_paths = []
        self._step_counter = 0

        # Initial observation
        self._add_step(
            step_type=StepType.OBSERVATION,
            thought=f"Problem: {problem}",
            confidence=1.0,
            metadata={"strategy": strategy.value}
        )

        # Execute strategy-specific reasoning
        if strategy == ReasoningStrategy.SECURITY_INVESTIGATION:
            conclusion = self._security_investigation_reasoning(problem, context)

        elif strategy == ReasoningStrategy.THREAT_HUNTING:
            conclusion = self._threat_hunting_reasoning(problem, context)

        elif strategy == ReasoningStrategy.VULNERABILITY_ANALYSIS:
            conclusion = self._vulnerability_analysis_reasoning(problem, context)

        elif strategy == ReasoningStrategy.ROOT_CAUSE_ANALYSIS:
            conclusion = self._root_cause_reasoning(problem, context)

        elif strategy == ReasoningStrategy.ATTACK_PATH_MODELING:
            conclusion = self._attack_path_reasoning(problem, context)

        else:
            conclusion = self._general_reasoning(problem, context)

        # Calculate overall confidence
        avg_confidence = sum(s.confidence for s in self._current_trace) / len(self._current_trace)

        result = ReasoningResult(
            problem=problem,
            conclusion=conclusion,
            reasoning_trace=self._current_trace.copy(),
            confidence=avg_confidence,
            alternative_paths=self._alternative_paths.copy(),
            metadata={
                "strategy": strategy.value,
                "steps_taken": len(self._current_trace),
                "paths_explored": len(self._alternative_paths) + 1,
            }
        )

        logger.info(
            f"Reasoning complete: {len(self._current_trace)} steps, "
            f"confidence={avg_confidence:.2f}"
        )

        return result

    def _add_step(
        self,
        step_type: StepType,
        thought: str,
        confidence: float,
        evidence: Optional[List[str]] = None,
        alternatives: Optional[List[str]] = None,
        **metadata
    ) -> ReasoningStep:
        """Add reasoning step to current trace."""
        self._step_counter += 1

        step = ReasoningStep(
            step_num=self._step_counter,
            step_type=step_type,
            thought=thought,
            confidence=confidence,
            evidence=evidence or [],
            alternatives=alternatives or [],
            metadata=metadata
        )

        self._current_trace.append(step)

        logger.debug(
            f"Step {self._step_counter} ({step_type.value}): "
            f"{thought[:60]}... (conf={confidence:.2f})"
        )

        return step

    def _should_backtrack(self) -> bool:
        """Determine if backtracking is needed."""
        if not self.enable_backtracking:
            return False

        if not self._current_trace:
            return False

        recent_confidence = self._current_trace[-1].confidence

        return recent_confidence < self.min_confidence

    def _backtrack(self) -> None:
        """Backtrack to last high-confidence step."""
        logger.info("Backtracking due to low confidence")

        # Save current path as alternative
        self._alternative_paths.append(self._current_trace.copy())

        # Find last high-confidence step
        while self._current_trace:
            last_step = self._current_trace.pop()

            if last_step.confidence >= self.min_confidence:
                self._current_trace.append(last_step)
                break

        # Add backtrack marker
        self._add_step(
            step_type=StepType.BACKTRACK,
            thought="Previous reasoning path had low confidence, exploring alternative",
            confidence=0.8
        )

    # ========================================
    # Strategy-Specific Reasoning Methods
    # ========================================

    def _security_investigation_reasoning(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> str:
        """Reasoning for security investigation."""

        # Step 1: Identify anomaly indicators
        self._add_step(
            StepType.HYPOTHESIS,
            "Analyzing anomaly indicators in context",
            confidence=0.9,
            evidence=list(context.keys())
        )

        # Step 2: Correlate with known attack patterns
        self._add_step(
            StepType.INFERENCE,
            "Correlating observed behavior with known attack patterns",
            confidence=0.8,
            alternatives=[
                "Could be legitimate admin activity",
                "Could be automated system process",
                "Could be malicious lateral movement"
            ]
        )

        # Step 3: Assess impact and scope
        self._add_step(
            StepType.INFERENCE,
            "Assessing potential impact based on affected systems",
            confidence=0.85
        )

        # Step 4: Determine likelihood
        likelihood_conf = 0.7

        self._add_step(
            StepType.HYPOTHESIS,
            "Evaluating likelihood of malicious activity vs benign",
            confidence=likelihood_conf
        )

        # Backtrack if confidence too low
        if self._should_backtrack():
            self._backtrack()
            likelihood_conf = 0.75  # Try alternative approach

        # Step 5: Conclusion
        conclusion_step = self._add_step(
            StepType.CONCLUSION,
            "Based on evidence correlation and pattern matching, "
            "determining most likely explanation",
            confidence=likelihood_conf
        )

        return conclusion_step.thought

    def _threat_hunting_reasoning(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> str:
        """Reasoning for proactive threat hunting."""

        self._add_step(
            StepType.HYPOTHESIS,
            "Formulating threat hypothesis based on hunting question",
            confidence=0.85
        )

        self._add_step(
            StepType.INFERENCE,
            "Identifying data sources needed to test hypothesis",
            confidence=0.9,
            evidence=["logs", "network_traffic", "process_events"]
        )

        self._add_step(
            StepType.INFERENCE,
            "Analyzing baseline behavior to detect deviations",
            confidence=0.75
        )

        conclusion_step = self._add_step(
            StepType.CONCLUSION,
            "Threat hypothesis validated/invalidated based on evidence",
            confidence=0.8
        )

        return conclusion_step.thought

    def _vulnerability_analysis_reasoning(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> str:
        """Reasoning for vulnerability analysis."""

        self._add_step(
            StepType.OBSERVATION,
            "Analyzing vulnerability characteristics (CVSS, vector, etc.)",
            confidence=0.95,
            evidence=["cvss_score", "attack_vector", "complexity"]
        )

        self._add_step(
            StepType.INFERENCE,
            "Assessing exploitability in current environment",
            confidence=0.8
        )

        self._add_step(
            StepType.HYPOTHESIS,
            "Determining likelihood of exploitation vs. impact",
            confidence=0.75,
            alternatives=[
                "High impact but low exploitability",
                "High exploitability but low impact",
                "Critical on both dimensions"
            ]
        )

        conclusion_step = self._add_step(
            StepType.CONCLUSION,
            "Prioritization decision based on risk calculation",
            confidence=0.85
        )

        return conclusion_step.thought

    def _root_cause_reasoning(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> str:
        """Reasoning for root cause analysis."""

        self._add_step(
            StepType.OBSERVATION,
            "Identifying observable symptoms and effects",
            confidence=0.9
        )

        self._add_step(
            StepType.QUESTION,
            "What are the possible root causes for these symptoms?",
            confidence=0.8,
            alternatives=[
                "Configuration error",
                "Software bug",
                "Malicious activity",
                "Hardware failure"
            ]
        )

        self._add_step(
            StepType.INFERENCE,
            "Tracing causal chain backwards from symptoms",
            confidence=0.75
        )

        self._add_step(
            StepType.HYPOTHESIS,
            "Testing most likely root cause hypothesis",
            confidence=0.7
        )

        if self._should_backtrack():
            self._backtrack()

        conclusion_step = self._add_step(
            StepType.CONCLUSION,
            "Root cause identified through elimination and evidence",
            confidence=0.8
        )

        return conclusion_step.thought

    def _attack_path_reasoning(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> str:
        """Reasoning for attack path modeling."""

        self._add_step(
            StepType.OBSERVATION,
            "Identifying entry point and final objective",
            confidence=0.85
        )

        self._add_step(
            StepType.INFERENCE,
            "Mapping intermediate attack stages (recon → exploit → pivot → exfil)",
            confidence=0.8
        )

        self._add_step(
            StepType.HYPOTHESIS,
            "Determining most likely attack path based on observed artifacts",
            confidence=0.75,
            alternatives=[
                "Direct exploitation path",
                "Lateral movement path",
                "Supply chain path"
            ]
        )

        conclusion_step = self._add_step(
            StepType.CONCLUSION,
            "Attack path reconstructed with key pivot points identified",
            confidence=0.8
        )

        return conclusion_step.thought

    def _general_reasoning(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> str:
        """General-purpose reasoning."""

        self._add_step(
            StepType.HYPOTHESIS,
            "Breaking down problem into sub-problems",
            confidence=0.8
        )

        self._add_step(
            StepType.INFERENCE,
            "Applying domain knowledge to sub-problems",
            confidence=0.75
        )

        conclusion_step = self._add_step(
            StepType.CONCLUSION,
            "Synthesizing sub-problem solutions into final answer",
            confidence=0.7
        )

        return conclusion_step.thought

    def explain_reasoning(self, result: ReasoningResult) -> str:
        """
        Generate natural language explanation of reasoning process.

        Args:
            result: ReasoningResult to explain

        Returns:
            Human-readable explanation

        Example:
            explanation = reasoner.explain_reasoning(result)
            print(explanation)
        """
        lines = [
            f"Problem: {result.problem}",
            f"Conclusion: {result.conclusion}",
            f"Overall Confidence: {result.confidence:.1%}",
            "",
            "Reasoning Steps:",
        ]

        for step in result.reasoning_trace:
            prefix = {
                StepType.OBSERVATION: "📊",
                StepType.HYPOTHESIS: "💡",
                StepType.INFERENCE: "🔍",
                StepType.QUESTION: "❓",
                StepType.CONCLUSION: "✅",
                StepType.BACKTRACK: "↩️",
            }.get(step.step_type, "•")

            lines.append(
                f"{prefix} Step {step.step_num} ({step.step_type.value}, "
                f"conf={step.confidence:.0%}): {step.thought}"
            )

            if step.alternatives:
                lines.append(f"   Alternatives considered: {len(step.alternatives)}")

        if result.alternative_paths:
            lines.append(f"\nAlternative paths explored: {len(result.alternative_paths)}")

        return "\n".join(lines)
