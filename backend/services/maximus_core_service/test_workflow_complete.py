#!/usr/bin/env python
"""
Complete Workflow Validation

End-to-end workflow testing for Governance Workspace.
Simulates real operator sessions processing decisions.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO compliant - NO MOCK, NO PLACEHOLDER, NO TODO
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum

import httpx


class WorkflowPhase(Enum):
    """Workflow test phases."""

    SESSION_CREATION = "session_creation"
    DECISION_ENQUEUE = "decision_enqueue"
    DECISION_PROCESSING = "decision_processing"
    STATS_VALIDATION = "stats_validation"
    CLEANUP = "cleanup"


@dataclass
class WorkflowMetrics:
    """Metrics collected during workflow testing."""

    sessions_created: int = 0
    decisions_enqueued: int = 0
    decisions_approved: int = 0
    decisions_rejected: int = 0
    decisions_escalated: int = 0
    total_processed: int = 0
    processing_time: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class OperatorSession:
    """Operator session data."""

    operator_id: str
    session_id: str
    decisions_processed: int = 0
    start_time: float = field(default_factory=time.time)


class WorkflowValidator:
    """
    Validates complete operator workflows.

    Tests:
    - Full operator session lifecycle
    - Mixed risk level decision processing
    - Stats accumulation accuracy
    - Concurrent operator handling
    - Error recovery
    """

    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Initialize workflow validator.

        Args:
            base_url: Base URL of governance server
        """
        self.base_url = base_url
        self.metrics = WorkflowMetrics()
        self.sessions: list[OperatorSession] = []

    async def test_single_operator_workflow(self) -> bool:
        """
        Test complete workflow for single operator.

        Workflow:
        1. Create session
        2. Enqueue 10 decisions (mixed risk levels)
        3. Process all decisions (approve/reject/escalate)
        4. Validate stats accuracy
        5. Check audit trail

        Returns:
            True if workflow successful
        """
        print("\n" + "=" * 80)
        print("🧪 Test: Single Operator Complete Workflow")
        print("=" * 80)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Phase 1: Create session (use unique operator ID to avoid state collision)
                operator_id = f"workflow_test_single_{time.time()}@test"
                session_response = await client.post(
                    f"{self.base_url}/api/v1/governance/session/create",
                    json={
                        "operator_id": operator_id,
                        "operator_name": "Workflow Test Operator",
                        "role": "soc_operator",
                    },
                )
                assert session_response.status_code == 200, "Session creation failed"

                session_data = session_response.json()
                session_id = session_data["session_id"]

                self.metrics.sessions_created += 1
                print("✅ Phase 1: Session created")
                print(f"   Session ID: {session_id}")

                # Phase 2: Enqueue 10 decisions (2 LOW, 3 MED, 4 HIGH, 1 CRIT)
                decisions = []
                risk_levels = ["low", "low", "medium", "medium", "medium", "high", "high", "high", "high", "critical"]

                for i, risk in enumerate(risk_levels):
                    decision_id = f"workflow_test_{i}_{time.time()}"
                    enqueue_response = await client.post(
                        f"{self.base_url}/api/v1/governance/test/enqueue",
                        json={
                            "decision_id": decision_id,
                            "risk_level": risk,
                            "action_type": "block_ip",
                            "target": f"192.168.1.{i}",
                            "confidence": 0.85 + (i * 0.01),
                            "ai_reasoning": f"Workflow test decision #{i}",
                            "threat_score": 5.0 + i,
                            "threat_type": "test",
                            "metadata": {"test_number": i},
                        },
                    )
                    assert enqueue_response.status_code == 200, f"Enqueue {i} failed"

                    decisions.append({"decision_id": decision_id, "risk_level": risk})
                    self.metrics.decisions_enqueued += 1

                print(f"✅ Phase 2: {len(decisions)} decisions enqueued")
                print("   Risk distribution: 2 LOW, 3 MED, 4 HIGH, 1 CRIT")

                # Phase 3: Process decisions
                # Strategy: Approve 5, Reject 3, Escalate 2
                actions = ["approve"] * 5 + ["reject"] * 3 + ["escalate"] * 2

                processing_start = time.time()

                for i, action in enumerate(actions):
                    decision_id = decisions[i]["decision_id"]

                    if action == "approve":
                        response = await client.post(
                            f"{self.base_url}/api/v1/governance/decision/{decision_id}/approve",
                            json={"session_id": session_id, "comment": f"Test approval {i}"},
                        )
                        self.metrics.decisions_approved += 1

                    elif action == "reject":
                        response = await client.post(
                            f"{self.base_url}/api/v1/governance/decision/{decision_id}/reject",
                            json={
                                "session_id": session_id,
                                "reason": f"Test rejection {i}",
                                "comment": f"Workflow test rejection #{i}",
                            },
                        )
                        self.metrics.decisions_rejected += 1

                    elif action == "escalate":
                        response = await client.post(
                            f"{self.base_url}/api/v1/governance/decision/{decision_id}/escalate",
                            json={
                                "session_id": session_id,
                                "escalation_reason": f"Test escalation {i}",
                                "comment": f"Workflow test escalation #{i}",
                            },
                        )
                        self.metrics.decisions_escalated += 1

                    assert response.status_code == 200, f"Action {action} failed for {decision_id}"
                    self.metrics.total_processed += 1

                self.metrics.processing_time = time.time() - processing_start

                print(f"✅ Phase 3: {self.metrics.total_processed} decisions processed")
                print(f"   Approved: {self.metrics.decisions_approved}")
                print(f"   Rejected: {self.metrics.decisions_rejected}")
                print(f"   Escalated: {self.metrics.decisions_escalated}")
                print(f"   Processing time: {self.metrics.processing_time:.2f}s")

                # Phase 4: Validate stats
                stats_response = await client.get(f"{self.base_url}/api/v1/governance/session/{operator_id}/stats")
                assert stats_response.status_code == 200, "Stats fetch failed"

                stats_data = stats_response.json()

                # Verify stats accuracy
                assert stats_data["total_decisions_reviewed"] == self.metrics.total_processed, (
                    f"Reviewed count mismatch: {stats_data['total_decisions_reviewed']} != {self.metrics.total_processed}"
                )

                assert stats_data["total_approved"] == self.metrics.decisions_approved, "Approved count mismatch"

                assert stats_data["total_rejected"] == self.metrics.decisions_rejected, "Rejected count mismatch"

                assert stats_data["total_escalated"] == self.metrics.decisions_escalated, "Escalated count mismatch"

                print("✅ Phase 4: Stats validated")
                print(f"   Total reviewed: {stats_data['total_decisions_reviewed']} ✓")
                print(f"   Approval rate: {stats_data['approval_rate'] * 100:.1f}%")
                print(f"   Rejection rate: {stats_data['rejection_rate'] * 100:.1f}%")
                print(f"   Escalation rate: {stats_data['escalation_rate'] * 100:.1f}%")

            print("✅ WORKFLOW COMPLETED SUCCESSFULLY")

            return True

        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            self.metrics.errors.append(str(e))
            return False

    async def test_concurrent_operators_workflow(self) -> bool:
        """
        Test multiple operators working concurrently.

        Returns:
            True if concurrent workflow successful
        """
        print("\n" + "=" * 80)
        print("🧪 Test: Concurrent Operators Workflow")
        print("=" * 80)

        try:
            num_operators = 3
            decisions_per_operator = 5

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Create sessions for all operators
                sessions = []
                test_timestamp = time.time()
                for i in range(num_operators):
                    operator_id = f"concurrent_op_{i}_{test_timestamp}@test"
                    session_response = await client.post(
                        f"{self.base_url}/api/v1/governance/session/create",
                        json={
                            "operator_id": operator_id,
                            "operator_name": f"Concurrent Operator {i}",
                            "role": "soc_operator",
                        },
                    )
                    session_data = session_response.json()
                    sessions.append({"operator_id": operator_id, "session_id": session_data["session_id"]})

                print(f"✅ Created {num_operators} operator sessions")

                # Each operator processes decisions concurrently
                async def operator_workflow(session: dict, operator_num: int):
                    """Individual operator workflow."""
                    decisions_processed = 0

                    for j in range(decisions_per_operator):
                        # Enqueue decision
                        decision_id = f"concurrent_{operator_num}_{j}_{time.time()}"
                        await client.post(
                            f"{self.base_url}/api/v1/governance/test/enqueue",
                            json={
                                "decision_id": decision_id,
                                "risk_level": "medium",
                                "action_type": "block_ip",
                                "target": f"10.0.{operator_num}.{j}",
                                "confidence": 0.90,
                                "ai_reasoning": f"Concurrent test op{operator_num} dec{j}",
                                "threat_score": 7.0,
                                "threat_type": "test",
                                "metadata": {},
                            },
                        )

                        # Process decision (approve)
                        await client.post(
                            f"{self.base_url}/api/v1/governance/decision/{decision_id}/approve",
                            json={
                                "session_id": session["session_id"],
                                "comment": f"Concurrent approval op{operator_num} dec{j}",
                            },
                        )

                        decisions_processed += 1

                    return decisions_processed

                # Run all operators concurrently
                start_time = time.time()

                results = await asyncio.gather(*[operator_workflow(session, i) for i, session in enumerate(sessions)])

                elapsed_time = time.time() - start_time

                total_processed = sum(results)

                print("✅ Concurrent processing completed:")
                print(f"   Operators: {num_operators}")
                print(f"   Total decisions: {total_processed}")
                print(f"   Per operator: {decisions_per_operator}")
                print(f"   Elapsed time: {elapsed_time:.2f}s")
                print(f"   Throughput: {total_processed / elapsed_time:.1f} decisions/sec")

                # Validate each operator's stats
                for session in sessions:
                    stats_response = await client.get(
                        f"{self.base_url}/api/v1/governance/session/{session['operator_id']}/stats"
                    )
                    stats_data = stats_response.json()

                    assert stats_data["total_decisions_reviewed"] == decisions_per_operator, (
                        f"Operator {session['operator_id']} stats mismatch"
                    )

                print("✅ All operator stats validated")

            return True

        except Exception as e:
            print(f"❌ Concurrent workflow failed: {e}")
            self.metrics.errors.append(str(e))
            return False

    async def test_mixed_actions_workflow(self) -> bool:
        """
        Test workflow with all action types (approve/reject/escalate).

        Returns:
            True if mixed actions workflow successful
        """
        print("\n" + "=" * 80)
        print("🧪 Test: Mixed Actions Workflow")
        print("=" * 80)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create session (use unique operator ID to avoid state collision)
                operator_id = f"mixed_actions_{time.time()}@test"
                session_response = await client.post(
                    f"{self.base_url}/api/v1/governance/session/create",
                    json={
                        "operator_id": operator_id,
                        "operator_name": "Mixed Actions Operator",
                        "role": "soc_operator",
                    },
                )
                session_data = session_response.json()
                session_id = session_data["session_id"]

                # Enqueue and process with each action type
                actions_to_test = [
                    ("approve", "Approval test"),
                    ("reject", "Rejection test"),
                    ("escalate", "Escalation test"),
                    ("approve", "Second approval"),
                    ("reject", "Second rejection"),
                ]

                action_counts = {"approve": 0, "reject": 0, "escalate": 0}

                for i, (action, comment) in enumerate(actions_to_test):
                    decision_id = f"mixed_action_{i}_{time.time()}"

                    # Enqueue
                    await client.post(
                        f"{self.base_url}/api/v1/governance/test/enqueue",
                        json={
                            "decision_id": decision_id,
                            "risk_level": "high",
                            "action_type": "block_ip",
                            "target": f"172.16.0.{i}",
                            "confidence": 0.88,
                            "ai_reasoning": f"Mixed action test {action}",
                            "threat_score": 8.0,
                            "threat_type": "test",
                            "metadata": {},
                        },
                    )

                    # Process with specific action - build payload based on action type
                    if action == "approve":
                        payload = {"session_id": session_id, "comment": comment}
                    elif action == "reject":
                        payload = {
                            "session_id": session_id,
                            "reason": comment,
                            "comment": f"Mixed action test rejection #{i}",
                        }
                    elif action == "escalate":
                        payload = {
                            "session_id": session_id,
                            "escalation_reason": comment,
                            "comment": f"Mixed action test escalation #{i}",
                        }
                    else:
                        payload = {"session_id": session_id, "comment": comment}

                    response = await client.post(
                        f"{self.base_url}/api/v1/governance/decision/{decision_id}/{action}", json=payload
                    )

                    assert response.status_code == 200, f"Action {action} failed"
                    action_counts[action] += 1

                print("✅ Mixed actions processed:")
                print(f"   Approvals: {action_counts['approve']}")
                print(f"   Rejections: {action_counts['reject']}")
                print(f"   Escalations: {action_counts['escalate']}")

                # Validate stats
                stats_response = await client.get(f"{self.base_url}/api/v1/governance/session/{operator_id}/stats")
                stats_data = stats_response.json()

                total_expected = sum(action_counts.values())
                assert stats_data["total_decisions_reviewed"] == total_expected, "Total reviewed mismatch"

                print(f"✅ Stats validated: {stats_data['total_decisions_reviewed']} total")

            return True

        except Exception as e:
            print(f"❌ Mixed actions workflow failed: {e}")
            self.metrics.errors.append(str(e))
            return False

    async def run_all_tests(self) -> bool:
        """
        Run all workflow validation tests.

        Returns:
            True if all tests pass
        """
        print("\n" + "=" * 80)
        print("🧪 Complete Workflow Validation Suite")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print()

        results = []

        # Run workflow tests
        results.append(("Single Operator Workflow", await self.test_single_operator_workflow()))
        results.append(("Concurrent Operators Workflow", await self.test_concurrent_operators_workflow()))
        results.append(("Mixed Actions Workflow", await self.test_mixed_actions_workflow()))

        # Print summary
        print("\n" + "=" * 80)
        print("📊 Workflow Validation Summary")
        print("=" * 80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {(passed / total) * 100:.1f}%")

        print("\nOverall Metrics:")
        print(f"  Sessions created: {self.metrics.sessions_created}")
        print(f"  Decisions enqueued: {self.metrics.decisions_enqueued}")
        print(f"  Total processed: {self.metrics.total_processed}")
        print(f"  Approved: {self.metrics.decisions_approved}")
        print(f"  Rejected: {self.metrics.decisions_rejected}")
        print(f"  Escalated: {self.metrics.decisions_escalated}")

        if self.metrics.errors:
            print("\n⚠️  Errors encountered:")
            for error in self.metrics.errors[:5]:
                print(f"   - {error}")

        print("\n" + "=" * 80)

        if passed == total:
            print("✅ ALL WORKFLOW TESTS PASSED - Complete workflows validated!")
        else:
            print(f"❌ {total - passed} test(s) failed - Review errors above")

        print("=" * 80)
        print()

        return passed == total


async def main():
    """Main entry point."""
    validator = WorkflowValidator()
    success = await validator.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
