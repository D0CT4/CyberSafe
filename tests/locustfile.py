from locust import HttpUser, task, between
import random

class AIBridgeUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Initialize user with API key"""
        self.api_key = "test_key"  # Replace with your test API key
    
    @task(3)
    def test_chat(self):
        """Simulate chat requests"""
        headers = {"X-API-Key": self.api_key}
        self.client.post("/chat", 
                        json={"prompt": "Test prompt"},
                        headers=headers)
    
    @task(2)
    def test_dashboard_data(self):
        """Simulate dashboard data requests"""
        headers = {"X-API-Key": self.api_key}
        self.client.get("/api/dashboard-data",
                       headers=headers)
    
    @task(1)
    def test_status(self):
        """Check system status"""
        headers = {"X-API-Key": self.api_key}
        self.client.get("/status",
                       headers=headers)
    
    @task(1)
    def test_provider_switch(self):
        """Test AI provider switching"""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        providers = ["gpt4all", "openai"]
        self.client.post("/switch-provider",
                        json={"mode": random.choice(providers)},
                        headers=headers)
