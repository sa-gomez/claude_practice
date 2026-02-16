import psutil
import time
import asyncio
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

console = Console()

class SystemMonitor:
    def __init__(self):
        self.process = None
        self.initial_memory = None
        self.peak_memory = 0
        self.start_time = time.time()

    def find_uvicorn_process(self):
        """Find the uvicorn server process"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'uvicorn' in ' '.join(proc.info['cmdline']):
                    self.process = proc
                    self.initial_memory = proc.memory_info().rss / 1024 / 1024
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def get_cpu_percent(self):
        """Get CPU usage percentage"""
        if self.process:
            try:
                return round(self.process.cpu_percent(interval=0.1), 2)
            except:
                return 0
        return psutil.cpu_percent(interval=0.1)

    def get_memory_info(self):
        """Get memory usage"""
        if self.process:
            try:
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                self.peak_memory = max(self.peak_memory, memory_mb)
                return {
                    "current": round(memory_mb, 2),
                    "peak": round(self.peak_memory, 2),
                    "initial": round(self.initial_memory, 2) if self.initial_memory else 0,
                    "delta": round(memory_mb - self.initial_memory, 2) if self.initial_memory else 0
                }
            except:
                pass

        # Fallback to system memory
        vm = psutil.virtual_memory()
        return {
            "current": round(vm.used / 1024 / 1024, 2),
            "peak": round(self.peak_memory, 2),
            "initial": round(self.initial_memory, 2) if self.initial_memory else 0,
            "delta": 0
        }

    def get_network_stats(self):
        """Get network I/O stats"""
        net = psutil.net_io_counters()
        return {
            "bytes_sent": round(net.bytes_sent / 1024 / 1024, 2),
            "bytes_recv": round(net.bytes_recv / 1024 / 1024, 2),
        }

def create_dashboard(monitor: SystemMonitor, load_test_results: dict = None):
    """Create monitoring dashboard"""
    layout = Layout()
    layout.split_column(
        Layout(name="header"),
        Layout(name="metrics"),
        Layout(name="footer"),
    )

    # Header
    layout["header"].update(
        Panel(
            Text("📊 API Load Test Monitoring Dashboard", justify="center", style="bold cyan"),
            style="blue"
        )
    )

    # Metrics
    metrics_table = Table(show_header=True, header_style="bold magenta")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")

    # System metrics
    cpu = monitor.get_cpu_percent()
    mem = monitor.get_memory_info()
    net = monitor.get_network_stats()
    elapsed = time.time() - monitor.start_time

    # CPU status
    cpu_status = "🟢" if cpu < 50 else "🟡" if cpu < 80 else "🔴"
    metrics_table.add_row(f"{cpu_status} CPU Usage", f"{cpu}%")

    # Memory status
    mem_status = "🟢" if mem["delta"] < 100 else "🟡" if mem["delta"] < 200 else "🔴"
    metrics_table.add_row(f"{mem_status} Memory (Current)", f"{mem['current']} MB")
    metrics_table.add_row("  └─ Peak", f"{mem['peak']} MB")
    metrics_table.add_row("  └─ Initial", f"{mem['initial']} MB")
    metrics_table.add_row("  └─ Delta", f"{mem['delta']} MB")

    metrics_table.add_row("📤 Network Sent", f"{net['bytes_sent']} MB")
    metrics_table.add_row("📥 Network Received", f"{net['bytes_recv']} MB")

    metrics_table.add_row("⏱️ Elapsed Time", f"{elapsed:.1f}s")

    # Load test results if available
    if load_test_results:
        metrics_table.add_row("", "")  # Separator
        metrics_table.add_row("[bold]Load Test Results[/bold]", "")
        metrics_table.add_row(f"  Requests", f"{load_test_results.get('total_requests', 'N/A')}")
        metrics_table.add_row(f"  Errors", f"{load_test_results.get('total_errors', 0)} ({load_test_results.get('error_rate', 0):.2f}%)")
        metrics_table.add_row(f"  Throughput", f"{load_test_results.get('requests_per_second', 'N/A')} req/s")
        metrics_table.add_row(f"  Avg Response", f"{load_test_results.get('response_time_avg', 'N/A')}ms")
        metrics_table.add_row(f"  P95 Response", f"{load_test_results.get('response_time_p95', 'N/A')}ms")
        metrics_table.add_row(f"  P99 Response", f"{load_test_results.get('response_time_p99', 'N/A')}ms")

    layout["metrics"].update(Panel(metrics_table, title="System & Load Metrics"))

    # Footer
    layout["footer"].update(
        Panel(
            Text("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 justify="center", style="dim"),
            style="blue"
        )
    )

    return layout

async def monitor_system(duration: int = 120):
    """Monitor system while load test runs"""
    monitor = SystemMonitor()

    console.print("[bold cyan]🚀 Initializing System Monitor...[/bold cyan]")

    if not monitor.find_uvicorn_process():
        console.print("[bold yellow]⚠️  Warning: Could not find Uvicorn process[/bold yellow]")
        console.print("[bold yellow]   Make sure the server is running: uvicorn main:app --reload[/bold yellow]")
    else:
        console.print("[bold green]✅ Found Uvicorn process[/bold green]")

    console.print(f"[bold cyan]Monitoring for {duration} seconds...[/bold cyan]\n")

    start_time = time.time()
    load_test_results = None

    try:
        with Live(create_dashboard(monitor), refresh_per_second=2, console=console) as live:
            while time.time() - start_time < duration:
                # Try to read load test results if available
                try:
                    if time.time() - start_time > 5:  # Wait 5 seconds before checking
                        with open("../load_test_results.json", "r") as f:
                            load_test_results = json.load(f)
                except:
                    pass

                live.update(create_dashboard(monitor, load_test_results))
                await asyncio.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️  Monitoring stopped by user[/bold yellow]")

def start_monitor(duration: int = 120):
    """Start the monitoring dashboard"""
    console.print("\n[bold cyan]=" * 50)
    console.print("📊 SYSTEM MONITOR", justify="center")
    console.print("=" * 50 + "[/bold cyan]\n")
    asyncio.run(monitor_system(duration))

if __name__ == "__main__":
    # Default 120 second monitoring
    start_monitor(120)
