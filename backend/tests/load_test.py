"""
DocuFlow AI - Load Testing Script
Simulates realistic user behavior with multiple concurrent users
"""

from locust import HttpUser, task, between, events
from locust.env import Environment
from faker import Faker
import random
import time
import json
from io import BytesIO

fake = Faker()


class DocuFlowUser(HttpUser):
    """Simulates a realistic user using DocuFlow AI."""
    
    # Wait time between tasks (simulates user "think time")
    wait_time = between(1, 5)  # 1-5 seconds between actions
    
    def on_start(self):
        """Called when a user starts - performs login."""
        self.token = None
        self.user_id = None
        self.uploaded_documents = []
        
        # Register or login
        if random.random() > 0.8:  # 20% register, 80% login
            self.register_user()
        else:
            self.login_existing_user()
    
    def register_user(self):
        """Register a new user."""
        username = fake.user_name() + str(random.randint(1000, 9999))
        email = fake.email()
        password = "TestPassword123!"
        
        response = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": fake.name()
        }, name="Register User")
        
        if response.status_code == 201:
            # Auto-login after registration
            self.login(username, password)
    
    def login_existing_user(self):
        """Login with existing test user."""
        # Use admin credentials for testing
        self.login("admin", "admin123")
    
    def login(self, username: str, password: str):
        """Perform login."""
        data = {
            "username": username,
            "password": password
        }
        
        response = self.client.post(
            "/api/v1/auth/login",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            name="Login"
        )
        
        if response.status_code == 200:
            result = response.json()
            self.token = result.get("access_token")
            
            # Get user info
            self.get_current_user()
    
    def get_current_user(self):
        """Get current user information."""
        if not self.token:
            return
        
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.token}"},
            name="Get Current User"
        )
        
        if response.status_code == 200:
            self.user_id = response.json().get("id")
    
    @task(10)  # Weight: 10 - Most common action
    def list_documents(self):
        """List user's documents."""
        if not self.token:
            return
        
        page = random.randint(1, 3)
        with self.client.get(
            f"/api/v1/documents/?page={page}&page_size=10",
            headers={"Authorization": f"Bearer {self.token}"},
            name="List Documents",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected, not a failure
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
            
    
    @task(5)  # Weight: 5
    def upload_document(self):
        """Upload a test document."""
        if not self.token:
            return
        
        # Create fake PDF content
        content = f"Test Document {fake.text()}\n" * 100
        file_data = content.encode('utf-8')
        
        files = {
            'file': ('test_document.pdf', BytesIO(file_data), 'application/pdf')
        }
        data = {
            'process_async': 'true'
        }
        
        response = self.client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {self.token}"},
            name="Upload Document",
            catch_response=True
        )
        
        if response.status_code == 201:
            doc = response.json()
            self.uploaded_documents.append(doc['id'])
            response.success()
        elif response.status_code == 429:
            # Rate limited - expected behavior
            response.success()  # Don't count as failure
        else:
            response.failure(f"Upload failed: {response.status_code}")
    
    @task(3)  # Weight: 3
    def view_document(self):
        """View a specific document."""
        if not self.token or not self.uploaded_documents:
            return
        
        doc_id = random.choice(self.uploaded_documents)
        self.client.get(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            name="View Document"
        )
    
    @task(2)  # Weight: 2
    def search_documents(self):
        """Search documents."""
        if not self.token:
            return
        
        queries = ["invoice", "contract", "report", "document", "test"]
        query = random.choice(queries)
        search_type = random.choice(["full-text", "semantic", "hybrid"])
        
        self.client.get(
            f"/api/v1/search/{search_type}?q={query}",
            headers={"Authorization": f"Bearer {self.token}"},
            name=f"Search ({search_type})"
        )
    
    @task(2)  # Weight: 2
    def view_analytics(self):
        """View analytics dashboard."""
        if not self.token:
            return
        
        endpoints = [
            "/api/v1/analytics/overview",
            "/api/v1/analytics/document-types",
            "/api/v1/analytics/upload-timeline?days=7"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(
            endpoint,
            headers={"Authorization": f"Bearer {self.token}"},
            name="View Analytics"
        )
    
    @task(1)  # Weight: 1
    def download_document(self):
        """Download a document."""
        if not self.token or not self.uploaded_documents:
            return
        
        doc_id = random.choice(self.uploaded_documents)
        self.client.get(
            f"/api/v1/documents/{doc_id}/download",
            headers={"Authorization": f"Bearer {self.token}"},
            name="Download Document"
        )
    
    @task(1)  # Weight: 1
    def view_audit_logs(self):
        """View audit logs."""
        if not self.token:
            return
        
        self.client.get(
            "/api/v1/audit/?page=1&page_size=20",
            headers={"Authorization": f"Bearer {self.token}"},
            name="View Audit Logs"
        )


# Event listeners for statistics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 80)
    print("🚀 DOCUFLOW AI - LOAD TEST STARTING")
    print("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - print summary."""
    print("\n" + "=" * 80)
    print("📊 LOAD TEST SUMMARY")
    print("=" * 80)
    
    stats = environment.stats
    
    print(f"\n📈 REQUESTS:")
    print(f"   Total: {stats.total.num_requests}")
    print(f"   Failures: {stats.total.num_failures}")
    print(f"   Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    
    print(f"\n⚡ RESPONSE TIMES:")
    print(f"   Median: {stats.total.median_response_time}ms")
    print(f"   Average: {stats.total.avg_response_time:.2f}ms")
    print(f"   95th Percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    print(f"   99th Percentile: {stats.total.get_response_time_percentile(0.99)}ms")
    print(f"   Max: {stats.total.max_response_time}ms")
    
    print(f"\n🔥 THROUGHPUT:")
    print(f"   Requests/sec: {stats.total.total_rps:.2f}")
    print(f"   Failures/sec: {stats.total.fail_ratio * stats.total.total_rps:.2f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Can be run directly for quick testing
    import os
    os.system("locust -f tests/load_test.py --host=http://localhost:8000")