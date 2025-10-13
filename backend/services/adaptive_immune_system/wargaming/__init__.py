"""
Wargaming Module - Automated security patch validation through attack simulation.

Components:
- WorkflowGenerator: Generates GitHub Actions workflows
- ExploitTemplateLibrary: CWE-specific exploit templates
- EvidenceCollector: Collects evidence from workflow runs
- VerdictCalculator: Calculates verdicts and confidence scores
- WargameOrchestrator: Orchestrates complete wargaming workflow

Features:
- GitHub Actions integration
- Multi-language exploit support (Python, JavaScript, bash)
- Automatic verdict calculation
- Auto-merge for high-confidence successes
- HITL escalation for edge cases
- Comprehensive evidence collection
"""

from .workflow_generator import (
    WorkflowGenerator,
    WorkflowStep,
    WorkflowJob,
    WorkflowConfig,
    ExploitContext,
)

from .exploit_templates import ExploitTemplateLibrary

from .evidence_collector import (
    EvidenceCollector,
    StepEvidence,
    WorkflowRunEvidence,
    WargameEvidence,
)

from .verdict_calculator import (
    VerdictCalculator,
    VerdictScore,
)

from .wargame_orchestrator import (
    WargameOrchestrator,
    WargameConfig,
    WargameReport,
)

__all__ = [
    # Workflow Generator
    "WorkflowGenerator",
    "WorkflowStep",
    "WorkflowJob",
    "WorkflowConfig",
    "ExploitContext",
    # Exploit Templates
    "ExploitTemplateLibrary",
    # Evidence Collector
    "EvidenceCollector",
    "StepEvidence",
    "WorkflowRunEvidence",
    "WargameEvidence",
    # Verdict Calculator
    "VerdictCalculator",
    "VerdictScore",
    # Orchestrator
    "WargameOrchestrator",
    "WargameConfig",
    "WargameReport",
]
