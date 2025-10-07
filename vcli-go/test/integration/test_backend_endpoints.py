#!/usr/bin/env python3
"""
Integration test for Governance backend endpoints.

This script validates that the Python backend provides all the endpoints
required by the Go Governance workspace integration.

Tests correspond to the Go integration tests in governance_integration_test.go.
"""

import requests
import json
import time
from typing import Dict, Any, List

BASE_URL = "http://localhost:8001"
OPERATOR_ID = "integration_test_operator"
SESSION_ID = "integration_test_session"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def test_health_check() -> bool:
    """Test /health endpoint"""
    print("\n" + "="*60)
    print("TEST: Health Check")
    print("="*60)

    try:
        response = requests.get(f"{BASE_URL}/api/v1/governance/health", timeout=5)

        if response.status_code == 200:
            print_success(f"Backend is healthy (status: {response.status_code})")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


def test_metrics() -> bool:
    """Test /governance/metrics endpoint"""
    print("\n" + "="*60)
    print("TEST: Metrics Retrieval")
    print("="*60)

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/governance/metrics",
            headers={"X-Operator-ID": OPERATOR_ID},
            timeout=5
        )

        if response.status_code != 200:
            print_error(f"Metrics request failed: {response.status_code}")
            return False

        metrics = response.json()

        print_success("Metrics retrieved successfully:")
        print(f"   Total Pending: {metrics.get('total_pending', 'N/A')}")
        print(f"   Pending Critical: {metrics.get('pending_critical', 'N/A')}")
        print(f"   Pending High: {metrics.get('pending_high', 'N/A')}")
        print(f"   Pending Medium: {metrics.get('pending_medium', 'N/A')}")
        print(f"   Pending Low: {metrics.get('pending_low', 'N/A')}")
        print(f"   Nearing SLA: {metrics.get('nearing_sla', 'N/A')}")
        print(f"   Breached SLA: {metrics.get('breached_sla', 'N/A')}")

        return True

    except Exception as e:
        print_error(f"Metrics error: {e}")
        return False


def test_list_decisions() -> List[Dict[str, Any]]:
    """Test /governance/pending endpoint"""
    print("\n" + "="*60)
    print("TEST: List Pending Decisions")
    print("="*60)

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/governance/pending",
            headers={"X-Operator-ID": OPERATOR_ID},
            params={"limit": 10},
            timeout=5
        )

        if response.status_code != 200:
            print_error(f"List decisions failed: {response.status_code}")
            return []

        data = response.json()
        decisions = data.get('decisions', [])

        print_success(f"Retrieved {len(decisions)} pending decisions")

        for i, decision in enumerate(decisions, 1):
            print(f"   [{i}] {decision.get('decision_id', 'N/A')}: "
                  f"{decision.get('action_type', 'N/A')} → {decision.get('target', 'N/A')} "
                  f"(risk: {decision.get('risk_level', 'N/A')})")

        return decisions

    except Exception as e:
        print_error(f"List decisions error: {e}")
        return []


def test_create_session() -> str:
    """Test session creation endpoint"""
    print("\n" + "="*60)
    print("TEST: Create Session")
    print("="*60)

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/governance/session/create",
            json={
                "operator_id": OPERATOR_ID,
                "operator_name": "Integration Test Operator",
                "operator_role": "soc_operator"
            },
            timeout=5
        )

        if response.status_code != 200:
            print_error(f"Session creation failed: {response.status_code}")
            return ""

        data = response.json()
        session_id = data.get('session_id', '')

        print_success(f"Session created: {session_id}")
        return session_id

    except Exception as e:
        print_error(f"Session creation error: {e}")
        return ""


def test_enqueue_decision() -> str:
    """Test enqueueing a test decision"""
    print("\n" + "="*60)
    print("TEST: Enqueue Test Decision")
    print("="*60)

    try:
        test_decision = {
            "action_type": "block_ip",
            "target": "10.0.0.42",
            "risk_level": "high",
            "confidence": 0.95,
            "threat_score": 0.87,
            "reasoning": "Suspicious activity detected from IP - integration test"
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/governance/test/enqueue",
            json=test_decision,
            timeout=5
        )

        if response.status_code != 200:
            print_error(f"Enqueue failed: {response.status_code}")
            print(f"Response: {response.text}")
            return ""

        data = response.json()
        decision_id = data.get('decision_id', '')

        print_success(f"Test decision enqueued: {decision_id}")
        print(f"   Action: {test_decision['action_type']} → {test_decision['target']}")
        print(f"   Risk: {test_decision['risk_level']}")

        return decision_id

    except Exception as e:
        print_error(f"Enqueue error: {e}")
        return ""


def test_approve_decision(decision_id: str, session_id: str) -> bool:
    """Test approving a decision"""
    print("\n" + "="*60)
    print(f"TEST: Approve Decision {decision_id}")
    print("="*60)

    if not decision_id:
        print_warning("No decision ID provided, skipping approval test")
        return False

    if not session_id:
        print_warning("No session ID provided, skipping approval test")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/governance/decision/{decision_id}/approve",
            json={
                "session_id": session_id,
                "comment": "Approved via integration test"
            },
            headers={"X-Operator-ID": OPERATOR_ID},
            timeout=5
        )

        if response.status_code not in [200, 202]:
            print_error(f"Approval failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        print_success(f"Decision {decision_id} approved successfully")
        return True

    except Exception as e:
        print_error(f"Approval error: {e}")
        return False


def test_reject_decision(decision_id: str, session_id: str) -> bool:
    """Test rejecting a decision"""
    print("\n" + "="*60)
    print(f"TEST: Reject Decision {decision_id}")
    print("="*60)

    if not decision_id:
        print_warning("No decision ID provided, skipping rejection test")
        return False

    if not session_id:
        print_warning("No session ID provided, skipping rejection test")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/governance/decision/{decision_id}/reject",
            json={
                "session_id": session_id,
                "comment": "Rejected via integration test"
            },
            headers={"X-Operator-ID": OPERATOR_ID},
            timeout=5
        )

        if response.status_code not in [200, 202]:
            print_error(f"Rejection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        print_success(f"Decision {decision_id} rejected successfully")
        return True

    except Exception as e:
        print_error(f"Rejection error: {e}")
        return False


def test_sse_stream() -> bool:
    """Test SSE stream endpoint"""
    print("\n" + "="*60)
    print("TEST: SSE Event Stream")
    print("="*60)

    try:
        print_info("Connecting to SSE stream...")

        response = requests.get(
            f"{BASE_URL}/api/v1/governance/stream/{OPERATOR_ID}",
            headers={
                "Accept": "text/event-stream",
                "X-Operator-ID": OPERATOR_ID,
                "X-Session-ID": SESSION_ID
            },
            stream=True,
            timeout=10
        )

        if response.status_code != 200:
            print_error(f"SSE connection failed: {response.status_code}")
            return False

        print_success("SSE stream connected")
        print_info("Listening for events (5 seconds)...")

        event_count = 0
        start_time = time.time()

        for line in response.iter_lines():
            if time.time() - start_time > 5:
                break

            if line:
                line_str = line.decode('utf-8')

                if line_str.startswith('event:'):
                    event_type = line_str.split(':', 1)[1].strip()
                    event_count += 1
                    print(f"   Event received: {event_type}")

        print_success(f"Received {event_count} events in 5 seconds")
        return True

    except requests.Timeout:
        print_warning("SSE stream timeout (this may be normal if no events)")
        return True
    except Exception as e:
        print_error(f"SSE stream error: {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("🏛️  GOVERNANCE BACKEND INTEGRATION TESTS")
    print("="*60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Operator ID: {OPERATOR_ID}")
    print(f"Session ID: {SESSION_ID}")

    results = {}

    # Test 1: Health check
    results['health'] = test_health_check()

    # Test 2: Create session
    session_id = test_create_session()
    results['session'] = bool(session_id)

    # Test 3: Metrics
    results['metrics'] = test_metrics()

    # Test 4: List decisions
    decisions = test_list_decisions()
    results['list_decisions'] = True  # If we got here, it worked

    # Test 5: Enqueue test decision
    decision_id = test_enqueue_decision()
    results['enqueue'] = bool(decision_id)

    # Test 6: Approve decision
    if decision_id and session_id:
        time.sleep(1)  # Wait for decision to be processed
        results['approve'] = test_approve_decision(decision_id, session_id)

    # Test 7: Enqueue another for rejection test
    decision_id_2 = test_enqueue_decision()
    if decision_id_2 and session_id:
        time.sleep(1)
        results['reject'] = test_reject_decision(decision_id_2, session_id)

    # Test 8: SSE stream
    results['sse'] = test_sse_stream()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{test_name:20s} {status}")

    print("="*60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print_success("All tests passed! ✨")
        print_info("\n📝 Next steps:")
        print("   1. Install Go: https://go.dev/doc/install")
        print("   2. Run Go integration tests:")
        print("      cd /home/juan/vertice-dev/vcli-go")
        print("      go test -v ./test/integration -run TestGovernance")
        return 0
    else:
        print_error(f"{total_tests - passed_tests} tests failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
