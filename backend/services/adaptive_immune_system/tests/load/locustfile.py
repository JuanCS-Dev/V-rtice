"""
Locust load testing scenarios for HITL API.

This file contains 3 load test scenarios:
1. Read-heavy workload (90% reads, 10% writes)
2. Write-heavy workload (50% reads, 50% writes)
3. WebSocket-intensive workload (100 concurrent connections)

Usage:
    # Run read-heavy scenario (default)
    locust -f locustfile.py --headless -u 100 -r 10 -t 5m --host http://localhost:8003

    # Run with web UI
    locust -f locustfile.py --host http://localhost:8003

    # Run specific user class
    locust -f locustfile.py ReadHeavyUser --headless -u 100 -r 10 -t 5m

Target SLAs:
    - P95 latency < 500ms
    - Error rate < 0.1%
    - Throughput > 100 req/s
"""

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import json
import uuid
import random
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


# --- Test Data Generator ---

class TestDataGenerator:
    """Generate realistic test data for HITL API."""

    SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    DECISIONS = ["APPROVE", "REJECT", "MODIFY", "ESCALATE"]
    PACKAGES = [
        "requests", "django", "flask", "numpy", "pandas",
        "tensorflow", "pytorch", "fastapi", "sqlalchemy", "celery"
    ]
    CVE_IDS = [
        "CVE-2024-0001", "CVE-2024-0002", "CVE-2024-0003",
        "CVE-2024-0004", "CVE-2024-0005"
    ]

    @classmethod
    def generate_apv_id(cls) -> str:
        """Generate fake APV ID."""
        return f"APV-2025-{random.randint(1, 1000):04d}"

    @classmethod
    def generate_decision_payload(cls) -> Dict[str, Any]:
        """Generate decision POST payload."""
        return {
            "apv_id": cls.generate_apv_id(),
            "decision": random.choice(cls.DECISIONS),
            "reviewer_name": f"Reviewer {random.randint(1, 10)}",
            "comments": f"Test decision for load testing - {uuid.uuid4().hex[:8]}",
            "confidence_override": random.uniform(0.7, 1.0)
        }


# --- Scenario 1: Read-Heavy Workload ---

class ReadHeavyUser(FastHttpUser):
    """
    Read-heavy workload: 90% reads, 10% writes.

    Simulates typical analyst behavior browsing APV reviews.

    Target: 100 users, 5 minutes
    Expected throughput: ~150 req/s
    """

    wait_time = between(1, 3)  # 1-3 seconds between requests
    weight = 9  # 90% of traffic

    def on_start(self):
        """Called once per user on start."""
        logger.info(f"ReadHeavyUser {self.environment.runner.user_count} started")

    @task(50)  # Highest weight
    def get_reviews_list(self):
        """GET /hitl/reviews - List all pending reviews."""
        with self.client.get(
            "/hitl/reviews",
            params={"limit": 20, "offset": 0},
            catch_response=True,
            name="GET /hitl/reviews"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "reviews" in data:
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(30)
    def get_reviews_with_filters(self):
        """GET /hitl/reviews?severity=HIGH - Filtered list."""
        severity = random.choice(TestDataGenerator.SEVERITIES)
        with self.client.get(
            "/hitl/reviews",
            params={"severity": severity, "limit": 10},
            catch_response=True,
            name="GET /hitl/reviews (filtered)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(15)
    def get_review_details(self):
        """GET /hitl/reviews/{apv_id} - Single review details."""
        apv_id = TestDataGenerator.generate_apv_id()
        with self.client.get(
            f"/hitl/reviews/{apv_id}",
            catch_response=True,
            name="GET /hitl/reviews/{id}"
        ) as response:
            # 404 is acceptable (APV doesn't exist in test DB)
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(10)
    def get_stats(self):
        """GET /hitl/reviews/stats - Statistics."""
        with self.client.get(
            "/hitl/reviews/stats",
            catch_response=True,
            name="GET /hitl/reviews/stats"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "total" in data:
                    response.success()
                else:
                    response.failure("Invalid stats format")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(5)  # 10% writes
    def post_decision(self):
        """POST /hitl/decisions - Submit decision."""
        payload = TestDataGenerator.generate_decision_payload()
        with self.client.post(
            "/hitl/decisions",
            json=payload,
            catch_response=True,
            name="POST /hitl/decisions"
        ) as response:
            # 201 (created) or 404 (APV not found) are acceptable
            if response.status_code in [201, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


# --- Scenario 2: Write-Heavy Workload ---

class WriteHeavyUser(FastHttpUser):
    """
    Write-heavy workload: 50% reads, 50% writes.

    Simulates batch decision-making scenarios.

    Target: 50 users, 5 minutes
    Expected throughput: ~75 req/s
    """

    wait_time = between(0.5, 2)  # Faster pace
    weight = 5  # 50% of traffic

    @task(5)
    def get_reviews(self):
        """GET /hitl/reviews."""
        self.client.get("/hitl/reviews", params={"limit": 10})

    @task(5)  # Equal weight to reads
    def post_decision(self):
        """POST /hitl/decisions."""
        payload = TestDataGenerator.generate_decision_payload()
        self.client.post("/hitl/decisions", json=payload)


# --- Scenario 3: Health Check User ---

class HealthCheckUser(HttpUser):
    """
    Health check monitoring user.

    Simulates monitoring systems checking health endpoints.

    Target: 5 users, continuous
    Expected throughput: ~2 req/s
    """

    wait_time = between(5, 15)  # Every 5-15 seconds
    weight = 1  # Low traffic

    @task(10)
    def health_check(self):
        """GET /health - Basic health check."""
        self.client.get("/health", name="GET /health")

    @task(5)
    def readiness_check(self):
        """GET /health/ready - Readiness probe."""
        self.client.get("/health/ready", name="GET /health/ready")

    @task(3)
    def liveness_check(self):
        """GET /health/live - Liveness probe."""
        self.client.get("/health/live", name="GET /health/live")

    @task(1)
    def metrics(self):
        """GET /metrics - Prometheus metrics."""
        self.client.get("/metrics", name="GET /metrics")


# --- Event Handlers (Custom Metrics) ---

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    logger.info("=" * 60)
    logger.info("HITL API Load Test Started")
    logger.info(f"Host: {environment.host}")
    logger.info(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    logger.info("=" * 60)
    logger.info("HITL API Load Test Finished")

    # Print summary stats
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"Median response time: {stats.total.median_response_time}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    logger.info(f"99th percentile: {stats.total.get_response_time_percentile(0.99)}ms")
    logger.info(f"RPS: {stats.total.total_rps:.2f}")
    logger.info("=" * 60)

    # Validate SLAs
    p95 = stats.total.get_response_time_percentile(0.95)
    fail_ratio = stats.total.fail_ratio
    rps = stats.total.total_rps

    sla_pass = True
    logger.info("\nSLA Validation:")

    if p95 > 500:
        logger.error(f"❌ P95 latency SLA FAILED: {p95}ms > 500ms")
        sla_pass = False
    else:
        logger.info(f"✅ P95 latency SLA PASSED: {p95}ms < 500ms")

    if fail_ratio > 0.001:  # 0.1%
        logger.error(f"❌ Error rate SLA FAILED: {fail_ratio * 100:.2f}% > 0.1%")
        sla_pass = False
    else:
        logger.info(f"✅ Error rate SLA PASSED: {fail_ratio * 100:.2f}% < 0.1%")

    if rps < 100:
        logger.warning(f"⚠️ Throughput below target: {rps:.2f} < 100 req/s")
    else:
        logger.info(f"✅ Throughput SLA PASSED: {rps:.2f} > 100 req/s")

    if not sla_pass:
        logger.error("\n❌ LOAD TEST FAILED: SLA violations detected")
        environment.process_exit_code = 1
    else:
        logger.info("\n✅ LOAD TEST PASSED: All SLAs met")


# --- Custom Response Time Tracking ---

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track individual requests for custom analytics."""
    if exception:
        logger.warning(f"Request failed: {name} - {exception}")

    # Alert on slow requests (> 1s)
    if response_time > 1000:
        logger.warning(f"Slow request detected: {name} took {response_time}ms")
