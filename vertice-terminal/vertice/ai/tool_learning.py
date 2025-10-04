"""
Tool Learning & Adaptation System
==================================

Learns which tools work best for different situations and adapts
tool selection based on historical performance and context.

Features:
- Tool performance tracking
- Context-aware tool selection
- Tool combination learning
- Effectiveness scoring
- Adaptive recommendation

Examples:
    learner = ToolLearner()

    # Record tool usage
    learner.record_tool_usage(
        tool="nmap",
        context={"target_type": "web_server", "ports": "80,443"},
        outcome="success",
        effectiveness=0.9
    )

    # Get best tool recommendation
    recommended = learner.recommend_tool(
        task="port_scan",
        context={"target": "10.0.0.1"}
    )
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Tool categories."""

    SCANNER = "scanner"  # Scanning tools (nmap, masscan, etc.)
    ANALYZER = "analyzer"  # Analysis tools (wireshark, volatility, etc.)
    EXPLOITER = "exploiter"  # Exploit tools (metasploit, etc.)
    ENUMERATION = "enumeration"  # Enumeration tools (enum4linux, etc.)
    OSINT = "osint"  # OSINT tools (shodan, maltego, etc.)
    FORENSICS = "forensics"  # Forensic tools (autopsy, sleuthkit, etc.)
    CREDENTIAL = "credential"  # Credential tools (hashcat, john, etc.)


@dataclass
class ToolUsage:
    """
    Record of tool usage and outcome.

    Attributes:
        tool_name: Name of tool used
        category: Tool category
        context: Context when tool was used
        outcome: Outcome (success/failure/partial)
        effectiveness: Effectiveness score (0-1)
        execution_time_seconds: Time taken
        timestamp: When tool was used
    """
    tool_name: str
    category: ToolCategory
    context: Dict[str, Any]
    outcome: str  # "success", "failure", "partial"
    effectiveness: float  # 0-1 score
    execution_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolRecommendation:
    """
    Tool recommendation with confidence.

    Attributes:
        tool_name: Recommended tool
        confidence: Confidence in recommendation (0-1)
        reasoning: Why this tool was recommended
        alternative_tools: Alternative tool suggestions
        estimated_effectiveness: Expected effectiveness
    """
    tool_name: str
    confidence: float
    reasoning: str
    alternative_tools: List[str] = field(default_factory=list)
    estimated_effectiveness: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolPerformanceProfile:
    """
    Performance profile for a tool.

    Attributes:
        tool_name: Tool name
        category: Tool category
        total_uses: Number of times used
        success_rate: Fraction of successful uses
        avg_effectiveness: Average effectiveness score
        avg_execution_time: Average execution time
        best_contexts: Contexts where tool performs best
        worst_contexts: Contexts where tool performs worst
    """
    tool_name: str
    category: ToolCategory
    total_uses: int
    success_rate: float
    avg_effectiveness: float
    avg_execution_time: float
    best_contexts: List[Dict[str, Any]] = field(default_factory=list)
    worst_contexts: List[Dict[str, Any]] = field(default_factory=list)
    last_used: Optional[datetime] = None


class ToolLearner:
    """
    Tool learning and adaptation system.

    Tracks tool performance across different contexts and learns
    which tools work best for specific scenarios.

    Example:
        learner = ToolLearner()

        # Record tool usages
        learner.record_tool_usage(
            tool="nmap",
            category=ToolCategory.SCANNER,
            context={"target": "web_server", "network": "external"},
            outcome="success",
            effectiveness=0.95,
            execution_time_seconds=15.3
        )

        # Get recommendation
        rec = learner.recommend_tool(
            task="port_scanning",
            context={"target": "web_server"}
        )

        print(f"Recommended: {rec.tool_name} (confidence: {rec.confidence:.0%})")
    """

    def __init__(
        self,
        learning_window_days: int = 90,
        min_uses_for_confidence: int = 5,
    ):
        """
        Initialize tool learner.

        Args:
            learning_window_days: Days of history to consider
            min_uses_for_confidence: Minimum uses for high confidence
        """
        self.learning_window_days = learning_window_days
        self.min_uses_for_confidence = min_uses_for_confidence

        # Tool usage history
        self._usage_history: List[ToolUsage] = []

        # Performance tracking
        self._tool_effectiveness: Dict[str, List[float]] = defaultdict(list)
        self._tool_success_count: Dict[str, int] = defaultdict(int)
        self._tool_total_count: Dict[str, int] = defaultdict(int)
        self._tool_execution_times: Dict[str, List[float]] = defaultdict(list)

        # Context-specific performance
        self._context_performance: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

        # Tool combinations that work well together
        self._tool_combinations: Dict[tuple, float] = {}

        logger.info(
            f"ToolLearner initialized (window={learning_window_days}d, "
            f"min_uses={min_uses_for_confidence})"
        )

    def record_tool_usage(
        self,
        tool: str,
        category: ToolCategory,
        context: Dict[str, Any],
        outcome: str,
        effectiveness: float,
        execution_time_seconds: float = 0.0,
        errors: Optional[List[str]] = None,
        **metadata
    ) -> ToolUsage:
        """
        Record tool usage and outcome.

        Args:
            tool: Tool name
            category: Tool category
            context: Usage context
            outcome: Outcome (success/failure/partial)
            effectiveness: Effectiveness score (0-1)
            execution_time_seconds: Execution time
            errors: Error messages if any
            **metadata: Additional metadata

        Returns:
            ToolUsage record

        Example:
            usage = learner.record_tool_usage(
                tool="metasploit",
                category=ToolCategory.EXPLOITER,
                context={"target_os": "windows", "vuln": "ms17-010"},
                outcome="success",
                effectiveness=1.0,
                execution_time_seconds=45.2
            )
        """
        usage = ToolUsage(
            tool_name=tool,
            category=category,
            context=context,
            outcome=outcome,
            effectiveness=effectiveness,
            execution_time_seconds=execution_time_seconds,
            errors=errors or [],
            metadata=metadata
        )

        # Store usage
        self._usage_history.append(usage)

        # Update performance tracking
        self._tool_total_count[tool] += 1

        if outcome == "success":
            self._tool_success_count[tool] += 1

        self._tool_effectiveness[tool].append(effectiveness)
        self._tool_execution_times[tool].append(execution_time_seconds)

        # Update context-specific performance
        context_key = self._serialize_context(context)
        self._context_performance[tool][context_key].append(effectiveness)

        logger.debug(
            f"Tool usage recorded: {tool} ({outcome}, "
            f"effectiveness={effectiveness:.2f})"
        )

        return usage

    def recommend_tool(
        self,
        task: str,
        context: Dict[str, Any],
        category: Optional[ToolCategory] = None,
        max_recommendations: int = 3,
    ) -> ToolRecommendation:
        """
        Recommend best tool for task and context.

        Args:
            task: Task description
            context: Current context
            category: Filter by tool category
            max_recommendations: Max alternative tools

        Returns:
            ToolRecommendation

        Example:
            rec = learner.recommend_tool(
                task="scan network for open ports",
                context={"network_size": "large", "stealth_required": True},
                category=ToolCategory.SCANNER
            )
        """
        logger.info(f"Recommending tool for: {task[:60]}...")

        # Get candidate tools
        candidates = self._get_candidate_tools(task, category)

        if not candidates:
            logger.warning(f"No candidate tools found for task: {task}")

            return ToolRecommendation(
                tool_name="unknown",
                confidence=0.0,
                reasoning="No tools in knowledge base for this task"
            )

        # Score each candidate
        scored_candidates = []

        for tool in candidates:
            score = self._score_tool_for_context(tool, context)
            scored_candidates.append((tool, score))

        # Sort by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Best recommendation
        best_tool, best_score = scored_candidates[0]

        # Calculate confidence
        uses = self._tool_total_count[best_tool]
        confidence = min(1.0, uses / self.min_uses_for_confidence) * best_score

        # Alternative tools
        alternatives = [tool for tool, score in scored_candidates[1:max_recommendations]]

        # Generate reasoning
        reasoning = self._generate_reasoning(best_tool, context, best_score)

        recommendation = ToolRecommendation(
            tool_name=best_tool,
            confidence=confidence,
            reasoning=reasoning,
            alternative_tools=alternatives,
            estimated_effectiveness=best_score
        )

        logger.info(
            f"Recommended: {best_tool} (confidence={confidence:.0%}, "
            f"estimated_effectiveness={best_score:.0%})"
        )

        return recommendation

    def get_tool_profile(self, tool: str) -> ToolPerformanceProfile:
        """
        Get performance profile for tool.

        Args:
            tool: Tool name

        Returns:
            ToolPerformanceProfile

        Example:
            profile = learner.get_tool_profile("nmap")

            print(f"Success rate: {profile.success_rate:.0%}")
            print(f"Avg effectiveness: {profile.avg_effectiveness:.0%}")
        """
        if tool not in self._tool_total_count:
            raise ValueError(f"No usage data for tool: {tool}")

        total_uses = self._tool_total_count[tool]
        success_count = self._tool_success_count[tool]
        success_rate = success_count / total_uses if total_uses > 0 else 0.0

        effectiveness_scores = self._tool_effectiveness[tool]
        avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)

        execution_times = self._tool_execution_times[tool]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0

        # Find best/worst contexts
        best_contexts, worst_contexts = self._analyze_context_performance(tool)

        # Find tool category
        tool_usages = [u for u in self._usage_history if u.tool_name == tool]
        category = tool_usages[0].category if tool_usages else ToolCategory.SCANNER

        # Last used
        last_used = max((u.timestamp for u in tool_usages)) if tool_usages else None

        profile = ToolPerformanceProfile(
            tool_name=tool,
            category=category,
            total_uses=total_uses,
            success_rate=success_rate,
            avg_effectiveness=avg_effectiveness,
            avg_execution_time=avg_execution_time,
            best_contexts=best_contexts,
            worst_contexts=worst_contexts,
            last_used=last_used
        )

        return profile

    def _get_candidate_tools(
        self,
        task: str,
        category: Optional[ToolCategory] = None
    ) -> List[str]:
        """Get candidate tools for task."""
        # In production, would use NLP/embeddings to match task to tools
        # For now, return tools we have data for

        all_tools = list(self._tool_total_count.keys())

        if category:
            # Filter by category
            all_tools = [
                tool for tool in all_tools
                if any(u.tool_name == tool and u.category == category for u in self._usage_history)
            ]

        return all_tools

    def _score_tool_for_context(
        self,
        tool: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Score tool suitability for given context.

        Returns:
            Score from 0-1
        """
        # Base score from overall effectiveness
        effectiveness_scores = self._tool_effectiveness.get(tool, [0.5])
        base_score = sum(effectiveness_scores) / len(effectiveness_scores)

        # Context-specific adjustment
        context_key = self._serialize_context(context)
        context_scores = self._context_performance[tool].get(context_key, [])

        if context_scores:
            context_score = sum(context_scores) / len(context_scores)
            # Weight context more heavily if we have data
            final_score = base_score * 0.3 + context_score * 0.7
        else:
            # No context-specific data, use base score
            final_score = base_score * 0.8  # Slight penalty for uncertainty

        return min(1.0, max(0.0, final_score))

    def _serialize_context(self, context: Dict[str, Any]) -> str:
        """Serialize context to string key."""
        # Sort keys for consistency
        sorted_items = sorted(context.items())
        return ";".join(f"{k}={v}" for k, v in sorted_items)

    def _generate_reasoning(
        self,
        tool: str,
        context: Dict[str, Any],
        score: float
    ) -> str:
        """Generate human-readable reasoning for recommendation."""
        uses = self._tool_total_count[tool]
        success_rate = self._tool_success_count[tool] / uses if uses > 0 else 0.0

        reasoning = (
            f"Based on {uses} previous uses, {tool} has {success_rate:.0%} success rate "
            f"and {score:.0%} estimated effectiveness for this context."
        )

        # Add context-specific insight if available
        context_key = self._serialize_context(context)
        context_scores = self._context_performance[tool].get(context_key, [])

        if context_scores:
            reasoning += (
                f" In similar contexts, achieved {sum(context_scores) / len(context_scores):.0%} "
                f"effectiveness across {len(context_scores)} uses."
            )

        return reasoning

    def _analyze_context_performance(
        self,
        tool: str
    ) -> tuple:
        """
        Analyze which contexts work best/worst for tool.

        Returns:
            (best_contexts, worst_contexts)
        """
        context_scores = self._context_performance[tool]

        if not context_scores:
            return [], []

        # Calculate average score per context
        context_avgs = {
            context: sum(scores) / len(scores)
            for context, scores in context_scores.items()
        }

        # Sort contexts
        sorted_contexts = sorted(context_avgs.items(), key=lambda x: x[1], reverse=True)

        # Top 3 best and worst
        best_contexts = [{"context": ctx, "avg_effectiveness": score} for ctx, score in sorted_contexts[:3]]
        worst_contexts = [{"context": ctx, "avg_effectiveness": score} for ctx, score in sorted_contexts[-3:]]

        return best_contexts, worst_contexts

    def get_stats(self) -> Dict[str, Any]:
        """
        Get tool learning statistics.

        Returns:
            Stats dict

        Example:
            stats = learner.get_stats()
            print(f"Tools tracked: {stats['total_tools']}")
            print(f"Total usages: {stats['total_usages']}")
        """
        return {
            "total_tools": len(self._tool_total_count),
            "total_usages": len(self._usage_history),
            "avg_tool_effectiveness": sum(
                sum(scores) / len(scores)
                for scores in self._tool_effectiveness.values()
                if scores
            ) / len(self._tool_effectiveness) if self._tool_effectiveness else 0.0,
            "most_used_tool": max(self._tool_total_count, key=self._tool_total_count.get) if self._tool_total_count else None,
            "highest_success_rate_tool": max(
                (
                    (tool, self._tool_success_count[tool] / self._tool_total_count[tool])
                    for tool in self._tool_total_count
                ),
                key=lambda x: x[1],
                default=(None, 0)
            )[0],
        }
