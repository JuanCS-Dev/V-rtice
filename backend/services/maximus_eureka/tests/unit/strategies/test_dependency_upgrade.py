"""
Unit Tests - Dependency Upgrade Strategy.

Tests for DependencyUpgradeStrategy.

Author: MAXIMUS Team
Date: 2025-01-10
"""

from pathlib import Path
from datetime import datetime

import pytest

# Setup path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from strategies.dependency_upgrade import DependencyUpgradeStrategy

# Import models
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "maximus_oraculo"))
from models.apv import APV, AffectedPackage, RemediationStrategy


# ===================== DEPENDENCY UPGRADE TESTS =====================


@pytest.mark.asyncio
async def test_dependency_upgrade_can_handle_with_fix(tmp_path, sample_apv_with_fix):
    """Test can_handle returns True when fix available and manifest exists."""
    # Create manifest
    (tmp_path / "pyproject.toml").write_text('[tool.poetry.dependencies]\npython = "^3.11"\n')
    
    strategy = DependencyUpgradeStrategy(codebase_root=tmp_path)
    confirmation = create_sample_confirmation()
    
    result = await strategy.can_handle(sample_apv_with_fix, confirmation)
    
    assert result is True


@pytest.mark.asyncio
async def test_dependency_upgrade_can_handle_no_fix(tmp_path, sample_apv_no_fix):
    """Test can_handle returns False when no fix available."""
    (tmp_path / "pyproject.toml").write_text('[tool.poetry.dependencies]\npython = "^3.11"\n')
    
    strategy = DependencyUpgradeStrategy(codebase_root=tmp_path)
    confirmation = create_sample_confirmation()
    
    result = await strategy.can_handle(sample_apv_no_fix, confirmation)
    
    assert result is False


@pytest.mark.asyncio
async def test_dependency_upgrade_can_handle_no_manifest(tmp_path, sample_apv_with_fix):
    """Test can_handle returns False when no manifest exists."""
    strategy = DependencyUpgradeStrategy(codebase_root=tmp_path)
    confirmation = create_sample_confirmation()
    
    result = await strategy.can_handle(sample_apv_with_fix, confirmation)
    
    assert result is False


@pytest.mark.asyncio
async def test_dependency_upgrade_apply_strategy_pyproject(tmp_path, sample_apv_with_fix):
    """Test apply_strategy generates correct diff for pyproject.toml."""
    # Create pyproject.toml with vulnerable package
    # IMPORTANT: Use same package name as in fixture (test-package)
    pyproject_content = '''[tool.poetry.dependencies]
python = "^3.11"
test-package = "^1.0.0"
flask = "^2.0.0"
'''
    (tmp_path / "pyproject.toml").write_text(pyproject_content)
    
    strategy = DependencyUpgradeStrategy(codebase_root=tmp_path)
    confirmation = create_sample_confirmation()
    
    patch = await strategy.apply_strategy(sample_apv_with_fix, confirmation)
    
    # Verify patch
    assert patch.cve_id == "CVE-2024-99999"
    assert patch.strategy_used == RemediationStrategy.DEPENDENCY_UPGRADE
    assert patch.confidence_score == 0.95  # High confidence
    assert len(patch.files_modified) == 1
    assert "pyproject.toml" in patch.files_modified[0]
    
    # Verify diff contains upgrade
    assert "test-package" in patch.diff_content
    assert "1.0.0" in patch.diff_content or "2.0.0" in patch.diff_content


@pytest.mark.asyncio
async def test_dependency_upgrade_strategy_type():
    """Test strategy_type property."""
    strategy = DependencyUpgradeStrategy(codebase_root=Path("/tmp"))
    
    assert strategy.strategy_type == RemediationStrategy.DEPENDENCY_UPGRADE


# ===================== HELPER FUNCTIONS =====================


def create_sample_confirmation():
    """Create sample confirmation result."""
    from eureka_models.confirmation.confirmation_result import (
        ConfirmationResult,
        ConfirmationStatus,
    )
    
    return ConfirmationResult(
        apv_id="CVE-2024-99999",
        cve_id="CVE-2024-99999",
        status=ConfirmationStatus.CONFIRMED,
        vulnerable_locations=[],
    )


# ===================== FIXTURES =====================


@pytest.fixture
def sample_apv_with_fix():
    """APV with fixed version available."""
    return APV(
        cve_id="CVE-2024-99999",
        aliases=["GHSA-test-1234"],
        published=datetime(2024, 1, 1),
        modified=datetime(2024, 1, 2),
        summary="Test vulnerability with fix",
        details="Detailed description of test vulnerability with fix available for testing",
        source_feed="OSV.dev",
        affected_packages=[
            AffectedPackage(
                ecosystem="PyPI",
                name="test-package",
                affected_versions=[">=1.0.0,<2.0.0"],
                fixed_versions=["2.0.0"],  # Fix available
            )
        ],
    )


@pytest.fixture
def sample_apv_no_fix():
    """APV without fixed version."""
    return APV(
        cve_id="CVE-2024-99998",
        aliases=["GHSA-test-9999"],
        published=datetime(2024, 1, 1),
        modified=datetime(2024, 1, 2),
        summary="Test vulnerability without fix",
        details="Detailed description of test vulnerability without fix available yet",
        source_feed="OSV.dev",
        affected_packages=[
            AffectedPackage(
                ecosystem="PyPI",
                name="test-package2",
                affected_versions=["1.0.0"],
                fixed_versions=[],  # No fix available
            )
        ],
    )
