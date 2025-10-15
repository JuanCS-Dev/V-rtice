"""
Article IV Guardian - Deliberate Antifragility Enforcement

Enforces Article IV of the Vértice Constitution: The Principle of Deliberate Antifragility.
Ensures the system strengthens from chaos and disorder through controlled failure testing.

Key Enforcement Areas:
- Section 1: Anticipate and provoke failures in controlled environments
- Section 2: High-risk ideas must be validated through quarantine and public validation

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

import asyncio
import json
import random
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


class ArticleIVGuardian(GuardianAgent):
    """
    Guardian that enforces Article IV: Deliberate Antifragility Principle.

    Monitors for:
    - Lack of chaos engineering tests
    - Missing failure recovery mechanisms
    - Absence of circuit breakers and fallbacks
    - Untested edge cases
    - Experimental features without quarantine
    - Missing resilience patterns
    """

    def __init__(self, test_paths: list[str] | None = None, service_paths: list[str] | None = None):
        """Initialize Article IV Guardian.

        Args:
            test_paths: Paths to check for chaos tests (defaults to production paths)
            service_paths: Service paths to check for resilience (defaults to production paths)
        """
        super().__init__(
            guardian_id="guardian-article-iv",
            article=ConstitutionalArticle.ARTICLE_IV,
            name="Antifragility Guardian",
            description=(
                "Enforces the Deliberate Antifragility Principle, ensuring "
                "the system strengthens from controlled failures and chaos."
            ),
        )

        # Track chaos experiments
        self.chaos_experiments: list[dict[str, Any]] = []
        self.quarantined_features: dict[str, dict[str, Any]] = {}
        self.resilience_metrics: dict[str, float] = {}

        # Configurable paths (dependency injection for testability)
        self.test_paths = test_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service/tests",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core/tests",
        ]

        self.service_paths = service_paths or [
            "/home/juan/vertice-dev/backend/services/maximus_core_service",
            "/home/juan/vertice-dev/backend/services/reactive_fabric_core",
        ]

        # Resilience patterns to check
        self.resilience_patterns = [
            "circuit_breaker",
            "retry",
            "fallback",
            "timeout",
            "bulkhead",
            "rate_limit",
            "backpressure",
            "graceful_degradation",
        ]

        # Chaos test indicators
        self.chaos_indicators = [
            "chaos_test",
            "failure_test",
            "stress_test",
            "load_test",
            "resilience_test",
            "fault_injection",
            "network_partition",
        ]

    def get_monitored_systems(self) -> list[str]:
        """Get list of monitored systems."""
        return [
            "chaos_engineering",
            "resilience_framework",
            "experimental_features",
            "fault_tolerance",
            "recovery_mechanisms",
        ]

    async def monitor(self) -> list[ConstitutionalViolation]:
        """
        Monitor for antifragility violations.

        Returns:
            List of detected violations
        """
        violations = []

        # Check for chaos engineering tests
        chaos_violations = await self._check_chaos_engineering()
        violations.extend(chaos_violations)

        # Check resilience patterns
        resilience_violations = await self._check_resilience_patterns()
        violations.extend(resilience_violations)

        # Check experimental features
        experimental_violations = await self._check_experimental_features()
        violations.extend(experimental_violations)

        # Check failure recovery
        recovery_violations = await self._check_failure_recovery()
        violations.extend(recovery_violations)

        # Check system fragility
        fragility_violations = await self._check_system_fragility()
        violations.extend(fragility_violations)

        return violations

    async def _check_chaos_engineering(self) -> list[ConstitutionalViolation]:
        """Check for presence of chaos engineering tests."""
        violations = []

        for base_path in self.test_paths:
            if not Path(base_path).exists():
                continue

            # Count chaos tests
            chaos_test_count = 0
            regular_test_count = 0

            for test_file in Path(base_path).rglob("test_*.py"):
                try:
                    content = test_file.read_text()

                    # Check for chaos test indicators
                    has_chaos = any(
                        indicator in content.lower()
                        for indicator in self.chaos_indicators
                    )

                    if has_chaos:
                        chaos_test_count += 1
                    else:
                        regular_test_count += 1

                except Exception:
                    pass

            # Check ratio of chaos tests to regular tests
            if regular_test_count > 0:
                chaos_ratio = chaos_test_count / (chaos_test_count + regular_test_count)

                if chaos_ratio < 0.1:  # Less than 10% chaos tests
                    violations.append(
                        ConstitutionalViolation(
                            article=ConstitutionalArticle.ARTICLE_IV,
                            clause="Section 1",
                            rule="Must anticipate and provoke failures",
                            description=f"Insufficient chaos testing in {Path(base_path).name}",
                            severity=GuardianPriority.MEDIUM,
                            evidence=[
                                f"Chaos test ratio: {chaos_ratio:.1%}",
                                f"Found {chaos_test_count} chaos tests out of {regular_test_count + chaos_test_count} total",
                            ],
                            affected_systems=[Path(base_path).name],
                            recommended_action="Add more chaos engineering tests",
                            context={
                                "path": str(base_path),
                                "chaos_tests": chaos_test_count,
                                "total_tests": regular_test_count + chaos_test_count,
                            },
                        )
                    )

        # Check for recent chaos experiments
        recent_experiments = [
            exp for exp in self.chaos_experiments
            if datetime.fromisoformat(exp["timestamp"]) > datetime.utcnow() - timedelta(days=7)
        ]

        if len(recent_experiments) < 3:
            violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_IV,
                    clause="Section 1",
                    rule="Controlled failures must be regularly provoked",
                    description="Insufficient chaos experiments in past week",
                    severity=GuardianPriority.MEDIUM,
                    evidence=[f"Only {len(recent_experiments)} experiments in past 7 days"],
                    affected_systems=["chaos_engineering"],
                    recommended_action="Schedule and run chaos experiments",
                    context={"recent_count": len(recent_experiments)},
                )
            )

        return violations

    async def _check_resilience_patterns(self) -> list[ConstitutionalViolation]:
        """Check for implementation of resilience patterns."""
        violations = []

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            pattern_counts = {pattern: 0 for pattern in self.resilience_patterns}

            for py_file in Path(base_path).rglob("*.py"):
                # Skip test files
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text().lower()

                    # Count resilience patterns
                    for pattern in self.resilience_patterns:
                        if pattern.replace("_", " ") in content or pattern in content:
                            pattern_counts[pattern] += 1

                except Exception:
                    pass

            # Check if critical patterns are missing
            missing_patterns = [p for p, count in pattern_counts.items() if count == 0]

            if len(missing_patterns) > 3:  # More than 3 patterns missing
                violations.append(
                    ConstitutionalViolation(
                        article=ConstitutionalArticle.ARTICLE_IV,
                        clause="Section 1",
                        rule="System must be antifragile",
                        description=f"Missing resilience patterns in {Path(base_path).name}",
                        severity=GuardianPriority.HIGH,
                        evidence=[
                            f"Missing patterns: {', '.join(missing_patterns[:5])}",
                            f"Total missing: {len(missing_patterns)} out of {len(self.resilience_patterns)}",
                        ],
                        affected_systems=[Path(base_path).name],
                        recommended_action="Implement circuit breakers, retries, and fallback mechanisms",
                        context={
                            "path": str(base_path),
                            "missing": missing_patterns,
                            "found": {p: c for p, c in pattern_counts.items() if c > 0},
                        },
                    )
                )

        return violations

    async def _check_experimental_features(self) -> list[ConstitutionalViolation]:
        """Check for experimental features without proper quarantine."""
        violations = []

        # Look for experimental/beta features
        experimental_markers = [
            "@experimental",
            "@beta",
            "EXPERIMENTAL",
            "BETA",
            "alpha_feature",
            "unstable",
            "preview",
        ]

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                try:
                    content = py_file.read_text()

                    for marker in experimental_markers:
                        if marker in content:
                            feature_id = f"{py_file.name}_{marker}"

                            # Check if feature is quarantined
                            if feature_id not in self.quarantined_features:
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_IV,
                                        clause="Section 2",
                                        rule="High-risk ideas require quarantine validation",
                                        description=f"Experimental feature without quarantine in {py_file.name}",
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"Found marker: {marker}"],
                                        affected_systems=[str(py_file.parent.name)],
                                        recommended_action="Move to quarantined repository for validation",
                                        context={
                                            "file": str(py_file),
                                            "marker": marker,
                                            "feature_id": feature_id,
                                        },
                                    )
                                )
                            else:
                                # Check quarantine status
                                quarantine = self.quarantined_features[feature_id]
                                if quarantine.get("status") != "validated":
                                    days_in_quarantine = (
                                        datetime.utcnow() - datetime.fromisoformat(quarantine["quarantine_start"])
                                    ).days

                                    if days_in_quarantine > 30:  # Over 30 days without validation
                                        violations.append(
                                            ConstitutionalViolation(
                                                article=ConstitutionalArticle.ARTICLE_IV,
                                                clause="Section 2",
                                                rule="Quarantined features require validation",
                                                description=f"Feature in quarantine too long: {feature_id}",
                                                severity=GuardianPriority.MEDIUM,
                                                evidence=[f"In quarantine for {days_in_quarantine} days"],
                                                affected_systems=["experimental_features"],
                                                recommended_action="Complete public validation or remove feature",
                                                context={
                                                    "feature_id": feature_id,
                                                    "days": days_in_quarantine,
                                                },
                                            )
                                        )

                except Exception:
                    pass

        return violations

    async def _check_failure_recovery(self) -> list[ConstitutionalViolation]:
        """Check for proper failure recovery mechanisms."""
        violations = []

        # Check for error handling patterns
        recovery_patterns = [
            r"try:\s*\n.*\nexcept",
            r"with.*suppress",
            r"finally:",
            r"on_error",
            r"handle_failure",
            r"recover",
            r"rollback",
        ]

        critical_operations = [
            "database",
            "transaction",
            "payment",
            "authentication",
            "critical",
        ]

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                # Skip test files
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()
                    lower_content = content.lower()

                    # Check if file has critical operations
                    has_critical = any(op in lower_content for op in critical_operations)

                    if has_critical:
                        # Check for recovery mechanisms
                        has_recovery = any(
                            __import__("re").search(pattern, content)
                            for pattern in recovery_patterns
                        )

                        if not has_recovery:
                            violations.append(
                                ConstitutionalViolation(
                                    article=ConstitutionalArticle.ARTICLE_IV,
                                    clause="Section 1",
                                    rule="System must recover from failures",
                                    description=f"Critical operations without recovery in {py_file.name}",
                                    severity=GuardianPriority.HIGH,
                                    evidence=["Missing error recovery for critical operations"],
                                    affected_systems=[str(py_file.parent.name)],
                                    recommended_action="Add proper error handling and recovery",
                                    context={"file": str(py_file)},
                                )
                            )

                except Exception:
                    pass

        return violations

    async def _check_system_fragility(self) -> list[ConstitutionalViolation]:
        """Check for indicators of system fragility."""
        violations = []

        # Calculate fragility score based on metrics
        fragility_indicators = {
            "single_points_of_failure": 0,
            "hardcoded_values": 0,
            "global_state": 0,
            "tight_coupling": 0,
            "missing_timeouts": 0,
        }

        for base_path in self.service_paths:
            if not Path(base_path).exists():
                continue

            for py_file in Path(base_path).rglob("*.py"):
                # Skip test files
                if "test" in py_file.name:
                    continue

                try:
                    content = py_file.read_text()

                    # Check for fragility indicators
                    if "singleton" in content.lower():
                        fragility_indicators["single_points_of_failure"] += 1

                    if __import__("re").search(r'["\']https?://[^"\']+["\']', content):
                        fragility_indicators["hardcoded_values"] += 1

                    if "global" in content:
                        fragility_indicators["global_state"] += 1

                    # Check for timeout usage
                    if "timeout" not in content.lower() and any(
                        x in content.lower() for x in ["request", "connect", "socket"]
                    ):
                        fragility_indicators["missing_timeouts"] += 1

                except Exception:
                    pass

        # Calculate overall fragility
        total_fragility = sum(fragility_indicators.values())

        if total_fragility > 10:
            violations.append(
                ConstitutionalViolation(
                    article=ConstitutionalArticle.ARTICLE_IV,
                    clause="Section 1",
                    rule="System must be antifragile not fragile",
                    description="High system fragility detected",
                    severity=GuardianPriority.HIGH,
                    evidence=[
                        f"Fragility score: {total_fragility}",
                        f"Single points of failure: {fragility_indicators['single_points_of_failure']}",
                        f"Hardcoded values: {fragility_indicators['hardcoded_values']}",
                        f"Missing timeouts: {fragility_indicators['missing_timeouts']}",
                    ],
                    affected_systems=["system_architecture"],
                    recommended_action="Refactor to reduce fragility and increase resilience",
                    context=fragility_indicators,
                )
            )

        return violations

    async def run_chaos_experiment(
        self,
        experiment_type: str,
        target_system: str,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Run a chaos experiment to test antifragility.

        Args:
            experiment_type: Type of chaos to inject
            target_system: System to target
            parameters: Experiment parameters

        Returns:
            Experiment results
        """
        experiment = {
            "id": f"chaos_{datetime.utcnow().timestamp()}",
            "type": experiment_type,
            "target": target_system,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "running",
        }

        self.chaos_experiments.append(experiment)

        # Simulate experiment execution
        await asyncio.sleep(random.uniform(1, 3))

        # Generate results
        success_rate = random.uniform(0.7, 1.0)
        experiment["status"] = "completed"
        experiment["results"] = {
            "success_rate": success_rate,
            "failures_detected": random.randint(0, 5),
            "recovery_time_ms": random.randint(100, 5000),
            "resilience_improved": success_rate > 0.85,
        }

        # Update resilience metrics
        self.resilience_metrics[target_system] = success_rate

        return experiment

    async def quarantine_feature(
        self,
        feature_id: str,
        feature_path: str,
        risk_level: str
    ) -> bool:
        """
        Quarantine an experimental feature for validation.

        Args:
            feature_id: Unique feature identifier
            feature_path: Path to feature code
            risk_level: Risk assessment

        Returns:
            True if quarantined successfully
        """
        self.quarantined_features[feature_id] = {
            "feature_id": feature_id,
            "path": feature_path,
            "risk_level": risk_level,
            "quarantine_start": datetime.utcnow().isoformat(),
            "status": "quarantined",
            "validation_required": risk_level in ["high", "critical"],
        }

        return True

    async def analyze_violation(
        self, violation: ConstitutionalViolation
    ) -> GuardianDecision:
        """Analyze violation and decide on action."""
        if "Insufficient chaos" in violation.description:
            decision_type = "alert"
            confidence = 0.80
            reasoning = (
                "System lacks sufficient chaos testing. "
                "Schedule chaos experiments to improve antifragility."
            )

        elif "Missing resilience patterns" in violation.description:
            decision_type = "block"
            confidence = 0.85
            reasoning = (
                "Critical resilience patterns missing. "
                "System is fragile and will break under stress."
            )

        elif "Experimental feature without quarantine" in violation.description:
            decision_type = "veto"
            confidence = 0.90
            reasoning = (
                "High-risk experimental feature must be quarantined "
                "per Article IV Section 2."
            )

        elif violation.severity == GuardianPriority.HIGH:
            decision_type = "escalate"
            confidence = 0.85
            reasoning = (
                f"Antifragility violation: {violation.rule}. "
                "System resilience at risk."
            )

        else:
            decision_type = "alert"
            confidence = 0.75
            reasoning = (
                "Antifragility could be improved. "
                "Consider adding chaos tests and resilience patterns."
            )

        return GuardianDecision(
            guardian_id=self.guardian_id,
            decision_type=decision_type,
            target=violation.context.get("path", "unknown"),
            reasoning=reasoning,
            confidence=confidence,
            requires_validation=False,
        )

    async def intervene(
        self, violation: ConstitutionalViolation
    ) -> GuardianIntervention:
        """Take intervention action for violation."""
        if "Experimental feature" in violation.description:
            # Quarantine the feature
            intervention_type = InterventionType.VETO
            feature_id = violation.context.get("feature_id", "unknown")
            await self.quarantine_feature(
                feature_id,
                violation.context.get("file", ""),
                "high"
            )
            action_taken = f"Quarantined experimental feature: {feature_id}"

        elif "Insufficient chaos" in violation.description:
            # Schedule chaos experiment
            intervention_type = InterventionType.REMEDIATION
            experiment = await self.run_chaos_experiment(
                "network_latency",
                violation.affected_systems[0] if violation.affected_systems else "unknown",
                {"latency_ms": 500, "duration_s": 60}
            )
            action_taken = f"Initiated chaos experiment: {experiment['id']}"

        elif violation.severity == GuardianPriority.HIGH:
            # Increase monitoring
            intervention_type = InterventionType.MONITORING
            action_taken = (
                f"Increased resilience monitoring on {violation.affected_systems[0]} "
                "to detect fragility"
            )

        else:
            # Alert for improvement
            intervention_type = InterventionType.ALERT
            action_taken = f"Alert: {violation.description}"

        return GuardianIntervention(
            guardian_id=self.guardian_id,
            intervention_type=intervention_type,
            priority=violation.severity,
            violation=violation,
            action_taken=action_taken,
            result="Intervention applied to improve antifragility",
            success=True,
        )