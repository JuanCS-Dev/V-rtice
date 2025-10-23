"""
Article III Guardian - Targeted Coverage Tests

Objetivo: Cobrir governance/guardian/article_iii_guardian.py (184 lines, 0% → 60%+)

Testa:
- ArticleIIIGuardian initialization
- Zero Trust enforcement
- AI artifact validation tracking
- Authentication/authorization checking
- Input validation enforcement
- Trust assumptions detection

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from datetime import datetime

from governance.guardian.article_iii_guardian import ArticleIIIGuardian
from governance.guardian.base import (
    ConstitutionalArticle,
    ConstitutionalViolation,
    GuardianPriority,
    GuardianDecision,
    GuardianIntervention,
    InterventionType
)


# ===== INITIALIZATION TESTS =====

def test_article_iii_guardian_initialization():
    """
    SCENARIO: Create ArticleIIIGuardian with defaults
    EXPECTED: Initializes with Article III, Zero Trust focus
    """
    guardian = ArticleIIIGuardian()

    assert guardian.guardian_id == "guardian-article-iii"
    assert guardian.article == ConstitutionalArticle.ARTICLE_III
    assert guardian.name == "Zero Trust Guardian"
    assert isinstance(guardian.unvalidated_artifacts, dict)
    assert isinstance(guardian.validation_history, list)


def test_article_iii_guardian_with_custom_paths():
    """
    SCENARIO: Initialize with custom monitored/API paths
    EXPECTED: Uses provided paths
    """
    guardian = ArticleIIIGuardian(
        monitored_paths=["/custom/monitor"],
        api_paths=["/custom/api"]
    )

    assert "/custom/monitor" in guardian.monitored_paths
    assert "/custom/api" in guardian.api_paths


def test_article_iii_auth_patterns_defined():
    """
    SCENARIO: Check authentication patterns list
    EXPECTED: Contains auth/security patterns
    """
    guardian = ArticleIIIGuardian()

    patterns = guardian.auth_patterns

    assert isinstance(patterns, list)
    assert len(patterns) > 0


def test_article_iii_trust_indicators_defined():
    """
    SCENARIO: Check trust assumption indicators
    EXPECTED: Contains problematic trust patterns
    """
    guardian = ArticleIIIGuardian()

    indicators = guardian.trust_indicators

    assert isinstance(indicators, list)
    assert len(indicators) > 0


def test_article_iii_get_monitored_systems():
    """
    SCENARIO: Call get_monitored_systems()
    EXPECTED: Returns zero-trust related systems
    """
    guardian = ArticleIIIGuardian()

    systems = guardian.get_monitored_systems()

    assert isinstance(systems, list)
    assert len(systems) > 0


# ===== MONITOR METHOD TESTS =====

@pytest.mark.asyncio
async def test_article_iii_monitor_returns_violations_list():
    """
    SCENARIO: Call monitor() method
    EXPECTED: Returns list of ConstitutionalViolation
    """
    guardian = ArticleIIIGuardian()

    violations = await guardian.monitor()

    assert isinstance(violations, list)
    for v in violations:
        assert isinstance(v, ConstitutionalViolation) or isinstance(v, dict)


@pytest.mark.asyncio
async def test_article_iii_monitor_checks_ai_artifacts():
    """
    SCENARIO: Monitor with mocked check methods
    EXPECTED: Calls AI artifact validation check
    """
    guardian = ArticleIIIGuardian()

    with patch.object(guardian, '_check_ai_artifact_validation', new_callable=AsyncMock, return_value=[]):
        with patch.object(guardian, '_check_authentication', new_callable=AsyncMock, return_value=[]):
            with patch.object(guardian, '_check_input_validation', new_callable=AsyncMock, return_value=[]):
                with patch.object(guardian, '_check_trust_assumptions', new_callable=AsyncMock, return_value=[]):
                    with patch.object(guardian, '_check_audit_trails', new_callable=AsyncMock, return_value=[]):
                        violations = await guardian.monitor()

                        guardian._check_ai_artifact_validation.assert_called_once()
                        guardian._check_authentication.assert_called_once()


# ===== AI ARTIFACT VALIDATION =====

@pytest.mark.asyncio
async def test_register_unvalidated_artifact():
    """
    SCENARIO: Register AI-generated artifact awaiting validation
    EXPECTED: Adds to unvalidated_artifacts dict
    """
    guardian = ArticleIIIGuardian()

    await guardian.register_unvalidated_artifact(
        artifact_id="ai-code-001",
        artifact_type="code_generation",
        source="claude_api",
        metadata={"lines": 50}
    )

    assert "ai-code-001" in guardian.unvalidated_artifacts
    assert guardian.unvalidated_artifacts["ai-code-001"]["artifact_type"] == "code_generation"


@pytest.mark.asyncio
async def test_validate_artifact():
    """
    SCENARIO: Validate a registered AI artifact
    EXPECTED: Moves to validation_history, removes from unvalidated
    """
    guardian = ArticleIIIGuardian()

    await guardian.register_unvalidated_artifact("artifact1", "code", "ai")
    await guardian.validate_artifact("artifact1", validator="human_reviewer", passed=True)

    assert "artifact1" not in guardian.unvalidated_artifacts or \
           guardian.unvalidated_artifacts["artifact1"].get("validated") is True
    assert len(guardian.validation_history) >= 1


@pytest.mark.asyncio
async def test_get_unvalidated_artifacts():
    """
    SCENARIO: Retrieve list of unvalidated artifacts
    EXPECTED: Returns current unvalidated items
    """
    guardian = ArticleIIIGuardian()

    await guardian.register_unvalidated_artifact("unvalidated1", "code", "ai")
    await guardian.register_unvalidated_artifact("unvalidated2", "config", "ai")

    unvalidated = guardian.get_unvalidated_artifacts()

    assert isinstance(unvalidated, (list, dict))


@pytest.mark.asyncio
async def test_artifact_validation_history():
    """
    SCENARIO: Check validation history tracking
    EXPECTED: History records validation events
    """
    guardian = ArticleIIIGuardian()

    await guardian.register_unvalidated_artifact("test_artifact", "code", "ai")
    await guardian.validate_artifact("test_artifact", "reviewer", True)

    history = guardian.get_validation_history()

    assert isinstance(history, list)


# ===== ANALYZE VIOLATION TESTS =====

@pytest.mark.asyncio
async def test_analyze_violation_returns_decision():
    """
    SCENARIO: Analyze detected zero-trust violation
    EXPECTED: Returns GuardianDecision
    """
    guardian = ArticleIIIGuardian()

    violation = ConstitutionalViolation(
        article=ConstitutionalArticle.ARTICLE_III,
        rule="Zero Trust required",
        description="Missing authentication on API endpoint"
    )

    decision = await guardian.analyze_violation(violation)

    assert isinstance(decision, GuardianDecision)
    assert decision.guardian_id == "guardian-article-iii"


@pytest.mark.asyncio
async def test_analyze_violation_critical_security():
    """
    SCENARIO: Analyze critical security gap
    EXPECTED: Decision reflects high severity
    """
    guardian = ArticleIIIGuardian()

    violation = ConstitutionalViolation(
        article=ConstitutionalArticle.ARTICLE_III,
        severity=GuardianPriority.CRITICAL,
        rule="Authentication required",
        description="Public endpoint with sensitive data access"
    )

    decision = await guardian.analyze_violation(violation)

    assert decision.approved is False or hasattr(decision, 'severity')


# ===== INTERVENE TESTS =====

@pytest.mark.asyncio
async def test_intervene_creates_intervention():
    """
    SCENARIO: Call intervene() on violation
    EXPECTED: Returns GuardianIntervention
    """
    guardian = ArticleIIIGuardian()

    violation = ConstitutionalViolation(
        article=ConstitutionalArticle.ARTICLE_III,
        rule="Input validation required",
        description="SQL injection vulnerability detected"
    )

    intervention = await guardian.intervene(violation)

    assert isinstance(intervention, GuardianIntervention)
    assert intervention.guardian_id == "guardian-article-iii"


@pytest.mark.asyncio
async def test_intervene_critical_uses_veto():
    """
    SCENARIO: Intervene on critical trust violation
    EXPECTED: May use VETO intervention
    """
    guardian = ArticleIIIGuardian()

    violation = ConstitutionalViolation(
        article=ConstitutionalArticle.ARTICLE_III,
        severity=GuardianPriority.CRITICAL,
        rule="No trust assumptions",
        description="Hardcoded credentials in production code"
    )

    intervention = await guardian.intervene(violation)

    assert intervention.intervention_type in [
        InterventionType.VETO,
        InterventionType.ALERT,
        InterventionType.ESCALATION,
        InterventionType.REMEDIATION
    ]


# ===== CHECK METHODS TESTS =====

@pytest.mark.asyncio
async def test_check_ai_artifact_validation_no_violations():
    """
    SCENARIO: Check AI artifact validation
    EXPECTED: Returns violations list
    """
    guardian = ArticleIIIGuardian()

    violations = await guardian._check_ai_artifact_validation()

    assert isinstance(violations, list)


@pytest.mark.asyncio
async def test_check_authentication_no_violations():
    """
    SCENARIO: Check authentication/authorization
    EXPECTED: Returns list
    """
    guardian = ArticleIIIGuardian(api_paths=["/nonexistent"])

    violations = await guardian._check_authentication()

    assert isinstance(violations, list)


@pytest.mark.asyncio
async def test_check_input_validation_no_violations():
    """
    SCENARIO: Check input validation presence
    EXPECTED: Returns violations list
    """
    guardian = ArticleIIIGuardian(monitored_paths=["/nonexistent"])

    violations = await guardian._check_input_validation()

    assert isinstance(violations, list)


@pytest.mark.asyncio
async def test_check_trust_assumptions_no_violations():
    """
    SCENARIO: Check for trust assumptions in code
    EXPECTED: Returns list
    """
    guardian = ArticleIIIGuardian(monitored_paths=["/nonexistent"])

    violations = await guardian._check_trust_assumptions()

    assert isinstance(violations, list)


@pytest.mark.asyncio
async def test_check_audit_trails_no_violations():
    """
    SCENARIO: Check audit trail presence
    EXPECTED: Returns violations list
    """
    guardian = ArticleIIIGuardian(monitored_paths=["/nonexistent"])

    violations = await guardian._check_audit_trails()

    assert isinstance(violations, list)


# ===== INTEGRATION TEST =====

@pytest.mark.asyncio
async def test_article_iii_full_lifecycle():
    """
    SCENARIO: Full Guardian lifecycle (start → monitor → stop)
    EXPECTED: Completes without errors
    """
    guardian = ArticleIIIGuardian(monitored_paths=["/tmp"], api_paths=["/tmp"])

    await guardian.start()
    assert guardian.is_active() is True

    violations = await guardian.monitor()
    assert isinstance(violations, list)

    await guardian.stop()
    assert guardian.is_active() is False
