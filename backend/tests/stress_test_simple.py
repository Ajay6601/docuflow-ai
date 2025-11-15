"""
Simple multi-threaded stress test without Locust
"""

import requests
import threading
import time
from datetime import datetime
from collections import defaultdict
import statistics


class StressTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = defaultdict(list)
        self.errors = []
        self.lock = threading.Lock()
    
    def login(self):
        """Login and get token."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    def test_endpoint(self, endpoint, method="GET", headers=None, data=None):
        """Test a single endpoint."""
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", headers=headers, json=data)
            
            duration = (time.time() - start_time) * 1000  # ms
            
            with self.lock:
                self.results[endpoint].append({
                    'status': response.status_code,
                    'duration': duration,
                    'success': response.status_code < 400
                })
        
        except Exception as e:
            with self.lock:
                self.errors.append({
                    'endpoint': endpoint,
                    'error': str(e),
                    'time': datetime.now()
                })
    
    def worker(self, thread_id, num_requests):
        """Worker thread that makes multiple requests."""
        # Login
        token = self.login()
        if not token:
            print(f"Thread {thread_id}: Login failed")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test different endpoints
        endpoints = [
            ("/api/v1/documents/", "GET"),
            ("/api/v1/analytics/overview", "GET"),
            ("/api/v1/audit/", "GET"),
        ]
        
        for i in range(num_requests):
            endpoint, method = endpoints[i % len(endpoints)]
            self.test_endpoint(endpoint, method, headers)
            
            # Small delay to simulate real user behavior
            time.sleep(0.1)
        
        print(f"Thread {thread_id}: Completed {num_requests} requests")
    
    def run(self, num_threads=100, requests_per_thread=10):
        """Run the stress test."""
        print("=" * 80)
        print(f"🚀 STARTING STRESS TEST")
        print(f"   Threads: {num_threads}")
        print(f"   Requests per thread: {requests_per_thread}")
        print(f"   Total requests: {num_threads * requests_per_thread}")
        print("=" * 80)
        
        threads = []
        start_time = time.time()
        
        # Create and start threads
        for i in range(num_threads):
            thread = threading.Thread(target=self.worker, args=(i, requests_per_thread))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Print results
        self.print_results(total_time)
    
    def print_results(self, total_time):
        """Print test results."""
        print("\n" + "=" * 80)
        print("📊 STRESS TEST RESULTS")
        print("=" * 80)
        
        total_requests = sum(len(results) for results in self.results.values())
        total_errors = len(self.errors)
        
        print(f"\n⏱️  EXECUTION TIME: {total_time:.2f}s")
        print(f"📈 TOTAL REQUESTS: {total_requests}")
        print(f"❌ TOTAL ERRORS: {total_errors}")
        print(f"✅ SUCCESS RATE: {((total_requests - total_errors) / total_requests * 100):.2f}%")
        print(f"🔥 THROUGHPUT: {total_requests / total_time:.2f} req/sec")
        
        print("\n📊 BY ENDPOINT:")
        for endpoint, results in self.results.items():
            if not results:
                continue
            
            durations = [r['duration'] for r in results]
            successes = sum(1 for r in results if r['success'])
            
            print(f"\n   {endpoint}")
            print(f"      Requests: {len(results)}")
            print(f"      Success: {successes}/{len(results)} ({successes/len(results)*100:.1f}%)")
            print(f"      Avg Time: {statistics.mean(durations):.2f}ms")
            print(f"      Min Time: {min(durations):.2f}ms")
            print(f"      Max Time: {max(durations):.2f}ms")
            if len(durations) > 1:
                print(f"      Std Dev: {statistics.stdev(durations):.2f}ms")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"   {error['endpoint']}: {error['error']}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more errors")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    test = StressTest()
    
    # Test scenarios:
    
    # Light load
    # test.run(num_threads=10, requests_per_thread=10)
    
    # Medium load
    # test.run(num_threads=50, requests_per_thread=20)
    
    # Heavy load
    test.run(num_threads=100, requests_per_thread=10)
    
    # Extreme load (be careful!)
    # test.run(num_threads=500, requests_per_thread=10)