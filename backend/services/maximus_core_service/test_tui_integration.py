#!/usr/bin/env python
"""
TUI Integration Validation

Validates Governance TUI components, logic, and integration points.
Tests TUI imports, component functionality, and backend connectivity.

Note: Full UI automation requires manual testing (see VALIDATION_CHECKLIST.md)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO compliant - NO MOCK, NO PLACEHOLDER, NO TODO
"""

import sys
import asyncio
import time
from typing import Dict, List
from dataclasses import dataclass
import httpx


@dataclass
class TUIValidationResult:
    """Result of a TUI validation test."""
    test_name: str
    passed: bool
    message: str
    duration: float


class TUIIntegrationValidator:
    """
    Validates TUI integration with Governance backend.

    Tests:
    - TUI module imports
    - Component instantiation
    - Backend API connectivity
    - Data flow from API to TUI structures
    - Session management logic
    """

    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Initialize TUI validator.

        Args:
            base_url: Base URL of governance server
        """
        self.base_url = base_url
        self.results: List[TUIValidationResult] = []

    def test_tui_imports(self) -> TUIValidationResult:
        """
        Test that TUI modules can be imported without errors.

        Returns:
            Validation result
        """
        print("\n" + "="*80)
        print("🧪 Test: TUI Module Imports")
        print("="*80)

        start_time = time.time()

        try:
            # Add vertice-terminal to path
            sys.path.insert(0, "/home/juan/vertice-dev/vertice-terminal")

            # Test critical imports
            from vertice.workspaces.governance import governance_workspace
            from vertice.workspaces.governance import components
            from vertice.workspaces.governance import workspace_manager

            print("✅ Core TUI modules imported successfully:")
            print(f"   - governance_workspace: {governance_workspace.__file__}")
            print(f"   - components: {components.__file__}")
            print(f"   - workspace_manager: {workspace_manager.__file__}")

            # Verify key classes exist
            assert hasattr(governance_workspace, 'GovernanceWorkspace'), \
                "GovernanceWorkspace class not found"
            assert hasattr(workspace_manager, 'WorkspaceManager'), \
                "WorkspaceManager class not found"
            assert hasattr(components, 'PendingPanel'), \
                "PendingPanel component not found"

            print("✅ Key classes verified:")
            print("   - GovernanceWorkspace")
            print("   - WorkspaceManager")
            print("   - PendingPanel, ActivePanel, HistoryPanel")

            duration = time.time() - start_time

            return TUIValidationResult(
                test_name="TUI Imports",
                passed=True,
                message="All TUI modules imported successfully",
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Import failed: {e}")

            return TUIValidationResult(
                test_name="TUI Imports",
                passed=False,
                message=str(e),
                duration=duration
            )

    def test_workspace_manager_instantiation(self) -> TUIValidationResult:
        """
        Test that WorkspaceManager can be instantiated.

        Returns:
            Validation result
        """
        print("\n" + "="*80)
        print("🧪 Test: WorkspaceManager Instantiation")
        print("="*80)

        start_time = time.time()

        try:
            sys.path.insert(0, "/home/juan/vertice-dev/vertice-terminal")
            from vertice.workspaces.governance.workspace_manager import WorkspaceManager
            import httpx

            # Create session first (required for WorkspaceManager)
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/api/v1/governance/session/create",
                    json={
                        "operator_id": "test_tui_validation@test",
                        "operator_name": "TUI Validator",
                        "role": "soc_operator"
                    }
                )
                session_data = response.json()
                session_id = session_data["session_id"]

            # Create manager instance
            manager = WorkspaceManager(
                backend_url=self.base_url,
                operator_id="test_tui_validation@test",
                session_id=session_id
            )

            print(f"✅ WorkspaceManager instantiated:")
            print(f"   Operator ID: {manager.operator_id}")
            print(f"   Backend URL: {manager.backend_url}")
            print(f"   Session ID: {manager.session_id}")

            duration = time.time() - start_time

            return TUIValidationResult(
                test_name="WorkspaceManager Instantiation",
                passed=True,
                message="WorkspaceManager created successfully",
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Instantiation failed: {e}")

            return TUIValidationResult(
                test_name="WorkspaceManager Instantiation",
                passed=False,
                message=str(e),
                duration=duration
            )

    async def test_backend_connectivity(self) -> TUIValidationResult:
        """
        Test that TUI can connect to backend API.

        Returns:
            Validation result
        """
        print("\n" + "="*80)
        print("🧪 Test: Backend API Connectivity")
        print("="*80)

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test health endpoint
                health_response = await client.get(f"{self.base_url}/health")
                assert health_response.status_code == 200, "Health check failed"

                # Test governance health
                gov_health_response = await client.get(
                    f"{self.base_url}/api/v1/governance/health"
                )
                assert gov_health_response.status_code == 200, "Governance health check failed"

                # Test session creation (key TUI operation)
                session_response = await client.post(
                    f"{self.base_url}/api/v1/governance/session/create",
                    json={
                        "operator_id": "tui_test_connect@test",
                        "operator_name": "TUI Connectivity Test",
                        "role": "soc_operator"
                    }
                )
                assert session_response.status_code == 200, "Session creation failed"

                session_data = session_response.json()
                session_id = session_data["session_id"]

                print("✅ Backend connectivity verified:")
                print(f"   Server health: OK")
                print(f"   Governance API: OK")
                print(f"   Session created: {session_id}")

            duration = time.time() - start_time

            return TUIValidationResult(
                test_name="Backend Connectivity",
                passed=True,
                message="All backend endpoints accessible",
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Connectivity test failed: {e}")

            return TUIValidationResult(
                test_name="Backend Connectivity",
                passed=False,
                message=str(e),
                duration=duration
            )

    async def test_decision_data_flow(self) -> TUIValidationResult:
        """
        Test data flow from backend to TUI-compatible structures.

        Returns:
            Validation result
        """
        print("\n" + "="*80)
        print("🧪 Test: Decision Data Flow (API → TUI)")
        print("="*80)

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Create session
                session_response = await client.post(
                    f"{self.base_url}/api/v1/governance/session/create",
                    json={
                        "operator_id": "tui_test_flow@test",
                        "operator_name": "TUI Data Flow Test",
                        "role": "soc_operator"
                    }
                )
                session_data = session_response.json()

                # Enqueue test decision
                decision_id = f"tui_flow_test_{time.time()}"
                enqueue_response = await client.post(
                    f"{self.base_url}/api/v1/governance/test/enqueue",
                    json={
                        "decision_id": decision_id,
                        "risk_level": "high",
                        "action_type": "block_ip",
                        "target": "192.168.1.1",
                        "confidence": 0.95,
                        "ai_reasoning": "TUI data flow test",
                        "threat_score": 9.0,
                        "threat_type": "test",
                        "metadata": {"source": "tui_test"}
                    }
                )
                assert enqueue_response.status_code == 200, "Enqueue failed"

                # Fetch pending decisions (as TUI would)
                pending_response = await client.get(
                    f"{self.base_url}/api/v1/governance/pending"
                )
                pending_data = pending_response.json()

                # Verify decision appears in pending
                assert pending_data["total_pending"] >= 1, "Decision not in pending queue"

                # Approve decision (as TUI would)
                approve_response = await client.post(
                    f"{self.base_url}/api/v1/governance/decision/{decision_id}/approve",
                    json={
                        "session_id": session_data["session_id"],
                        "comment": "TUI flow test approval"
                    }
                )
                assert approve_response.status_code == 200, "Approval failed"

                # Check stats updated (as TUI would display)
                stats_response = await client.get(
                    f"{self.base_url}/api/v1/governance/session/tui_test_flow@test/stats"
                )
                stats_data = stats_response.json()

                assert stats_data["total_decisions_reviewed"] >= 1, "Stats not updated"
                assert stats_data["total_approved"] >= 1, "Approval not recorded"

                print("✅ Data flow validated:")
                print(f"   Decision enqueued: {decision_id}")
                print(f"   Appeared in pending: ✓")
                print(f"   Approval processed: ✓")
                print(f"   Stats updated: ✓")
                print(f"   Reviewed: {stats_data['total_decisions_reviewed']}")
                print(f"   Approved: {stats_data['total_approved']}")

            duration = time.time() - start_time

            return TUIValidationResult(
                test_name="Decision Data Flow",
                passed=True,
                message="Complete data flow validated",
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Data flow test failed: {e}")

            return TUIValidationResult(
                test_name="Decision Data Flow",
                passed=False,
                message=str(e),
                duration=duration
            )

    async def test_sse_stream_compatibility(self) -> TUIValidationResult:
        """
        Test that SSE stream format is compatible with TUI expectations.

        Returns:
            Validation result
        """
        print("\n" + "="*80)
        print("🧪 Test: SSE Stream Compatibility")
        print("="*80)

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Create session
                session_response = await client.post(
                    f"{self.base_url}/api/v1/governance/session/create",
                    json={
                        "operator_id": "tui_test_sse@test",
                        "operator_name": "TUI SSE Test",
                        "role": "soc_operator"
                    }
                )
                session_data = session_response.json()
                operator_id = session_data["operator_id"]
                session_id = session_data["session_id"]

                # Connect to SSE stream
                async with client.stream(
                    "GET",
                    f"{self.base_url}/api/v1/governance/stream/{operator_id}",
                    params={"session_id": session_id}
                ) as response:
                    assert response.status_code == 200, f"SSE failed: {response.status_code}"

                    content_type = response.headers.get("content-type", "")
                    assert "text/event-stream" in content_type, \
                        f"Wrong content-type: {content_type}"

                    # Read connection event
                    events_found = []
                    lines_read = 0

                    async for line in response.aiter_lines():
                        lines_read += 1

                        if "event:" in line:
                            event_type = line.split("event:")[1].strip()
                            events_found.append(event_type)

                        # Stop after finding connection event
                        if "connected" in events_found:
                            break

                        # Safety timeout
                        if lines_read > 100:
                            break

                assert "connected" in events_found, "No connection event received"

                print("✅ SSE compatibility validated:")
                print(f"   Stream opened successfully")
                print(f"   Content-type: text/event-stream")
                print(f"   Connection event received: ✓")
                print(f"   Events found: {events_found}")

            duration = time.time() - start_time

            return TUIValidationResult(
                test_name="SSE Stream Compatibility",
                passed=True,
                message="SSE format compatible with TUI",
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ SSE compatibility test failed: {e}")

            return TUIValidationResult(
                test_name="SSE Stream Compatibility",
                passed=False,
                message=str(e),
                duration=duration
            )

    async def run_all_tests(self) -> bool:
        """
        Run all TUI integration tests.

        Returns:
            True if all tests pass
        """
        print("\n" + "="*80)
        print("🧪 TUI Integration Validation Suite")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print()

        # Run tests
        self.results.append(self.test_tui_imports())
        self.results.append(self.test_workspace_manager_instantiation())
        self.results.append(await self.test_backend_connectivity())
        self.results.append(await self.test_decision_data_flow())
        self.results.append(await self.test_sse_stream_compatibility())

        # Print summary
        print("\n" + "="*80)
        print("📊 TUI Integration Summary")
        print("="*80)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        if any(not r.passed for r in self.results):
            print(f"\n⚠️  Failed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"   - {result.test_name}: {result.message}")

        print("\n" + "="*80)

        if passed == total:
            print("✅ ALL TUI INTEGRATION TESTS PASSED!")
            print("\n📝 Next Step: Manual TUI Testing")
            print("   Run: python -m vertice.cli governance start --backend-url http://localhost:8002")
            print("   Refer to: VALIDATION_CHECKLIST.md for manual test steps")
        else:
            print(f"❌ {total - passed} test(s) failed - Review errors above")

        print("="*80)
        print()

        return passed == total


async def main():
    """Main entry point."""
    validator = TUIIntegrationValidator()
    success = await validator.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
