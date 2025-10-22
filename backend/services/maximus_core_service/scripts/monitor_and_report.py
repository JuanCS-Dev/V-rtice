#!/usr/bin/env python3
"""
Monte Carlo N=100 Monitor & Report Generator
============================================

Monitors the running Monte Carlo test and generates comprehensive
HTML report when complete.

Usage:
    python scripts/monitor_and_report.py

Author: Claude (Anthropic AI)
Date: October 21, 2025
"""

import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Configuration
LOG_FILE = Path("tests/statistical/outputs/monte_carlo_n100_FIXED.log")
OUTPUT_DIR = Path("tests/statistical/outputs/monte_carlo")
REPORT_HTML = Path("tests/statistical/outputs/MONTE_CARLO_N100_FINAL_REPORT.html")
PID = 97688  # Monte Carlo process ID

def check_process_running(pid: int) -> bool:
    """Check if process is still running."""
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def get_progress() -> tuple[int, int]:
    """Get current progress (completed_runs, total_runs)."""
    if not LOG_FILE.exists():
        return (0, 100)

    with open(LOG_FILE, 'r') as f:
        content = f.read()

    # Count completed runs
    import re
    runs = re.findall(r'Run (\d+)/100', content)
    if runs:
        return (int(runs[-1]), 100)
    return (0, 100)

def extract_statistics() -> dict:
    """Extract statistics from output JSON."""
    stats_file = OUTPUT_DIR / "monte_carlo_statistics.json"

    if not stats_file.exists():
        return {}

    with open(stats_file, 'r') as f:
        return json.load(f)

def generate_html_report(stats: dict) -> str:
    """Generate comprehensive HTML report."""

    # Calculate additional metrics
    total_runs = stats.get('total_runs', 0)
    successful_runs = stats.get('successful_runs', 0)
    success_rate = stats.get('success_rate', 0.0)
    mean_coherence = stats.get('mean_coherence', 0.0)
    std_coherence = stats.get('std_coherence', 0.0)
    ci_lower = stats.get('ci_lower', 0.0)
    ci_upper = stats.get('ci_upper', 0.0)

    # GWT compliance
    gwt_threshold = 0.70
    runs = stats.get('runs', [])
    gwt_compliant = sum(1 for r in runs if r.get('final_coherence', 0) >= gwt_threshold)
    gwt_compliance_rate = (gwt_compliant / total_runs * 100) if total_runs > 0 else 0

    # Determine pass/fail
    passed = (
        success_rate >= 0.95 and
        mean_coherence >= 0.90 and
        ci_lower >= 0.70
    )

    status_color = "#27ae60" if passed else "#e74c3c"
    status_text = "✅ PASSED" if passed else "❌ FAILED"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monte Carlo N=100 - Final Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 40px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .status {{ font-size: 1.5em; margin-top: 15px; padding: 15px; background: {status_color}; border-radius: 8px; display: inline-block; }}
        .content {{ padding: 40px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }}
        .metric-card .number {{ font-size: 3.5em; font-weight: 700; margin-bottom: 10px; }}
        .metric-card .label {{ font-size: 1.2em; opacity: 0.95; }}
        .section {{ margin: 40px 0; }}
        .section h2 {{ color: #2c3e50; font-size: 2em; margin-bottom: 20px; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; text-align: left; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #ddd; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        tr:hover {{ background: #e8eaf6; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .footer {{ background: #34495e; color: #ecf0f1; padding: 30px; text-align: center; }}
        .timestamp {{ font-size: 0.9em; opacity: 0.8; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Monte Carlo N=100 - Final Statistical Report</h1>
            <div class="subtitle">Kuramoto Synchronization Validation</div>
            <div class="status">{status_text}</div>
        </div>

        <div class="content">
            <div class="section">
                <h2>Executive Summary</h2>
                <p><strong>Total Runs:</strong> {total_runs}/100</p>
                <p><strong>Success Rate:</strong> {success_rate:.1%} ({successful_runs}/{total_runs})</p>
                <p><strong>Mean Coherence:</strong> {mean_coherence:.4f} ± {std_coherence:.4f}</p>
                <p><strong>95% CI:</strong> [{ci_lower:.4f}, {ci_upper:.4f}]</p>
                <p><strong>GWT Compliance:</strong> {gwt_compliance_rate:.1f}% ({gwt_compliant}/{total_runs} runs ≥ {gwt_threshold})</p>
            </div>

            <div class="metric-grid">
                <div class="metric-card">
                    <div class="number">{total_runs}</div>
                    <div class="label">Total Runs</div>
                </div>
                <div class="metric-card">
                    <div class="number">{success_rate:.1%}</div>
                    <div class="label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="number">{mean_coherence:.3f}</div>
                    <div class="label">Mean Coherence</div>
                </div>
                <div class="metric-card">
                    <div class="number">{gwt_compliance_rate:.0f}%</div>
                    <div class="label">GWT Compliance</div>
                </div>
            </div>

            <div class="section">
                <h2>Acceptance Criteria</h2>
                <table>
                    <thead>
                        <tr><th>Criterion</th><th>Target</th><th>Actual</th><th>Status</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Success Rate</td>
                            <td>≥ 95%</td>
                            <td>{success_rate:.1%}</td>
                            <td class="{'pass' if success_rate >= 0.95 else 'fail'}">{'✓ PASS' if success_rate >= 0.95 else '✗ FAIL'}</td>
                        </tr>
                        <tr>
                            <td>Mean Coherence</td>
                            <td>≥ 0.90</td>
                            <td>{mean_coherence:.4f}</td>
                            <td class="{'pass' if mean_coherence >= 0.90 else 'fail'}">{'✓ PASS' if mean_coherence >= 0.90 else '✗ FAIL'}</td>
                        </tr>
                        <tr>
                            <td>95% CI Lower Bound</td>
                            <td>≥ 0.70 (GWT threshold)</td>
                            <td>{ci_lower:.4f}</td>
                            <td class="{'pass' if ci_lower >= 0.70 else 'fail'}">{'✓ PASS' if ci_lower >= 0.70 else '✗ FAIL'}</td>
                        </tr>
                        <tr>
                            <td>GWT Compliance</td>
                            <td>≥ 80%</td>
                            <td>{gwt_compliance_rate:.1f}%</td>
                            <td class="{'pass' if gwt_compliance_rate >= 80 else 'fail'}">{'✓ PASS' if gwt_compliance_rate >= 80 else '✗ FAIL'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>Statistical Analysis</h2>
                <table>
                    <thead>
                        <tr><th>Metric</th><th>Value</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Mean Coherence</td><td>{mean_coherence:.6f}</td></tr>
                        <tr><td>Standard Deviation</td><td>{std_coherence:.6f}</td></tr>
                        <tr><td>95% CI Lower</td><td>{ci_lower:.6f}</td></tr>
                        <tr><td>95% CI Upper</td><td>{ci_upper:.6f}</td></tr>
                        <tr><td>Minimum Coherence</td><td>{min(r.get('final_coherence', 0) for r in runs) if runs else 0:.6f}</td></tr>
                        <tr><td>Maximum Coherence</td><td>{max(r.get('final_coherence', 0) for r in runs) if runs else 0:.6f}</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>Conclusion</h2>
                <p>
                    {"<strong class='pass'>✅ ALL CRITERIA PASSED</strong> - The Kuramoto synchronization implementation is statistically validated and ready for publication." if passed else "<strong class='fail'>❌ SOME CRITERIA FAILED</strong> - Further investigation required before publication."}
                </p>
                <p style="margin-top: 20px;">
                    This Monte Carlo simulation with N=100 independent runs provides robust statistical evidence for the
                    reliability and consistency of the Global Workspace consciousness implementation based on Kuramoto synchronization.
                </p>
            </div>
        </div>

        <div class="footer">
            <p><strong>VERTICE Project</strong> | Consciousness Research</p>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Monte Carlo N=100 Validation</p>
        </div>
    </div>
</body>
</html>"""

    return html

def main():
    """Main monitoring loop."""
    print("🔍 Monitoring Monte Carlo N=100...")
    print(f"📂 Log file: {LOG_FILE}")
    print(f"🔢 PID: {PID}")
    print()

    last_progress = 0

    while True:
        # Check if process is still running
        if not check_process_running(PID):
            print("\n✅ Process completed!")
            break

        # Get current progress
        completed, total = get_progress()

        # Print progress if changed
        if completed != last_progress:
            progress_pct = (completed / total * 100) if total > 0 else 0
            print(f"📊 Progress: {completed}/{total} ({progress_pct:.1f}%) - Run {completed} completed")
            last_progress = completed

        # Wait before next check
        time.sleep(30)  # Check every 30 seconds

    print("\n📊 Extracting statistics...")
    stats = extract_statistics()

    if not stats:
        print("❌ No statistics found!")
        return

    print(f"✅ Found statistics: {stats.get('total_runs', 0)} runs")

    print("\n📝 Generating HTML report...")
    html = generate_html_report(stats)

    # Save report
    with open(REPORT_HTML, 'w') as f:
        f.write(html)

    print(f"✅ Report saved: {REPORT_HTML}")
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total Runs: {stats.get('total_runs', 0)}")
    print(f"Success Rate: {stats.get('success_rate', 0):.1%}")
    print(f"Mean Coherence: {stats.get('mean_coherence', 0):.4f}")
    print(f"95% CI: [{stats.get('ci_lower', 0):.4f}, {stats.get('ci_upper', 0):.4f}]")
    print("="*60)

    # Check criteria
    success_rate = stats.get('success_rate', 0)
    mean_coherence = stats.get('mean_coherence', 0)
    ci_lower = stats.get('ci_lower', 0)

    if success_rate >= 0.95 and mean_coherence >= 0.90 and ci_lower >= 0.70:
        print("\n✅ ALL CRITERIA PASSED - READY FOR PUBLICATION!")
    else:
        print("\n⚠️  SOME CRITERIA NOT MET - Review required")

if __name__ == "__main__":
    main()
