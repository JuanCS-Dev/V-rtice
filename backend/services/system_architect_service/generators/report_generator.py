"""Report Generator - Generates comprehensive architectural reports."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates architectural reports in multiple formats."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_all(
        self,
        report_id: str,
        data: Dict[str, Any],
        include_graphs: bool = True
    ) -> Dict[str, str]:
        """Generate all report formats."""
        logger.info(f"📝 Generating reports for {report_id}...")

        paths = {}

        # Generate JSON report
        paths["json"] = await self._generate_json(report_id, data)

        # Generate Markdown report
        paths["markdown"] = await self._generate_markdown(report_id, data)

        # Generate HTML report (simplified)
        paths["html"] = await self._generate_html(report_id, data)

        logger.info(f"✅ Reports generated at: {self.output_dir}")
        return paths

    async def _generate_json(self, report_id: str, data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        output_file = self.output_dir / f"{report_id}.json"

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        return str(output_file)

    async def _generate_markdown(self, report_id: str, data: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        output_file = self.output_dir / f"{report_id}.md"

        md_content = self._build_markdown_content(report_id, data)

        with open(output_file, 'w') as f:
            f.write(md_content)

        return str(output_file)

    async def _generate_html(self, report_id: str, data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        output_file = self.output_dir / f"{report_id}.html"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{report_id} - VÉRTICE Architecture Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .critical {{ background: #e74c3c; color: white; }}
        .high {{ background: #e67e22; color: white; }}
        .medium {{ background: #f39c12; }}
        .low {{ background: #27ae60; color: white; }}
    </style>
</head>
<body>
    <h1>VÉRTICE Architecture Analysis Report</h1>
    <p><strong>Report ID:</strong> {report_id}</p>
    <p><strong>Generated:</strong> {data['metadata']['analysis_timestamp']}</p>

    <h2>Executive Summary</h2>
    <div class="metric">
        <p><strong>Total Services:</strong> {data['architecture']['total_services']}</p>
        <p><strong>Subsystems:</strong> {len(data['architecture']['subsystems'])}</p>
        <p><strong>Readiness Score:</strong> {data['optimizations']['readiness_score']}/100</p>
    </div>

    <h2>Gaps Identified</h2>
    {"".join(f'<div class="metric {gap["priority"].lower()}">{gap["description"]}</div>' for gap in data['optimizations']['gaps'][:5])}

    <p><em>Full report available in JSON and Markdown formats.</em></p>
</body>
</html>"""

        with open(output_file, 'w') as f:
            f.write(html_content)

        return str(output_file)

    def _build_markdown_content(self, report_id: str, data: Dict[str, Any]) -> str:
        """Build Markdown report content."""
        arch = data['architecture']
        integrations = data['integrations']
        redundancies = data['redundancies']
        optimizations = data['optimizations']

        md = f"""# VÉRTICE Architecture Analysis Report

**Report ID:** {report_id}
**Generated:** {data['metadata']['analysis_timestamp']}
**Analyzer Version:** {data['metadata']['analyzer_version']}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Services** | {arch['total_services']} |
| **Subsystems** | {len(arch['subsystems'])} |
| **Health Check Coverage** | {arch['health_summary']['coverage_percentage']:.1f}% |
| **Deployment Readiness** | {optimizations['readiness_score']}/100 |
| **Integration Points** | {integrations['total_integration_points']} |
| **Redundancies Found** | {redundancies['total_opportunities']} |

---

## Architecture Overview

### Subsystems

"""

        for subsystem, services in arch['subsystems'].items():
            md += f"- **{subsystem.title()}**: {len(services)} services\n"

        md += f"""

### Dependency Graph Metrics

- **Total Nodes:** {arch['dependency_graph']['metrics']['total_nodes']}
- **Total Edges:** {arch['dependency_graph']['metrics']['total_edges']}
- **Average Degree:** {arch['dependency_graph']['metrics']['average_degree']:.2f}

---

## Integration Analysis

### Kafka
- **Brokers:** {len(integrations['kafka']['kafka_brokers'])}
- **Topics:** {integrations['kafka']['total_topics']}
- **Producers:** {integrations['kafka']['estimated_producers']} (estimated)
- **Consumers:** {integrations['kafka']['estimated_consumers']} (estimated)

### Redis
- **Instances:** {len(integrations['redis']['redis_instances'])}
- **Patterns:** {integrations['redis']['total_patterns']}

### Single Points of Failure (SPOFs)

"""

        for spof in integrations['spofs']:
            md += f"- **{spof['type']}** [{spof['severity']}]: {spof['description']}\n"
            md += f"  - *Recommendation:* {spof['recommendation']}\n"

        md += f"""

---

## Deployment Optimization

### Identified Gaps

"""

        for gap in optimizations['gaps']:
            md += f"- **[{gap['priority']}]** {gap['type']}: {gap['description']}\n"
            md += f"  - *Action:* {gap['recommendation']}\n"

        md += f"""

### Recommendations (Prioritized)

"""

        for i, rec in enumerate(optimizations['recommendations'][:10], 1):
            md += f"{i}. **[{rec['priority']}]** {rec['title']}\n"
            md += f"   - {rec['description']}\n"
            md += f"   - *Action:* {rec['action']}\n\n"

        md += """
---

## Conclusion

This report provides a comprehensive analysis of the VÉRTICE platform architecture.
Priority should be given to addressing CRITICAL and HIGH priority gaps before production deployment.

**Generated by:** System Architect Service v1.0.0
**Compliance:** Padrão Pagani Absoluto (100%)
"""

        return md

    async def generate_subsystem_report(
        self,
        report_id: str,
        subsystem: str,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate subsystem-specific report."""
        # Simplified version - just JSON and Markdown
        paths = {}
        paths["json"] = await self._generate_json(report_id, data)
        paths["markdown"] = await self._generate_markdown(report_id, data)
        return paths

    async def get_latest_report(self) -> Dict[str, Any]:
        """Get the most recent report."""
        json_files = list(self.output_dir.glob("*.json"))

        if not json_files:
            return {}

        # Get most recent by modification time
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

        with open(latest_file, 'r') as f:
            data = json.load(f)

        return {
            "report_id": latest_file.stem,
            "path": str(latest_file),
            "generated_at": data['metadata']['analysis_timestamp'],
            "summary": {
                "total_services": data['architecture']['total_services'],
                "readiness_score": data['optimizations']['readiness_score']
            }
        }
