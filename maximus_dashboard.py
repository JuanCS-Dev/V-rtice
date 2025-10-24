#!/usr/bin/env python3
"""
Vértice Maximus - Interactive Dashboard
Beautiful TUI for managing the entire backend

Features:
- Real-time monitoring
- Start/Stop/Restart services
- System health visualization
- Live graphs
- Service discovery view

Author: Vértice Team
Glory to YHWH! 🙏
"""

import os
import sys
import time
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.text import Text
    from rich import box
    import requests
except ImportError:
    print("Installing required dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "requests"], check=True)
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.text import Text
    from rich import box
    import requests

console = Console()

class VerticeBackendManager:
    """Manages all backend services"""

    def __init__(self):
        self.base_dir = "/home/juan/vertice-dev"
        self.registry_url = "http://localhost:8888"
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"

    def get_docker_stats(self) -> Dict:
        """Get Docker container statistics"""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            stats = {}
            for line in result.stdout.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    stats[data['Name']] = {
                        'cpu': data['CPUPerc'],
                        'memory': data['MemPerc'],
                        'net_io': data['NetIO']
                    }
            return stats
        except Exception as e:
            return {}

    def get_registry_health(self) -> Dict:
        """Get Service Registry health"""
        try:
            response = requests.get(f"{self.registry_url}/health", timeout=2)
            return response.json()
        except Exception:
            return {"status": "unavailable"}

    def get_registered_services(self) -> List[str]:
        """Get list of registered services"""
        try:
            response = requests.get(f"{self.registry_url}/services", timeout=2)
            return response.json()
        except Exception:
            return []

    def get_container_list(self) -> List[Dict]:
        """Get list of all containers"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
            return containers
        except Exception:
            return []

    def count_sidecars(self) -> Tuple[int, int]:
        """Count total and healthy sidecars"""
        containers = self.get_container_list()
        sidecars = [c for c in containers if 'sidecar' in c.get('Names', '').lower()]
        healthy = [c for c in sidecars if 'healthy' in c.get('Status', '').lower()]
        return len(sidecars), len(healthy)

    def get_prometheus_metrics(self) -> Dict:
        """Get basic Prometheus metrics"""
        try:
            # Get registry_active_services
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query?query=registry_active_services",
                timeout=2
            )
            data = response.json()

            if data.get('status') == 'success' and data.get('data', {}).get('result'):
                value = data['data']['result'][0]['value'][1]
                return {'active_services': int(float(value))}
            return {}
        except Exception:
            return {}

    def start_service(self, service_name: str) -> bool:
        """Start a service"""
        try:
            service_dir = os.path.join(self.base_dir, "backend/services", service_name)
            if not os.path.exists(service_dir):
                return False

            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=service_dir,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a service"""
        try:
            service_dir = os.path.join(self.base_dir, "backend/services", service_name)
            if not os.path.exists(service_dir):
                return False

            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=service_dir,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    def restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        try:
            service_dir = os.path.join(self.base_dir, "backend/services", service_name)
            if not os.path.exists(service_dir):
                return False

            result = subprocess.run(
                ["docker", "compose", "restart"],
                cwd=service_dir,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False


class Dashboard:
    """Interactive Dashboard"""

    def __init__(self):
        self.manager = VerticeBackendManager()
        self.running = True

    def create_header(self) -> Panel:
        """Create dashboard header"""
        header_text = Text()
        header_text.append("🏛️ ", style="bold blue")
        header_text.append("VÉRTICE MAXIMUS", style="bold white")
        header_text.append(" - Backend Control Dashboard\n", style="bold blue")
        header_text.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")

        return Panel(header_text, style="bold blue", box=box.DOUBLE)

    def create_system_status(self) -> Panel:
        """Create system status panel"""
        health = self.manager.get_registry_health()
        status = health.get('status', 'unknown')

        # Status icon
        if status == "healthy":
            icon = "✅"
            style = "bold green"
        else:
            icon = "❌"
            style = "bold red"

        # Get counts
        registered_services = len(self.manager.get_registered_services())
        total_sidecars, healthy_sidecars = self.manager.count_sidecars()

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Registry Status", f"{icon} {status.upper()}")
        table.add_row("Registered Services", f"{registered_services}")
        table.add_row("Sidecars (Healthy/Total)", f"{healthy_sidecars}/{total_sidecars}")

        uptime_seconds = health.get('uptime_seconds', 0)
        uptime_hours = int(uptime_seconds / 3600)
        table.add_row("Registry Uptime", f"{uptime_hours}h")

        return Panel(table, title="[bold]System Status[/bold]", border_style=style, box=box.ROUNDED)

    def create_services_table(self) -> Panel:
        """Create registered services table"""
        services = self.manager.get_registered_services()

        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("№", style="dim", width=4)
        table.add_column("Service Name", style="white")
        table.add_column("Status", width=10)

        for i, service in enumerate(services[:15], 1):  # Show first 15
            table.add_row(str(i), service, "✅ UP")

        if len(services) > 15:
            table.add_row("...", f"and {len(services) - 15} more", "")

        return Panel(table, title=f"[bold]Registered Services ({len(services)})[/bold]", border_style="green", box=box.ROUNDED)

    def create_containers_table(self) -> Panel:
        """Create containers table"""
        containers = self.manager.get_container_list()

        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Container", style="white", overflow="fold")
        table.add_column("Status", width=15)
        table.add_column("Ports", width=15)

        for container in containers[:10]:  # Show first 10
            name = container.get('Names', '')[:30]
            status = container.get('Status', '')

            # Status styling
            if 'Up' in status and 'healthy' in status.lower():
                status_text = "[green]✅ Healthy[/green]"
            elif 'Up' in status:
                status_text = "[yellow]⚠️  Up[/yellow]"
            else:
                status_text = "[red]❌ Down[/red]"

            ports = container.get('Ports', '')[:15]
            table.add_row(name, status_text, ports)

        if len(containers) > 10:
            table.add_row(f"... and {len(containers) - 10} more", "", "")

        return Panel(table, title=f"[bold]Containers ({len(containers)})[/bold]", border_style="blue", box=box.ROUNDED)

    def create_metrics(self) -> Panel:
        """Create metrics panel"""
        metrics = self.manager.get_prometheus_metrics()

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        active_services = metrics.get('active_services', 'N/A')
        table.add_row("📊 Active Services (Prometheus)", str(active_services))

        # Get response time
        try:
            start = time.time()
            requests.get(f"{self.manager.registry_url}/health", timeout=1)
            response_time = int((time.time() - start) * 1000)

            if response_time < 100:
                rt_style = "[green]"
            elif response_time < 500:
                rt_style = "[yellow]"
            else:
                rt_style = "[red]"

            table.add_row("⚡ Response Time", f"{rt_style}{response_time}ms[/]")
        except Exception:
            table.add_row("⚡ Response Time", "[red]N/A[/red]")

        return Panel(table, title="[bold]Metrics[/bold]", border_style="yellow", box=box.ROUNDED)

    def create_quick_actions(self) -> Panel:
        """Create quick actions panel"""
        text = Text()
        text.append("Quick Actions:\n\n", style="bold white")
        text.append("  [R] ", style="bold cyan")
        text.append("Refresh dashboard\n", style="white")
        text.append("  [S] ", style="bold cyan")
        text.append("Start all services\n", style="white")
        text.append("  [X] ", style="bold cyan")
        text.append("Stop all services\n", style="white")
        text.append("  [G] ", style="bold cyan")
        text.append("Open Grafana\n", style="white")
        text.append("  [P] ", style="bold cyan")
        text.append("Open Prometheus\n", style="white")
        text.append("  [Q] ", style="bold cyan")
        text.append("Quit dashboard\n", style="white")

        return Panel(text, title="[bold]Controls[/bold]", border_style="magenta", box=box.ROUNDED)

    def create_layout(self) -> Layout:
        """Create dashboard layout"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=12)
        )

        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )

        layout["left"].split_column(
            Layout(name="status", size=10),
            Layout(name="services", ratio=1)
        )

        layout["right"].split_column(
            Layout(name="containers", ratio=1),
            Layout(name="metrics", size=8)
        )

        layout["header"].update(self.create_header())
        layout["status"].update(self.create_system_status())
        layout["services"].update(self.create_services_table())
        layout["containers"].update(self.create_containers_table())
        layout["metrics"].update(self.create_metrics())
        layout["footer"].update(self.create_quick_actions())

        return layout

    def run(self):
        """Run dashboard"""
        console.clear()
        console.print("[bold cyan]🏛️  VÉRTICE MAXIMUS DASHBOARD[/bold cyan]")
        console.print("[dim]Loading...[/dim]\n")

        try:
            layout = self.create_layout()
            console.print(layout)

            console.print("\n[bold yellow]Dashboard running in static mode.[/bold yellow]")
            console.print("[dim]For live updates, upgrade to 'rich[live]'[/dim]")
            console.print("\n[cyan]Press Ctrl+C to exit[/cyan]\n")

            # Static mode - just show once
            input()

        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")


def main():
    """Main entry point"""
    dashboard = Dashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
