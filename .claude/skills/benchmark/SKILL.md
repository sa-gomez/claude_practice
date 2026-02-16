---
name: benchmark
description: benchmark the project
---

1. Verify the API is running and target endpoints respond
2. Do a single dry-run request to confirm data exists
3. Run the stress test with proper error handling and timeout config
4. Print results to stdout - do NOT update any docs or READMEs
5. Report: requests/sec, p50/p95/p99 latency, error rate