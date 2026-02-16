import asyncio
import aiohttp
import time
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

BASE_URL = "http://localhost:8000"

class LoadTestMetrics:
    def __init__(self):
        self.requests_count = 0
        self.errors_count = 0
        self.response_times: List[float] = []
        self.response_times_by_endpoint: Dict[str, List[float]] = defaultdict(list)
        self.start_time = None
        self.end_time = None
        self.error_details = defaultdict(int)

    def add_request(self, endpoint: str, response_time: float, status: int):
        self.requests_count += 1
        self.response_times.append(response_time)
        self.response_times_by_endpoint[endpoint].append(response_time)

        if status >= 400:
            self.errors_count += 1
            self.error_details[f"{endpoint} ({status})"] += 1

    def get_stats(self):
        if not self.response_times:
            return {}

        # Convert response times from seconds to microseconds
        sorted_times = sorted([t * 1_000_000 for t in self.response_times])
        duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        rps = self.requests_count / duration if duration > 0 else 0

        return {
            "total_requests": self.requests_count,
            "total_errors": self.errors_count,
            "error_rate": (self.errors_count / self.requests_count * 100) if self.requests_count > 0 else 0,
            "duration_seconds": round(duration, 2),
            "requests_per_second": round(rps, 2),
            "response_time_min": round(min(sorted_times), 3),
            "response_time_max": round(max(sorted_times), 3),
            "response_time_avg": round(sum(sorted_times) / len(sorted_times), 3),
            "response_time_p50": round(sorted_times[len(sorted_times) // 2], 3),
            "response_time_p95": round(sorted_times[int(len(sorted_times) * 0.95)], 3),
            "response_time_p99": round(sorted_times[int(len(sorted_times) * 0.99)], 3),
        }

metrics = LoadTestMetrics()

async def make_request(session: aiohttp.ClientSession, method: str, endpoint: str, data: dict = None):
    """Make an HTTP request and record metrics"""
    url = f"{BASE_URL}{endpoint}"
    try:
        start = time.time()
        async with session.request(method, url, json=data) as response:
            await response.json()
            response_time = time.time() - start
            metrics.add_request(endpoint, response_time, response.status)
            return response.status
    except Exception as e:
        response_time = time.time() - start
        metrics.add_request(endpoint, response_time, 500)
        print(f"❌ Error on {method} {endpoint}: {e}")
        return 500

async def scenario_create_todos(session: aiohttp.ClientSession, count: int):
    """Create multiple todos"""
    print(f"📝 Creating {count} todos...")
    tasks = []
    for i in range(count):
        data = {
            "title": f"Todo {i}",
            "description": f"Description for todo {i}"
        }
        tasks.append(make_request(session, "POST", "/todos", data))

    await asyncio.gather(*tasks)
    print(f"✅ Created {count} todos")

async def scenario_read_todos(session: aiohttp.ClientSession, count: int):
    """Read todos multiple times"""
    print(f"📖 Reading todos {count} times...")
    tasks = [make_request(session, "GET", "/todos") for _ in range(count)]
    await asyncio.gather(*tasks)
    print(f"✅ Read todos {count} times")

async def scenario_mixed_workload(session: aiohttp.ClientSession, iterations: int):
    """Mixed CRUD operations"""
    print(f"🔄 Running mixed workload ({iterations} iterations)...")

    for i in range(iterations):
        # Create
        create_task = make_request(session, "POST", "/todos", {"title": f"Mixed {i}"})
        todo_id = i % 10 + 1  # Use various IDs

        # Read
        read_task = make_request(session, "GET", f"/todos/{todo_id}")

        # Update
        update_task = make_request(session, "PUT", f"/todos/{todo_id}",
                                  {"title": f"Updated {i}", "completed": i % 2 == 0})

        # Delete occasionally
        delete_task = make_request(session, "DELETE", f"/todos/{todo_id}") if i % 5 == 0 else None

        tasks = [create_task, read_task, update_task]
        if delete_task:
            tasks.append(delete_task)

        await asyncio.gather(*tasks)

    print(f"✅ Completed {iterations} mixed iterations")

async def scenario_concurrent_spikes(session: aiohttp.ClientSession, spike_count: int, spikes: int):
    """Simulate traffic spikes"""
    print(f"⚡ Simulating {spikes} traffic spikes ({spike_count} requests each)...")

    for spike_num in range(spikes):
        tasks = []
        for i in range(spike_count):
            data = {"title": f"Spike {spike_num}-{i}"}
            tasks.append(make_request(session, "POST", "/todos", data))

        await asyncio.gather(*tasks)
        print(f"  Spike {spike_num + 1}/{spikes} completed")
        await asyncio.sleep(1)  # Cool down between spikes

    print(f"✅ All spikes completed")

async def scenario_sustained_load(session: aiohttp.ClientSession, duration_seconds: int, rps_target: int):
    """Sustained load test"""
    print(f"🔥 Running sustained load ({rps_target} RPS for {duration_seconds}s)...")

    request_interval = 1 / rps_target
    end_time = time.time() + duration_seconds
    request_count = 0

    while time.time() < end_time:
        start_loop = time.time()

        # Create mixed requests
        tasks = [
            make_request(session, "GET", "/todos"),
            make_request(session, "POST", "/todos", {"title": f"Load {request_count}"}),
        ]

        await asyncio.gather(*tasks)
        request_count += 2

        # Maintain target RPS
        elapsed = time.time() - start_loop
        sleep_time = max(0, request_interval - elapsed)
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

    print(f"✅ Sustained load completed ({request_count} requests)")

async def run_load_tests():
    """Run all load testing scenarios"""
    connector = aiohttp.TCPConnector(limit=500, limit_per_host=250)
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        metrics.start_time = time.time()

        # Run scenarios sequentially to see each one's impact
        try:
            # Scenario 1: Create many todos
            await scenario_create_todos(session, 500)
            await asyncio.sleep(1)

            # Scenario 2: Read todos multiple times
            await scenario_read_todos(session, 1000)
            await asyncio.sleep(1)

            # Scenario 3: Mixed workload
            await scenario_mixed_workload(session, 200)
            await asyncio.sleep(1)

            # Scenario 4: Concurrent spikes
            await scenario_concurrent_spikes(session, 500, 5)
            await asyncio.sleep(1)

            # Scenario 5: Sustained load (1000 RPS for 30 seconds)
            await scenario_sustained_load(session, 30, 1000)

        except Exception as e:
            print(f"❌ Test failed: {e}")

        metrics.end_time = time.time()

def print_results():
    """Print test results"""
    stats = metrics.get_stats()

    print("\n" + "=" * 70)
    print("📊 LOAD TEST RESULTS")
    print("=" * 70)
    print(f"Total Requests:        {stats['total_requests']}")
    print(f"Total Errors:          {stats['total_errors']} ({stats['error_rate']:.2f}%)")
    print(f"Duration:              {stats['duration_seconds']}s")
    print(f"Throughput:            {stats['requests_per_second']} req/s")
    print(f"\nResponse Times (microseconds):")
    print(f"  Min:                 {stats['response_time_min']}μs")
    print(f"  Max:                 {stats['response_time_max']}μs")
    print(f"  Avg:                 {stats['response_time_avg']}μs")
    print(f"  P50 (median):        {stats['response_time_p50']}μs")
    print(f"  P95:                 {stats['response_time_p95']}μs")
    print(f"  P99:                 {stats['response_time_p99']}μs")
    print("=" * 70)

    # Save results to JSON
    with open("load_test_results.json", "w") as f:
        stats["timestamp"] = datetime.now().isoformat()
        json.dump(stats, f, indent=2)

    print(f"\n✅ Results saved to load_test_results.json")

async def main():
    print("🚀 Starting Load Tests...")
    print(f"Target: {BASE_URL}")
    print()

    await run_load_tests()
    print_results()

if __name__ == "__main__":
    asyncio.run(main())
