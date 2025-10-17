"""Locust Load Testing - Cockpit Soberano E2E Performance.

Simulates 100 concurrent users (agents + operators) interacting with Cockpit system.

Usage:
    locust -f tests/e2e/locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10

Metrics:
    - Throughput: > 100 req/s
    - Latency P95: < 1000ms
    - Error rate: < 1%

Author: IA Dev Sênior sob Constituição Vértice v2.7
"""

from locust import HttpUser, between, task
from uuid import uuid4


class AgentSimulator(HttpUser):
    """Simulates malicious/benign agents sending telemetry."""

    wait_time = between(0.5, 2)
    weight = 3  # 3x more agents than operators

    @task(5)
    def send_benign_telemetry(self):
        """Send benign telemetry (most common)."""
        telemetry = {
            "agent_id": str(uuid4()),
            "message": "System operational. Memory at 60%, CPU at 40%.",
            "metadata": {
                "ip": f"10.0.{self._random_byte()}.{self._random_byte()}",
                "user_agent": "monitoring-bot/1.0",
            },
        }
        with self.client.post(
            "/narrative-filter/analyze",
            json=telemetry,
            catch_response=True,
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def send_suspicious_telemetry(self):
        """Send suspicious telemetry."""
        telemetry = {
            "agent_id": str(uuid4()),
            "message": "Attempting to access restricted resources... just kidding!",
            "metadata": {
                "ip": f"192.168.{self._random_byte()}.{self._random_byte()}",
                "user_agent": "suspicious-client/0.1",
            },
        }
        self.client.post("/narrative-filter/analyze", json=telemetry)

    @task(1)
    def send_malicious_telemetry(self):
        """Send clearly malicious telemetry."""
        telemetry = {
            "agent_id": str(uuid4()),
            "message": "Exfiltrating data to external server. Command and control established.",
            "metadata": {
                "ip": f"203.0.113.{self._random_byte()}",
                "user_agent": "malware-agent/666",
            },
        }
        self.client.post("/narrative-filter/analyze", json=telemetry)

    def _random_byte(self):
        """Generate random byte for IP addresses."""
        import random

        return random.randint(1, 254)


class OperatorSimulator(HttpUser):
    """Simulates human operators monitoring cockpit and issuing commands."""

    wait_time = between(2, 5)
    weight = 1  # 1x operators

    @task(5)
    def fetch_verdicts(self):
        """Fetch recent verdicts (most common operator action)."""
        with self.client.get(
            "/verdicts?limit=20&order=desc",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to fetch verdicts: {response.status_code}")

    @task(3)
    def fetch_specific_agent(self):
        """Fetch verdicts for specific agent."""
        agent_id = str(uuid4())  # In real scenario, would be from UI selection
        self.client.get(f"/verdicts?agent_id={agent_id}")

    @task(2)
    def fetch_metrics(self):
        """Fetch cockpit metrics (dashboard KPIs)."""
        self.client.get("/metrics/summary")

    @task(1)
    def send_mute_command(self):
        """Issue MUTE command (least common, high impact)."""
        command = {
            "command_id": str(uuid4()),
            "command_type": "MUTE",
            "target_agent_id": str(uuid4()),
            "issuer": "operator-load-test",
        }
        with self.client.post(
            "/commands",
            json=command,
            catch_response=True,
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Command failed: {response.status_code}")

    @task(1)
    def check_audit_logs(self):
        """Check audit logs for recent commands."""
        self.client.get("/audits?limit=10")


class StressTestUser(HttpUser):
    """Stress test user - sends requests at maximum rate."""

    wait_time = between(0.1, 0.3)
    weight = 0  # Disabled by default, enable with --user-class

    @task
    def rapid_fire_telemetry(self):
        """Send telemetry as fast as possible."""
        telemetry = {
            "agent_id": str(uuid4()),
            "message": "Stress test payload",
            "metadata": {"ip": "127.0.0.1"},
        }
        self.client.post("/narrative-filter/analyze", json=telemetry)


# Performance thresholds for CI/CD validation
PERFORMANCE_THRESHOLDS = {
    "max_response_time_ms": 1000,  # P95 should be < 1s
    "max_error_rate": 0.01,  # < 1%
    "min_throughput_rps": 100,  # > 100 req/s
}
