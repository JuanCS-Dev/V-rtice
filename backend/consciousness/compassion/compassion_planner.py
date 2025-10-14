"""
Compassion Planner Module

Plans compassionate interventions based on detected suffering events.
Uses template-based approach with customizable intervention strategies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from .event_detector import EventType, SufferingEvent


class InterventionType(str, Enum):
    """Types of compassionate interventions."""

    IMMEDIATE_SUPPORT = "immediate_support"
    GUIDANCE = "guidance"
    ESCALATION = "escalation"
    MONITORING = "monitoring"
    RESOURCE_ALLOCATION = "resource_allocation"


@dataclass
class CompassionPlan:
    """
    Represents a plan for compassionate intervention.

    Attributes:
        plan_id: Unique identifier for this plan
        event: The suffering event that triggered this plan
        intervention_type: Type of intervention to perform
        actions: List of specific actions to take
        priority: Priority level from 1 (low) to 10 (critical)
        estimated_duration_minutes: Estimated time to execute plan
        resources_required: Resources needed for execution
        success_criteria: Criteria to determine if intervention succeeded
        created_at: When the plan was created
        metadata: Additional metadata
    """

    plan_id: UUID
    event: SufferingEvent
    intervention_type: InterventionType
    actions: List[str]
    priority: int
    estimated_duration_minutes: int
    resources_required: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate priority range."""
        if not isinstance(self.priority, int):
            raise ValueError(f"Priority must be int, got {type(self.priority)}")
        if not 1 <= self.priority <= 10:
            raise ValueError(f"Priority must be 1-10, got {self.priority}")
        if not isinstance(self.intervention_type, InterventionType):
            raise TypeError(f"intervention_type must be InterventionType enum")


class CompassionPlanner:
    """
    Plans compassionate interventions based on suffering events.

    Uses template-based planning with customizable strategies for each event type.
    Automatically determines intervention type, actions, and priority based on
    event severity and type.
    """

    # Intervention templates for each event type
    DISTRESS_TEMPLATES = {
        "high_severity": {
            "intervention_type": InterventionType.ESCALATION,
            "actions": [
                "Alert human operator immediately",
                "Pause non-critical operations",
                "Collect diagnostic information",
                "Activate emergency protocols"
            ],
            "resources": ["human_operator", "diagnostic_tools", "emergency_protocols"],
            "success_criteria": ["Human acknowledged alert", "Systems stabilized"],
            "duration": 15
        },
        "medium_severity": {
            "intervention_type": InterventionType.IMMEDIATE_SUPPORT,
            "actions": [
                "Provide error recovery guidance",
                "Allocate additional resources",
                "Monitor system closely",
                "Log incident for review"
            ],
            "resources": ["recovery_tools", "monitoring_system"],
            "success_criteria": ["Error rate decreased", "Recovery initiated"],
            "duration": 30
        },
        "low_severity": {
            "intervention_type": InterventionType.MONITORING,
            "actions": [
                "Log event for analysis",
                "Continue monitoring",
                "Prepare contingency plan"
            ],
            "resources": ["monitoring_system"],
            "success_criteria": ["Event logged", "No escalation needed"],
            "duration": 5
        }
    }

    CONFUSION_TEMPLATES = {
        "high_severity": {
            "intervention_type": InterventionType.GUIDANCE,
            "actions": [
                "Provide step-by-step clarification",
                "Offer alternative approaches",
                "Connect to knowledge base",
                "Escalate if confusion persists"
            ],
            "resources": ["knowledge_base", "guidance_system"],
            "success_criteria": ["Agent understands task", "Confusion resolved"],
            "duration": 20
        },
        "medium_severity": {
            "intervention_type": InterventionType.GUIDANCE,
            "actions": [
                "Provide contextual help",
                "Suggest similar examples",
                "Monitor understanding"
            ],
            "resources": ["knowledge_base"],
            "success_criteria": ["Agent proceeds with task"],
            "duration": 10
        },
        "low_severity": {
            "intervention_type": InterventionType.MONITORING,
            "actions": [
                "Offer assistance if needed",
                "Track resolution"
            ],
            "resources": ["monitoring_system"],
            "success_criteria": ["Agent self-resolves"],
            "duration": 5
        }
    }

    ISOLATION_TEMPLATES = {
        "high_severity": {
            "intervention_type": InterventionType.RESOURCE_ALLOCATION,
            "actions": [
                "Attempt to restore connections",
                "Provide alternative communication paths",
                "Alert network administrator",
                "Activate backup systems"
            ],
            "resources": ["network_tools", "backup_systems", "administrator"],
            "success_criteria": ["Connections restored", "Agent reintegrated"],
            "duration": 25
        },
        "medium_severity": {
            "intervention_type": InterventionType.IMMEDIATE_SUPPORT,
            "actions": [
                "Check network status",
                "Attempt reconnection",
                "Provide local resources"
            ],
            "resources": ["network_tools"],
            "success_criteria": ["Connection established"],
            "duration": 15
        },
        "low_severity": {
            "intervention_type": InterventionType.MONITORING,
            "actions": [
                "Monitor connectivity",
                "Log isolation event"
            ],
            "resources": ["monitoring_system"],
            "success_criteria": ["Normal connectivity resumed"],
            "duration": 5
        }
    }

    def __init__(self):
        """Initialize the compassion planner."""
        self._plans: List[CompassionPlan] = []

    def plan_intervention(self, event: SufferingEvent) -> CompassionPlan:
        """
        Create a compassion plan for a suffering event.

        Args:
            event: The suffering event to plan for

        Returns:
            CompassionPlan with appropriate interventions
        """
        # Determine severity category
        severity_category = self._categorize_severity(event.severity)

        # Select template based on event type
        template = self._select_template(event.event_type, severity_category)

        # Calculate priority (higher severity = higher priority)
        priority = self._calculate_priority(event.severity, event.event_type)

        # Create plan
        plan = CompassionPlan(
            plan_id=uuid4(),
            event=event,
            intervention_type=template["intervention_type"],
            actions=template["actions"].copy(),
            priority=priority,
            estimated_duration_minutes=template["duration"],
            resources_required=template["resources"].copy(),
            success_criteria=template["success_criteria"].copy(),
            metadata={"severity_category": severity_category}
        )

        self._plans.append(plan)
        return plan

    def _categorize_severity(self, severity: int) -> str:
        """
        Categorize severity into low/medium/high.

        Args:
            severity: Severity level 1-10

        Returns:
            Category string
        """
        if severity >= 8:
            return "high_severity"
        elif severity >= 5:
            return "medium_severity"
        else:
            return "low_severity"

    def _select_template(self, event_type: EventType, severity_category: str) -> Dict:
        """
        Select intervention template based on event type and severity.

        Args:
            event_type: Type of suffering event
            severity_category: Severity category

        Returns:
            Template dictionary
        """
        if event_type == EventType.DISTRESS:
            return self.DISTRESS_TEMPLATES[severity_category]
        elif event_type == EventType.CONFUSION:
            return self.CONFUSION_TEMPLATES[severity_category]
        elif event_type == EventType.ISOLATION:
            return self.ISOLATION_TEMPLATES[severity_category]
        else:
            # Unknown event type - use generic monitoring
            return {
                "intervention_type": InterventionType.MONITORING,
                "actions": ["Monitor event", "Log for analysis"],
                "resources": ["monitoring_system"],
                "success_criteria": ["Event resolved"],
                "duration": 5
            }

    def _calculate_priority(self, severity: int, event_type: EventType) -> int:
        """
        Calculate intervention priority.

        Priority is based on severity with adjustments for event type.
        Distress events get +1 priority, isolation gets +0.5 (rounded).

        Args:
            severity: Event severity 1-10
            event_type: Type of event

        Returns:
            Priority 1-10
        """
        priority = severity

        # Adjust based on event type
        if event_type == EventType.DISTRESS:
            priority += 1
        elif event_type == EventType.ISOLATION:
            priority += 0.5

        # Clamp to 1-10 range
        return max(1, min(10, int(priority)))

    def get_plan(self, plan_id: UUID) -> Optional[CompassionPlan]:
        """
        Retrieve a plan by ID.

        Args:
            plan_id: Plan identifier

        Returns:
            Plan if found, None otherwise
        """
        for plan in self._plans:
            if plan.plan_id == plan_id:
                return plan
        return None

    def get_plans_for_agent(
        self,
        agent_id: UUID,
        active_only: bool = False
    ) -> List[CompassionPlan]:
        """
        Get all plans for a specific agent.

        Args:
            agent_id: Agent identifier
            active_only: If True, only return high-priority plans

        Returns:
            List of plans for the agent
        """
        plans = [p for p in self._plans if p.event.agent_id == agent_id]

        if active_only:
            plans = [p for p in plans if p.priority >= 7]

        return sorted(plans, key=lambda p: p.priority, reverse=True)

    def get_high_priority_plans(self, threshold: int = 7) -> List[CompassionPlan]:
        """
        Get all high-priority plans.

        Args:
            threshold: Minimum priority level (default 7)

        Returns:
            List of high-priority plans, sorted by priority descending
        """
        plans = [p for p in self._plans if p.priority >= threshold]
        return sorted(plans, key=lambda p: p.priority, reverse=True)

    def clear_plans(self):
        """Clear all plans."""
        self._plans.clear()

    def __repr__(self) -> str:
        """String representation."""
        return f"CompassionPlanner(plans={len(self._plans)})"
