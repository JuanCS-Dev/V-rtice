"""
Unit Tests - Base Strategy.

Tests for BaseStrategy abstract class and StrategySelector.

Author: MAXIMUS Team
Date: 2025-01-10
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# Setup path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from strategies.base_strategy import BaseStrategy
from strategies.strategy_selector import StrategySelector, NoStrategyAvailableError

# Import models
from backend.shared.models.apv import RemediationStrategy


# ===================== CONCRETE STRATEGY FOR TESTING =====================


class MockStrategy(BaseStrategy):
    """Mock strategy for testing."""
    
    def __init__(self, can_handle_result: bool = True):
        self._can_handle_result = can_handle_result
    
    @property
    def strategy_type(self) -> RemediationStrategy:
        return RemediationStrategy.DEPENDENCY_UPGRADE
    
    async def can_handle(self, apv, confirmation) -> bool:
        return self._can_handle_result
    
    async def apply_strategy(self, apv, confirmation):
        from eureka_models.patch import Patch
        return Patch(
            patch_id=self._generate_patch_id(apv.cve_id),
            cve_id=apv.cve_id,
            strategy_used=self.strategy_type,
            diff_content="test diff",
            files_modified=["test.py"],
            confidence_score=0.9,
        )


# ===================== BASE STRATEGY TESTS =====================


def test_base_strategy_generate_patch_id():
    """Test patch ID generation."""
    strategy = MockStrategy()
    patch_id = strategy._generate_patch_id("CVE-2024-99999")
    
    assert patch_id.startswith("patch-CVE-2024-99999-")
    assert len(patch_id) > len("patch-CVE-2024-99999-")


def test_base_strategy_generate_branch_name():
    """Test branch name generation."""
    strategy = MockStrategy()
    branch = strategy._generate_branch_name("CVE-2024-99999")
    
    assert branch.startswith("security/fix-CVE-2024-99999-")


def test_base_strategy_repr():
    """Test string representation."""
    strategy = MockStrategy()
    repr_str = repr(strategy)
    
    assert "MockStrategy" in repr_str
    assert "dependency_upgrade" in repr_str


# ===================== STRATEGY SELECTOR TESTS =====================


@pytest.mark.asyncio
async def test_strategy_selector_selects_first_applicable(sample_apv, sample_confirmation):
    """Test selector returns first strategy that can handle."""
    strategy1 = MockStrategy(can_handle_result=False)
    strategy2 = MockStrategy(can_handle_result=True)
    strategy3 = MockStrategy(can_handle_result=True)
    
    selector = StrategySelector([strategy1, strategy2, strategy3])
    
    selected = await selector.select_strategy(sample_apv, sample_confirmation)
    
    assert selected == strategy2  # First one that can handle


@pytest.mark.asyncio
async def test_strategy_selector_raises_when_none_applicable(sample_apv, sample_confirmation):
    """Test selector raises when no strategy can handle."""
    strategy1 = MockStrategy(can_handle_result=False)
    strategy2 = MockStrategy(can_handle_result=False)
    
    selector = StrategySelector([strategy1, strategy2])
    
    with pytest.raises(NoStrategyAvailableError):
        await selector.select_strategy(sample_apv, sample_confirmation)


@pytest.mark.asyncio
async def test_strategy_selector_handles_exception_in_can_handle(sample_apv, sample_confirmation):
    """Test selector handles exceptions in can_handle gracefully."""
    strategy1 = MockStrategy(can_handle_result=True)
    strategy1.can_handle = AsyncMock(side_effect=Exception("Test error"))
    
    strategy2 = MockStrategy(can_handle_result=True)
    
    selector = StrategySelector([strategy1, strategy2])
    
    # Should skip strategy1 and select strategy2
    selected = await selector.select_strategy(sample_apv, sample_confirmation)
    assert selected == strategy2


def test_strategy_selector_get_strategies():
    """Test getting strategy list."""
    strategy1 = MockStrategy()
    strategy2 = MockStrategy()
    
    selector = StrategySelector([strategy1, strategy2])
    strategies = selector.get_strategies()
    
    assert len(strategies) == 2
    assert strategies[0] == strategy1
    assert strategies[1] == strategy2


# ===================== FIXTURES =====================


@pytest.fixture
def sample_apv():
    """Sample APV for testing."""
    from datetime import datetime
    from models.apv import APV, AffectedPackage
    
    return APV(
        cve_id="CVE-2024-99999",
        aliases=["GHSA-test-1234"],
        published=datetime(2024, 1, 1),
        modified=datetime(2024, 1, 2),
        summary="Test vulnerability",
        details="Detailed description of test vulnerability for testing purposes",
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


@pytest.fixture
def sample_confirmation():
    """Sample confirmation result for testing."""
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
