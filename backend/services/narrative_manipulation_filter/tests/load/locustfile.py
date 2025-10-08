"""
Load Testing for Cognitive Defense System - Locust

Run with:
    locust -f locustfile.py --host=http://localhost:8013

For distributed testing:
    locust -f locustfile.py --host=http://api.cognitive-defense.vertice.dev --users 1000 --spawn-rate 50

"""

import random

from locust import between, events, task
from locust.contrib.fasthttp import FastHttpUser

# ============================================================================
# TEST DATA - Realistic content samples
# ============================================================================

FAKE_NEWS_SAMPLES = [
    "Governo anuncia que vai distribuir R$ 10.000 para todos os brasileiros na próxima semana!",
    "Cientistas descobrem que vacinas causam autismo, estudo comprova teoria!",
    "Político corrupto confessa desvio de bilhões em vídeo vazado!",
    "Novo tratamento milagroso cura câncer em 24 horas, médicos confirmam!",
    "País vai adotar moeda digital e acabar com o Real a partir de amanhã!",
]

REAL_NEWS_SAMPLES = [
    "Ministério da Saúde divulga novo boletim epidemiológico com dados atualizados.",
    "Congresso aprova projeto de lei após amplo debate parlamentar.",
    "Pesquisa do IBGE mostra crescimento da economia no último trimestre.",
    "Universidade publica estudo sobre mudanças climáticas no Brasil.",
    "Banco Central mantém taxa de juros em 10,5% ao ano.",
]

PROPAGANDA_SAMPLES = [
    "Vote no candidato X! Ele é o ÚNICO que pode salvar o Brasil da destruição total!",
    "Nossos adversários querem destruir tudo que é sagrado! Não deixe isso acontecer!",
    "A oposição é composta INTEIRAMENTE por comunistas e criminosos!",
    "Se você não votar em mim, o país vai virar uma Venezuela! É agora ou nunca!",
]

SOURCE_DOMAINS = [
    "nytimes.com",
    "bbc.com",
    "folha.uol.com.br",
    "estadao.com.br",
    "g1.globo.com",
    "unknown-blog.com",
    "fake-news-site.net",
    "suspicious-news.org",
]


def get_random_content() -> str:
    """Get random test content."""
    all_samples = FAKE_NEWS_SAMPLES + REAL_NEWS_SAMPLES + PROPAGANDA_SAMPLES
    return random.choice(all_samples)


def get_random_source() -> str:
    """Get random source domain."""
    return random.choice(SOURCE_DOMAINS)


# ============================================================================
# LOCUST USER CLASS
# ============================================================================


class CognitiveDefenseUser(FastHttpUser):
    """
    Simulates user behavior for the Cognitive Defense System.

    Uses FastHttpUser for better performance (gevent + httpx).
    """

    # Wait time between tasks (simulates think time)
    wait_time = between(1, 3)  # 1-3 seconds between requests

    # Connection pool settings
    connection_timeout = 10.0
    network_timeout = 30.0

    def on_start(self):
        """Called when a user starts. Setup auth, cache, etc."""
        # Health check first
        self.client.get("/health", name="[Setup] Health Check")

        # Optional: Authenticate if needed
        # self.client.post("/auth/login", json={"username": "test", "password": "test"})

    @task(10)  # Weight: 10 (most common operation)
    def analyze_content_fast(self):
        """Tier 1 analysis - fast track."""
        payload = {
            "content": get_random_content(),
            "source_info": {
                "domain": get_random_source(),
                "url": f"https://{get_random_source()}/article/123",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            "mode": "FAST_TRACK",
        }

        with self.client.post(
            "/api/v2/analyze",
            json=payload,
            catch_response=True,
            name="Analyze Content (Fast)",
        ) as response:
            if response.status_code == 200:
                result = response.json()

                # Validate response
                if "manipulation_score" in result and "threat_level" in result:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            else:
                response.failure(f"Got status {response.status_code}")

    @task(5)  # Weight: 5
    def analyze_content_standard(self):
        """Tier 1 + Tier 2 analysis - standard mode."""
        payload = {
            "content": get_random_content(),
            "source_info": {
                "domain": get_random_source(),
                "url": f"https://{get_random_source()}/article/456",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            "mode": "STANDARD",
        }

        with self.client.post(
            "/api/v2/analyze",
            json=payload,
            catch_response=True,
            name="Analyze Content (Standard)",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)  # Weight: 2
    def analyze_content_deep(self):
        """Full deep analysis with KG verification."""
        payload = {
            "content": FAKE_NEWS_SAMPLES[0],  # Use specific claim for KG
            "source_info": {
                "domain": "unknown-blog.com",
                "url": "https://unknown-blog.com/fake-article/789",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            "mode": "DEEP_ANALYSIS",
        }

        with self.client.post(
            "/api/v2/analyze",
            json=payload,
            catch_response=True,
            name="Analyze Content (Deep)",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)  # Weight: 3
    def get_analysis_history(self):
        """Retrieve historical analysis results."""
        params = {"limit": 10, "offset": 0}

        with self.client.get(
            "/api/v2/history",
            params=params,
            catch_response=True,
            name="Get Analysis History",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)  # Weight: 2
    def verify_specific_claim(self):
        """Verify a specific claim against fact-checkers."""
        payload = {"claim": random.choice(FAKE_NEWS_SAMPLES)}

        with self.client.post(
            "/api/v2/verify-claim",
            json=payload,
            catch_response=True,
            name="Verify Claim",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)  # Weight: 1 (metrics endpoint)
    def get_metrics(self):
        """Fetch Prometheus metrics."""
        with self.client.get("/metrics", catch_response=True, name="Get Metrics") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)  # Weight: 1
    def health_check(self):
        """Health check endpoint."""
        with self.client.get("/health", catch_response=True, name="Health Check") as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("Service not healthy")
            else:
                response.failure(f"Got status {response.status_code}")


# ============================================================================
# EVENT HANDLERS - Custom metrics and reporting
# ============================================================================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("\n" + "=" * 80)
    print("COGNITIVE DEFENSE SYSTEM - LOAD TEST STARTING")
    print("=" * 80)
    print(f"Host: {environment.host}")
    print(f"Users: {environment.runner.user_count if environment.runner else 'N/A'}")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("\n" + "=" * 80)
    print("LOAD TEST COMPLETED")
    print("=" * 80)

    if environment.stats:
        print(f"\nTotal Requests: {environment.stats.total.num_requests}")
        print(f"Total Failures: {environment.stats.total.num_failures}")
        print(f"Median Response Time: {environment.stats.total.median_response_time}ms")
        print(f"95th Percentile: {environment.stats.total.get_response_time_percentile(0.95)}ms")
        print(f"Requests/sec: {environment.stats.total.total_rps:.2f}")

        if environment.stats.total.num_requests > 0:
            failure_rate = (environment.stats.total.num_failures / environment.stats.total.num_requests) * 100
            print(f"Failure Rate: {failure_rate:.2f}%")

    print("=" * 80 + "\n")


# ============================================================================
# CUSTOM LOAD SHAPES (optional)
# ============================================================================

from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern - gradually increase load.

    Step 1: 10 users for 2 minutes
    Step 2: 50 users for 2 minutes
    Step 3: 100 users for 2 minutes
    Step 4: 200 users for 2 minutes
    Step 5: 500 users for 2 minutes
    """

    step_time = 120  # 2 minutes per step
    step_load = [10, 50, 100, 200, 500]
    spawn_rate = 10
    time_limit = 600  # 10 minutes total

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = int(run_time // self.step_time)

        if current_step >= len(self.step_load):
            return None

        return (self.step_load[current_step], self.spawn_rate)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
"""
# Basic test (10 users, 1/sec spawn rate)
locust -f locustfile.py --host=http://localhost:8013 --users 10 --spawn-rate 1

# Stress test (1000 users, 50/sec spawn rate, 10 minutes)
locust -f locustfile.py --host=http://api.vertice.dev --users 1000 --spawn-rate 50 --run-time 10m

# Distributed test (master + workers)
# Master:
locust -f locustfile.py --host=http://api.vertice.dev --master

# Worker (run on multiple machines):
locust -f locustfile.py --worker --master-host=<master-ip>

# With custom load shape:
locust -f locustfile.py --host=http://api.vertice.dev --headless -u 500 -r 10 --run-time 10m

# Headless mode with CSV output:
locust -f locustfile.py --host=http://api.vertice.dev --headless --users 100 --spawn-rate 10 \
       --run-time 5m --csv=results --html=report.html
"""
