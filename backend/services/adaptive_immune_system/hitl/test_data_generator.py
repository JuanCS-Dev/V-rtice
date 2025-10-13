"""
Test Data Generator - Create realistic APV test data for E2E testing.

Generates APVs with:
- Different severities (critical, high, medium, low)
- Different wargame verdicts (effective, inconclusive, insufficient)
- Different patch strategies
- Realistic CVE data
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from hitl.models import ReviewContext

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Generate realistic test APV data."""

    def __init__(self) -> None:
        self.apv_counter = 0

    def generate_apv(
        self,
        severity: str = "high",
        wargame_verdict: str = "PATCH_EFFECTIVE",
        patch_strategy: str = "version_bump",
        confirmed: bool = True,
    ) -> ReviewContext:
        """Generate a single test APV."""
        self.apv_counter += 1
        apv_code = f"APV-TEST-{self.apv_counter:03d}"
        apv_id = str(uuid.uuid4())

        # Map severity to CVSS score
        severity_score_map = {
            "critical": 9.8,
            "high": 7.5,
            "medium": 5.3,
            "low": 3.1,
        }

        # CVE templates by severity
        cve_templates = {
            "critical": {
                "cve_id": f"CVE-2024-{10000 + self.apv_counter}",
                "title": "Remote Code Execution via Deserialization",
                "description": "A critical vulnerability allows remote attackers to execute arbitrary code through unsafe deserialization of user-supplied data.",
                "cwe_ids": ["CWE-502"],
                "package": "fastapi-utils",
                "vulnerable_code": "pickle.loads(user_data)",
                "code_type": "deserialization",
            },
            "high": {
                "cve_id": f"CVE-2024-{20000 + self.apv_counter}",
                "title": "SQL Injection in User Authentication",
                "description": "SQL injection vulnerability in authentication module allows attackers to bypass authentication or extract sensitive data.",
                "cwe_ids": ["CWE-89"],
                "package": "django-auth-extensions",
                "vulnerable_code": "execute(f\"SELECT * FROM users WHERE username='{username}'\")",
                "code_type": "sql_query",
            },
            "medium": {
                "cve_id": f"CVE-2024-{30000 + self.apv_counter}",
                "title": "Cross-Site Scripting (XSS) in User Profile",
                "description": "Reflected XSS vulnerability allows attackers to inject malicious scripts through user profile fields.",
                "cwe_ids": ["CWE-79"],
                "package": "flask-profiles",
                "vulnerable_code": "return f\"<div>{user_input}</div>\"",
                "code_type": "html_template",
            },
            "low": {
                "cve_id": f"CVE-2024-{40000 + self.apv_counter}",
                "title": "Information Disclosure via Error Messages",
                "description": "Verbose error messages expose sensitive information about internal system structure.",
                "cwe_ids": ["CWE-209"],
                "package": "error-handler-utils",
                "vulnerable_code": "logger.error(f\"Database error: {db_credentials}\")",
                "code_type": "logging_statement",
            },
        }

        template = cve_templates.get(severity, cve_templates["medium"])

        # Patch strategies
        patch_diffs = {
            "version_bump": f"""--- a/requirements.txt
+++ b/requirements.txt
-{template['package']}==1.2.3
+{template['package']}==1.2.4  # Security update
""",
            "code_rewrite": f"""--- a/app/handlers.py
+++ b/app/handlers.py
-{template['vulnerable_code']}
+# Secure implementation
+safe_data = sanitize_input(user_data)
+process(safe_data)
""",
            "config_change": """--- a/config/security.yaml
+++ b/config/security.yaml
-allow_unsafe_deserialization: true
+allow_unsafe_deserialization: false
+strict_input_validation: true
""",
        }

        # Wargame evidence
        wargame_evidence_map = {
            "PATCH_EFFECTIVE": {
                "before_exit_code": 0,
                "after_exit_code": 1,
                "before_exploit_result": "SUCCESS: Exploit executed successfully",
                "after_exploit_result": "FAIL: Exploit blocked by patch",
                "workflow_duration_seconds": 45,
            },
            "INCONCLUSIVE": {
                "before_exit_code": 0,
                "after_exit_code": 0,
                "before_exploit_result": "PARTIAL: Some vectors blocked",
                "after_exploit_result": "PARTIAL: Some vectors still work",
                "workflow_duration_seconds": 62,
            },
            "PATCH_INSUFFICIENT": {
                "before_exit_code": 0,
                "after_exit_code": 0,
                "before_exploit_result": "SUCCESS: Full exploitation",
                "after_exploit_result": "SUCCESS: Patch bypassed",
                "workflow_duration_seconds": 38,
            },
        }

        wargame_confidence_map = {
            "PATCH_EFFECTIVE": 0.92,
            "INCONCLUSIVE": 0.58,
            "PATCH_INSUFFICIENT": 0.45,
        }

        now = datetime.utcnow()
        created_at = now - timedelta(hours=self.apv_counter * 0.5)

        return ReviewContext(
            # APV Information
            apv_id=apv_id,
            apv_code=apv_code,
            priority=self._severity_to_priority(severity),
            status="pending_human_review",
            # CVE Information
            cve_id=template["cve_id"],
            cve_title=template["title"],
            cve_description=template["description"],
            cvss_score=severity_score_map[severity],
            severity=severity,
            cwe_ids=template["cwe_ids"],
            # Dependency Information
            package_name=template["package"],
            package_version="1.2.3",
            package_ecosystem="pypi",
            fixed_version="1.2.4" if patch_strategy == "version_bump" else None,
            # Vulnerability Details
            vulnerable_code_signature=template["vulnerable_code"],
            vulnerable_code_type=template["code_type"],
            affected_files=[
                "app/handlers.py",
                "requirements.txt",
            ],
            # Confirmation Scores
            confirmed=confirmed,
            confirmation_confidence=0.85 if confirmed else 0.45,
            static_confidence=0.88,
            dynamic_confidence=0.82,
            false_positive_probability=0.05,
            # Patch Information
            patch_strategy=patch_strategy,
            patch_description=f"Apply {patch_strategy} to fix {template['cve_id']}",
            patch_diff=patch_diffs.get(patch_strategy, patch_diffs["version_bump"]),
            patch_confidence=0.9,
            patch_risk_level="low" if patch_strategy == "version_bump" else "medium",
            # Validation Results
            validation_passed=True,
            validation_confidence=0.95,
            validation_warnings=[
                "Tests for new code path missing",
            ] if patch_strategy == "code_rewrite" else [],
            # PR Information
            pr_number=1000 + self.apv_counter,
            pr_url=f"https://github.com/test-org/test-repo/pull/{1000 + self.apv_counter}",
            pr_branch=f"security/fix-{template['cve_id'].lower()}",
            # Wargaming Results
            wargame_verdict=wargame_verdict,
            wargame_confidence=wargame_confidence_map.get(wargame_verdict, 0.7),
            wargame_run_url=f"https://github.com/test-org/test-repo/actions/runs/{90000 + self.apv_counter}",
            wargame_evidence=wargame_evidence_map.get(
                wargame_verdict, wargame_evidence_map["PATCH_EFFECTIVE"]
            ),
            # Timestamps
            created_at=created_at,
            updated_at=now,
        )

    def _severity_to_priority(self, severity: str) -> int:
        """Convert severity to priority (1-10)."""
        severity_priority_map = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 2,
        }
        return severity_priority_map.get(severity, 5)

    def generate_test_suite(self) -> List[ReviewContext]:
        """Generate complete test suite with varied APVs."""
        apvs: List[ReviewContext] = []

        # Critical APVs
        apvs.append(
            self.generate_apv(
                severity="critical",
                wargame_verdict="PATCH_EFFECTIVE",
                patch_strategy="version_bump",
            )
        )
        apvs.append(
            self.generate_apv(
                severity="critical",
                wargame_verdict="INCONCLUSIVE",
                patch_strategy="code_rewrite",
            )
        )
        apvs.append(
            self.generate_apv(
                severity="critical",
                wargame_verdict="PATCH_INSUFFICIENT",
                patch_strategy="config_change",
            )
        )

        # High APVs
        for i in range(5):
            apvs.append(
                self.generate_apv(
                    severity="high",
                    wargame_verdict="PATCH_EFFECTIVE" if i < 3 else "INCONCLUSIVE",
                    patch_strategy="version_bump" if i % 2 == 0 else "code_rewrite",
                )
            )

        # Medium APVs
        for i in range(4):
            apvs.append(
                self.generate_apv(
                    severity="medium",
                    wargame_verdict="PATCH_EFFECTIVE" if i < 2 else "INCONCLUSIVE",
                    patch_strategy="version_bump",
                )
            )

        # Low APVs
        for i in range(3):
            apvs.append(
                self.generate_apv(
                    severity="low",
                    wargame_verdict="PATCH_EFFECTIVE",
                    patch_strategy="version_bump",
                )
            )

        logger.info(f"Generated {len(apvs)} test APVs")
        return apvs

    def generate_stress_test_suite(self, count: int = 100) -> List[ReviewContext]:
        """Generate large dataset for performance testing."""
        import random

        apvs: List[ReviewContext] = []

        severities = ["critical", "high", "medium", "low"]
        verdicts = ["PATCH_EFFECTIVE", "INCONCLUSIVE", "PATCH_INSUFFICIENT"]
        strategies = ["version_bump", "code_rewrite", "config_change"]

        for _ in range(count):
            apvs.append(
                self.generate_apv(
                    severity=random.choice(severities),
                    wargame_verdict=random.choice(verdicts),
                    patch_strategy=random.choice(strategies),
                    confirmed=random.choice([True, True, True, False]),  # 75% confirmed
                )
            )

        logger.info(f"Generated {len(apvs)} stress test APVs")
        return apvs


def generate_mock_apv_json(apv: ReviewContext) -> Dict[str, Any]:
    """Convert ReviewContext to JSON for API mock."""
    return {
        "apv_id": apv.apv_id,
        "apv_code": apv.apv_code,
        "priority": apv.priority,
        "status": apv.status,
        "cve_id": apv.cve_id,
        "cve_title": apv.cve_title,
        "cve_description": apv.cve_description,
        "cvss_score": apv.cvss_score,
        "severity": apv.severity,
        "cwe_ids": apv.cwe_ids,
        "package_name": apv.package_name,
        "package_version": apv.package_version,
        "package_ecosystem": apv.package_ecosystem,
        "fixed_version": apv.fixed_version,
        "vulnerable_code_signature": apv.vulnerable_code_signature,
        "vulnerable_code_type": apv.vulnerable_code_type,
        "affected_files": apv.affected_files,
        "confirmed": apv.confirmed,
        "confirmation_confidence": apv.confirmation_confidence,
        "static_confidence": apv.static_confidence,
        "dynamic_confidence": apv.dynamic_confidence,
        "false_positive_probability": apv.false_positive_probability,
        "patch_strategy": apv.patch_strategy,
        "patch_description": apv.patch_description,
        "patch_diff": apv.patch_diff,
        "patch_confidence": apv.patch_confidence,
        "patch_risk_level": apv.patch_risk_level,
        "validation_passed": apv.validation_passed,
        "validation_confidence": apv.validation_confidence,
        "validation_warnings": apv.validation_warnings,
        "pr_number": apv.pr_number,
        "pr_url": apv.pr_url,
        "pr_branch": apv.pr_branch,
        "wargame_verdict": apv.wargame_verdict,
        "wargame_confidence": apv.wargame_confidence,
        "wargame_run_url": apv.wargame_run_url,
        "wargame_evidence": apv.wargame_evidence,
        "created_at": apv.created_at.isoformat(),
        "updated_at": apv.updated_at.isoformat(),
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    generator = TestDataGenerator()

    # Generate standard test suite
    test_apvs = generator.generate_test_suite()
    print(f"\n✅ Generated {len(test_apvs)} test APVs:")
    for apv in test_apvs:
        print(
            f"  - {apv.apv_code}: {apv.severity.upper()} | "
            f"{apv.wargame_verdict} | {apv.patch_strategy}"
        )

    # Generate stress test suite
    print("\n🔥 Generating stress test suite (100 APVs)...")
    stress_apvs = generator.generate_stress_test_suite(100)
    print(f"✅ Generated {len(stress_apvs)} stress test APVs")

    # Show severity distribution
    from collections import Counter

    severity_counts = Counter(apv.severity for apv in stress_apvs)
    print("\nSeverity distribution:")
    for severity, count in severity_counts.most_common():
        print(f"  - {severity}: {count}")
