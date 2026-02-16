# Test concurrency (number RPS)
- pretty reliable results when pushing bounds of concurrency. Things break down >500 concurrent RPS but that's pretty unrealistic territory for a single server.

# Number of workers
Needs to be retested now with realistic concurrencies. Maybe try 10 RPS, 50RPS, and 200RPS

# Request patterns
Need to try:
- All read
- Mostly read
- Mostly write
- All write