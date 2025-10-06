"""Base classes and interfaces for ethical frameworks.

This module defines the abstract base class that all ethical frameworks must implement,
ensuring a consistent interface for ethical evaluation across the VÉRTICE platform.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class EthicalVerdict(str, Enum):
    """Possible verdicts from ethical evaluation."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"  # Approved with conditions


@dataclass
class EthicalFrameworkResult:
    """Result from an ethical framework evaluation.

    Attributes:
        framework_name: Name of the framework (kantian, consequentialist, etc.)
        approved: Whether the action is ethically approved
        confidence: Confidence score (0.0 to 1.0)
        veto: Whether this framework vetoes the decision (overrides others)
        explanation: Human-readable explanation of the decision
        reasoning_steps: List of reasoning steps taken
        verdict: Final verdict (APPROVED, REJECTED, CONDITIONAL)
        latency_ms: Time taken for evaluation in milliseconds
        metadata: Additional framework-specific data
    """

    framework_name: str
    approved: bool
    confidence: float
    veto: bool
    explanation: str
    reasoning_steps: List[str]
    verdict: EthicalVerdict
    latency_ms: int
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


@dataclass
class ActionContext:
    """Context for an action requiring ethical evaluation.

    Attributes:
        action_type: Type of action (offensive, defensive, policy_change, etc.)
        action_description: Detailed description of the proposed action
        system_component: Which component is proposing the action
        threat_data: Information about the threat (if applicable)
        target_info: Information about the target (IP, domain, etc.)
        impact_assessment: Estimated impact of the action
        alternatives: Alternative actions considered
        urgency: Urgency level (low, medium, high, critical)
        operator_context: Human operator information (if HITL)
    """

    action_type: str
    action_description: str
    system_component: str
    threat_data: Optional[Dict[str, Any]] = None
    target_info: Optional[Dict[str, Any]] = None
    impact_assessment: Optional[Dict[str, Any]] = None
    alternatives: Optional[List[Dict[str, Any]]] = None
    urgency: str = "medium"
    operator_context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate action context fields."""
        # Validate action_type
        valid_action_types = [
            "offensive_action",
            "auto_response",
            "threat_mitigation",
            "policy_update",
            "data_access",
            "surveillance",
            "monitoring",
            "threat_investigation",
            "red_team_operation",
            "malware_analysis",
            "vulnerability_patching",
            "security_improvement",
            "do_nothing",
        ]
        if not self.action_type:
            raise ValueError("action_type is required and cannot be empty")
        if len(self.action_type) > 100:
            raise ValueError("action_type must be less than 100 characters")

        # Validate action_description
        if not self.action_description:
            raise ValueError("action_description is required and cannot be empty")
        if len(self.action_description) < 10:
            raise ValueError(
                "action_description must be at least 10 characters (provide meaningful description)"
            )
        if len(self.action_description) > 1000:
            raise ValueError("action_description must be less than 1000 characters")

        # Validate system_component
        if not self.system_component:
            raise ValueError("system_component is required and cannot be empty")
        if len(self.system_component) > 100:
            raise ValueError("system_component must be less than 100 characters")

        # Validate urgency
        valid_urgency = ["low", "medium", "high", "critical"]
        if self.urgency not in valid_urgency:
            raise ValueError(
                f"urgency must be one of {valid_urgency}, got '{self.urgency}'"
            )

        # Validate threat_data if present
        if self.threat_data:
            if "severity" in self.threat_data:
                severity = self.threat_data["severity"]
                if not isinstance(severity, (int, float)) or not 0.0 <= severity <= 1.0:
                    raise ValueError(
                        "threat_data.severity must be a number between 0.0 and 1.0"
                    )

            if "confidence" in self.threat_data:
                confidence = self.threat_data["confidence"]
                if (
                    not isinstance(confidence, (int, float))
                    or not 0.0 <= confidence <= 1.0
                ):
                    raise ValueError(
                        "threat_data.confidence must be a number between 0.0 and 1.0"
                    )

        # Validate impact_assessment if present
        if self.impact_assessment:
            if "disruption_level" in self.impact_assessment:
                disruption = self.impact_assessment["disruption_level"]
                if (
                    not isinstance(disruption, (int, float))
                    or not 0.0 <= disruption <= 1.0
                ):
                    raise ValueError(
                        "impact_assessment.disruption_level must be a number between 0.0 and 1.0"
                    )

        logger.debug(
            f"ActionContext validated: {self.action_type} - {self.action_description[:50]}..."
        )


class EthicalFramework(ABC):
    """Abstract base class for all ethical frameworks.

    All ethical frameworks (Kantian, Consequentialist, Virtue Ethics, Principialism)
    must inherit from this class and implement the evaluate() method.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ethical framework.

        Args:
            config: Configuration dictionary for the framework
        """
        self.config = config or {}
        self.name = self.__class__.__name__.lower()

    @abstractmethod
    async def evaluate(self, action_context: ActionContext) -> EthicalFrameworkResult:
        """Evaluate an action ethically.

        Args:
            action_context: Context about the action to be evaluated

        Returns:
            EthicalFrameworkResult with the framework's verdict and reasoning
        """
        pass

    @abstractmethod
    def get_framework_principles(self) -> List[str]:
        """Get the core principles of this framework.

        Returns:
            List of core principles that guide this framework's decisions
        """
        pass

    def get_name(self) -> str:
        """Get the framework name.

        Returns:
            Name of the framework
        """
        return self.name

    def get_version(self) -> str:
        """Get the framework version.

        Returns:
            Version string
        """
        return self.config.get("version", "1.0.0")


class EthicalCache:
    """Simple in-memory cache for ethical decisions.

    Caches decisions for identical actions to reduce latency on repeated evaluations.
    """

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        """Initialize the cache.

        Args:
            max_size: Maximum number of cached decisions
            ttl_seconds: Time-to-live for cached decisions in seconds
        """
        self._cache: Dict[str, Tuple[EthicalFrameworkResult, float]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def get(self, cache_key: str) -> Optional[EthicalFrameworkResult]:
        """Get a cached decision.

        Args:
            cache_key: Unique key for the decision

        Returns:
            Cached result or None if not found/expired
        """
        import time

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.ttl_seconds:
                return result
            else:
                # Expired, remove it
                del self._cache[cache_key]

        return None

    def set(self, cache_key: str, result: EthicalFrameworkResult):
        """Cache a decision.

        Args:
            cache_key: Unique key for the decision
            result: Result to cache
        """
        import time

        # Evict oldest if at max size
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        self._cache[cache_key] = (result, time.time())

    def generate_key(self, action_context: ActionContext, framework_name: str) -> str:
        """Generate a cache key from action context.

        Args:
            action_context: Action context
            framework_name: Name of the framework

        Returns:
            Unique cache key string
        """
        import hashlib
        import json

        # Create a deterministic string from action context
        context_str = json.dumps(
            {
                "action_type": action_context.action_type,
                "action_description": action_context.action_description,
                "system_component": action_context.system_component,
                "urgency": action_context.urgency,
                "framework": framework_name,
            },
            sort_keys=True,
        )

        return hashlib.sha256(context_str.encode()).hexdigest()


class EthicalException(Exception):
    """Base exception for ethical framework errors."""

    pass


class VetoException(EthicalException):
    """Exception raised when a framework vetoes a decision."""

    def __init__(self, framework_name: str, reason: str):
        self.framework_name = framework_name
        self.reason = reason
        super().__init__(f"{framework_name} vetoed the decision: {reason}")
