"""
Load testing para backend services do MAXIMUS AI 3.0
Execute: locust -f locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between
import random
import json

class MaximusUser(HttpUser):
    """Simula usuário interagindo com MAXIMUS services"""
    wait_time = between(1, 3)  # Espera entre 1-3 segundos entre requests
    
    def on_start(self):
        """Executado uma vez quando usuário inicia"""
        self.client.verify = False  # Para ambientes de teste
        
    @task(3)
    def health_check(self):
        """Task mais comum - health checks"""
        services = [
            "/health",
            "/api/v1/health",
            "/status"
        ]
        endpoint = random.choice(services)
        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def consciousness_query(self):
        """Consulta ao sistema de consciência"""
        payload = {
            "query": "What is your current state?",
            "context": {"user_id": "test_user"}
        }
        with self.client.post(
            "/api/v1/consciousness/query",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Consciousness query failed: {response.status_code}")
    
    @task(2)
    def episodic_memory_store(self):
        """Armazenar evento na memória episódica"""
        event = {
            "timestamp": "2025-01-10T10:00:00Z",
            "event_type": "user_interaction",
            "data": {"action": "test_action"},
            "importance": random.uniform(0.5, 1.0)
        }
        with self.client.post(
            "/api/v1/memory/episodic",
            json=event,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Memory store failed: {response.status_code}")
    
    @task(1)
    def episodic_memory_retrieve(self):
        """Recuperar memórias episódicas"""
        params = {
            "start_time": "2025-01-10T00:00:00Z",
            "end_time": "2025-01-10T23:59:59Z",
            "limit": 10
        }
        with self.client.get(
            "/api/v1/memory/episodic",
            params=params,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Memory retrieve failed: {response.status_code}")
    
    @task(1)
    def sandbox_execute(self):
        """Executar código no sandbox"""
        code_payload = {
            "code": "print('Hello from sandbox')",
            "timeout": 5,
            "resource_limits": {
                "cpu_percent": 50,
                "memory_mb": 256
            }
        }
        with self.client.post(
            "/api/v1/sandbox/execute",
            json=code_payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Sandbox execution failed: {response.status_code}")
    
    @task(1)
    def offensive_recon(self):
        """Executar reconhecimento de rede"""
        recon_payload = {
            "target": "192.168.1.0/24",
            "scan_type": "quick",
            "ports": "80,443,22"
        }
        with self.client.post(
            "/api/v1/recon/scan",
            json=recon_payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:  # 202 = Accepted for processing
                response.success()
            else:
                response.failure(f"Recon scan failed: {response.status_code}")

class StressTestUser(HttpUser):
    """Usuário para stress testing - requisições mais pesadas"""
    wait_time = between(0.5, 1)  # Mais agressivo
    
    @task
    def heavy_computation(self):
        """Tarefa computacionalmente intensiva"""
        payload = {
            "task": "llm_inference",
            "prompt": "Explain quantum computing in detail",
            "max_tokens": 1000
        }
        with self.client.post(
            "/api/v1/inference/generate",
            json=payload,
            timeout=30,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                response.failure("Service overloaded")
            else:
                response.failure(f"Failed: {response.status_code}")