# Load Testing & Performance Monitoring

Comprehensive load testing suite for the Todo API with real-time system monitoring.

## Quick Start

### Prerequisites
- Make sure the Todo API server is running
- Install test dependencies: `pip install -r requirements.txt`

### Run Everything
```bash
# From the test/ directory
./run_load_test.sh
```

This will:
1. ✅ Check if the server is running
2. ✅ Install dependencies
3. ✅ Start a real-time system monitor
4. ✅ Run the load test scenarios
5. ✅ Display results and save to JSON

## Components

### 1. load_test.py
Async load testing script that hammers the API with realistic scenarios.

**Run alone:**
```bash
source ../claude_practice_venv/bin/activate
python3 load_test.py
```

**What it tests:**
- **Scenario 1: Create Load** - Creates 50 todos rapidly
- **Scenario 2: Read Heavy** - Reads all todos 100 times
- **Scenario 3: Mixed Workload** - Random CRUD operations (50 iterations)
- **Scenario 4: Traffic Spikes** - 3 spikes of 30 requests each
- **Scenario 5: Sustained Load** - 20 requests/second for 10 seconds

**Metrics collected:**
- Total requests & errors
- Requests per second (throughput)
- Response times: min, max, avg, p50, p95, p99
- Error rate and error types
- Results saved to `load_test_results.json`

### 2. monitor.py
Real-time system monitoring dashboard (runs in parallel with load test).

**Run alone:**
```bash
python3 monitor.py
```

**Displays:**
- 🖥️ CPU usage (with status indicator)
- 💾 Memory usage (current, peak, initial, delta)
- 📤 Network I/O
- ⏱️ Elapsed time
- 📊 Load test results (when available)

**Visual Indicators:**
- 🟢 Green - Healthy (CPU < 50%, Memory delta < 100 MB)
- 🟡 Yellow - Caution (CPU < 80%, Memory delta < 200 MB)
- 🔴 Red - Warning (High resource usage)

### 3. run_load_test.sh
Convenience script that runs everything in the right order.

## Customizing Tests

### Modify load_test.py

Change test scenarios by editing the `run_load_tests()` function:

```python
# More aggressive create load
await scenario_create_todos(session, 200)  # was 50

# Longer sustained load
await scenario_sustained_load(session, 30, 50)  # was 10 seconds, 20 RPS
```

### Adjust concurrent connections

Edit the connector settings:
```python
# More connections
connector = aiohttp.TCPConnector(limit=200, limit_per_host=100)
```

## Understanding Results

### Response Time Percentiles
- **P50 (median)** - The middle value, 50% of requests are faster
- **P95** - 95% of requests complete within this time (good for user experience)
- **P99** - 99% of requests, includes slower outliers

### Key Performance Indicators
- **Requests/second** - Throughput capacity
- **Error rate** - Stability under load
- **P99 response time** - Worst-case performance

## Example Output

```
======================================================================
📊 LOAD TEST RESULTS
======================================================================
Total Requests:        2450
Total Errors:          0 (0.00%)
Duration:              45.32s
Throughput:            54.10 req/s

Response Times:
  Min:                 0.012ms
  Max:                 124.567ms
  Avg:                 15.234ms
  P50 (median):        12.456ms
  P95:                 45.123ms
  P99:                 98.765ms
======================================================================
```

## Common Issues

### Server crashes during test
- Check `/var/log/` for error messages
- Increase connection limits if getting "Too many open files"
- The API uses in-memory storage; very large datasets may cause issues

### Monitor shows no data
- Make sure Uvicorn is running with `ps aux | grep uvicorn`
- Monitor looks for processes with "uvicorn" in the name
- Falls back to system-wide metrics if process not found

### Low throughput (< 100 req/s)
- This is normal for in-memory storage with complex operations
- Network latency and system resources are the limiting factors
- Consider running on a different machine for more realistic production metrics

## Advanced Testing

### Test from different machines
```bash
# Edit BASE_URL in load_test.py
BASE_URL = "http://192.168.1.100:8000"
```

### Sustained load test (different duration)
```python
await scenario_sustained_load(session, duration_seconds=60, rps_target=100)
```

### Custom scenarios
Add new async functions to `load_test.py`:
```python
async def scenario_custom(session: aiohttp.ClientSession):
    """Your custom test scenario"""
    for i in range(1000):
        await make_request(session, "GET", "/todos")
```

Then call in `run_load_tests()`:
```python
await scenario_custom(session)
```

## Performance Optimization Tips

1. **Connection pooling** - Already optimized in load_test.py
2. **Async operations** - All I/O is non-blocking
3. **Error handling** - Gracefully handles timeout/failures
4. **Resource cleanup** - Proper session management

## Next Steps

- Run tests with different concurrency levels
- Monitor CPU/memory growth over extended periods
- Compare results across different hardware
- Test edge cases (very large payloads, many concurrent deletions)
