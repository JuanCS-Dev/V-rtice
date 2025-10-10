"""Baseline performance test - multiple services"""
from locust import HttpUser, task, between
import random

class BaselineTest(HttpUser):
    """Test health endpoints across services"""
    wait_time = between(0.5, 1.5)
    
    @task
    def health_check(self):
        """Health check - works on most services"""
        self.client.get("/health", name="/health")
