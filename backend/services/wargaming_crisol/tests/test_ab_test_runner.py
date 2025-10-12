"""
Unit tests for ABTestRunner.

Phase: 5.6
Glory to YHWH - Validator of learning systems
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add wargaming_crisol to path for internal imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ab_testing.ab_test_runner import ABTestRunner, ABTestResult


@pytest.fixture
def mock_ab_store():
    """Create mock A/B test store."""
    store = AsyncMock()
    store.store_result = AsyncMock(return_value=1)
    return store


@pytest.fixture
def ab_runner(mock_ab_store):
    """Create test AB runner with 100% rate for deterministic testing."""
    return ABTestRunner(
        ab_store=mock_ab_store,
        ab_test_rate=1.0,  # Force 100% for testing
        model_version="rf_v1_test"
    )


@pytest.fixture
def ab_runner_10_percent(mock_ab_store):
    """Create test AB runner with 10% rate."""
    return ABTestRunner(
        ab_store=mock_ab_store,
        ab_test_rate=0.10,
        model_version="rf_v1_test"
    )


# Test should_ab_test logic
def test_should_ab_test_always_true(ab_runner):
    """Test A/B test selection at 100% rate."""
    # With 100% rate, should always select
    assert ab_runner.should_ab_test() == True
    assert ab_runner.should_ab_test() == True


def test_should_ab_test_probabilistic(ab_runner_10_percent):
    """Test A/B test selection at 10% rate (probabilistic)."""
    # Run 1000 trials, expect ~10% (allow 5-15% for randomness)
    trials = 1000
    selected = sum(1 for _ in range(trials) if ab_runner_10_percent.should_ab_test())
    rate = selected / trials
    
    assert 0.05 <= rate <= 0.15, f"Expected ~10% selection rate, got {rate*100:.1f}%"


# Test run_with_ab_test - ML and Wargaming MATCH
@pytest.mark.asyncio
async def test_run_with_ab_test_match(ab_runner, mock_ab_store):
    """Test A/B test when ML matches wargaming (both valid)."""
    # Mock data
    apv_dict = {"id": "apv-001", "cve_id": "CVE-2024-1234"}
    patch_dict = {"id": "patch-001"}
    exploit_dict = {"id": "exploit-001"}
    
    # Mock ML predictor (predicts VALID, confidence 0.95)
    ml_predictor = AsyncMock()
    ml_predictor.predict = AsyncMock(return_value={
        "valid": True,
        "confidence": 0.95,
        "shap_values": {"feature_1": 0.5}
    })
    
    # Mock wargaming runner (also returns VALID)
    wargaming_runner = AsyncMock()
    wargaming_runner.validate = AsyncMock(return_value={
        "patch_validated": True,
        "reason": "Exploit failed on patched version"
    })
    
    # Run A/B test
    result, was_ab_tested = await ab_runner.run_with_ab_test(
        apv_dict, patch_dict, exploit_dict,
        ml_predictor, wargaming_runner
    )
    
    # Assertions
    assert was_ab_tested == True, "Should have run A/B test at 100% rate"
    assert result["valid"] == True, "Should return ML prediction (valid)"
    assert result["confidence"] == 0.95
    
    # Check store was called
    mock_ab_store.store_result.assert_called_once()
    stored_result = mock_ab_store.store_result.call_args[0][0]
    
    assert stored_result.apv_id == "apv-001"
    assert stored_result.patch_id == "patch-001"
    assert stored_result.ml_prediction == True
    assert stored_result.wargaming_result == True
    assert stored_result.ml_correct == True, "ML should match wargaming"
    assert stored_result.disagreement_reason is None


# Test run_with_ab_test - ML and Wargaming DISAGREE (False Positive)
@pytest.mark.asyncio
async def test_run_with_ab_test_false_positive(ab_runner, mock_ab_store):
    """Test A/B test when ML predicts VALID but wargaming says INVALID."""
    apv_dict = {"id": "apv-002", "cve_id": "CVE-2024-5678"}
    patch_dict = {"id": "patch-002"}
    exploit_dict = {"id": "exploit-002"}
    
    # ML predicts VALID (confident but wrong)
    ml_predictor = AsyncMock()
    ml_predictor.predict = AsyncMock(return_value={
        "valid": True,
        "confidence": 0.85,
    })
    
    # Wargaming says INVALID (exploit still worked)
    wargaming_runner = AsyncMock()
    wargaming_runner.validate = AsyncMock(return_value={
        "patch_validated": False,
        "reason": "Exploit succeeded on patched version"
    })
    
    result, was_ab_tested = await ab_runner.run_with_ab_test(
        apv_dict, patch_dict, exploit_dict,
        ml_predictor, wargaming_runner
    )
    
    # Should still return ML result (we trust ML for production)
    assert result["valid"] == True
    assert was_ab_tested == True
    
    # But should store disagreement
    stored_result = mock_ab_store.store_result.call_args[0][0]
    assert stored_result.ml_correct == False, "ML was wrong"
    assert "false positive" in stored_result.disagreement_reason.lower()


# Test run_with_ab_test - ML and Wargaming DISAGREE (False Negative)
@pytest.mark.asyncio
async def test_run_with_ab_test_false_negative(ab_runner, mock_ab_store):
    """Test A/B test when ML predicts INVALID but wargaming says VALID."""
    apv_dict = {"id": "apv-003", "cve_id": "CVE-2024-9999"}
    patch_dict = {"id": "patch-003"}
    exploit_dict = {"id": "exploit-003"}
    
    # ML predicts INVALID (too conservative)
    ml_predictor = AsyncMock()
    ml_predictor.predict = AsyncMock(return_value={
        "valid": False,
        "confidence": 0.60,
    })
    
    # Wargaming says VALID (patch actually worked)
    wargaming_runner = AsyncMock()
    wargaming_runner.validate = AsyncMock(return_value={
        "patch_validated": True,
        "reason": "Exploit failed on patched version"
    })
    
    result, was_ab_tested = await ab_runner.run_with_ab_test(
        apv_dict, patch_dict, exploit_dict,
        ml_predictor, wargaming_runner
    )
    
    # Returns ML result (invalid)
    assert result["valid"] == False
    
    # Stores false negative
    stored_result = mock_ab_store.store_result.call_args[0][0]
    assert stored_result.ml_correct == False
    assert "false negative" in stored_result.disagreement_reason.lower()


# Test run_with_ab_test - Store failure gracefully handled
@pytest.mark.asyncio
async def test_run_with_ab_test_store_failure(ab_runner, mock_ab_store):
    """Test that store failure doesn't crash the validation."""
    apv_dict = {"id": "apv-004"}
    patch_dict = {"id": "patch-004"}
    exploit_dict = {"id": "exploit-004"}
    
    ml_predictor = AsyncMock()
    ml_predictor.predict = AsyncMock(return_value={"valid": True, "confidence": 0.9})
    
    wargaming_runner = AsyncMock()
    wargaming_runner.validate = AsyncMock(return_value={"patch_validated": True})
    
    # Make store fail
    mock_ab_store.store_result = AsyncMock(side_effect=Exception("Database down"))
    
    # Should not crash
    result, was_ab_tested = await ab_runner.run_with_ab_test(
        apv_dict, patch_dict, exploit_dict,
        ml_predictor, wargaming_runner
    )
    
    # Should still return result
    assert result["valid"] == True
    assert was_ab_tested == True


# Test run_with_ab_test - Skip A/B test (not selected)
@pytest.mark.asyncio
async def test_run_without_ab_test(ab_runner_10_percent):
    """Test that most requests skip A/B testing at 10% rate."""
    apv_dict = {"id": "apv-005"}
    patch_dict = {"id": "patch-005"}
    exploit_dict = {"id": "exploit-005"}
    
    ml_predictor = AsyncMock()
    ml_predictor.predict = AsyncMock(return_value={"valid": True, "confidence": 0.9})
    
    wargaming_runner = AsyncMock()
    
    # Mock random to force skip
    with patch('ab_testing.ab_test_runner.random.random', return_value=0.95):
        result, was_ab_tested = await ab_runner_10_percent.run_with_ab_test(
            apv_dict, patch_dict, exploit_dict,
            ml_predictor, wargaming_runner
        )
    
    # Should skip A/B test
    assert was_ab_tested == False
    assert result["valid"] == True
    
    # Wargaming should not have been called
    wargaming_runner.validate.assert_not_called()
