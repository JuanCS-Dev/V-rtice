"""Simple and effective load test for MAXIMUS services"""
from locust import HttpUser, task, between

class QuickTest(HttpUser):
    """Quick load test - boring but necessary"""
    wait_time = between(0.5, 2)
    
    @task(5)
    def health_check(self):
        """Most common endpoint"""
        self.client.get("/health", name="health_check")
    
    @task(2)
    def api_health(self):
        """API health endpoint"""
        self.client.get("/api/v1/health", name="api_health")
    
    @task(1)
    def root(self):
        """Root endpoint"""
        self.client.get("/", name="root")
