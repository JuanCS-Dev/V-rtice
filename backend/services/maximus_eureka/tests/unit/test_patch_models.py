"""
Unit Tests - Patch Models.

Tests for Patch and RemediationResult models.

Author: MAXIMUS Team
Date: 2025-01-10
"""

from datetime import datetime
from pathlib import Path

import pytest

# Setup path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from eureka_models.patch import Patch, PatchStatus, RemediationResult

# Import APV from Oráculo
from backend.shared.models.apv import RemediationStrategy


# ===================== PATCH TESTS =====================


def test_patch_creation_valid():
    """Test valid patch creation."""
    patch = Patch(
        patch_id="patch-CVE-2024-99999-20250110",
        cve_id="CVE-2024-99999",
        strategy_used=RemediationStrategy.DEPENDENCY_UPGRADE,
        diff_content="--- a/file.py\n+++ b/file.py\n",
        files_modified=["file.py"],
        confidence_score=0.95,
    )
    
    assert patch.patch_id == "patch-CVE-2024-99999-20250110"
    assert patch.cve_id == "CVE-2024-99999"
    assert patch.strategy_used == RemediationStrategy.DEPENDENCY_UPGRADE
    assert patch.confidence_score == 0.95
    assert not patch.validation_passed


def test_patch_confidence_bounds():
    """Test confidence score must be 0.0-1.0."""
    # Valid
    patch = Patch(
        patch_id="test",
        cve_id="CVE-2024-99999",
        strategy_used=RemediationStrategy.DEPENDENCY_UPGRADE,
        diff_content="diff",
        files_modified=["file.py"],
        confidence_score=0.5,
    )
    assert patch.confidence_score == 0.5
    
    # Invalid - should raise ValidationError
    with pytest.raises(Exception):  # Pydantic ValidationError
        Patch(
            patch_id="test",
            cve_id="CVE-2024-99999",
            strategy_used=RemediationStrategy.DEPENDENCY_UPGRADE,
            diff_content="diff",
            files_modified=["file.py"],
            confidence_score=1.5,  # > 1.0
        )


def test_patch_with_validation():
    """Test patch with validation results."""
    patch = Patch(
        patch_id="test",
        cve_id="CVE-2024-99999",
        strategy_used=RemediationStrategy.CODE_PATCH,
        diff_content="diff",
        files_modified=["file.py"],
        confidence_score=0.7,
        validation_passed=True,
        test_results={
            "exit_code": 0,
            "stdout": "All tests passed",
            "stderr": "",
            "duration_seconds": 12.5,
        },
    )
    
    assert patch.validation_passed
    assert patch.test_results["exit_code"] == 0


def test_patch_with_git_metadata():
    """Test patch with Git metadata."""
    patch = Patch(
        patch_id="test",
        cve_id="CVE-2024-99999",
        strategy_used=RemediationStrategy.DEPENDENCY_UPGRADE,
        diff_content="diff",
        files_modified=["file.py"],
        confidence_score=0.95,
        branch_name="security/fix-CVE-2024-99999",
        commit_sha="abc123def456",
        pr_url="https://github.com/org/repo/pull/123",
    )
    
    assert patch.branch_name == "security/fix-CVE-2024-99999"
    assert patch.commit_sha == "abc123def456"
    assert patch.pr_url == "https://github.com/org/repo/pull/123"


# ===================== REMEDIATION RESULT TESTS =====================


def test_remediation_result_success(sample_apv):
    """Test successful remediation result."""
    patch = Patch(
        patch_id="test",
        cve_id="CVE-2024-99999",
        strategy_used=RemediationStrategy.DEPENDENCY_UPGRADE,
        diff_content="diff",
        files_modified=["file.py"],
        confidence_score=0.95,
    )
    
    result = RemediationResult(
        apv=sample_apv,
        patch=patch,
        status=PatchStatus.APPLIED,
        started_at=datetime(2024, 1, 1, 12, 0, 0),
        completed_at=datetime(2024, 1, 1, 12, 5, 0),
        time_to_patch_seconds=300.0,
        strategy_attempts=[RemediationStrategy.DEPENDENCY_UPGRADE],
    )
    
    assert result.patch == patch
    assert result.status == PatchStatus.APPLIED
    assert result.time_to_patch_seconds == 300.0
    assert len(result.strategy_attempts) == 1


def test_remediation_result_failed(sample_apv):
    """Test failed remediation result."""
    result = RemediationResult(
        apv=sample_apv,
        patch=None,
        status=PatchStatus.FAILED,
        error_message="Strategy failed to generate patch",
        started_at=datetime(2024, 1, 1, 12, 0, 0),
        strategy_attempts=[
            RemediationStrategy.DEPENDENCY_UPGRADE,
            RemediationStrategy.CODE_PATCH,
        ],
    )
    
    assert result.patch is None
    assert result.status == PatchStatus.FAILED
    assert result.error_message is not None
    assert len(result.strategy_attempts) == 2


# ===================== FIXTURES =====================


@pytest.fixture
def sample_apv():
    """Sample APV for testing."""
    from models.apv import APV, AffectedPackage
    
    return APV(
        cve_id="CVE-2024-99999",
        aliases=["GHSA-test-1234"],
        published=datetime(2024, 1, 1),
        modified=datetime(2024, 1, 2),
        summary="Test vulnerability",
        details="Detailed description of test vulnerability for testing purposes only",
        source_feed="OSV.dev",
        affected_packages=[
            AffectedPackage(
                ecosystem="PyPI",
                name="test-package",
                affected_versions=["1.0.0"],
                fixed_versions=["2.0.0"],
            )
        ],
    )
