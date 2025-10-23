"""
Code Scanner - Targeted Coverage Tests

Objetivo: Cobrir code_scanner.py (29 lines, 0% → 90%+)

Testa CodeScanner: scan_code, get_status, vulnerability/performance/refactoring analysis

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from code_scanner import CodeScanner
from datetime import datetime


# ===== INITIALIZATION TESTS =====

def test_code_scanner_initialization():
    """
    SCENARIO: CodeScanner created
    EXPECTED: Default attributes set
    """
    scanner = CodeScanner()

    assert scanner.scan_history == []
    assert scanner.last_scan_time is None
    assert scanner.current_status == "ready_to_scan"


# ===== SCAN_CODE METHOD - VULNERABILITY ANALYSIS =====

@pytest.mark.asyncio
async def test_scan_code_vulnerability_eval_detection():
    """
    SCENARIO: scan_code() with eval() in code
    EXPECTED: Detects code injection vulnerability
    """
    scanner = CodeScanner()
    code = "result = eval(user_input)"

    results = await scanner.scan_code(code, "python", "vulnerability")

    assert results["language"] == "python"
    assert results["analysis_type"] == "vulnerability"
    assert len(results["findings"]) > 0
    assert any("eval/exec" in f["description"] for f in results["findings"])
    assert any(f["severity"] == "high" for f in results["findings"])


@pytest.mark.asyncio
async def test_scan_code_vulnerability_exec_detection():
    """
    SCENARIO: scan_code() with exec() in code
    EXPECTED: Detects code injection vulnerability
    """
    scanner = CodeScanner()
    code = "exec('print(1)')"

    results = await scanner.scan_code(code, "python", "vulnerability")

    assert len(results["findings"]) > 0
    assert any("eval/exec" in f["description"] for f in results["findings"])


@pytest.mark.asyncio
async def test_scan_code_vulnerability_hardcoded_password():
    """
    SCENARIO: scan_code() with hardcoded password
    EXPECTED: Detects hardcoded password vulnerability
    """
    scanner = CodeScanner()
    code = 'password = "mysecret123"'

    results = await scanner.scan_code(code, "python", "vulnerability")

    assert len(results["findings"]) > 0
    assert any("password" in f["description"].lower() for f in results["findings"])
    assert any(f["severity"] == "medium" for f in results["findings"])


@pytest.mark.asyncio
async def test_scan_code_vulnerability_no_findings():
    """
    SCENARIO: scan_code() with safe code
    EXPECTED: No vulnerabilities found
    """
    scanner = CodeScanner()
    code = "x = 1 + 2"

    results = await scanner.scan_code(code, "python", "vulnerability")

    assert results["findings"] == []


# ===== SCAN_CODE METHOD - PERFORMANCE ANALYSIS =====

@pytest.mark.asyncio
async def test_scan_code_performance_inefficient_loop():
    """
    SCENARIO: scan_code() with inefficient loop
    EXPECTED: Detects performance issue
    """
    scanner = CodeScanner()
    code = "for i in range(1000000): pass"

    results = await scanner.scan_code(code, "python", "performance")

    assert len(results["findings"]) > 0
    assert any("loop" in f["description"].lower() for f in results["findings"])
    assert any(f["type"] == "performance" for f in results["findings"])


@pytest.mark.asyncio
async def test_scan_code_performance_no_findings():
    """
    SCENARIO: scan_code() with efficient code
    EXPECTED: No performance issues found
    """
    scanner = CodeScanner()
    code = "for i in range(10): pass"

    results = await scanner.scan_code(code, "python", "performance")

    assert results["findings"] == []


# ===== SCAN_CODE METHOD - REFACTORING ANALYSIS =====

@pytest.mark.asyncio
async def test_scan_code_refactoring_high_complexity():
    """
    SCENARIO: scan_code() with many if statements (high cyclomatic complexity)
    EXPECTED: Detects refactoring opportunity
    """
    scanner = CodeScanner()
    # Code with 11 if statements
    code = "\n".join([f"if x == {i}: pass" for i in range(11)])

    results = await scanner.scan_code(code, "python", "refactoring")

    assert len(results["findings"]) > 0
    assert any("complexity" in f["description"].lower() for f in results["findings"])
    assert any(f["type"] == "refactoring" for f in results["findings"])


@pytest.mark.asyncio
async def test_scan_code_refactoring_low_complexity():
    """
    SCENARIO: scan_code() with simple code
    EXPECTED: No refactoring suggestions
    """
    scanner = CodeScanner()
    code = "if x: pass"

    results = await scanner.scan_code(code, "python", "refactoring")

    assert results["findings"] == []


# ===== SCAN_CODE METHOD - ERROR HANDLING =====

@pytest.mark.asyncio
async def test_scan_code_unsupported_analysis_type():
    """
    SCENARIO: scan_code() with unsupported analysis_type
    EXPECTED: Raises ValueError
    """
    scanner = CodeScanner()

    with pytest.raises(ValueError, match="Unsupported analysis type"):
        await scanner.scan_code("x = 1", "python", "unsupported_type")


# ===== SCAN_CODE METHOD - SCAN HISTORY =====

@pytest.mark.asyncio
async def test_scan_code_updates_history():
    """
    SCENARIO: scan_code() called
    EXPECTED: Scan added to history
    """
    scanner = CodeScanner()
    code = "x = 1"

    await scanner.scan_code(code, "python", "vulnerability")

    assert len(scanner.scan_history) == 1
    assert "code_snippet_hash" in scanner.scan_history[0]
    assert "results" in scanner.scan_history[0]


@pytest.mark.asyncio
async def test_scan_code_updates_last_scan_time():
    """
    SCENARIO: scan_code() called
    EXPECTED: last_scan_time updated to datetime
    """
    scanner = CodeScanner()

    await scanner.scan_code("x = 1", "python", "vulnerability")

    assert scanner.last_scan_time is not None
    assert isinstance(scanner.last_scan_time, datetime)


@pytest.mark.asyncio
async def test_scan_code_multiple_scans_history():
    """
    SCENARIO: scan_code() called multiple times
    EXPECTED: All scans tracked in history
    """
    scanner = CodeScanner()

    await scanner.scan_code("code1", "python", "vulnerability")
    await scanner.scan_code("code2", "python", "performance")

    assert len(scanner.scan_history) == 2


# ===== SCAN_CODE METHOD - RESULT FORMAT =====

@pytest.mark.asyncio
async def test_scan_code_result_has_timestamp():
    """
    SCENARIO: scan_code() result
    EXPECTED: Contains timestamp field
    """
    scanner = CodeScanner()

    results = await scanner.scan_code("x = 1", "python", "vulnerability")

    assert "timestamp" in results
    assert isinstance(results["timestamp"], str)


@pytest.mark.asyncio
async def test_scan_code_result_has_language():
    """
    SCENARIO: scan_code() result
    EXPECTED: Contains language field
    """
    scanner = CodeScanner()

    results = await scanner.scan_code("x = 1", "javascript", "vulnerability")

    assert results["language"] == "javascript"


@pytest.mark.asyncio
async def test_scan_code_result_has_analysis_type():
    """
    SCENARIO: scan_code() result
    EXPECTED: Contains analysis_type field
    """
    scanner = CodeScanner()

    results = await scanner.scan_code("x = 1", "python", "performance")

    assert results["analysis_type"] == "performance"


@pytest.mark.asyncio
async def test_scan_code_result_findings_is_list():
    """
    SCENARIO: scan_code() result
    EXPECTED: findings is a list
    """
    scanner = CodeScanner()

    results = await scanner.scan_code("x = 1", "python", "vulnerability")

    assert isinstance(results["findings"], list)


# ===== GET_STATUS METHOD TESTS =====

@pytest.mark.asyncio
async def test_get_status_initial_state():
    """
    SCENARIO: get_status() on new scanner
    EXPECTED: status=ready_to_scan, 0 scans, last_scan=N/A
    """
    scanner = CodeScanner()

    status = await scanner.get_status()

    assert status["status"] == "ready_to_scan"
    assert status["total_scans_performed"] == 0
    assert status["last_scan"] == "N/A"


@pytest.mark.asyncio
async def test_get_status_after_scan():
    """
    SCENARIO: get_status() after performing a scan
    EXPECTED: total_scans_performed=1, last_scan has timestamp
    """
    scanner = CodeScanner()
    await scanner.scan_code("x = 1", "python", "vulnerability")

    status = await scanner.get_status()

    assert status["total_scans_performed"] == 1
    assert status["last_scan"] != "N/A"
    assert isinstance(status["last_scan"], str)


@pytest.mark.asyncio
async def test_get_status_multiple_scans():
    """
    SCENARIO: get_status() after multiple scans
    EXPECTED: total_scans_performed matches scan count
    """
    scanner = CodeScanner()
    await scanner.scan_code("code1", "python", "vulnerability")
    await scanner.scan_code("code2", "python", "performance")
    await scanner.scan_code("code3", "python", "refactoring")

    status = await scanner.get_status()

    assert status["total_scans_performed"] == 3


@pytest.mark.asyncio
async def test_get_status_returns_dict():
    """
    SCENARIO: get_status() called
    EXPECTED: Returns dictionary with expected keys
    """
    scanner = CodeScanner()

    status = await scanner.get_status()

    assert isinstance(status, dict)
    assert "status" in status
    assert "total_scans_performed" in status
    assert "last_scan" in status


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
async def test_multiple_vulnerabilities_detected():
    """
    SCENARIO: Code with multiple vulnerabilities
    EXPECTED: All vulnerabilities detected
    """
    scanner = CodeScanner()
    code = '''
eval(user_input)
password = "secret123"
exec("malicious_code")
'''

    results = await scanner.scan_code(code, "python", "vulnerability")

    # Should detect both eval, exec, and password
    assert len(results["findings"]) >= 2


@pytest.mark.asyncio
async def test_scan_workflow_complete():
    """
    SCENARIO: Complete scan workflow
    EXPECTED: All operations work together
    """
    scanner = CodeScanner()

    # Initial status
    status = await scanner.get_status()
    assert status["total_scans_performed"] == 0

    # Perform scan
    results = await scanner.scan_code("eval(x)", "python", "vulnerability")
    assert len(results["findings"]) > 0

    # Check status updated
    status = await scanner.get_status()
    assert status["total_scans_performed"] == 1
    assert status["last_scan"] != "N/A"

    # Perform another scan
    results2 = await scanner.scan_code("x = 1", "python", "performance")
    assert results2["findings"] == []

    # Check status again
    status = await scanner.get_status()
    assert status["total_scans_performed"] == 2
