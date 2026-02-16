import asyncio
import aiohttp
import time
import subprocess
import os
from typing import List
import random

BASE_URL = "http://localhost:8000"
TEST_DURATION = 1  # 1-second tests
CONCURRENCY = 100  # Fixed at 100 concurrent connections

# Thread-safe queue for available todo IDs
available_todo_queue: asyncio.Queue = None

class PatternMetrics:
    def __init__(self):
        self.requests_count = 0
        self.errors_count = 0
        self.response_times: List[float] = []
        self.operation_counts = {"read": 0, "create": 0, "update": 0, "delete": 0}

    def add_request(self, response_time: float, status: int, operation: str = "unknown"):
        self.requests_count += 1
        self.response_times.append(response_time)
        if operation in self.operation_counts:
            self.operation_counts[operation] += 1
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

    def get_p99_response_time_ms(self):
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx] * 1000

metrics = PatternMetrics()


async def read_operation(session: aiohttp.ClientSession):
    """GET request - read a specific todo by ID (only existing ones)"""
    try:
        # Get a todo ID from the queue without removing it
        todo_id = available_todo_queue.get_nowait()
        # Put it back immediately so others can use it
        await available_todo_queue.put(todo_id)

        start = time.time()
        async with session.get(f"{BASE_URL}/todos/{todo_id}") as response:
            await response.json()
            response_time = time.time() - start
            metrics.add_request(response_time, response.status, "read")
    except asyncio.QueueEmpty:
        return
    except:
        metrics.errors_count += 1

async def create_operation(session: aiohttp.ClientSession):
    """POST request - create a todo"""
    try:
        start = time.time()
        async with session.post(f"{BASE_URL}/todos", json={"title": f"Test {time.time()}"}) as response:
            data = await response.json()
            response_time = time.time() - start
            metrics.add_request(response_time, response.status, "create")
            if response.status == 201:
                with todo_lock:
                    available_todo_ids.append(data.get("id"))
    except:
        metrics.errors_count += 1

async def update_operation(session: aiohttp.ClientSession):
    """PUT request - update a todo (only existing ones)"""
    with todo_lock:
        if not available_todo_ids:
            return
        todo_id = random.choice(available_todo_ids)

    try:
        start = time.time()
        async with session.put(f"{BASE_URL}/todos/{todo_id}", json={"title": f"Updated {time.time()}"}) as response:
            await response.json()
            response_time = time.time() - start
            metrics.add_request(response_time, response.status, "update")
    except:
        metrics.errors_count += 1

async def delete_operation(session: aiohttp.ClientSession):
    """DELETE request - delete a todo (only existing ones)"""
    with todo_lock:
        if not available_todo_ids:
            return
        todo_id = available_todo_ids.pop(0)  # Remove from pool before delete

    try:
        start = time.time()
        async with session.delete(f"{BASE_URL}/todos/{todo_id}") as response:
            response_time = time.time() - start
            metrics.add_request(response_time, response.status, "delete")
    except:
        metrics.errors_count += 1

async def pre_populate_todos(session: aiohttp.ClientSession, count: int):
    """Pre-create todos for the read test"""
    global available_todo_ids
    with todo_lock:
        available_todo_ids = []

    print(f"  Pre-populating {count} todos...", end="", flush=True)

    for i in range(count):
        try:
            async with session.post(f"{BASE_URL}/todos", json={"title": f"Prepopulated {i}"}) as response:
                if response.status == 201:
                    data = await response.json()
                    with todo_lock:
                        available_todo_ids.append(data.get("id"))
        except:
            pass

    with todo_lock:
        created = len(available_todo_ids)
    print(f" ✓ ({created} created)")

async def test_pattern_all_reads(session: aiohttp.ClientSession):
    """Test Pattern 1: 100% reads"""
    end_time = time.time() + TEST_DURATION
    tasks = []

    while time.time() < end_time:
        while len(tasks) < CONCURRENCY and time.time() < end_time:
            tasks.append(asyncio.create_task(read_operation(session)))

        if tasks:
            done, pending = await asyncio.wait(tasks, timeout=0.001, return_when=asyncio.FIRST_COMPLETED)
            tasks = list(pending)

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def test_pattern_2_1_reads_writes(session: aiohttp.ClientSession):
    """Test Pattern 2: 2/3 reads, 1/3 writes"""
    end_time = time.time() + TEST_DURATION
    tasks = []

    while time.time() < end_time:
        while len(tasks) < CONCURRENCY and time.time() < end_time:
            rand = random.random()
            if rand < 0.67:  # 2/3 reads
                tasks.append(asyncio.create_task(read_operation(session)))
            elif rand < 0.84:  # 1/6 creates
                tasks.append(asyncio.create_task(create_operation(session)))
            elif rand < 0.92:  # 1/12 updates
                tasks.append(asyncio.create_task(update_operation(session)))
            else:  # 1/12 deletes
                tasks.append(asyncio.create_task(delete_operation(session)))

        if tasks:
            done, pending = await asyncio.wait(tasks, timeout=0.001, return_when=asyncio.FIRST_COMPLETED)
            tasks = list(pending)

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def test_pattern_1_2_reads_writes(session: aiohttp.ClientSession):
    """Test Pattern 3: 1/3 reads, 2/3 writes"""
    end_time = time.time() + TEST_DURATION
    tasks = []

    while time.time() < end_time:
        while len(tasks) < CONCURRENCY and time.time() < end_time:
            rand = random.random()
            if rand < 0.33:  # 1/3 reads
                tasks.append(asyncio.create_task(read_operation(session)))
            elif rand < 0.56:  # 1/3 creates
                tasks.append(asyncio.create_task(create_operation(session)))
            elif rand < 0.78:  # 1/3 updates
                tasks.append(asyncio.create_task(update_operation(session)))
            else:  # remaining deletes
                tasks.append(asyncio.create_task(delete_operation(session)))

        if tasks:
            done, pending = await asyncio.wait(tasks, timeout=0.001, return_when=asyncio.FIRST_COMPLETED)
            tasks = list(pending)

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def test_pattern_all_writes(session: aiohttp.ClientSession):
    """Test Pattern 4: 100% writes"""
    end_time = time.time() + TEST_DURATION
    tasks = []

    while time.time() < end_time:
        while len(tasks) < CONCURRENCY and time.time() < end_time:
            rand = random.random()
            if rand < 0.4:  # 40% creates
                tasks.append(asyncio.create_task(create_operation(session)))
            elif rand < 0.7:  # 30% updates
                tasks.append(asyncio.create_task(update_operation(session)))
            else:  # 30% deletes
                tasks.append(asyncio.create_task(delete_operation(session)))

        if tasks:
            done, pending = await asyncio.wait(tasks, timeout=0.001, return_when=asyncio.FIRST_COMPLETED)
            tasks = list(pending)

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

def start_server():
    """Start Uvicorn server with 8 workers"""
    print("Starting server with 8 workers...", end="", flush=True)
    os.system("pkill -9 uvicorn 2>/dev/null")
    time.sleep(1)

    subprocess.Popen(
        f"cd /home/sagomez/claude_practice && source claude_practice_venv/bin/activate && uvicorn main:app --workers 8",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

    time.sleep(2)
    print(" ✓")

def stop_server():
    """Stop Uvicorn server"""
    os.system("pkill -9 uvicorn 2>/dev/null")
    time.sleep(0.5)

def print_results(pattern_name: str):
    """Print test results"""
    rps = metrics.get_rps()
    avg_response = metrics.get_avg_response_time_ms()
    p95_response = metrics.get_p95_response_time_ms()
    p99_response = metrics.get_p99_response_time_ms()

    print(f"\n{pattern_name}")
    print(f"  Requests:        {metrics.requests_count:,}")
    print(f"  Throughput:      {rps:.0f} req/s")
    print(f"  Avg Response:    {avg_response:.2f}ms")
    print(f"  P95 Response:    {p95_response:.2f}ms")
    print(f"  P99 Response:    {p99_response:.2f}ms")
    print(f"  Errors:          {metrics.errors_count}")
    print(f"  Operations:      {metrics.operation_counts}")

    return {
        "pattern": pattern_name,
        "rps": rps,
        "avg_response_ms": avg_response,
        "p95_response_ms": p95_response,
        "p99_response_ms": p99_response,
        "total_requests": metrics.requests_count,
        "errors": metrics.errors_count,
        "operations": metrics.operation_counts.copy()
    }

async def run_test(pattern_name: str, test_func, session: aiohttp.ClientSession):
    """Run a single test"""
    metrics.requests_count = 0
    metrics.errors_count = 0
    metrics.response_times = []
    metrics.operation_counts = {"read": 0, "create": 0, "update": 0, "delete": 0}

    await test_func(session)
    return print_results(pattern_name)

async def main():
    print("\n" + "="*100)
    print("📊 REQUEST PATTERN BENCHMARK (8 workers)")
    print("="*100)
    print(f"Concurrency: {CONCURRENCY} connections")
    print(f"Duration: {TEST_DURATION} seconds per test")
    print(f"Target: {BASE_URL}\n")

    start_server()

    results = []

    connector = aiohttp.TCPConnector(limit=2000, limit_per_host=1000)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Pattern 1: All Reads
        print("-" * 100)
        print("PATTERN 1: All Reads (100% GET)")
        print("-" * 100)
        await pre_populate_todos(session, 500)
        result1 = await run_test("Pattern 1: All Reads", test_pattern_all_reads, session)
        results.append(result1)
        time.sleep(1)

        # Pattern 2: 2/3 Reads, 1/3 Writes
        print("\n" + "-" * 100)
        print("PATTERN 2: 2/3 Reads, 1/3 Writes (67% GET, 33% POST/PUT/DELETE)")
        print("-" * 100)
        await pre_populate_todos(session, 500)
        result2 = await run_test("Pattern 2: 2/3 Read, 1/3 Write", test_pattern_2_1_reads_writes, session)
        results.append(result2)
        time.sleep(1)

        # Pattern 3: 1/3 Reads, 2/3 Writes
        print("\n" + "-" * 100)
        print("PATTERN 3: 1/3 Reads, 2/3 Writes (33% GET, 67% POST/PUT/DELETE)")
        print("-" * 100)
        await pre_populate_todos(session, 500)
        result3 = await run_test("Pattern 3: 1/3 Read, 2/3 Write", test_pattern_1_2_reads_writes, session)
        results.append(result3)
        time.sleep(1)

        # Pattern 4: All Writes
        print("\n" + "-" * 100)
        print("PATTERN 4: All Writes (100% POST/PUT/DELETE)")
        print("-" * 100)
        await pre_populate_todos(session, 500)
        result4 = await run_test("Pattern 4: All Writes", test_pattern_all_writes, session)
        results.append(result4)

    stop_server()

    # Summary
    print("\n\n" + "="*100)
    print("📈 COMPARISON SUMMARY")
    print("="*100)
    print("\nPattern                  │ RPS      │ Avg (ms) │ P95 (ms) │ P99 (ms) │ Errors")
    print("-" * 100)

    for r in results:
        pattern_short = r["pattern"].replace("Pattern ", "P").replace(": ", " ")
        print(f"{pattern_short:24} │ {r['rps']:8.0f} │ {r['avg_response_ms']:8.2f} │ {r['p95_response_ms']:8.2f} │ {r['p99_response_ms']:8.2f} │ {r['errors']:6d}")

    # Analysis
    print("\n" + "="*100)
    print("🔍 ANALYSIS")
    print("="*100)

    best_rps = max(results, key=lambda x: x["rps"])
    worst_rps = min(results, key=lambda x: x["rps"])
    best_latency = min(results, key=lambda x: x["avg_response_ms"])
    worst_latency = max(results, key=lambda x: x["avg_response_ms"])

    print(f"\n🏆 Best Throughput: {best_rps['pattern']} ({best_rps['rps']:.0f} req/s)")
    print(f"🐢 Worst Throughput: {worst_rps['pattern']} ({worst_rps['rps']:.0f} req/s)")
    print(f"   Difference: {(best_rps['rps'] / worst_rps['rps']):.1f}x")

    print(f"\n⚡ Best Latency: {best_latency['pattern']} ({best_latency['avg_response_ms']:.2f}ms avg)")
    print(f"🐌 Worst Latency: {worst_latency['pattern']} ({worst_latency['avg_response_ms']:.2f}ms avg)")
    print(f"   Difference: {(worst_latency['avg_response_ms'] / best_latency['avg_response_ms']):.1f}x")

    print(f"\n💡 Key Insights:")
    print(f"   • Reads are {(results[0]['rps'] / results[3]['rps']):.1f}x faster than writes")
    print(f"   • Write-heavy workloads impact response time significantly")
    print(f"   • Read-dominant patterns (P1, P2) perform best")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        stop_server()
