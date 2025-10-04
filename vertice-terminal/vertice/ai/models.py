"""
Autopilot Mode Data Models
===========================

Data structures for AI-powered autonomous workflow execution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum


class PhaseStatus(Enum):
    """Execution phase status."""
    PENDING = "pending"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepStatus(Enum):
    """Execution step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevel(Enum):
    """Risk level for execution phases."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ObjectiveType(Enum):
    """Type of autopilot objective."""
    PENTEST = "pentest"
    DEFEND = "defend"
    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    CUSTOM = "custom"


@dataclass
class ExecutionStep:
    """
    Single step in an execution phase.

    Example:
        step = ExecutionStep(
            id="1.1",
            name="Ping sweep 10.10.1.0/24",
            tool="nmap",
            command="nmap -sn 10.10.1.0/24",
            description="Find live hosts",
            estimated_time=30,
            requires_approval=False
        )
    """
    id: str
    name: str
    tool: str
    command: str
    description: str
    estimated_time: int = 60  # seconds
    requires_approval: bool = False
    status: StepStatus = StepStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[int]:
        """Calculate step duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    @property
    def is_complete(self) -> bool:
        """Check if step is complete (success or failure)."""
        return self.status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]


@dataclass
class ExecutionPhase:
    """
    Execution phase containing multiple steps.

    Example:
        phase = ExecutionPhase(
            id="1",
            name="Reconnaissance",
            description="Discover live hosts and enumerate services",
            steps=[step1, step2, step3],
            estimated_time=300,
            requires_approval=False,
            risk_level=RiskLevel.LOW
        )
    """
    id: str
    name: str
    description: str
    steps: List[ExecutionStep]
    estimated_time: int = 300  # seconds
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[int]:
        """Calculate phase duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    @property
    def progress(self) -> float:
        """Calculate phase progress (0.0 to 1.0)."""
        if not self.steps:
            return 0.0

        completed = sum(1 for step in self.steps if step.is_complete)
        return completed / len(self.steps)

    @property
    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return all(step.is_complete for step in self.steps)


@dataclass
class ExecutionPlan:
    """
    Complete execution plan with multiple phases.

    Example:
        plan = ExecutionPlan(
            name="Penetration Test - 10.10.1.0/24",
            objective=ObjectiveType.PENTEST,
            target="10.10.1.0/24",
            phases=[phase1, phase2, phase3],
            workspace="pentest-10.10.1.0"
        )
    """
    name: str
    objective: ObjectiveType
    target: str
    phases: List[ExecutionPhase]
    workspace: str
    description: Optional[str] = None
    estimated_time: int = 0  # Total estimated time in seconds
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approved_by_user: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate total estimated time from phases."""
        if self.estimated_time == 0:
            self.estimated_time = sum(phase.estimated_time for phase in self.phases)

    @property
    def total_steps(self) -> int:
        """Total number of steps across all phases."""
        return sum(len(phase.steps) for phase in self.phases)

    @property
    def completed_steps(self) -> int:
        """Number of completed steps."""
        return sum(
            sum(1 for step in phase.steps if step.is_complete)
            for phase in self.phases
        )

    @property
    def progress(self) -> float:
        """Overall plan progress (0.0 to 1.0)."""
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps

    @property
    def duration(self) -> Optional[int]:
        """Calculate plan duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all phases are complete."""
        return all(phase.is_complete for phase in self.phases)

    @property
    def current_phase(self) -> Optional[ExecutionPhase]:
        """Get currently executing phase."""
        for phase in self.phases:
            if phase.status == PhaseStatus.RUNNING:
                return phase
            if not phase.is_complete:
                return phase
        return None

    def get_phase_by_id(self, phase_id: str) -> Optional[ExecutionPhase]:
        """Get phase by ID."""
        for phase in self.phases:
            if phase.id == phase_id:
                return phase
        return None

    def get_step_by_id(self, step_id: str) -> Optional[ExecutionStep]:
        """Get step by ID (format: phase_id.step_num)."""
        for phase in self.phases:
            for step in phase.steps:
                if step.id == step_id:
                    return step
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for serialization."""
        return {
            "name": self.name,
            "objective": self.objective.value,
            "target": self.target,
            "workspace": self.workspace,
            "description": self.description,
            "estimated_time": self.estimated_time,
            "risk_level": self.risk_level.value,
            "total_steps": self.total_steps,
            "progress": self.progress,
            "phases": [
                {
                    "id": phase.id,
                    "name": phase.name,
                    "description": phase.description,
                    "estimated_time": phase.estimated_time,
                    "requires_approval": phase.requires_approval,
                    "risk_level": phase.risk_level.value,
                    "status": phase.status.value,
                    "progress": phase.progress,
                    "steps": [
                        {
                            "id": step.id,
                            "name": step.name,
                            "tool": step.tool,
                            "command": step.command,
                            "description": step.description,
                            "estimated_time": step.estimated_time,
                            "requires_approval": step.requires_approval,
                            "status": step.status.value
                        }
                        for step in phase.steps
                    ]
                }
                for phase in self.phases
            ]
        }


@dataclass
class PlanResult:
    """
    Result of plan execution.

    Contains execution statistics, findings, and generated report.
    """
    plan: ExecutionPlan
    success: bool
    total_duration: int  # seconds
    findings: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    report_path: Optional[str] = None
    workspace_path: Optional[str] = None

    @property
    def summary(self) -> str:
        """Generate execution summary."""
        status = "✅ Success" if self.success else "❌ Failed"
        duration_min = self.total_duration // 60

        summary = f"""
Execution Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: {status}
Duration: {duration_min} minutes
Steps: {self.plan.completed_steps}/{self.plan.total_steps}
Workspace: {self.plan.workspace}
"""

        if self.findings:
            summary += f"\nFindings:\n"
            for key, value in self.findings.items():
                summary += f"  - {key}: {value}\n"

        if self.errors:
            summary += f"\nErrors: {len(self.errors)}\n"
            for error in self.errors[:5]:  # Show first 5 errors
                summary += f"  - {error}\n"

        return summary
