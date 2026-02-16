import asyncio
import aiohttp
import time
import psutil
import sys
from typing import List

BASE_URL = "http://localhost:8000"

class DebugMetrics:
    def __init__(self):
        self.requests_count = 0
        self.errors_count = 0
        self.response_times: List[float] = []
        self.start_time = None
        self.end_time = None

    def add_request(self, response_time: float, status: int):
        self.requests_count += 1
        self.response_times.append(response_time)
        if status >= 400:
            self.errors_count += 1

    def get_rps(self):
        if not self.start_time or not self.end_time:
            return 0
        duration = self.end_time - self.start_time
        return self.requests_count / duration if duration > 0 else 0

    def get_avg_response_time_ms(self):
        if not self.response_times:
            return 0
        return (sum(self.response_times) / len(self.response_times)) * 1000

metrics = DebugMetrics()

async def make_request(session: aiohttp.ClientSession):
    """Make a simple GET request and record time"""
    try:
        start = time.time()
        async with session.get(f"{BASE_URL}/todos") as response:
            await response.json()
            response_time = time.time() - start
            metrics.add_request(response_time, response.status)
    except Exception as e:
        metrics.errors_count += 1

async def aggressive_throughput_test(duration_seconds: int, concurrent_requests: int):
    """Aggressively blast the server to find max throughput"""
    connector = aiohttp.TCPConnector(
        limit=2000,  # Much higher limit
        limit_per_host=1000,
        ttl_dns_cache=300
    )
    timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        metrics.start_time = time.time()
        end_time = metrics.start_time + duration_seconds

        request_count = 0
        tasks = []

        print(f"🚀 Blasting server with {concurrent_requests} concurrent requests...")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Target: {BASE_URL}\n")

        while time.time() < end_time:
            # Create concurrent tasks without waiting
            while len(tasks) < concurrent_requests and time.time() < end_time:
                tasks.append(make_request(session))
                request_count += 1

            # Gather and remove completed tasks
            if tasks:
                done, pending = await asyncio.wait(
                    tasks,
                    timeout=0.01,  # Don't wait long
                    return_when=asyncio.FIRST_COMPLETED
                )
                tasks = list(pending)

            # Print progress every second
            elapsed = time.time() - metrics.start_time
            if elapsed > 0 and int(elapsed) % 1 == 0 and request_count % 100 == 0:
                current_rps = request_count / elapsed
                print(f"Progress: {int(elapsed)}s | Requests sent: {request_count} | Current RPS: {current_rps:.0f}")

        # Wait for all remaining tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        metrics.end_time = time.time()

def print_results():
    """Print detailed results"""
    print("\n" + "=" * 70)
    print("📊 THROUGHPUT DEBUG RESULTS")
    print("=" * 70)
    print(f"Total Requests Sent:   {metrics.requests_count}")
    print(f"Successful Responses:  {metrics.requests_count - metrics.errors_count}")
    print(f"Errors:                {metrics.errors_count}")
    print(f"Error Rate:            {metrics.errors_count/metrics.requests_count*100:.2f}%" if metrics.requests_count > 0 else "N/A")
    print(f"Duration:              {metrics.end_time - metrics.start_time:.2f}s")
    print(f"Throughput (RPS):      {metrics.get_rps():.2f} req/s")
    print(f"Avg Response Time:     {metrics.get_avg_response_time_ms():.3f}ms")

    if metrics.response_times:
        sorted_times = sorted([t * 1_000_000 for t in metrics.response_times])
        print(f"\nResponse Times (microseconds):")
        print(f"  Min:                 {sorted_times[0]:.0f}μs")
        print(f"  P50 (median):        {sorted_times[len(sorted_times)//2]:.0f}μs")
        print(f"  P99:                 {sorted_times[int(len(sorted_times)*0.99)]:.0f}μs")
        print(f"  Max:                 {sorted_times[-1]:.0f}μs")

    print("=" * 70)

async def test_suite():
    """Run tests with increasing concurrency"""
    print("=" * 70)
    print("🔬 PERFORMANCE DEBUG SUITE")
    print("=" * 70)
    print(f"Target: {BASE_URL}")
    print(f"Storage: In-memory")
    print(f"Test: Pure throughput (no interval throttling)\n")

    # Get system info
    cpu_count = psutil.cpu_count()
    print(f"System Info:")
    print(f"  CPU Cores: {cpu_count}")
    print(f"  CPU Usage (before test): {psutil.cpu_percent(interval=0.1)}%")
    print(f"  Memory Available: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f}GB\n")

    # Test with different concurrency levels
    concurrency_levels = [10, 50, 100, 200, 500, 1000]

    for concurrency in concurrency_levels:
        print(f"\n{'='*70}")
        print(f"Test with {concurrency} concurrent connections (10 seconds)")
        print(f"{'='*70}")

        # Reset metrics
        metrics.requests_count = 0
        metrics.errors_count = 0
        metrics.response_times = []

        await aggressive_throughput_test(duration_seconds=10, concurrent_requests=concurrency)
        print_results()

        # System stats after test
        print(f"CPU Usage (after test): {psutil.cpu_percent(interval=0.1)}%")
        print(f"Memory Used: {psutil.virtual_memory().percent}%")

        await asyncio.sleep(1)  # Cool down between tests

async def main():
    try:
        await test_suite()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔍 FastAPI Performance Debug Tool\n")
    asyncio.run(main())
