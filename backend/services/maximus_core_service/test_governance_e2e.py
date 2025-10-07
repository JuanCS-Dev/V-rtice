#!/usr/bin/env python
"""
E2E Validation Script for Governance Production Server

Validates all endpoints programmatically before manual TUI testing.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO compliant
"""

import asyncio
import json
import time
from typing import Dict, List
import httpx


class GovernanceE2EValidator:
    """
    End-to-end validator for Governance Production Server.

    Tests all critical endpoints and workflows.
    """

    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Initialize validator.

        Args:
            base_url: Base URL of governance server
        """
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
        self.results: List[Dict] = []

    def test(self, name: str, func):
        """
        Run a test and record result.

        Args:
            name: Test name
            func: Test function
        """
        print(f"\n{'='*80}")
        print(f"🧪 Test: {name}")
        print(f"{'='*80}")

        try:
            start_time = time.time()
            func()
            elapsed = time.time() - start_time

            self.results.append({
                "test": name,
                "status": "PASS",
                "elapsed": f"{elapsed:.3f}s"
            })
            print(f"✅ PASS ({elapsed:.3f}s)")

        except Exception as e:
            elapsed = time.time() - start_time
            self.results.append({
                "test": name,
                "status": "FAIL",
                "error": str(e),
                "elapsed": f"{elapsed:.3f}s"
            })
            print(f"❌ FAIL ({elapsed:.3f}s): {e}")

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get(f"{self.base_url}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["service"] == "Governance Workspace Production Server"
        assert data["version"] == "1.0.0"
        assert "governance_api" in data

        print(f"   Service: {data['service']}")
        print(f"   Version: {data['version']}")

    def test_health_endpoint(self):
        """Test health endpoint."""
        response = self.client.get(f"{self.base_url}/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["status"] == "healthy"
        assert data["components"]["decision_queue"] is True
        assert data["components"]["operator_interface"] is True
        assert data["components"]["decision_framework"] is True

        print(f"   Status: {data['status']}")
        print(f"   Components: ✅ All healthy")

    def test_governance_health(self):
        """Test governance health endpoint."""
        response = self.client.get(f"{self.base_url}/api/v1/governance/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["status"] == "healthy"
        assert "active_connections" in data
        assert "queue_size" in data

        print(f"   Status: {data['status']}")
        print(f"   Active connections: {data['active_connections']}")
        print(f"   Queue size: {data['queue_size']}")

    def test_session_creation(self):
        """Test operator session creation."""
        payload = {
            "operator_id": "test_e2e@test",
            "operator_name": "E2E Test Operator",
            "role": "soc_operator"
        }

        response = self.client.post(
            f"{self.base_url}/api/v1/governance/session/create",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "session_id" in data, "Response missing session_id"
        assert data["operator_id"] == "test_e2e@test", "Operator ID mismatch"
        assert "message" in data, "Response missing message"

        self.session_id = data["session_id"]

        print(f"   Session ID: {self.session_id}")
        print(f"   Operator: {data['operator_id']}")
        print(f"   Expires: {data.get('expires_at', 'N/A')}")

    def test_pending_decisions(self):
        """Test get pending decisions."""
        response = self.client.get(f"{self.base_url}/api/v1/governance/pending")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, dict), "Expected dict response"
        assert "total_pending" in data, "Response missing total_pending"
        assert "by_risk_level" in data, "Response missing by_risk_level"

        print(f"   Total pending: {data['total_pending']}")
        print(f"   By risk: {data['by_risk_level']}")
        print(f"   SLA violations: {data.get('sla_violations', 0)}")

    def test_enqueue_decision(self):
        """Test enqueuing a test decision."""
        decision_data = {
            "decision_id": f"test_e2e_{time.time()}",
            "risk_level": "high",
            "action_type": "block_ip",
            "target": "192.168.1.100",
            "confidence": 0.85,
            "ai_reasoning": "E2E test decision for validation",
            "threat_score": 8.5,
            "threat_type": "command_and_control",
            "metadata": {
                "source": "e2e_validator",
                "timestamp": time.time()
            }
        }

        response = self.client.post(
            f"{self.base_url}/api/v1/governance/test/enqueue",
            json=decision_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["status"] == "success", f"Expected status='success', got '{data.get('status')}'"
        assert "decision_id" in data, "Response missing decision_id"

        self.test_decision_id = data["decision_id"]

        print(f"   Decision ID: {self.test_decision_id}")
        print(f"   Risk: {data['risk_level']}")
        print(f"   Message: {data.get('message', 'N/A')}")

    def test_approve_decision(self):
        """Test approving a decision."""
        payload = {
            "session_id": self.session_id,
            "comment": "E2E test approval"
        }

        response = self.client.post(
            f"{self.base_url}/api/v1/governance/decision/{self.test_decision_id}/approve",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["status"] == "approved"
        assert data["decision_id"] == self.test_decision_id

        print(f"   Decision: {data['status']}")
        print(f"   By: {data.get('approved_by', 'system')}")

    def test_session_stats(self):
        """Test operator session stats."""
        response = self.client.get(
            f"{self.base_url}/api/v1/governance/session/test_e2e@test/stats"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "operator_id" in data, "Response missing operator_id"
        assert "total_decisions_reviewed" in data, "Response missing total_decisions_reviewed"
        assert data["operator_id"] == "test_e2e@test", "Operator ID mismatch"

        print(f"   Operator: {data['operator_id']}")
        print(f"   Sessions: {data.get('total_sessions', 0)}")
        print(f"   Reviewed: {data['total_decisions_reviewed']}")
        print(f"   Approved: {data.get('total_approved', 0)}")
        print(f"   Approval rate: {data.get('approval_rate', 0)*100:.1f}%")

    def run_all_tests(self):
        """Run all validation tests."""
        print("\n" + "="*80)
        print("🧪 Governance E2E Validation Suite")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print()

        # Run tests in order
        self.test("Root Endpoint", self.test_root_endpoint)
        self.test("Health Endpoint", self.test_health_endpoint)
        self.test("Governance Health", self.test_governance_health)
        self.test("Session Creation", self.test_session_creation)
        self.test("Pending Decisions", self.test_pending_decisions)
        self.test("Enqueue Decision", self.test_enqueue_decision)
        self.test("Approve Decision", self.test_approve_decision)
        self.test("Session Stats", self.test_session_stats)

        # Print summary
        print("\n" + "="*80)
        print("📊 Test Summary")
        print("="*80)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total = len(self.results)

        print(f"\nTotal: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        if failed > 0:
            print("\n⚠️  Failed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"   - {result['test']}: {result['error']}")

        print("\n" + "="*80)

        if failed == 0:
            print("✅ ALL TESTS PASSED - Server is production-ready!")
        else:
            print(f"❌ {failed} test(s) failed - Review errors above")

        print("="*80)
        print()

        return failed == 0


if __name__ == "__main__":
    validator = GovernanceE2EValidator()
    success = validator.run_all_tests()

    exit(0 if success else 1)
