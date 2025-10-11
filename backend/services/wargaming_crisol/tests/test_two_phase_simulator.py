"""
Unit tests for Two-Phase Attack Simulator.

Tests wargaming validation logic without Docker (mocked).
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from two_phase_simulator import (
    TwoPhaseSimulator,
    WargamingResult,
    PhaseResult,
    WargamingPhase,
    WargamingStatus,
    validate_patch_via_wargaming,
)

from exploit_database import ExploitResult, ExploitStatus, ExploitCategory


# Fixtures

@pytest.fixture
def mock_apv():
    """Mock APV object"""
    apv = Mock()
    apv.apv_id = "apv_001"
    apv.cve_id = "CVE-2024-TEST"
    apv.cwe_ids = ["CWE-89"]
    return apv


@pytest.fixture
def mock_patch():
    """Mock Patch object"""
    patch = Mock()
    patch.patch_id = "patch_001"
    patch.unified_diff = "diff content"
    return patch


@pytest.fixture
def mock_exploit():
    """Mock ExploitScript"""
    exploit = Mock()
    exploit.exploit_id = "test_exploit"
    exploit.name = "Test Exploit"
    exploit.category = ExploitCategory.SQL_INJECTION
    return exploit


@pytest.fixture
def successful_exploit_result():
    """Mock successful exploit result"""
    return ExploitResult(
        exploit_id="test",
        category=ExploitCategory.SQL_INJECTION,
        status=ExploitStatus.SUCCESS,
        success=True,
        output="Exploit succeeded",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )


@pytest.fixture
def failed_exploit_result():
    """Mock failed exploit result"""
    return ExploitResult(
        exploit_id="test",
        category=ExploitCategory.SQL_INJECTION,
        status=ExploitStatus.FAILED,
        success=False,
        output="Exploit failed",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )


# Tests: Initialization

def test_simulator_initialization():
    """Test simulator can be initialized"""
    simulator = TwoPhaseSimulator()
    
    assert simulator.timeout_seconds == 300
    assert simulator.cleanup_on_complete is True


def test_simulator_custom_config():
    """Test simulator with custom config"""
    simulator = TwoPhaseSimulator(
        timeout_seconds=600,
        cleanup_on_complete=False
    )
    
    assert simulator.timeout_seconds == 600
    assert simulator.cleanup_on_complete is False


# Tests: execute_wargaming (successful path)

@pytest.mark.asyncio
async def test_execute_wargaming_success(
    mock_apv,
    mock_patch,
    mock_exploit,
    successful_exploit_result,
    failed_exploit_result
):
    """Test successful wargaming (both phases pass)"""
    simulator = TwoPhaseSimulator()
    
    # Mock exploit execution
    # Phase 1: Exploit succeeds (vulnerable)
    # Phase 2: Exploit fails (patched)
    mock_exploit.execute_func = AsyncMock(
        side_effect=[successful_exploit_result, failed_exploit_result]
    )
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    # Assertions
    assert result.status == WargamingStatus.SUCCESS
    assert result.patch_validated is True
    assert result.phase_1_result.phase_passed is True
    assert result.phase_2_result.phase_passed is True
    assert result.phase_1_result.exploit_success is True  # Vulnerable
    assert result.phase_2_result.exploit_success is False  # Patched


@pytest.mark.asyncio
async def test_execute_wargaming_phase_1_fails(
    mock_apv,
    mock_patch,
    mock_exploit,
    failed_exploit_result
):
    """Test wargaming when Phase 1 fails (exploit doesn't work on vulnerable)"""
    simulator = TwoPhaseSimulator()
    
    # Phase 1: Exploit fails (should succeed!)
    mock_exploit.execute_func = AsyncMock(return_value=failed_exploit_result)
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.status == WargamingStatus.FAILED
    assert result.patch_validated is False
    assert result.phase_1_result.phase_passed is False


@pytest.mark.asyncio
async def test_execute_wargaming_phase_2_fails(
    mock_apv,
    mock_patch,
    mock_exploit,
    successful_exploit_result
):
    """Test wargaming when Phase 2 fails (exploit still works on patched)"""
    simulator = TwoPhaseSimulator()
    
    # Phase 1: Succeeds
    # Phase 2: Succeeds (should fail! = patch ineffective)
    mock_exploit.execute_func = AsyncMock(return_value=successful_exploit_result)
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.status == WargamingStatus.FAILED
    assert result.patch_validated is False
    assert result.phase_2_result.phase_passed is False


# Tests: PhaseResult

def test_phase_result_to_dict():
    """Test PhaseResult to dictionary"""
    result = PhaseResult(
        phase=WargamingPhase.PHASE_1_VULNERABLE,
        exploit_id="test",
        exploit_success=True,
        expected_result=True,
        phase_passed=True,
        output="Test output",
        error=None,
        duration_seconds=2.5,
        metadata={"key": "value"}
    )
    
    data = result.to_dict()
    
    assert data["phase"] == "phase_1_vulnerable"
    assert data["exploit_success"] is True
    assert data["phase_passed"] is True
    assert data["duration_seconds"] == 2.5


# Tests: WargamingResult

def test_wargaming_result_to_dict():
    """Test WargamingResult to dictionary"""
    phase_1 = PhaseResult(
        phase=WargamingPhase.PHASE_1_VULNERABLE,
        exploit_id="test",
        exploit_success=True,
        expected_result=True,
        phase_passed=True,
        output="",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )
    
    phase_2 = PhaseResult(
        phase=WargamingPhase.PHASE_2_PATCHED,
        exploit_id="test",
        exploit_success=False,
        expected_result=False,
        phase_passed=True,
        output="",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )
    
    result = WargamingResult(
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        exploit_id="test",
        phase_1_result=phase_1,
        phase_2_result=phase_2,
        status=WargamingStatus.SUCCESS,
        patch_validated=True,
        total_duration_seconds=2.5,
        executed_at=datetime.now()
    )
    
    data = result.to_dict()
    
    assert data["apv_id"] == "apv_001"
    assert data["status"] == "success"
    assert data["patch_validated"] is True


def test_wargaming_result_summary_success():
    """Test summary generation for successful validation"""
    phase_1 = PhaseResult(
        phase=WargamingPhase.PHASE_1_VULNERABLE,
        exploit_id="test",
        exploit_success=True,
        expected_result=True,
        phase_passed=True,
        output="",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )
    
    phase_2 = PhaseResult(
        phase=WargamingPhase.PHASE_2_PATCHED,
        exploit_id="test",
        exploit_success=False,
        expected_result=False,
        phase_passed=True,
        output="",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )
    
    result = WargamingResult(
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        exploit_id="test",
        phase_1_result=phase_1,
        phase_2_result=phase_2,
        status=WargamingStatus.SUCCESS,
        patch_validated=True,
        total_duration_seconds=2.5,
        executed_at=datetime.now()
    )
    
    summary = result.summary()
    
    assert "✅ PATCH VALIDATED" in summary
    assert "CVE-2024-TEST" in summary
    assert "Phase 1" in summary
    assert "Phase 2" in summary


def test_wargaming_result_summary_failed():
    """Test summary generation for failed validation"""
    phase_1 = PhaseResult(
        phase=WargamingPhase.PHASE_1_VULNERABLE,
        exploit_id="test",
        exploit_success=False,  # Should have succeeded!
        expected_result=True,
        phase_passed=False,
        output="",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )
    
    phase_2 = PhaseResult(
        phase=WargamingPhase.PHASE_2_PATCHED,
        exploit_id="test",
        exploit_success=False,
        expected_result=False,
        phase_passed=True,
        output="",
        error=None,
        duration_seconds=1.0,
        metadata={}
    )
    
    result = WargamingResult(
        apv_id="apv_001",
        cve_id="CVE-2024-TEST",
        exploit_id="test",
        phase_1_result=phase_1,
        phase_2_result=phase_2,
        status=WargamingStatus.FAILED,
        patch_validated=False,
        total_duration_seconds=2.5,
        executed_at=datetime.now()
    )
    
    summary = result.summary()
    
    assert "❌ PATCH VALIDATION FAILED" in summary
    assert "CVE-2024-TEST" in summary


# Tests: Error handling

@pytest.mark.asyncio
async def test_execute_wargaming_timeout(mock_apv, mock_patch, mock_exploit):
    """Test wargaming timeout"""
    simulator = TwoPhaseSimulator(timeout_seconds=1)
    
    # Mock slow exploit
    async def slow_exploit(*args, **kwargs):
        await asyncio.sleep(10)
        return ExploitResult(
            exploit_id="test",
            category=ExploitCategory.SQL_INJECTION,
            status=ExploitStatus.SUCCESS,
            success=True,
            output="",
            error=None,
            duration_seconds=10.0,
            metadata={}
        )
    
    mock_exploit.execute_func = slow_exploit
    
    # Note: Timeout not fully implemented yet, will be added with Docker
    # For now, test that it doesn't crash
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    # Should complete without crashing
    assert result is not None


@pytest.mark.asyncio
async def test_execute_wargaming_exception(mock_apv, mock_patch, mock_exploit):
    """Test wargaming with exception"""
    simulator = TwoPhaseSimulator()
    
    # Mock exploit that raises exception
    mock_exploit.execute_func = AsyncMock(side_effect=Exception("Test error"))
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.status == WargamingStatus.ERROR
    assert result.patch_validated is False


# Tests: Enums

def test_wargaming_phase_enum():
    """Test WargamingPhase enum values"""
    assert WargamingPhase.PHASE_1_VULNERABLE.value == "phase_1_vulnerable"
    assert WargamingPhase.PHASE_2_PATCHED.value == "phase_2_patched"


def test_wargaming_status_enum():
    """Test WargamingStatus enum values"""
    assert WargamingStatus.SUCCESS.value == "success"
    assert WargamingStatus.FAILED.value == "failed"
    assert WargamingStatus.ERROR.value == "error"
    assert WargamingStatus.TIMEOUT.value == "timeout"


# Tests: Convenience function

@pytest.mark.asyncio
async def test_validate_patch_via_wargaming(
    mock_apv,
    mock_patch,
    mock_exploit,
    successful_exploit_result,
    failed_exploit_result
):
    """Test convenience function"""
    mock_exploit.execute_func = AsyncMock(
        side_effect=[successful_exploit_result, failed_exploit_result]
    )
    
    result = await validate_patch_via_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.patch_validated is True


# Tests: Phase execution details

@pytest.mark.asyncio
async def test_phase_1_expected_success(
    mock_apv,
    mock_patch,
    mock_exploit,
    successful_exploit_result,
    failed_exploit_result
):
    """Test Phase 1 expects exploit to succeed"""
    simulator = TwoPhaseSimulator()
    
    mock_exploit.execute_func = AsyncMock(
        side_effect=[successful_exploit_result, failed_exploit_result]
    )
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.phase_1_result.expected_result is True
    assert result.phase_1_result.exploit_success is True
    assert result.phase_1_result.phase_passed is True


@pytest.mark.asyncio
async def test_phase_2_expected_failure(
    mock_apv,
    mock_patch,
    mock_exploit,
    successful_exploit_result,
    failed_exploit_result
):
    """Test Phase 2 expects exploit to fail"""
    simulator = TwoPhaseSimulator()
    
    mock_exploit.execute_func = AsyncMock(
        side_effect=[successful_exploit_result, failed_exploit_result]
    )
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.phase_2_result.expected_result is False
    assert result.phase_2_result.exploit_success is False
    assert result.phase_2_result.phase_passed is True


# Tests: Edge cases

@pytest.mark.asyncio
async def test_both_phases_exploit_succeeds(
    mock_apv,
    mock_patch,
    mock_exploit,
    successful_exploit_result
):
    """Test when exploit succeeds in both phases (patch ineffective)"""
    simulator = TwoPhaseSimulator()
    
    # Exploit succeeds in both phases
    mock_exploit.execute_func = AsyncMock(return_value=successful_exploit_result)
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.phase_1_result.phase_passed is True  # Expected success
    assert result.phase_2_result.phase_passed is False  # Expected failure, got success!
    assert result.patch_validated is False


@pytest.mark.asyncio
async def test_both_phases_exploit_fails(
    mock_apv,
    mock_patch,
    mock_exploit,
    failed_exploit_result
):
    """Test when exploit fails in both phases (vulnerability not present?)"""
    simulator = TwoPhaseSimulator()
    
    # Exploit fails in both phases
    mock_exploit.execute_func = AsyncMock(return_value=failed_exploit_result)
    
    result = await simulator.execute_wargaming(
        apv=mock_apv,
        patch=mock_patch,
        exploit=mock_exploit
    )
    
    assert result.phase_1_result.phase_passed is False  # Expected success, got failure!
    assert result.phase_2_result.phase_passed is True   # Expected failure, got failure
    assert result.patch_validated is False
