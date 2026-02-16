# Deployment & Configuration Guide

## Overview

This guide covers how to properly configure and deploy the FastAPI Todo API for different environments.

## Critical Discovery: Worker Configuration

**Performance Impact**: Improper worker configuration can reduce throughput by **160x**.

### The Issue
- Default Uvicorn configuration uses **1 worker process**
- Only utilizes **1 CPU core**, leaving others idle
- Results in severe latency and limited throughput

### The Solution
- Use **multiple worker processes** to utilize multi-core CPUs
- Distribute requests across cores in parallel

## Configuration

### Development Environment

```bash
# Auto-reload on code changes (single worker)
uvicorn main:app --reload
```

**Characteristics**:
- Single worker process
- Auto-reload on file changes
- Fast iteration for development
- Not suitable for performance testing

### Testing Environment

```bash
# Balanced performance without overload
uvicorn main:app --workers 8
```

**Characteristics**:
- 8 worker processes
- Good performance for testing
- Simulates multi-core environment
- Safe for stress testing

### Production Environment

```bash
# Calculate optimal workers: (2 × CPU_cores) + 1
# For most systems, use: 8-16 workers

# Example for 28-core system:
uvicorn main:app --workers 16
```

**Characteristics**:
- Multiple worker processes
- Utilizes available CPU cores
- Optimized throughput
- Consistent response times

## Worker Count Calculator

```
Optimal Workers = (2 × CPU_Cores) + 1

Examples:
  2-core CPU:   (2 × 2) + 1  = 5 workers
  4-core CPU:   (2 × 4) + 1  = 9 workers
  8-core CPU:   (2 × 8) + 1  = 17 workers
  16-core CPU:  (2 × 16) + 1 = 33 workers
  28-core CPU:  (2 × 28) + 1 = 57 workers (max tested)
```

## Performance Baseline

These measurements are from actual load testing with in-memory storage:

### Single Worker (Default)
```
Concurrency Level: 500 concurrent connections
Throughput:        66.8 req/s (BOTTLENECKED)
Response Time:     5,988ms average
P99 Latency:       8,201ms (8.2 seconds!)
```

### 16 Workers (Optimized)
```
Concurrency Level: 500 concurrent connections
Throughput:        10,759 req/s (160x faster!)
Response Time:     44.2ms average
P99 Latency:       52.8μs (52 microseconds!)
```

## Deployment Steps

### 1. Prepare Environment

```bash
# Clone or setup project
cd /home/sagomez/claude_practice

# Create virtual environment
python3 -m venv claude_practice_venv
source claude_practice_venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Determine CPU Core Count

```bash
# Linux/Mac
nproc
# or
python3 -c "import multiprocessing; print(multiprocessing.cpu_count())"
```

### 3. Calculate Worker Count

Use formula: `(2 × CPU_cores) + 1` or default to 8-16 for safe performance

### 4. Start Server with Workers

```bash
# Production startup
uvicorn main:app --workers 16 --host 0.0.0.0 --port 8000
```

### 5. Verify Performance (Optional)

```bash
# Run load tests
cd test
source ../claude_practice_venv/bin/activate
python3 debug_load_test.py
```

## Advanced Configuration

### Custom Host/Port

```bash
uvicorn main:app --workers 16 --host 0.0.0.0 --port 8080
```

### With Logging

```bash
uvicorn main:app --workers 16 --log-level info
```

### With Access Logs

```bash
uvicorn main:app --workers 16 --access-log
```

### Full Example (Production)

```bash
uvicorn main:app \
  --workers 16 \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info \
  --access-log
```

## Monitoring

### CPU Usage
```bash
# Watch CPU and worker processes
htop
```

Expected at load:
- Single worker: 5-10% CPU (severely underutilized)
- Multiple workers: 20-40% CPU (properly utilized)

### Memory Usage
```bash
# Check memory per worker
ps aux | grep uvicorn
```

Expected per worker: 20-50MB

### Throughput Monitoring
```bash
# If using the debug load test
python3 test/debug_load_test.py
```

## Troubleshooting

### Server Crashes
```bash
# Check logs
tail -f /var/log/uvicorn.log

# Increase worker count carefully
# If crashing, reduce by half and add back gradually
```

### High Memory Usage
```bash
# Reduce worker count
uvicorn main:app --workers 8  # instead of 16
```

### Still Low Throughput
```bash
# Verify worker count
ps aux | grep uvicorn | wc -l

# Try increasing workers
uvicorn main:app --workers 32

# Monitor CPU - if CPU < 30%, add more workers
# If CPU > 80%, reduce workers
```

## Performance Tuning

### If Throughput < Expected

1. **Check worker count**
   ```bash
   ps aux | grep uvicorn | grep -v grep | wc -l
   ```

2. **Check CPU utilization**
   ```bash
   top -p <uvicorn_pid>
   ```

3. **Monitor response times**
   ```bash
   # Run debug load test
   python3 test/debug_load_test.py
   ```

### If Response Times Are High

1. **Increase worker count** (if CPU < 50%)
2. **Check system resources** (memory, disk I/O)
3. **Profile application** (see test/debug_load_test.py)

## Summary

| Environment | Command | Workers | Auto-reload |
|---|---|---|---|
| **Development** | `uvicorn main:app --reload` | 1 | Yes |
| **Testing** | `uvicorn main:app --workers 8` | 8 | No |
| **Production** | `uvicorn main:app --workers 16` | 16 | No |

**Key Takeaway**: Always use multiple workers in production. A simple `--workers 16` flag can provide **160x performance improvement** over the default configuration.

---

For detailed performance analysis, see: `test/results/2026-02-15_worker_optimization_comparison.md`
