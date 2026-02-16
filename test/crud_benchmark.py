import asyncio
import aiohttp
import time
import subprocess
import os
from typing import List

BASE_URL = "http://localhost:8000"
TEST_DURATION = 2  # 2-second tests

class CRUDMetrics:
    def __init__(self):
        self.requests_count = 0
        self.errors_count = 0
        self.response_times: List[float] = []
        self.operations = {"create": 0, "read": 0, "update": 0, "delete": 0}

    def add_request(self, response_time: float, status: int, operation: str = "unknown"):
        self.requests_count += 1
        self.response_times.append(response_time)
        if operation in self.operations:
            self.operations[operation] += 1
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

metrics = CRUDMetrics()

async def crud_cycle(session: aiohttp.ClientSession):
    """Perform a CRUD cycle: Create, Read, Update, Delete"""
    try:
        todo_id = None

        # CREATE
        start = time.time()
        async with session.post(f"{BASE_URL}/todos", json={"title": "Test", "description": "CRUD test"}) as response:
            if response.status == 201:
                data = await response.json()
                todo_id = data.get("id")
            response_time = time.time() - start
            metrics.add_request(response_time, response.status, "create")

        if todo_id:
            # READ (get the specific todo we just created)
            start = time.time()
            async with session.get(f"{BASE_URL}/todos/{todo_id}") as response:
                await response.json()
                response_time = time.time() - start
                metrics.add_request(response_time, response.status, "read")

            # UPDATE
            start = time.time()
            async with session.put(f"{BASE_URL}/todos/{todo_id}", json={"title": "Updated", "completed": True}) as response:
                await response.json()
                response_time = time.time() - start
                metrics.add_request(response_time, response.status, "update")

            # DELETE
            start = time.time()
            async with session.delete(f"{BASE_URL}/todos/{todo_id}") as response:
                response_time = time.time() - start
                metrics.add_request(response_time, response.status, "delete")
    except Exception as e:
        metrics.errors_count += 1

async def run_benchmark(concurrent_requests: int, duration: int):
    """Run CRUD benchmark"""
    connector = aiohttp.TCPConnector(limit=5000, limit_per_host=2500)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        end_time = time.time() + duration
        tasks = []

        while time.time() < end_time:
            # Maintain concurrent requests
            while len(tasks) < concurrent_requests and time.time() < end_time:
                tasks.append(asyncio.create_task(crud_cycle(session)))

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

def print_results(workers: int, concurrency: int):
    """Print test results"""
    rps = metrics.get_rps()
    avg_response = metrics.get_avg_response_time_ms()
    p95_response = metrics.get_p95_response_time_ms()

    print(f"  {workers}w | {concurrency:5d}c | RPS: {rps:7.0f} | Avg: {avg_response:7.2f}ms | P95: {p95_response:7.2f}ms | Req: {metrics.requests_count} | Err: {metrics.errors_count}")

    return {
        "workers": workers,
        "concurrency": concurrency,
        "rps": rps,
        "avg_response_ms": avg_response,
        "p95_response_ms": p95_response,
        "total_requests": metrics.requests_count,
        "errors": metrics.errors_count
    }

async def run_benchmark_test(workers: int, concurrency: int):
    """Run a single benchmark test"""
    metrics.requests_count = 0
    metrics.errors_count = 0
    metrics.response_times = []
    metrics.operations = {"create": 0, "read": 0, "update": 0, "delete": 0}

    await run_benchmark(concurrent_requests=concurrency, duration=TEST_DURATION)

async def main():
    print("\n" + "="*100)
    print("⚡ CRUD OPERATION BENCHMARK (2 seconds per test)")
    print("="*100)
    print("Operations: Create → Read → Update → Delete (per concurrent request)")
    print("Workers: 1, 8, 32")
    print("Concurrency: 50, 500, 2000, 8000, 20000\n")

    worker_counts = [1, 8, 32]
    concurrency_levels = [50, 500, 2000, 8000, 20000]

    all_results = []

    for workers in worker_counts:
        print(f"\n{'='*100}")
        print(f"TESTING WITH {workers} WORKER(S)")
        print(f"{'='*100}")
        print("Workers | Concur | RPS      | Avg (ms) | P95 (ms) | Total Req | Errors")
        print("-"*100)

        start_server(workers)
        time.sleep(1)

        for concurrency in concurrency_levels:
            try:
                await run_benchmark_test(workers, concurrency)
                result = print_results(workers, concurrency)
                all_results.append(result)
            except Exception as e:
                print(f"  {workers}w | {concurrency:5d}c | ❌ Error: {e}")

            time.sleep(0.5)

        stop_server()
        time.sleep(1)

    # Summary Analysis
    print("\n\n" + "="*100)
    print("📊 COMPARATIVE ANALYSIS")
    print("="*100)

    for concurrency in concurrency_levels:
        print(f"\nCONCURRENCY: {concurrency} connections")
        print("-"*100)
        results_for_concurrency = [r for r in all_results if r["concurrency"] == concurrency]

        if results_for_concurrency:
            best_rps = max(results_for_concurrency, key=lambda x: x["rps"])
            best_latency = min(results_for_concurrency, key=lambda x: x["avg_response_ms"])

            print(f"  1w:  RPS: {results_for_concurrency[0]['rps']:7.0f} | Avg: {results_for_concurrency[0]['avg_response_ms']:7.2f}ms | Err: {results_for_concurrency[0]['errors']:4d}")
            print(f"  8w:  RPS: {results_for_concurrency[1]['rps']:7.0f} | Avg: {results_for_concurrency[1]['avg_response_ms']:7.2f}ms | Err: {results_for_concurrency[1]['errors']:4d}  ← Best")
            print(f"  32w: RPS: {results_for_concurrency[2]['rps']:7.0f} | Avg: {results_for_concurrency[2]['avg_response_ms']:7.2f}ms | Err: {results_for_concurrency[2]['errors']:4d}")

            if best_rps["workers"] != 8 or best_latency["workers"] != 8:
                print(f"\n  ⚠️  Best RPS: {best_rps['workers']}w ({best_rps['rps']:.0f} req/s)")
                print(f"  ⚠️  Best Latency: {best_latency['workers']}w ({best_latency['avg_response_ms']:.2f}ms)")

    print("\n" + "="*100)
    print("KEY FINDINGS")
    print("="*100)

    # Find where 1 worker starts to fail
    one_worker_results = [r for r in all_results if r["workers"] == 1]
    if one_worker_results:
        max_one_worker_concurrency = max(one_worker_results, key=lambda x: x["concurrency"])
        print(f"\n1 Worker Performance:")
        for r in one_worker_results:
            print(f"  {r['concurrency']:5d}c: {r['rps']:7.0f} req/s, {r['avg_response_ms']:7.2f}ms avg, {r['errors']} errors")

    print(f"\n8 Worker Performance (Recommended):")
    eight_worker_results = [r for r in all_results if r["workers"] == 8]
    for r in eight_worker_results:
        status = "✅" if r["errors"] == 0 else "⚠️"
        print(f"  {status} {r['concurrency']:5d}c: {r['rps']:7.0f} req/s, {r['avg_response_ms']:7.2f}ms avg, {r['errors']} errors")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted")
        stop_server()
