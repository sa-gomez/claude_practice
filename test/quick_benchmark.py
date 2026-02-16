import asyncio
import aiohttp
import time
import subprocess
import signal
import os
from typing import List

BASE_URL = "http://localhost:8000"
TEST_DURATION = 5  # Quick 5-second tests

class QuickMetrics:
    def __init__(self):
        self.requests_count = 0
        self.errors_count = 0
        self.response_times: List[float] = []

    def add_request(self, response_time: float, status: int):
        self.requests_count += 1
        self.response_times.append(response_time)
        if status >= 400:
            self.errors_count += 1

    def get_rps(self):
        return self.requests_count / TEST_DURATION if self.requests_count > 0 else 0

    def get_avg_response_time_ms(self):
        if not self.response_times:
            return 0
        return (sum(self.response_times) / len(self.response_times)) * 1000

    def get_p95_response_time_ms(self):
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx] * 1000

metrics = QuickMetrics()

async def make_request(session: aiohttp.ClientSession):
    """Make a simple GET request"""
    try:
        start = time.time()
        async with session.get(f"{BASE_URL}/todos") as response:
            await response.json()
            response_time = time.time() - start
            metrics.add_request(response_time, response.status)
    except Exception as e:
        metrics.errors_count += 1

async def run_benchmark(concurrent_requests: int, duration: int):
    """Run quick benchmark"""
    connector = aiohttp.TCPConnector(limit=2000, limit_per_host=1000)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        end_time = time.time() + duration
        tasks = []

        while time.time() < end_time:
            # Maintain concurrent requests
            while len(tasks) < concurrent_requests and time.time() < end_time:
                tasks.append(asyncio.create_task(make_request(session)))

            # Process completed tasks
            if tasks:
                done, pending = await asyncio.wait(
                    tasks,
                    timeout=0.001,
                    return_when=asyncio.FIRST_COMPLETED
                )
                tasks = list(pending)

        # Wait for remaining tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

def start_server(workers: int) -> int:
    """Start Uvicorn server with given worker count"""
    print(f"  Starting server with {workers} workers...", end="", flush=True)

    # Kill any existing uvicorn process
    os.system("pkill -9 uvicorn 2>/dev/null")
    time.sleep(1)

    # Start new server
    process = subprocess.Popen(
        f"cd /home/sagomez/claude_practice && source claude_practice_venv/bin/activate && uvicorn main:app --workers {workers}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

    # Wait for server to start
    time.sleep(2)

    print(" ✓")
    return process.pid

def stop_server():
    """Stop Uvicorn server"""
    os.system("pkill -9 uvicorn 2>/dev/null")
    time.sleep(0.5)

def print_header():
    print("\n" + "="*80)
    print("⚡ QUICK WORKER OPTIMIZATION BENCHMARK (5 seconds per test)")
    print("="*80)
    print(f"Concurrency: 200 concurrent connections")
    print(f"Test Duration: {TEST_DURATION} seconds per configuration")
    print(f"Target: {BASE_URL}\n")

def print_results(workers: int, duration_taken: float):
    """Print test results"""
    rps = metrics.get_rps()
    avg_response = metrics.get_avg_response_time_ms()
    p95_response = metrics.get_p95_response_time_ms()

    print(f"Workers: {workers:2d} | RPS: {rps:7.0f} | Avg: {avg_response:6.2f}ms | P95: {p95_response:6.2f}ms | Requests: {metrics.requests_count}")

    return {
        "workers": workers,
        "rps": rps,
        "avg_response_ms": avg_response,
        "p95_response_ms": p95_response,
        "total_requests": metrics.requests_count,
        "errors": metrics.errors_count
    }

async def run_benchmark_test(workers: int):
    """Run a single benchmark test"""
    metrics.requests_count = 0
    metrics.errors_count = 0
    metrics.response_times = []

    await run_benchmark(concurrent_requests=200, duration=TEST_DURATION)

async def main():
    print_header()

    results = []

    # Test worker counts: 1, 8, 32
    worker_counts = [1, 8, 32]

    print("Workers | RPS      | Avg (ms) | P95 (ms) | Total Requests")
    print("-" * 80)

    for workers in worker_counts:
        start_server(workers)

        try:
            await run_benchmark_test(workers)
            result = print_results(workers, TEST_DURATION)
            results.append(result)
        except Exception as e:
            print(f"Workers: {workers:2d} | ❌ Error: {e}")

        time.sleep(0.5)

    stop_server()

    # Analysis
    print("\n" + "="*80)
    print("📊 ANALYSIS")
    print("="*80)

    if results:
        best_rps = max(results, key=lambda x: x["rps"])
        best_response = min(results, key=lambda x: x["avg_response_ms"])

        print(f"\n🏆 Best Throughput:")
        print(f"   {best_rps['workers']} workers = {best_rps['rps']:.0f} req/s")

        print(f"\n⚡ Best Response Time:")
        print(f"   {best_response['workers']} workers = {best_response['avg_response_ms']:.2f}ms average")

        # Find sweet spot (best balance)
        print(f"\n🎯 Sweet Spot Analysis:")

        # Sweet spot is where RPS is high but response time is still good
        max_rps = max(r["rps"] for r in results)
        min_rps = min(r["rps"] for r in results)
        max_response = max(r["avg_response_ms"] for r in results)
        min_response = min(r["avg_response_ms"] for r in results)

        # Normalize scores (0-100)
        scores = []
        for r in results:
            rps_score = ((r["rps"] - min_rps) / (max_rps - min_rps)) * 50  # 50% weight
            response_score = ((max_response - r["avg_response_ms"]) / (max_response - min_response)) * 50  # 50% weight
            total_score = rps_score + response_score
            scores.append({"workers": r["workers"], "score": total_score})

        best_sweet_spot = max(scores, key=lambda x: x["score"])

        print(f"\n   {best_sweet_spot['workers']} workers = Best balance of throughput & latency")

        # Recommendations
        print(f"\n💡 Recommendations:")
        print(f"   • Development:  uvicorn main:app --reload")
        print(f"   • Production:   uvicorn main:app --workers {best_sweet_spot['workers']}")
        print(f"   • Max load:     uvicorn main:app --workers {best_rps['workers']}")

        print(f"\n   Throughput improvement: {best_rps['rps'] / results[0]['rps']:.1f}x (vs 4 workers)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted")
        stop_server()
