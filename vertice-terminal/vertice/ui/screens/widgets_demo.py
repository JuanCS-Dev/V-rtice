"""
🎨 Widgets Demo Screen
Demonstração de todos os widgets primorosos
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from rich.text import Text
import random

from ..components import (
    SpinnerWidget,
    ProgressWidget,
    LogWidget,
    SparklineWidget,
    BarChartWidget,
    VerticeTable
)
from ..themes import THEME


class WidgetsDemoScreen(Screen):
    """
    Tela de demonstração dos widgets.
    Mostra todos os componentes em ação!
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("r", "refresh_demo", "Refresh Data", show=True),
        Binding("s", "toggle_spinner", "Toggle Spinner", show=True),
    ]

    CSS = """
    WidgetsDemoScreen {
        background: $background;
    }

    .demo-container {
        padding: 1 2;
        height: 1fr;
    }

    .demo-section {
        height: auto;
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
        background: $panel;
    }

    .section-title {
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._spinner = None
        self._progress = None
        self._log = None
        self._sparkline = None
        self._bar_chart = None
        self._table = None

    def compose(self) -> ComposeResult:
        """Compor layout de demonstração"""
        yield Header()

        with ScrollableContainer(classes="demo-container"):
            # Seção 1: Spinners
            with Vertical(classes="demo-section"):
                yield Static("🌀 Spinners", classes="section-title")
                with Horizontal():
                    self._spinner = SpinnerWidget("Processing data...", "dots")
                    yield self._spinner
                    yield SpinnerWidget("Analyzing threats...", "arrow")
                    yield SpinnerWidget("Scanning network...", "clock")

            # Seção 2: Progress Bars
            with Vertical(classes="demo-section"):
                yield Static("📊 Progress Bars", classes="section-title")
                self._progress = ProgressWidget(100, "Threat Scan", indeterminate=False)
                yield self._progress
                yield ProgressWidget(100, "Processing...", indeterminate=True)

            # Seção 3: Charts
            with Vertical(classes="demo-section"):
                yield Static("📈 Charts & Sparklines", classes="section-title")
                with Horizontal():
                    with Vertical():
                        # Sparkline
                        self._sparkline = SparklineWidget("Network Traffic", max_points=30)
                        yield self._sparkline

                        # Bar Chart
                        self._bar_chart = BarChartWidget({
                            "Critical": 23,
                            "High": 45,
                            "Medium": 78,
                            "Low": 12,
                            "Info": 156
                        })
                        yield self._bar_chart

            # Seção 4: Table
            with Vertical(classes="demo-section"):
                yield Static("📋 Advanced Table", classes="section-title")
                self._table = VerticeTable(show_cursor=True, zebra_stripes=True)
                yield self._table

            # Seção 5: Logs
            with Vertical(classes="demo-section"):
                yield Static("📝 Logs with Syntax Highlighting", classes="section-title")
                self._log = LogWidget(max_lines=500, show_timestamp=True)
                yield self._log

        yield Footer()

    def on_mount(self) -> None:
        """Inicializa dados de demonstração"""
        self._populate_demo_data()
        self._start_updates()

    def _populate_demo_data(self) -> None:
        """Popula widgets com dados demo"""
        # Sparkline data
        if self._sparkline:
            data = [random.randint(10, 100) for _ in range(30)]
            self._sparkline.set_data(data)

        # Table data
        if self._table:
            threats_data = [
                {"IP": "192.168.1.100", "Type": "Malware", "Severity": "High", "Blocked": True},
                {"IP": "10.0.0.45", "Type": "Phishing", "Severity": "Critical", "Blocked": True},
                {"IP": "172.16.0.23", "Type": "DDoS", "Severity": "Medium", "Blocked": False},
                {"IP": "8.8.8.8", "Type": "Scan", "Severity": "Low", "Blocked": False},
                {"IP": "1.1.1.1", "Type": "Recon", "Severity": "Info", "Blocked": False},
            ]
            self._table.load_data(threats_data, columns=["IP", "Type", "Severity", "Blocked"])

        # Logs
        if self._log:
            self._log.log_info("Widgets demo initialized")
            self._log.log_success("All components loaded successfully")
            self._log.log_warning("This is a demonstration - no real threats detected")

            # Log JSON example
            self._log.log_json({
                "event": "threat_detected",
                "ip": "192.168.1.100",
                "severity": "high",
                "timestamp": "2025-10-03T15:30:00Z"
            }, title="Threat Event")

            # Log code example
            code_example = """def analyze_threat(ip_address):
    threat = scan_ip(ip_address)
    if threat.severity == 'high':
        block_ip(ip_address)
        alert_soc_team(threat)
    return threat"""

            self._log.log_code(code_example, "python", "Threat Analysis Function")

    def _start_updates(self) -> None:
        """Inicia updates em tempo real"""
        # Simula progresso
        self.set_interval(0.1, self._update_progress)

        # Adiciona dados ao sparkline
        self.set_interval(1.0, self._update_sparkline)

    def _update_progress(self) -> None:
        """Atualiza progress bar"""
        if self._progress and self._progress.progress < self._progress.total:
            self._progress.advance(0.5)

    def _update_sparkline(self) -> None:
        """Adiciona ponto ao sparkline"""
        if self._sparkline:
            new_value = random.randint(10, 100)
            self._sparkline.add_data_point(new_value)

    def action_refresh_demo(self) -> None:
        """Refresh demo data"""
        if self._log:
            self._log.log_info("Refreshing demo data...")

        self._populate_demo_data()

        if self._progress:
            self._progress.reset()

        if self._log:
            self._log.log_success("Demo data refreshed!")

    def action_toggle_spinner(self) -> None:
        """Toggle spinner"""
        if self._spinner:
            if self._spinner.is_spinning:
                self._spinner.stop()
                if self._log:
                    self._log.log_info("Spinner stopped")
            else:
                self._spinner.start()
                if self._log:
                    self._log.log_info("Spinner started")
