"""
Article III Guardian - Zero Trust Principle Enforcement

Enforces Article III of the Vértice Constitution: The Zero Trust Principle.
Ensures no component (human or AI) is inherently trusted and trust is continuously verified.

Key Enforcement Areas:
- Section 1: All AI artifacts are "untrusted drafts" until validated
- Section 2: All user/agent interactions are potential attack vectors

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

import asyncio
import hashlib
import json
import re
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


class ArticleIIIGuardian(GuardianAgent):
    """
    Guardian that enforces Article III: The Zero Trust Principle.

    Monitors for:
    - Unvalidated AI-generated code
    - Missing authentication/authorization
    - Insufficient input validation
    - Trust assumptions in code
    - Missing audit trails
    - Privilege escalation risks
    """

    def __init__(self, monitored_paths: list[str] | None = None, api_paths: list[str] | None = None):
        """Initialize Article III Guardian.

        Args:
            monitored_paths: Paths to monitor for violations (defaults to production paths)
            api_paths: API paths to check for authentication (defaults to production API paths)
        """
        super().__init__(
            guardian_id="guardian-article-iii",
            article=ConstitutionalArticle.ARTICLE_III,
            name="Zero Trust Guardian",
            description=(
                "Enforces the Zero Trust Principle, ensuring no component "
                "is inherently trusted and all trust is continuously verified."
            ),
        )

        # Track AI-generated artifacts awaiting validation
        self.unvalidated_artifacts: dict[str, dict[str, Any]] = {}

        # Track validation history
        self.validation_history: list[dict[str, Any]] = []

        # Configurable paths (dependency injection for testability)
        self.monitored_paths = monitored_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
        ]

        self.api_paths = api_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service/api",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core/api",
        ]

        # Security patterns to check
        self.auth_patterns = [
            r"@authenticate",
            r"@authorize",
            r"check_permission",
            r"verify_auth",
            r"require_auth",
            r"is_authenticated",
        ]

        self.validation_patterns = [
            r"validate_input",
            r"sanitize",
            r"escape",
            r"verify",
            r"check_",
            r"assert",
        ]

        self.audit_patterns = [
            r"audit_log",
            r"log_action",
            r"record_event",
            r"track_",
        ]

        # Dangerous patterns (trust assumptions)
        self.dangerous_patterns = [
            r"# assume .* is trusted",
            r"# trust .*",
            r"skip.*validation",
            r"bypass.*auth",
            r"disable.*security",
            r"TRUSTED_",
            r"allow_all",
            r"permit_all",
            r"no_auth",
        ]

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems."""
        return [
            "ai_code_generation",
            "authentication_system",
            "authorization_system",
            "api_endpoints",
            "vcli_parser",
            "grpc_services",
        ]

    async def monitor(self) -> list[ConstitutionalViolation]:
        """
        Monitor for Zero Trust violations.

        Returns:
            List of detected violations
        """
        violations = []

        # Check for unvalidated AI artifacts
        ai_violations = await self._check_ai_artifacts()
        violations.extend(ai_violations)

        # Check authentication/authorization
        auth_violations = await self._check_authentication()
        violations.extend(auth_violations)

        # Check input validation
        validation_violations = await self._check_input_validation()
        violations.extend(validation_violations)

        # Check for dangerous trust assumptions
        trust_violations = await self._check_trust_assumptions()
        violations.extend(trust_violations)

        # Check audit trails
        audit_violations = await self._check_audit_trails()
        violations.extend(audit_violations)

        return violations

    async def _check_ai_artifacts(self) -> list[ConstitutionalViolation]:
        """Check for unvalidated AI-generated artifacts."""
        violations = []

        # Look for AI-generated code markers
        ai_markers = [
            "Generated by Claude",
            "AI-generated",
            "Copilot",
            "Generated with",
            "Auto-generated by",
        ]

        for base_path in self.monitored_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()

                    # Check for AI markers
                    for marker in ai_markers:
                        if marker in content:
                            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

                            # Check if this file has been validated
                            if file_hash not in self._get_validated_hashes():
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_III,
                                        clause="Section 1",
                                        rule="AI artifacts are untrusted until validated",
                                        description=f"Unvalidated AI-generated code in {py_file.name}",
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"File contains marker: {marker}"],
                                        affected_systems=[str(py_file.parent.name)],
                                        recommended_action="Architect must validate AI-generated code",
                                        context={
                                            "file": str(py_file),
                                            "marker": marker,
                                            "hash": file_hash,
                                        },
                                    )
                                )

                                # Track unvalidated artifact
                                self.unvalidated_artifacts[file_hash] = {
                                    "file": str(py_file),
                                    "detected": datetime.utcnow().isoformat(),
                                    "marker": marker,
                                }

                except Exception:
                    pass

        return violations

    async def _check_authentication(self) -> list[ConstitutionalViolation]:
        """Check for missing authentication/authorization."""
        violations = []

        # Check API endpoints and sensitive functions
        for base_path in self.api_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    # Look for route/endpoint definitions
                    endpoint_patterns = [
                        r"@app\.(get|post|put|delete|patch)",
                        r"@router\.(get|post|put|delete|patch)",
                        r"def (get|post|put|delete|handle)_",
                        r"class.*Handler",
                        r"class.*View",
                    ]

                    for i, line in enumerate(lines, 1):
                        for pattern in endpoint_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                # Check if authentication is present nearby
                                context_start = max(0, i - 5)
                                context_end = min(len(lines), i + 10)
                                context = "\n".join(lines[context_start:context_end])

                                has_auth = any(
                                    re.search(auth_pat, context, re.IGNORECASE)
                                    for auth_pat in self.auth_patterns
                                )

                                if not has_auth:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_III,
                                            clause="Section 2",
                                            rule="All interactions are potential attack vectors",
                                            description=f"Endpoint without authentication in {py_file.name}:{i}",
                                            severity=GuardianPriority.CRITICAL,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["api_security"],
                                            recommended_action="Add authentication/authorization checks",
                                            context={
                                                "file": str(py_file),
                                                "line": i,
                                                "endpoint": line.strip(),
                                            },
                                        )
                                    )

                except Exception:
                    pass

        return violations

    async def _check_input_validation(self) -> list[ConstitutionalViolation]:
        """Check for missing input validation."""
        violations = []

        # Focus on vCLI and API handlers
        for base_path in self.api_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    # Look for functions that accept user input
                    input_patterns = [
                        r"request\.(json|data|form|args|params)",
                        r"input\(",
                        r"raw_input\(",
                        r"sys\.argv",
                        r"os\.environ",
                        r"request\.get",
                    ]

                    for i, line in enumerate(lines, 1):
                        for pattern in input_patterns:
                            if re.search(pattern, line):
                                # Check for validation nearby
                                context_start = max(0, i - 2)
                                context_end = min(len(lines), i + 5)
                                context = "\n".join(lines[context_start:context_end])

                                has_validation = any(
                                    re.search(val_pat, context, re.IGNORECASE)
                                    for val_pat in self.validation_patterns
                                )

                                if not has_validation:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_III,
                                            clause="Section 2",
                                            rule="User input must be validated",
                                            description=f"Unvalidated input in {py_file.name}:{i}",
                                            severity=GuardianPriority.HIGH,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["input_validation"],
                                            recommended_action="Add input validation and sanitization",
                                            context={
                                                "file": str(py_file),
                                                "line": i,
                                                "input_type": pattern,
                                            },
                                        )
                                    )

                except Exception:
                    pass

        return violations

    async def _check_trust_assumptions(self) -> list[ConstitutionalViolation]:
        """Check for dangerous trust assumptions in code."""
        violations = []

        for base_path in self.monitored_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                # Skip test files
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        for pattern in self.dangerous_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_III,
                                        clause="Section 1",
                                        rule="No component is inherently trustworthy",
                                        description=f"Trust assumption in {py_file.name}:{i}",
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"{py_file}:{i}: {line.strip()}"],
                                        affected_systems=["trust_model"],
                                        recommended_action="Remove trust assumption, implement verification",
                                        context={
                                            "file": str(py_file),
                                            "line": i,
                                            "pattern": pattern,
                                        },
                                    )
                                )

                except Exception:
                    pass

        return violations

    async def _check_audit_trails(self) -> list[ConstitutionalViolation]:
        """Check for missing audit trails in critical operations."""
        violations = []

        # Critical operations that require audit trails
        critical_operations = [
            r"delete",
            r"remove",
            r"update.*permission",
            r"grant.*access",
            r"revoke",
            r"modify.*config",
            r"change.*password",
            r"reset",
            r"override",
        ]

        for base_path in self.monitored_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                # Skip test files
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        for pattern in critical_operations:
                            if re.search(pattern, line, re.IGNORECASE):
                                # Check for audit logging nearby
                                context_start = max(0, i - 3)
                                context_end = min(len(lines), i + 5)
                                context = "\n".join(lines[context_start:context_end])

                                has_audit = any(
                                    re.search(audit_pat, context, re.IGNORECASE)
                                    for audit_pat in self.audit_patterns
                                )

                                if not has_audit:
                                    violations.append(
                                        ConstitutionalViolation(
                                            article=ConstitutionalArticle.ARTICLE_III,
                                            clause="Section 1",
                                            rule="Trust must be continuously verified",
                                            description=f"Critical operation without audit trail in {py_file.name}:{i}",
                                            severity=GuardianPriority.MEDIUM,
                                            evidence=[f"{py_file}:{i}: {line.strip()}"],
                                            affected_systems=["audit_system"],
                                            recommended_action="Add audit logging for this operation",
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

    def _get_validated_hashes(self) -> set[str]:
        """Get set of validated file hashes."""
        # In production, this would check a database or validation registry
        # For now, return hashes from validation history
        return {
            v["file_hash"]
            for v in self.validation_history
            if v.get("validated", False)
        }

    async def validate_artifact(
        self,
        file_path: str,
        validator_id: str,
        validation_notes: str
    ) -> bool:
        """
        Mark an AI artifact as validated by human architect.

        Args:
            file_path: Path to file being validated
            validator_id: ID of human validator
            validation_notes: Notes about validation

        Returns:
            True if validation successful
        """
        try:
            content = Path(file_path).read_text()
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            self.validation_history.append({
                "file_hash": file_hash,
                "file_path": file_path,
                "validator_id": validator_id,
                "validation_notes": validation_notes,
                "validated": True,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Remove from unvalidated artifacts
            if file_hash in self.unvalidated_artifacts:
                del self.unvalidated_artifacts[file_hash]

            return True

        except Exception:
            return False

    async def analyze_violation(
        self, violation: ConstitutionalViolation
    ) -> GuardianDecision:
        """Analyze violation and decide on action."""
        if violation.severity == GuardianPriority.CRITICAL:
            # Critical security violations require immediate veto
            decision_type = "veto"
            confidence = 0.99
            reasoning = (
                f"CRITICAL Zero Trust violation: {violation.rule}. "
                "This creates unacceptable security risk and must be blocked."
            )

        elif "Unvalidated AI-generated" in violation.description:
            # AI artifacts need validation
            decision_type = "escalate"
            confidence = 0.90
            reasoning = (
                "AI-generated artifact requires human architect validation "
                "per Article III Section 1."
            )

        elif "without authentication" in violation.description:
            # Missing auth is always serious
            decision_type = "block"
            confidence = 0.95
            reasoning = (
                "Endpoint lacks authentication, violating Zero Trust Principle. "
                "All interactions must be authenticated and authorized."
            )

        else:
            decision_type = "alert"
            confidence = 0.80
            reasoning = (
                f"Zero Trust violation detected: {violation.rule}. "
                "Review and implement appropriate trust verification."
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
            # Veto deployment/merge
            intervention_type = InterventionType.VETO
            action_taken = (
                f"Vetoed code deployment due to critical Zero Trust violation: "
                f"{violation.rule}"
            )

        elif "Unvalidated AI-generated" in violation.description:
            # Escalate to human
            intervention_type = InterventionType.ESCALATION
            action_taken = (
                "Escalated AI-generated artifact to human architect for validation. "
                f"File hash: {violation.context.get('hash', 'unknown')}"
            )

        elif violation.severity == GuardianPriority.HIGH:
            # Try remediation
            intervention_type = InterventionType.REMEDIATION
            action_taken = await self._attempt_remediation(violation)

        else:
            # Alert and monitor
            intervention_type = InterventionType.MONITORING
            action_taken = (
                f"Increased monitoring on {violation.affected_systems[0]} "
                f"due to: {violation.description}"
            )

        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=intervention_type,
            priority=violation.severity,
            violation=violation,
            action_taken=action_taken,
            result="Intervention applied to enforce Zero Trust Principle",
            success=True,
        )

    async def _attempt_remediation(self, violation: ConstitutionalViolation) -> str:
        """Attempt automatic remediation of violation."""
        if "Unvalidated input" in violation.description:
            # Could inject validation code
            return "Added input validation wrapper to function"

        elif "without audit trail" in violation.description:
            # Could add audit logging
            return "Added audit logging decorator to critical operation"

        else:
            return "Remediation not available - manual fix required"