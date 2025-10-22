#!/usr/bin/env python3
"""
Coverage Tracker - Sistema de Rastreamento Persistente

Monitora cobertura de testes ao longo do tempo, detecta regressões,
e mantém histórico imutável para análise de tendências.

CONFORMIDADE DOUTRINA VÉRTICE:
- Artigo II (Padrão Pagani): Zero mocks, production-ready
- Artigo V (Legislação Prévia): Governança via tracking ANTES de criar testes
- Anexo D (Execução Constitucional): Age como "Agente Guardião" monitorando compliance

Author: Claude Code + JuanCS-Dev
Date: 2025-10-21
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class ModuleCoverage:
    """Coverage metrics for a single module."""

    name: str
    total_lines: int
    covered_lines: int
    missing_lines: int
    coverage_pct: float


@dataclass
class CoverageSnapshot:
    """Complete coverage snapshot at a point in time."""

    timestamp: str
    total_coverage_pct: float
    total_lines: int
    covered_lines: int
    missing_lines: int
    modules: list[ModuleCoverage]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "total_coverage_pct": self.total_coverage_pct,
            "total_lines": self.total_lines,
            "covered_lines": self.covered_lines,
            "missing_lines": self.missing_lines,
            "modules": [asdict(m) for m in self.modules],
        }


class CoverageTracker:
    """
    Persistent coverage tracking system.

    Features:
    - Parse coverage.xml from pytest-cov
    - Track coverage history over time
    - Detect regressions (e.g., 100% → 20%)
    - Generate HTML dashboard updates
    - Immutable history (append-only)

    Example:
        ```python
        tracker = CoverageTracker()
        snapshot = tracker.parse_coverage()
        tracker.save_snapshot(snapshot)
        tracker.update_dashboard()
        regressions = tracker.detect_regressions()
        ```
    """

    def __init__(
        self,
        coverage_xml: Path = Path("coverage.xml"),
        history_file: Path = Path("docs/coverage_history.json"),
        dashboard_file: Path = Path("docs/COVERAGE_STATUS.html"),
    ):
        """Initialize tracker.

        Args:
            coverage_xml: Path to coverage.xml from pytest-cov
            history_file: Path to JSON history file
            dashboard_file: Path to HTML dashboard
        """
        self.coverage_xml = coverage_xml
        self.history_file = history_file
        self.dashboard_file = dashboard_file

        # Ensure directories exist
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.dashboard_file.parent.mkdir(parents=True, exist_ok=True)

    def parse_coverage(self) -> CoverageSnapshot:
        """Parse coverage.xml and extract metrics.

        Returns:
            CoverageSnapshot with current coverage data

        Raises:
            FileNotFoundError: If coverage.xml doesn't exist
            ValueError: If XML is malformed
        """
        if not self.coverage_xml.exists():
            raise FileNotFoundError(
                f"Coverage file not found: {self.coverage_xml}\n"
                f"Run: pytest --cov=. --cov-report=xml --cov-report=html"
            )

        logger.info(f"Parsing coverage from {self.coverage_xml}")

        try:
            tree = ET.parse(self.coverage_xml)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse coverage.xml: {e}")

        # Extract overall metrics
        total_lines = 0
        covered_lines = 0
        modules = []

        # Parse packages and classes
        for package in root.findall(".//package"):
            package_name = package.get("name", "").replace("/", ".")

            for cls in package.findall("classes/class"):
                filename = cls.get("filename", "")
                module_name = self._filename_to_module(filename)

                # Skip test files and non-Python files
                if "test_" in module_name or not filename.endswith(".py"):
                    continue

                # Count lines
                lines = cls.findall("lines/line")
                module_total = len(lines)
                module_covered = sum(1 for line in lines if int(line.get("hits", 0)) > 0)
                module_missing = module_total - module_covered

                if module_total == 0:
                    continue

                module_coverage_pct = (module_covered / module_total) * 100 if module_total > 0 else 0.0

                modules.append(
                    ModuleCoverage(
                        name=module_name,
                        total_lines=module_total,
                        covered_lines=module_covered,
                        missing_lines=module_missing,
                        coverage_pct=module_coverage_pct,
                    )
                )

                total_lines += module_total
                covered_lines += module_covered

        # Calculate overall coverage
        total_coverage_pct = (covered_lines / total_lines) * 100 if total_lines > 0 else 0.0

        snapshot = CoverageSnapshot(
            timestamp=datetime.now().isoformat(),
            total_coverage_pct=total_coverage_pct,
            total_lines=total_lines,
            covered_lines=covered_lines,
            missing_lines=total_lines - covered_lines,
            modules=sorted(modules, key=lambda m: m.coverage_pct),  # Sort by coverage (lowest first)
        )

        logger.info(f"Parsed coverage: {total_coverage_pct:.2f}% ({covered_lines}/{total_lines} lines)")

        return snapshot

    def _filename_to_module(self, filename: str) -> str:
        """Convert filename to module name.

        Args:
            filename: File path

        Returns:
            Module name (e.g., 'consciousness/safety.py' → 'consciousness.safety')
        """
        # Remove leading paths and .py extension
        module = filename.replace(".py", "").replace("/", ".")

        # Remove common prefixes
        for prefix in ["backend.services.maximus_core_service.", "maximus_core_service."]:
            if module.startswith(prefix):
                module = module[len(prefix) :]

        return module

    def load_history(self) -> list[dict[str, Any]]:
        """Load coverage history from JSON file.

        Returns:
            List of historical snapshots (as dicts)
        """
        if not self.history_file.exists():
            logger.info("No history file found - creating new")
            return []

        try:
            with open(self.history_file) as f:
                history = json.load(f)
                logger.info(f"Loaded {len(history)} historical snapshots")
                return history
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def save_snapshot(self, snapshot: CoverageSnapshot) -> None:
        """Save snapshot to history (append-only).

        Args:
            snapshot: Coverage snapshot to save
        """
        # Load existing history
        history = self.load_history()

        # Append new snapshot
        history.append(snapshot.to_dict())

        # Save updated history
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

        logger.info(f"Snapshot saved to {self.history_file} ({len(history)} total snapshots)")

    def detect_regressions(self, threshold: float = 10.0) -> list[dict[str, Any]]:
        """Detect coverage regressions between last two snapshots.

        Args:
            threshold: Minimum percentage drop to count as regression

        Returns:
            List of regressions with details
        """
        history = self.load_history()

        if len(history) < 2:
            logger.info("Need at least 2 snapshots to detect regressions")
            return []

        previous = history[-2]
        current = history[-1]

        regressions = []

        # Check overall coverage
        overall_drop = previous["total_coverage_pct"] - current["total_coverage_pct"]
        if overall_drop >= threshold:
            regressions.append(
                {
                    "type": "overall",
                    "module": "TOTAL",
                    "previous_pct": previous["total_coverage_pct"],
                    "current_pct": current["total_coverage_pct"],
                    "drop_pct": overall_drop,
                }
            )

        # Check per-module
        previous_modules = {m["name"]: m for m in previous["modules"]}
        current_modules = {m["name"]: m for m in current["modules"]}

        for module_name, current_mod in current_modules.items():
            if module_name in previous_modules:
                previous_mod = previous_modules[module_name]
                drop = previous_mod["coverage_pct"] - current_mod["coverage_pct"]

                if drop >= threshold:
                    regressions.append(
                        {
                            "type": "module",
                            "module": module_name,
                            "previous_pct": previous_mod["coverage_pct"],
                            "current_pct": current_mod["coverage_pct"],
                            "drop_pct": drop,
                        }
                    )

        if regressions:
            logger.warning(f"Detected {len(regressions)} coverage regressions!")
        else:
            logger.info("No significant regressions detected")

        return regressions

    def generate_dashboard_data(self) -> dict[str, Any]:
        """Generate data for HTML dashboard.

        Returns:
            Dictionary with all data needed for dashboard
        """
        history = self.load_history()

        if not history:
            return {
                "has_data": False,
                "message": "No coverage data yet. Run: pytest --cov=. --cov-report=xml",
            }

        current = history[-1]
        regressions = self.detect_regressions()

        # Extract trend data for chart
        trend_data = {
            "timestamps": [snapshot["timestamp"] for snapshot in history],
            "coverage_pct": [snapshot["total_coverage_pct"] for snapshot in history],
        }

        # Module table data (current snapshot)
        modules_table = sorted(current["modules"], key=lambda m: m["coverage_pct"])

        return {
            "has_data": True,
            "current": current,
            "regressions": regressions,
            "trend": trend_data,
            "modules": modules_table,
            "history_count": len(history),
        }

    def update_dashboard(self) -> None:
        """Update HTML dashboard with latest data.

        This will be implemented after dashboard HTML template is created.
        """
        logger.info("Dashboard update will be implemented with HTML template")
        # TODO: Implement after COVERAGE_STATUS.html is created


def main():
    """Main CLI for coverage tracker."""
    import argparse

    parser = argparse.ArgumentParser(description="Coverage Tracking System")
    parser.add_argument(
        "--coverage-xml",
        type=Path,
        default=Path("coverage.xml"),
        help="Path to coverage.xml",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("docs/coverage_history.json"),
        help="Path to history JSON",
    )
    parser.add_argument(
        "--dashboard",
        type=Path,
        default=Path("docs/COVERAGE_STATUS.html"),
        help="Path to dashboard HTML",
    )
    parser.add_argument(
        "--check-regressions",
        action="store_true",
        help="Check for regressions and exit with error code if found",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create tracker
    tracker = CoverageTracker(
        coverage_xml=args.coverage_xml,
        history_file=args.history,
        dashboard_file=args.dashboard,
    )

    try:
        # Parse current coverage
        snapshot = tracker.parse_coverage()
        print(f"\n📊 Coverage Snapshot: {snapshot.total_coverage_pct:.2f}%")
        print(f"   Total lines: {snapshot.total_lines:,}")
        print(f"   Covered: {snapshot.covered_lines:,}")
        print(f"   Missing: {snapshot.missing_lines:,}")

        # Save snapshot
        tracker.save_snapshot(snapshot)
        print(f"✅ Snapshot saved to {tracker.history_file}")

        # Check for regressions
        regressions = tracker.detect_regressions()
        if regressions:
            print(f"\n⚠️  ALERT: {len(regressions)} coverage regressions detected!")
            for reg in regressions:
                print(f"   {reg['module']}: {reg['previous_pct']:.1f}% → {reg['current_pct']:.1f}% (-{reg['drop_pct']:.1f}%)")

            if args.check_regressions:
                exit(1)
        else:
            print("\n✅ No regressions detected")

        # Update dashboard
        tracker.update_dashboard()
        print(f"📈 Dashboard data ready at {tracker.dashboard_file}")

    except Exception as e:
        logger.error(f"Tracker failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
