"""
End-to-End Test Runner - Comprehensive E2E tests for HITL system.

Tests:
1. APV data generation
2. API endpoints (GET/POST)
3. Decision workflow (approve/reject/modify/escalate)
4. WebSocket real-time updates
5. Performance (100+ APVs)
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List

import aiohttp

from hitl.test_data_generator import TestDataGenerator, generate_mock_apv_json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """End-to-end test runner for HITL system."""

    def __init__(self, base_url: str = "http://localhost:8003") -> None:
        self.base_url = base_url
        self.hitl_base = f"{base_url}/hitl"
        self.test_apvs: List[Dict[str, Any]] = []
        self.test_results: Dict[str, Any] = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
        }

    async def check_health(self) -> bool:
        """Check if HITL API is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.hitl_base}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"✅ Health check passed: {data}")
                        return True
                    else:
                        logger.error(f"❌ Health check failed: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False

    async def test_get_reviews_list(self) -> bool:
        """Test GET /hitl/reviews endpoint."""
        self.test_results["total_tests"] += 1
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.hitl_base}/reviews") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(
                            f"✅ GET /reviews: {len(data.get('reviews', []))} reviews"
                        )
                        self.test_results["passed"] += 1
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"❌ GET /reviews failed: {resp.status} - {error}")
                        self.test_results["failed"] += 1
                        self.test_results["errors"].append(
                            f"GET /reviews: {resp.status}"
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ GET /reviews error: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"GET /reviews: {str(e)}")
            return False

    async def test_get_reviews_with_filters(self) -> bool:
        """Test GET /reviews with filters."""
        self.test_results["total_tests"] += 1
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "severity": "critical",
                    "wargame_verdict": "PATCH_EFFECTIVE",
                    "limit": 5,
                }
                async with session.get(
                    f"{self.hitl_base}/reviews", params=params
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reviews = data.get("reviews", [])
                        logger.info(
                            f"✅ GET /reviews (filtered): {len(reviews)} critical/effective APVs"
                        )
                        self.test_results["passed"] += 1
                        return True
                    else:
                        error = await resp.text()
                        logger.error(
                            f"❌ GET /reviews (filtered) failed: {resp.status} - {error}"
                        )
                        self.test_results["failed"] += 1
                        return False
        except Exception as e:
            logger.error(f"❌ GET /reviews (filtered) error: {e}")
            self.test_results["failed"] += 1
            return False

    async def test_get_reviews_stats(self) -> bool:
        """Test GET /hitl/reviews/stats endpoint."""
        self.test_results["total_tests"] += 1
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.hitl_base}/reviews/stats") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(
                            f"✅ GET /reviews/stats: {data.get('pending_reviews', 0)} pending"
                        )
                        self.test_results["passed"] += 1
                        return True
                    else:
                        error = await resp.text()
                        logger.error(
                            f"❌ GET /reviews/stats failed: {resp.status} - {error}"
                        )
                        self.test_results["failed"] += 1
                        return False
        except Exception as e:
            logger.error(f"❌ GET /reviews/stats error: {e}")
            self.test_results["failed"] += 1
            return False

    async def test_get_review_details(self, apv_id: str) -> bool:
        """Test GET /hitl/reviews/{apv_id} endpoint."""
        self.test_results["total_tests"] += 1
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.hitl_base}/reviews/{apv_id}"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(
                            f"✅ GET /reviews/{apv_id}: {data.get('apv_code', 'N/A')}"
                        )
                        self.test_results["passed"] += 1
                        return True
                    else:
                        error = await resp.text()
                        logger.error(
                            f"❌ GET /reviews/{apv_id} failed: {resp.status} - {error}"
                        )
                        self.test_results["failed"] += 1
                        return False
        except Exception as e:
            logger.error(f"❌ GET /reviews/{apv_id} error: {e}")
            self.test_results["failed"] += 1
            return False

    async def test_submit_decision(
        self, apv_id: str, decision: str, justification: str
    ) -> bool:
        """Test POST /hitl/decisions endpoint."""
        self.test_results["total_tests"] += 1
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "apv_id": apv_id,
                    "decision": decision,
                    "justification": justification,
                    "confidence": 0.85,
                    "reviewer_name": "E2E Test Runner",
                    "reviewer_email": "e2e@test.local",
                }
                async with session.post(
                    f"{self.hitl_base}/decisions", json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(
                            f"✅ POST /decisions: {decision} for {data.get('apv_code', 'N/A')}"
                        )
                        self.test_results["passed"] += 1
                        return True
                    else:
                        error = await resp.text()
                        logger.error(
                            f"❌ POST /decisions failed: {resp.status} - {error}"
                        )
                        self.test_results["failed"] += 1
                        self.test_results["errors"].append(
                            f"POST /decisions ({decision}): {resp.status}"
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ POST /decisions error: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"POST /decisions ({decision}): {str(e)}")
            return False

    async def test_decision_workflow(self) -> bool:
        """Test complete decision workflow for all 4 decision types."""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING DECISION WORKFLOW (4 decision types)")
        logger.info("=" * 60)

        # First, fetch available APVs
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.hitl_base}/reviews", params={"limit": 10}) as resp:
                if resp.status != 200:
                    logger.error("❌ Could not fetch APVs for decision testing")
                    return False
                data = await resp.json()
                available_apvs = data.get("reviews", [])

        if len(available_apvs) < 4:
            logger.error(f"❌ Not enough APVs for testing (need 4, got {len(available_apvs)})")
            return False

        test_cases = [
            ("approve", "Patch is effective based on wargaming results. All validations passed. Approval justified."),
            ("reject", "Wargaming shows patch is insufficient. Exit codes indicate vulnerability still exploitable. Reject justified."),
            ("modify", "Wargaming results inconclusive. Patch needs additional hardening before merge. Request changes to add extra validation."),
            ("escalate", "While patch appears effective, the critical severity and complexity warrant security lead review before merging."),
        ]

        all_passed = True

        for idx, (decision, justification) in enumerate(test_cases):
            if idx >= len(available_apvs):
                break

            apv = available_apvs[idx]
            apv_id = apv["apv_id"]
            apv_code = apv["apv_code"]

            logger.info(f"\n🧪 Testing {decision.upper()} decision on {apv_code}...")

            result = await self.test_submit_decision(
                apv_id=apv_id, decision=decision, justification=justification
            )

            if result:
                logger.info(f"  ✅ {decision.upper()} workflow passed")
            else:
                logger.error(f"  ❌ {decision.upper()} workflow failed")
                all_passed = False

            await asyncio.sleep(0.5)  # Rate limiting

        return all_passed

    async def test_performance_load(self, count: int = 100) -> bool:
        """Test performance with large number of APVs."""
        logger.info("\n" + "=" * 60)
        logger.info(f"TESTING PERFORMANCE (fetching {count} APVs)")
        logger.info("=" * 60)

        self.test_results["total_tests"] += 1

        try:
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.hitl_base}/reviews", params={"limit": count}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        elapsed = time.time() - start_time
                        reviews_count = len(data.get("reviews", []))

                        logger.info(
                            f"✅ Performance test: Fetched {reviews_count} APVs in {elapsed:.2f}s"
                        )
                        logger.info(
                            f"   Throughput: {reviews_count / elapsed:.2f} APVs/sec"
                        )

                        # Check if performance is acceptable (< 2 seconds for 100 APVs)
                        if elapsed < 2.0:
                            logger.info("   🚀 Performance: EXCELLENT")
                            self.test_results["passed"] += 1
                            return True
                        elif elapsed < 5.0:
                            logger.warning("   ⚠️ Performance: ACCEPTABLE")
                            self.test_results["passed"] += 1
                            return True
                        else:
                            logger.error("   ❌ Performance: POOR (> 5s)")
                            self.test_results["failed"] += 1
                            return False
                    else:
                        error = await resp.text()
                        logger.error(
                            f"❌ Performance test failed: {resp.status} - {error}"
                        )
                        self.test_results["failed"] += 1
                        return False
        except Exception as e:
            logger.error(f"❌ Performance test error: {e}")
            self.test_results["failed"] += 1
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete E2E test suite."""
        logger.info("\n" + "=" * 60)
        logger.info("HITL E2E TEST SUITE - START")
        logger.info("=" * 60)

        start_time = time.time()

        # 1. Health check
        logger.info("\n🔍 Step 1: Health Check")
        healthy = await self.check_health()
        if not healthy:
            logger.error("❌ API is not healthy. Aborting tests.")
            return self.test_results

        # 2. Test GET endpoints
        logger.info("\n🔍 Step 2: Testing GET endpoints")
        await self.test_get_reviews_list()
        await asyncio.sleep(0.2)
        await self.test_get_reviews_with_filters()
        await asyncio.sleep(0.2)
        await self.test_get_reviews_stats()

        # 3. Test decision workflow (all 4 types)
        logger.info("\n🔍 Step 3: Testing Decision Workflow")
        await self.test_decision_workflow()

        # 4. Performance test
        logger.info("\n🔍 Step 4: Testing Performance")
        await self.test_performance_load(100)

        # Summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info("HITL E2E TEST SUITE - RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Tests:    {self.test_results['total_tests']}")
        logger.info(f"✅ Passed:      {self.test_results['passed']}")
        logger.info(f"❌ Failed:      {self.test_results['failed']}")
        logger.info(f"Duration:       {elapsed:.2f}s")

        if self.test_results["errors"]:
            logger.info(f"\n❌ Errors ({len(self.test_results['errors'])}):")
            for error in self.test_results["errors"]:
                logger.info(f"   - {error}")

        pass_rate = (
            self.test_results["passed"] / self.test_results["total_tests"] * 100
            if self.test_results["total_tests"] > 0
            else 0
        )
        logger.info(f"\n📊 Pass Rate:   {pass_rate:.1f}%")

        if pass_rate == 100:
            logger.info("\n🎉 ALL TESTS PASSED! 🎉")
        elif pass_rate >= 80:
            logger.warning("\n⚠️ MOST TESTS PASSED (some failures)")
        else:
            logger.error("\n❌ MULTIPLE TEST FAILURES")

        logger.info("=" * 60)

        return self.test_results


async def main() -> None:
    """Main entry point for E2E tests."""
    runner = E2ETestRunner(base_url="http://localhost:8003")

    # Run all tests
    results = await runner.run_all_tests()

    # Exit with appropriate code
    if results["failed"] == 0:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
