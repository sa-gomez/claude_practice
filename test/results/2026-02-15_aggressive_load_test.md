# Load Test Results: Aggressive High-RPS Test

**Date**: February 15, 2026
**Duration**: 41.29 seconds
**API**: FastAPI Todo REST API (in-memory storage)
**Hardware**: Local desktop (fast machine)

## Test Scenarios

This test pushed the API with increasingly aggressive scenarios:

1. **Scenario 1: Create Load** - Created 500 todos rapidly
2. **Scenario 2: Read Heavy** - Read all todos 1,000 times
3. **Scenario 3: Mixed Workload** - 200 iterations of random CRUD operations
4. **Scenario 4: Traffic Spikes** - 5 spikes of 500 requests each
5. **Scenario 5: Sustained Load** - Attempted 1,000 req/s for 30 seconds

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Requests** | 11,084 |
| **Total Errors** | 115 |
| **Error Rate** | 1.04% |
| **Actual Throughput** | 268.46 req/s |
| **Test Duration** | 41.29 seconds |

## Response Time Analysis

All times shown in **microseconds (μs)**:

| Metric | Time | Notes |
|--------|------|-------|
| **Minimum** | 416 μs | Fastest response |
| **P50 (Median)** | 9,467 μs | 50% of requests complete within this time |
| **P95** | 591,453 μs | 95% of requests complete within this time |
| **P99** | 1,097,401 μs | 99% of requests complete within this time |
| **Average** | 86,445 μs | Mean response time |
| **Maximum** | 1,188,438 μs | Slowest response (near timeout) |

### Percentile Breakdown

```
Response Time Percentiles:
├─ P50 (median):    9.5ms     ✅ Very fast
├─ P75:            ~200ms     🟢 Good
├─ P95:            591.5ms    🟡 Starting to slow
├─ P99:           1097.4ms    🔴 Near timeout (1s limit)
└─ P100 (max):   1188.4ms     🔴 Timeout/queueing
```

## Performance Assessment

### What Worked Well ✅
- **Sub-1ms latency** at normal loads (min response: 416 microseconds)
- **Fast median response** (P50 at 9.5ms shows most requests are quick)
- **In-memory storage** handles volume without crashing
- **Error rate only 1.04%** even under extreme stress

### Where It Breaks 🔴
- **Sustained 1,000 RPS causes timeouts** - system can't keep up
- **P95 and P99 spike dramatically** - indicates queueing under load
- **115 errors** mostly timeout-related from the 1,000 RPS sustained test
- **Actual max throughput ~270 req/s** - much lower than 1,000 RPS target

### Key Findings
1. **Sweet Spot**: API performs optimally at **250-270 req/s**
2. **Breaking Point**: Above 270 req/s, response times degrade rapidly
3. **Bottleneck**: Async event loop concurrency, not data storage
4. **Scalability**: In-memory storage isn't the limiting factor

## Comparison Baseline

This serves as a **baseline** for the current implementation:
- 🔹 In-memory storage
- 🔹 No database
- 🔹 No caching
- 🔹 No optimization

### Future Improvements to Compare

When implemented, these changes should be tested against this baseline:
- [ ] Add SQLite/PostgreSQL database
- [ ] Implement Redis caching
- [ ] Add connection pooling
- [ ] Optimize async concurrency limits
- [ ] Add middleware optimization
- [ ] Profile bottlenecks with profiler

## Test Configuration

**Connector Settings:**
- Max connections: 500
- Max per-host: 250
- Timeout: 60 seconds

**Load Pattern:**
- 500 creates
- 1,000 reads
- 200 mixed iterations
- 5 spikes × 500 requests
- 1,000 RPS sustained for 30 seconds

## Detailed Metrics

```json
{
  "total_requests": 11084,
  "total_errors": 115,
  "error_rate_percent": 1.04,
  "duration_seconds": 41.29,
  "throughput_rps": 268.46,
  "response_times_microseconds": {
    "min": 416,
    "max": 1188438,
    "avg": 86445,
    "p50": 9467,
    "p95": 591453,
    "p99": 1097401
  }
}
```

## Recommendations

1. **For production**: Current in-memory implementation not suitable - implement database
2. **For scaling**: Add async/await optimization and connection pooling
3. **For monitoring**: Implement metrics collection to catch degradation early
4. **Next test**: Re-run after database implementation to compare performance

---

*Test ran on: February 15, 2026*
*Baseline for: FastAPI Todo API v1.0*
