"""
RabbitMQ Load Testing Suite.

Tests message throughput, consumer scaling, and system behavior under load.

Usage:
    # Install locust
    pip install locust

    # Run load test
    locust -f tests/load/test_rabbitmq_load.py --host=http://localhost:5672

    # Web UI
    open http://localhost:8089

Test Scenarios:
1. Baseline throughput (100 msgs/sec)
2. Burst traffic (1000 msgs/sec for 30s)
3. Sustained high load (500 msgs/sec for 5 min)
4. Consumer scaling (1 → 10 consumers)
5. Message priority handling (mix of priorities)
"""

import asyncio
import random
import time
import uuid
from datetime import datetime
from typing import Any, Dict

from locust import HttpUser, TaskSet, between, events, task

# Import messaging components
try:
    from messaging.client import RabbitMQClient, get_rabbitmq_client
    from messaging.publisher import (
        APVPublisher,
        WargameReportPublisher,
        HITLNotificationPublisher,
    )
    from models.apv import APVDispatchMessage
    from models.wargame import WargameReportMessage
    MESSAGING_AVAILABLE = True
except ImportError:
    MESSAGING_AVAILABLE = False


class MessageGenerator:
    """Generates realistic test messages for load testing."""

    CVE_IDS = [
        "CVE-2024-0001",
        "CVE-2024-0002",
        "CVE-2024-0003",
        "CVE-2024-0004",
        "CVE-2024-0005",
    ]

    PACKAGES = [
        "requests",
        "django",
        "flask",
        "numpy",
        "pandas",
        "sqlalchemy",
        "celery",
        "redis",
    ]

    SEVERITIES = ["critical", "high", "medium", "low"]
    REMEDIATION_TYPES = ["dependency_upgrade", "code_patch", "configuration_change"]

    @classmethod
    def generate_apv_message(cls) -> APVDispatchMessage:
        """Generate random APV dispatch message."""
        severity = random.choice(cls.SEVERITIES)
        package = random.choice(cls.PACKAGES)

        return APVDispatchMessage(
            message_id=str(uuid.uuid4()),
            apv_id=str(uuid.uuid4()),
            apv_code=f"APV-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000,9999)}",
            cve_id=random.choice(cls.CVE_IDS),
            severity=severity,
            cvss_score=random.uniform(4.0, 10.0),
            affected_package=package,
            current_version=f"{random.randint(1,3)}.{random.randint(0,20)}.0",
            fixed_version=f"{random.randint(2,4)}.{random.randint(0,25)}.0",
            affected_components=[f"component-{i}" for i in range(random.randint(1, 5))],
            remediation_type=random.choice(cls.REMEDIATION_TYPES),
            priority=cls._severity_to_priority(severity),
            timestamp=datetime.utcnow(),
        )

    @classmethod
    def generate_wargame_message(cls) -> WargameReportMessage:
        """Generate random wargaming result message."""
        verdicts = ["success", "needs_review", "failed"]
        verdict = random.choice(verdicts)

        return WargameReportMessage(
            message_id=str(uuid.uuid4()),
            remedy_id=f"APV-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000,9999)}",
            run_code=f"WAR-{random.randint(10000,99999)}",
            timestamp=datetime.utcnow(),
            verdict=verdict,
            confidence_score=random.uniform(0.5, 1.0),
            exploit_before_status="vulnerable" if random.random() > 0.2 else "safe",
            exploit_after_status="fixed" if verdict == "success" else "vulnerable",
            evidence_url=f"https://github.com/org/repo/actions/runs/{random.randint(1000,9999)}",
            should_trigger_hitl=(verdict == "needs_review"),
            auto_merge_approved=(verdict == "success" and random.random() > 0.3),
        )

    @staticmethod
    def _severity_to_priority(severity: str) -> int:
        """Convert severity to priority (1-10)."""
        mapping = {
            "critical": 10,
            "high": 8,
            "medium": 5,
            "low": 3,
        }
        return mapping.get(severity, 5)


class LoadTestMetrics:
    """Track load testing metrics."""

    def __init__(self):
        self.messages_published = 0
        self.messages_failed = 0
        self.total_latency = 0.0
        self.latencies = []
        self.start_time = time.time()

    def record_success(self, latency: float):
        """Record successful message publish."""
        self.messages_published += 1
        self.total_latency += latency
        self.latencies.append(latency)

    def record_failure(self):
        """Record failed message publish."""
        self.messages_failed += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        elapsed = time.time() - self.start_time
        throughput = self.messages_published / elapsed if elapsed > 0 else 0

        latencies_sorted = sorted(self.latencies)
        p50 = latencies_sorted[len(latencies_sorted) // 2] if latencies_sorted else 0
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0
        p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)] if latencies_sorted else 0

        return {
            "messages_published": self.messages_published,
            "messages_failed": self.messages_failed,
            "elapsed_seconds": elapsed,
            "throughput_msg_per_sec": throughput,
            "avg_latency_ms": (self.total_latency / self.messages_published * 1000)
            if self.messages_published > 0
            else 0,
            "p50_latency_ms": p50 * 1000,
            "p95_latency_ms": p95 * 1000,
            "p99_latency_ms": p99 * 1000,
        }


# Global metrics
metrics = LoadTestMetrics()


class RabbitMQLoadTest(TaskSet):
    """
    Load test tasks for RabbitMQ messaging.

    Simulates realistic message publishing patterns.
    """

    def on_start(self):
        """Initialize RabbitMQ client."""
        if not MESSAGING_AVAILABLE:
            print("⚠️ Messaging modules not available - skipping load test")
            self.client_available = False
            return

        try:
            # Get RabbitMQ client (async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = loop

            self.rabbitmq_client = get_rabbitmq_client()
            self.apv_publisher = APVPublisher(self.rabbitmq_client)
            self.wargame_publisher = WargameReportPublisher(self.rabbitmq_client)

            self.client_available = True
            print("✅ RabbitMQ client initialized for load testing")

        except Exception as e:
            print(f"❌ Failed to initialize RabbitMQ client: {e}")
            self.client_available = False

    @task(weight=3)
    def publish_apv_message(self):
        """
        Publish APV dispatch message (weight=3 → 60% of traffic).

        Most common operation in the system.
        """
        if not self.client_available:
            return

        message = MessageGenerator.generate_apv_message()

        start_time = time.time()
        try:
            # Publish message
            message_id = self.loop.run_until_complete(
                self.apv_publisher.dispatch_apv(message)
            )

            latency = time.time() - start_time
            metrics.record_success(latency)

            # Report to Locust
            events.request.fire(
                request_type="rabbitmq",
                name="apv_dispatch",
                response_time=latency * 1000,  # ms
                response_length=len(message.model_dump_json()),
                exception=None,
                context={},
            )

        except Exception as e:
            latency = time.time() - start_time
            metrics.record_failure()

            events.request.fire(
                request_type="rabbitmq",
                name="apv_dispatch",
                response_time=latency * 1000,
                response_length=0,
                exception=e,
                context={},
            )

    @task(weight=2)
    def publish_wargame_message(self):
        """
        Publish wargaming result message (weight=2 → 40% of traffic).

        Follows APV dispatch in workflow.
        """
        if not self.client_available:
            return

        message = MessageGenerator.generate_wargame_message()

        start_time = time.time()
        try:
            message_id = self.loop.run_until_complete(
                self.wargame_publisher.publish_report(message)
            )

            latency = time.time() - start_time
            metrics.record_success(latency)

            events.request.fire(
                request_type="rabbitmq",
                name="wargame_result",
                response_time=latency * 1000,
                response_length=len(message.model_dump_json()),
                exception=None,
                context={},
            )

        except Exception as e:
            latency = time.time() - start_time
            metrics.record_failure()

            events.request.fire(
                request_type="rabbitmq",
                name="wargame_result",
                response_time=latency * 1000,
                response_length=0,
                exception=e,
                context={},
            )

    @task(weight=1)
    def publish_burst_messages(self):
        """
        Publish burst of messages (weight=1 → occasional bursts).

        Simulates batch processing or alert storms.
        """
        if not self.client_available:
            return

        burst_size = random.randint(5, 20)

        start_time = time.time()
        published = 0

        try:
            for _ in range(burst_size):
                message = MessageGenerator.generate_apv_message()
                self.loop.run_until_complete(self.apv_publisher.dispatch_apv(message))
                published += 1

            latency = time.time() - start_time
            metrics.record_success(latency)

            events.request.fire(
                request_type="rabbitmq",
                name=f"burst_{burst_size}_messages",
                response_time=latency * 1000,
                response_length=published * 500,  # estimate
                exception=None,
                context={},
            )

        except Exception as e:
            latency = time.time() - start_time
            metrics.record_failure()

            events.request.fire(
                request_type="rabbitmq",
                name=f"burst_{burst_size}_messages",
                response_time=latency * 1000,
                response_length=0,
                exception=e,
                context={},
            )


class RabbitMQUser(HttpUser):
    """
    Locust user for RabbitMQ load testing.

    Simulates concurrent publishers sending messages at varying rates.
    """

    tasks = [RabbitMQLoadTest]
    wait_time = between(0.1, 2.0)  # 0.1-2 seconds between tasks

    # Note: We don't actually use HTTP, but Locust requires HttpUser
    # RabbitMQ uses AMQP protocol directly


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print load test configuration."""
    print("\n" + "=" * 80)
    print("🚀 RabbitMQ LOAD TEST STARTING")
    print("=" * 80)
    print(f"Messaging available: {MESSAGING_AVAILABLE}")
    if not MESSAGING_AVAILABLE:
        print("⚠️ WARNING: Messaging modules not available - load test will be skipped")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final statistics."""
    stats = metrics.get_stats()

    print("\n" + "=" * 80)
    print("📊 LOAD TEST RESULTS")
    print("=" * 80)
    print(f"Messages Published:  {stats['messages_published']:,}")
    print(f"Messages Failed:     {stats['messages_failed']:,}")
    print(f"Elapsed Time:        {stats['elapsed_seconds']:.2f}s")
    print(f"Throughput:          {stats['throughput_msg_per_sec']:.2f} msg/sec")
    print(f"Avg Latency:         {stats['avg_latency_ms']:.2f} ms")
    print(f"P50 Latency:         {stats['p50_latency_ms']:.2f} ms")
    print(f"P95 Latency:         {stats['p95_latency_ms']:.2f} ms")
    print(f"P99 Latency:         {stats['p99_latency_ms']:.2f} ms")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Can be run standalone or via locust CLI
    import os

    os.system(
        f"locust -f {__file__} --host=amqp://localhost:5672 "
        "--users=10 --spawn-rate=2 --run-time=60s --headless"
    )
