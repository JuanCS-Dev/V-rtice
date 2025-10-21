#!/usr/bin/env python3
"""
Coverage Report Analyzer & Delta Calculator
Tracks coverage progress and compares against baseline

Author: Claude Code + JuanCS-Dev
Date: 2025-10-20
Usage: python scripts/coverage_report.py [--baseline htmlcov_baseline] [--current htmlcov]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class CoverageAnalyzer:
    """Analyze coverage reports and calculate deltas."""

    def __init__(self, current_report: Path, baseline_report: Optional[Path] = None):
        """
        Initialize analyzer.

        Args:
            current_report: Path to current coverage htmlcov directory
            baseline_report: Path to baseline coverage (optional)
        """
        self.current_report = current_report
        self.baseline_report = baseline_report

    def load_coverage_data(self, report_path: Path) -> Dict:
        """
        Load coverage data from status.json.

        Args:
            report_path: Path to htmlcov directory

        Returns:
            Coverage data dict
        """
        status_file = report_path / "status.json"
        if not status_file.exists():
            raise FileNotFoundError(f"Coverage status file not found: {status_file}")

        with open(status_file, 'r') as f:
            data = json.load(f)

        return data

    def calculate_totals(self, coverage_data: Dict) -> Dict[str, int]:
        """
        Calculate total coverage statistics.

        Args:
            coverage_data: Coverage data from status.json

        Returns:
            Dict with totals
        """
        total_statements = 0
        total_missing = 0
        total_covered = 0
        file_count = 0

        for filename, filedata in coverage_data.get('files', {}).items():
            nums = filedata.get('index', {}).get('nums', {})
            statements = nums.get('n_statements', 0)
            missing = nums.get('n_missing', 0)

            total_statements += statements
            total_missing += missing
            file_count += 1

        total_covered = total_statements - total_missing
        coverage_pct = (total_covered / total_statements * 100) if total_statements > 0 else 0

        return {
            'files': file_count,
            'statements': total_statements,
            'covered': total_covered,
            'missing': total_missing,
            'coverage_pct': coverage_pct
        }

    def analyze_by_module(self, coverage_data: Dict) -> List[Tuple[str, Dict, float]]:
        """
        Group coverage by module/directory.

        Args:
            coverage_data: Coverage data

        Returns:
            List of (module_name, stats, coverage_pct) tuples
        """
        modules = defaultdict(lambda: {'files': 0, 'statements': 0, 'missing': 0, 'covered': 0})

        for filename, filedata in coverage_data.get('files', {}).items():
            path = filedata.get('index', {}).get('file', '')
            nums = filedata.get('index', {}).get('nums', {})

            # Extract module name (first directory or root)
            module = path.split('/')[0] if '/' in path else 'root'

            modules[module]['files'] += 1
            modules[module]['statements'] += nums.get('n_statements', 0)
            modules[module]['missing'] += nums.get('n_missing', 0)

        # Calculate coverage and sort
        module_stats = []
        for module, stats in modules.items():
            stats['covered'] = stats['statements'] - stats['missing']
            coverage = (stats['covered'] / stats['statements'] * 100) if stats['statements'] > 0 else 0
            module_stats.append((module, stats, coverage))

        module_stats.sort(key=lambda x: x[2], reverse=True)
        return module_stats

    def calculate_delta(self) -> Dict:
        """
        Calculate coverage delta between baseline and current.

        Returns:
            Dict with delta statistics
        """
        if not self.baseline_report:
            return {}

        baseline_data = self.load_coverage_data(self.baseline_report)
        current_data = self.load_coverage_data(self.current_report)

        baseline_totals = self.calculate_totals(baseline_data)
        current_totals = self.calculate_totals(current_data)

        return {
            'baseline': baseline_totals,
            'current': current_totals,
            'delta_coverage': current_totals['coverage_pct'] - baseline_totals['coverage_pct'],
            'delta_covered': current_totals['covered'] - baseline_totals['covered'],
            'delta_statements': current_totals['statements'] - baseline_totals['statements']
        }

    def print_report(self, show_modules: bool = True, top_n: int = 20):
        """
        Print formatted coverage report.

        Args:
            show_modules: Whether to show per-module breakdown
            top_n: Number of top modules to show
        """
        current_data = self.load_coverage_data(self.current_report)
        totals = self.calculate_totals(current_data)

        print("=" * 80)
        print("📊 COVERAGE REPORT")
        print("=" * 80)
        print(f"Total Files:      {totals['files']:,}")
        print(f"Total Statements: {totals['statements']:,}")
        print(f"Covered Lines:    {totals['covered']:,}")
        print(f"Missing Lines:    {totals['missing']:,}")
        print(f"Coverage:         {totals['coverage_pct']:.2f}%")
        print("=" * 80)

        # Delta if baseline available
        if self.baseline_report:
            delta = self.calculate_delta()
            delta_cov = delta['delta_coverage']
            delta_sign = "+" if delta_cov > 0 else ""
            delta_emoji = "📈" if delta_cov > 0 else "📉" if delta_cov < 0 else "➡️"

            print(f"\n{delta_emoji} DELTA vs BASELINE:")
            print(f"   Coverage:  {delta_sign}{delta_cov:.2f}%")
            print(f"   Lines:     +{delta['delta_covered']:,}")
            print(f"   Statements: +{delta['delta_statements']:,}")

            # Check if meets minimum delta
            if delta_cov < 5.0 and delta['current']['coverage_pct'] < 90:
                print(f"\n⚠️  WARNING: Coverage delta ({delta_cov:.2f}%) below threshold (5%)")

        # Module breakdown
        if show_modules:
            print(f"\n📦 COVERAGE BY MODULE (Top {top_n}):")
            print("=" * 80)
            print(f"{'Module':<35} {'Files':>6} {'Lines':>8} {'Covered':>8} {'Coverage':>10}")
            print("-" * 80)

            module_stats = self.analyze_by_module(current_data)
            for module, stats, cov in module_stats[:top_n]:
                # Color code coverage
                if cov >= 90:
                    emoji = "✅"
                elif cov >= 70:
                    emoji = "🟡"
                elif cov >= 50:
                    emoji = "🟠"
                else:
                    emoji = "🔴"

                print(f"{emoji} {module:<33} {stats['files']:>6} {stats['statements']:>8,} "
                      f"{stats['covered']:>8,} {cov:>9.2f}%")

        # Coverage targets
        print(f"\n🎯 TARGETS:")
        print("=" * 80)
        for target in [70, 80, 85, 90]:
            lines_needed = int((target / 100) * totals['statements'])
            additional = lines_needed - totals['covered']

            if additional <= 0:
                print(f"   {target}% ✅ ACHIEVED (target: {lines_needed:,})")
            else:
                print(f"   {target}% 🎯 Need +{additional:,} lines (target: {lines_needed:,})")

    def generate_badge(self, output_path: Path):
        """
        Generate shields.io badge URL for coverage.

        Args:
            output_path: Where to save badge markdown
        """
        totals = self.calculate_totals(self.load_coverage_data(self.current_report))
        coverage = totals['coverage_pct']

        # Color based on coverage
        if coverage >= 90:
            color = "brightgreen"
        elif coverage >= 70:
            color = "yellow"
        elif coverage >= 50:
            color = "orange"
        else:
            color = "red"

        badge_url = f"https://img.shields.io/badge/coverage-{coverage:.1f}%25-{color}"
        badge_md = f"![Coverage]({badge_url})"

        with open(output_path, 'w') as f:
            f.write(badge_md)

        print(f"\n🏷️  Badge generated: {output_path}")
        print(f"   Markdown: {badge_md}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze coverage reports and calculate deltas"
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=Path("htmlcov"),
        help="Path to current coverage report (default: htmlcov)"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Path to baseline coverage report for delta calculation"
    )
    parser.add_argument(
        "--modules",
        action="store_true",
        help="Show per-module breakdown"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Number of top modules to show (default: 20)"
    )
    parser.add_argument(
        "--badge",
        type=Path,
        help="Generate coverage badge markdown to file"
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        help="Fail if coverage is below this percentage"
    )

    args = parser.parse_args()

    # Validate paths
    if not args.current.exists():
        print(f"❌ Current coverage report not found: {args.current}")
        sys.exit(1)

    if args.baseline and not args.baseline.exists():
        print(f"❌ Baseline coverage report not found: {args.baseline}")
        sys.exit(1)

    # Analyze
    analyzer = CoverageAnalyzer(args.current, args.baseline)

    try:
        analyzer.print_report(show_modules=args.modules, top_n=args.top_n)

        # Generate badge if requested
        if args.badge:
            analyzer.generate_badge(args.badge)

        # Check threshold
        if args.fail_under:
            totals = analyzer.calculate_totals(analyzer.load_coverage_data(args.current))
            if totals['coverage_pct'] < args.fail_under:
                print(f"\n❌ FAILED: Coverage {totals['coverage_pct']:.2f}% below threshold {args.fail_under}%")
                sys.exit(1)
            else:
                print(f"\n✅ PASSED: Coverage {totals['coverage_pct']:.2f}% meets threshold {args.fail_under}%")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    from typing import Optional
    main()
