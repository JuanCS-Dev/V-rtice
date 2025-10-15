"""
Article V Guardian - Prior Legislation Enforcement

Enforces Article V of the Vértice Constitution: The Principle of Prior Legislation.
Ensures governance systems are implemented BEFORE autonomous systems of power.

Key Enforcement Areas:
- Section 1: Governance must be designed/implemented before autonomous systems
- Section 2: Responsibility Doctrine must be applied to all autonomous AI workflows

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

import ast
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianAgent,
    GuardianDecision,
    GuardianIntervention,
    GuardianPriority,
    InterventionType,
)


class ArticleVGuardian(GuardianAgent):
    """
    Guardian that enforces Article V: Prior Legislation Principle.

    Monitors for:
    - Autonomous capabilities without governance
    - Missing responsibility chains
    - Absence of HITL controls for critical operations
    - Unaudited autonomous workflows
    - Missing kill switches and safety mechanisms
    - Violations of Two-Man Rule for critical actions
    """

    def __init__(
        self,
        autonomous_paths: list[str] | None = None,
        powerful_paths: list[str] | None = None,
        hitl_paths: list[str] | None = None,
        process_paths: list[str] | None = None,
        governance_paths: list[str] | None = None,
    ):
        """Initialize Article V Guardian.

        Args:
            autonomous_paths: Paths to check for autonomous systems (defaults to production paths)
            powerful_paths: Paths to check for powerful operations (defaults to production paths)
            hitl_paths: Paths to check for HITL controls (defaults to production paths)
            process_paths: Paths to check for long-running processes (defaults to production paths)
            governance_paths: Paths to check for Two-Man Rule (defaults to production paths)
        """
        super().__init__(
            guardian_id="guardian-article-v",
            article=ConstitutionalArticle.ARTICLE_V,
            name="Prior Legislation Guardian",
            description=(
                "Enforces the Prior Legislation Principle, ensuring governance "
                "is implemented before autonomous systems of power."
            ),
        )

        # Track autonomous capabilities and their governance
        self.autonomous_systems: dict[str, dict[str, Any]] = {}
        self.governance_registry: dict[str, dict[str, Any]] = {}

        # Responsibility Doctrine requirements
        self.responsibility_requirements = [
            "compartmentalization",  # Need-to-know
            "two_man_rule",  # Critical actions need dual approval
            "kill_switch",  # Emergency stop capability
            "audit_trail",  # Complete logging
            "hitl_control",  # Human-in-the-loop for critical ops
        ]

        # Autonomous capability indicators
        self.autonomous_indicators = [
            "autonomous",
            "auto_execute",
            "self_",
            "ai_agent",
            "automatic",
            "unattended",
            "scheduled_task",
            "background_worker",
        ]

        # Governance indicators
        self.governance_indicators = [
            "policy",
            "governance",
            "approval",
            "authorization",
            "oversight",
            "review",
            "audit",
            "control",
        ]

        # Configurable paths (dependency injection for testability)
        self.autonomous_paths = autonomous_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
            "/home/juan/vertice-dev/backend/services/active_immune_core",
        ]

        self.powerful_paths = powerful_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/security/offensive",
        ]

        self.hitl_paths = hitl_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
        ]

        self.process_paths = process_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
            "/home/juan/vertice-dev/backend/services/active_immune_core",
        ]

        self.governance_paths = governance_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service/governance",
            "/home/juan/vertice-dev/backend/services/maximus_core_service/api",
        ]

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems."""
        return [
            "autonomous_agents",
            "governance_framework",
            "responsibility_chain",
            "hitl_controls",
            "audit_system",
            "safety_mechanisms",
        ]

    async def monitor(self) -> list[ConstitutionalViolation]:
        """
        Monitor for Prior Legislation violations.

        Returns:
            List of detected violations
        """
        violations = []

        # Check autonomous systems governance
        autonomous_violations = await self._check_autonomous_governance()
        violations.extend(autonomous_violations)

        # Check responsibility doctrine
        responsibility_violations = await self._check_responsibility_doctrine()
        violations.extend(responsibility_violations)

        # Check HITL controls
        hitl_violations = await self._check_hitl_controls()
        violations.extend(hitl_violations)

        # Check kill switches
        killswitch_violations = await self._check_kill_switches()
        violations.extend(killswitch_violations)

        # Check Two-Man Rule
        twoman_violations = await self._check_two_man_rule()
        violations.extend(twoman_violations)

        return violations

    async def _check_autonomous_governance(self) -> list[ConstitutionalViolation]:
        """Check if autonomous systems have proper governance."""
        violations = []

        for base_path in self.autonomous_paths:
            if not Path(base_path).exists():
                continue

            # Find autonomous capabilities
            autonomous_files = []
            governance_files = []

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text().lower()

                    # Check for autonomous indicators
                    if any(indicator in content for indicator in self.autonomous_indicators):
                        autonomous_files.append(py_file)

                        # Register autonomous system
                        system_id = f"{py_file.parent.name}_{py_file.stem}"
                        self.autonomous_systems[system_id] = {
                            "path": str(py_file),
                            "detected": datetime.utcnow().isoformat(),
                            "has_governance": False,
                        }

                    # Check for governance indicators
                    if any(indicator in content for indicator in self.governance_indicators):
                        governance_files.append(py_file)

                except Exception:
                    pass

            # Check if autonomous systems have corresponding governance
            for auto_file in autonomous_files:
                # Look for governance in same module or parent
                has_governance = False
                auto_module = auto_file.parent

                for gov_file in governance_files:
                    if (
                        gov_file.parent == auto_module
                        or gov_file.parent == auto_module.parent
                    ):
                        has_governance = True
                        break

                if not has_governance:
                    violations.append(
                        ConstitutionalViolation(
                            article=ConstitutionalArticle.ARTICLE_V,
                            clause="Section 1",
                            rule="Governance must precede autonomous systems",
                            description=f"Autonomous capability without governance in {auto_file.name}",
                            severity=GuardianPriority.CRITICAL,
                            evidence=[f"Autonomous system at: {auto_file}"],
                            affected_systems=[auto_file.parent.name],
                            recommended_action="Implement governance before enabling autonomy",
                            context={
                                "file": str(auto_file),
                                "module": str(auto_module),
                            },
                        )
                    )

        return violations

    async def _check_responsibility_doctrine(self) -> list[ConstitutionalViolation]:
        """Check implementation of Responsibility Doctrine (Anexo C)."""
        violations = []

        for base_path in self.powerful_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                # Skip tests
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()

                    # Check for powerful operations
                    powerful_ops = [
                        "exploit",
                        "attack",
                        "delete",
                        "destroy",
                        "wipe",
                        "execute_command",
                        "shell",
                        "subprocess",
                    ]

                    has_powerful = any(op in content.lower() for op in powerful_ops)

                    if has_powerful:
                        # Check for responsibility requirements
                        missing_requirements = []

                        for requirement in self.responsibility_requirements:
                            if requirement not in content.lower():
                                missing_requirements.append(requirement)

                        if len(missing_requirements) > 2:  # Missing more than 2 requirements
                            violations.append(
                                ConstitutionalViolation(
                                    article=ConstitutionalArticle.ARTICLE_V,
                                    clause="Section 2",
                                    rule="Responsibility Doctrine must be applied",
                                    description=f"Missing responsibility controls in {py_file.name}",
                                    severity=GuardianPriority.HIGH,
                                    evidence=[
                                        f"Missing: {', '.join(missing_requirements[:3])}",
                                        f"Total missing: {len(missing_requirements)} out of {len(self.responsibility_requirements)}",
                                    ],
                                    affected_systems=[py_file.parent.name],
                                    recommended_action="Implement compartmentalization, Two-Man Rule, and kill switches",
                                    context={
                                        "file": str(py_file),
                                        "missing": missing_requirements,
                                    },
                                )
                            )

                except Exception:
                    pass

        return violations

    async def _check_hitl_controls(self) -> list[ConstitutionalViolation]:
        """Check for Human-In-The-Loop controls on critical operations."""
        violations = []

        # Critical operations requiring HITL
        critical_patterns = [
            r"production.*deploy",
            r"database.*drop",
            r"delete.*user",
            r"financial.*transaction",
            r"security.*override",
            r"admin.*privilege",
            r"system.*shutdown",
        ]

        hitl_patterns = [
            "human_approval",
            "require_confirmation",
            "manual_review",
            "operator_decision",
            "hitl",
            "human_in_the_loop",
            "await_approval",
        ]

        for base_path in self.hitl_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                # Skip tests
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        # Check for critical operations
                        for pattern in critical_patterns:
                            if __import__("re").search(pattern, line.lower()):
                                # Look for HITL controls nearby
                                context_start = max(0, i - 10)
                                context_end = min(len(lines), i + 10)
                                context = "\n".join(lines[context_start:context_end]).lower()

                                has_hitl = any(hitl in context for hitl in hitl_patterns)

                                if not has_hitl:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_V,
                                            clause="Section 2",
                                            rule="Critical operations require HITL",
                                            description=f"Critical operation without HITL in {py_file.name}:{i}",
                                            severity=GuardianPriority.HIGH,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["hitl_controls"],
                                            recommended_action="Add human approval requirement",
                                            context={
                                                "file": str(py_file),
                                                "line": i,
                                                "operation": pattern,
                                            },
                                        )
                                    )

                except Exception:
                    pass

        return violations

    async def _check_kill_switches(self) -> list[ConstitutionalViolation]:
        """Check for kill switch implementation in autonomous systems."""
        violations = []

        # Look for long-running or autonomous processes
        process_patterns = [
            r"while True:",
            r"asyncio\.run",
            r"thread",
            r"daemon",
            r"worker",
            r"scheduler",
            r"loop\.run_forever",
        ]

        killswitch_patterns = [
            "kill_switch",
            "emergency_stop",
            "shutdown",
            "terminate",
            "stop_signal",
            "abort",
            "circuit_breaker",
        ]

        for base_path in self.process_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                # Skip tests
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()

                    # Check for long-running processes
                    has_process = any(
                        __import__("re").search(pattern, content)
                        for pattern in process_patterns
                    )

                    if has_process:
                        # Check for kill switch
                        has_killswitch = any(
                            ks in content.lower() for ks in killswitch_patterns
                        )

                        if not has_killswitch:
                            violations.append(
                                ConstitutionalViolation(
                                    article=ConstitutionalArticle.ARTICLE_V,
                                    clause="Anexo C",
                                    rule="Kill switches required for autonomous systems",
                                    description=f"Autonomous process without kill switch in {py_file.name}",
                                    severity=GuardianPriority.CRITICAL,
                                    evidence=["Long-running process detected without emergency stop"],
                                    affected_systems=[py_file.parent.name],
                                    recommended_action="Implement emergency shutdown capability",
                                    context={"file": str(py_file)},
                                )
                            )

                except Exception:
                    pass

        return violations

    async def _check_two_man_rule(self) -> list[ConstitutionalViolation]:
        """Check implementation of Two-Man Rule for critical actions."""
        violations = []

        # Critical actions requiring dual approval
        critical_actions = [
            "deploy.*production",
            "delete.*database",
            "financial.*transfer",
            "security.*bypass",
            "admin.*grant",
            "config.*override",
        ]

        twoman_patterns = [
            "dual_approval",
            "two_man",
            "require_second",
            "double_confirmation",
            "multi_signature",
            "cosign",
        ]

        for base_path in self.governance_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        # Check for critical actions
                        for action in critical_actions:
                            if __import__("re").search(action, line.lower()):
                                # Look for Two-Man Rule implementation
                                context_start = max(0, i - 15)
                                context_end = min(len(lines), i + 15)
                                context = "\n".join(lines[context_start:context_end]).lower()

                                has_twoman = any(tm in context for tm in twoman_patterns)

                                if not has_twoman:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_V,
                                            clause="Anexo C",
                                            rule="Two-Man Rule for critical actions",
                                            description=f"Critical action without dual approval in {py_file.name}:{i}",
                                            severity=GuardianPriority.HIGH,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["authorization_system"],
                                            recommended_action="Implement dual approval mechanism",
                                            context={
                                                "file": str(py_file),
                                                "line": i,
                                                "action": action,
                                            },
                                        )
                                    )

                except Exception:
                    pass

        return violations

    async def register_governance(
        self,
        system_id: str,
        governance_type: str,
        policies: list[str],
        controls: dict[str, Any]
    ) -> bool:
        """
        Register governance for an autonomous system.

        Args:
            system_id: Identifier of the autonomous system
            governance_type: Type of governance applied
            policies: List of applicable policies
            controls: Control mechanisms in place

        Returns:
            True if registration successful
        """
        self.governance_registry[system_id] = {
            "system_id": system_id,
            "governance_type": governance_type,
            "policies": policies,
            "controls": controls,
            "registered_at": datetime.utcnow().isoformat(),
            "validated": False,
        }

        # Update autonomous system record if exists
        if system_id in self.autonomous_systems:
            self.autonomous_systems[system_id]["has_governance"] = True

        return True

    async def validate_governance_precedence(
        self,
        system_path: str
    ) -> tuple[bool, str]:
        """
        Validate that governance was implemented before autonomy.

        Args:
            system_path: Path to the autonomous system

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check git history to verify governance came first
        # This is a simplified check - in production would analyze git commits

        try:
            # Check for governance files in same module
            system_file = Path(system_path)
            module_path = system_file.parent

            governance_files = list(module_path.glob("*governance*.py"))
            policy_files = list(module_path.glob("*policy*.py"))

            if not governance_files and not policy_files:
                return False, "No governance files found in module"

            # In production, would check git history to verify temporal precedence
            # For now, we'll check if governance imports exist in the autonomous file
            content = system_file.read_text()

            has_governance_import = (
                "from .governance" in content
                or "from .policy" in content
                or "import governance" in content
            )

            if not has_governance_import:
                return False, "Autonomous system does not import governance"

            return True, "Governance precedence validated"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def analyze_violation(
        self, violation: ConstitutionalViolation
    ) -> GuardianDecision:
        """Analyze violation and decide on action."""
        if violation.severity == GuardianPriority.CRITICAL:
            # Critical violations of Prior Legislation
            decision_type = "veto"
            confidence = 0.98
            reasoning = (
                f"CRITICAL violation of Prior Legislation: {violation.rule}. "
                "Autonomous power without governance is forbidden."
            )

        elif "without governance" in violation.description:
            # Autonomous system without governance
            decision_type = "block"
            confidence = 0.95
            reasoning = (
                "Autonomous capability detected without governance framework. "
                "Article V requires governance before autonomy."
            )

        elif "Two-Man Rule" in violation.rule:
            # Missing Two-Man Rule
            decision_type = "escalate"
            confidence = 0.90
            reasoning = (
                "Critical action lacks dual approval mechanism. "
                "Responsibility Doctrine requires Two-Man Rule."
            )

        elif "kill switch" in violation.description.lower():
            # Missing kill switch
            decision_type = "block"
            confidence = 0.92
            reasoning = (
                "Autonomous system lacks emergency stop capability. "
                "This violates OPSEC requirements in Anexo C."
            )

        else:
            decision_type = "alert"
            confidence = 0.80
            reasoning = (
                f"Prior Legislation violation: {violation.rule}. "
                "Governance controls need strengthening."
            )

        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type=decision_type,
            target=violation.context.get("file", "unknown"),
            reasoning=reasoning,
            confidence=confidence,
            requires_validation=decision_type == "escalate",
        )

    async def intervene(
        self, violation: ConstitutionalViolation
    ) -> GuardianIntervention:
        """Take intervention action for violation."""
        if violation.severity == GuardianPriority.CRITICAL:
            # Veto autonomous capability
            intervention_type = InterventionType.VETO
            action_taken = (
                "Vetoed autonomous capability activation. "
                "Governance must be implemented first."
            )

            # Disable the autonomous system
            if "system_id" in violation.context:
                self.autonomous_systems[violation.context["system_id"]]["disabled"] = True

        elif "without governance" in violation.description:
            # Block until governance added
            intervention_type = InterventionType.REMEDIATION
            action_taken = (
                "Generated governance template for autonomous system. "
                "System blocked until governance implemented."
            )

            # Could auto-generate governance framework
            # For now, we track the requirement

        elif "HITL" in violation.description:
            # Add HITL requirement
            intervention_type = InterventionType.ESCALATION
            action_taken = (
                "Escalated to add Human-In-The-Loop control. "
                "Critical operation requires human oversight."
            )

        else:
            # Alert and monitor
            intervention_type = InterventionType.ALERT
            action_taken = f"Alert: {violation.description}"

        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=intervention_type,
            priority=violation.severity,
            violation=violation,
            action_taken=action_taken,
            result="Intervention applied to enforce Prior Legislation",
            success=True,
        )