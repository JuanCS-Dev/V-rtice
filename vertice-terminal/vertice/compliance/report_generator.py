"""
📊 Report Generator - Geração de relatórios de compliance e auditoria

Suporta múltiplos formatos:
- JSON (machine-readable)
- HTML (web-based reports)
- PDF (formal documentation)
- CSV (data export)
- Markdown (documentation)

Report Types:
- Compliance Assessment Reports
- Audit Trail Reports
- Gap Analysis Reports
- Control Status Reports
- Metrics & KPI Reports
- Executive Summaries
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Formatos de relatório"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"
    MARKDOWN = "markdown"


class ReportType(Enum):
    """Tipos de relatório"""
    COMPLIANCE_ASSESSMENT = "compliance_assessment"
    AUDIT_TRAIL = "audit_trail"
    GAP_ANALYSIS = "gap_analysis"
    CONTROL_STATUS = "control_status"
    METRICS_DASHBOARD = "metrics_dashboard"
    EXECUTIVE_SUMMARY = "executive_summary"
    INCIDENT_SUMMARY = "incident_summary"


@dataclass
class Report:
    """
    Relatório de compliance/auditoria

    Attributes:
        id: Unique report ID
        report_type: Type of report
        title: Report title
        generated_at: When generated
        generated_by: Who generated
        time_period: Reporting period
        data: Report data
        format: Output format
        output_path: Where saved
        metadata: Additional metadata
    """
    id: str
    report_type: ReportType
    title: str
    generated_at: datetime
    generated_by: str

    # Time period
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Data
    data: Dict[str, Any] = field(default_factory=dict)

    # Output
    format: ReportFormat = ReportFormat.JSON
    output_path: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class ReportGenerator:
    """
    Compliance & Audit Report Generator

    Features:
    - Multi-format report generation
    - Template-based rendering
    - Data aggregation
    - Chart generation
    - Executive summaries
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        output_dir: Optional[Path] = None,
    ):
        """
        Args:
            backend_url: URL do reporting_service
            use_backend: Se True, usa backend
            output_dir: Output directory for reports
        """
        self.backend_url = backend_url or "http://localhost:8016"
        self.use_backend = use_backend

        # Output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.home() / ".vertice" / "reports"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Report registry
        self.reports: List[Report] = []

    def generate_compliance_assessment_report(
        self,
        assessment: Any,  # Assessment from ComplianceEngine
        format: ReportFormat = ReportFormat.HTML,
        generated_by: str = "system",
    ) -> Report:
        """
        Gera relatório de assessment de compliance

        Args:
            assessment: Assessment object
            format: Output format
            generated_by: Who generated

        Returns:
            Report object
        """
        import uuid

        report = Report(
            id=f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            report_type=ReportType.COMPLIANCE_ASSESSMENT,
            title=f"Compliance Assessment: {assessment.framework.value.upper()}",
            generated_at=datetime.now(),
            generated_by=generated_by,
            period_start=assessment.assessment_date,
            period_end=assessment.assessment_date,
            format=format,
        )

        # Build report data
        report.data = {
            "assessment_id": assessment.id,
            "framework": assessment.framework.value,
            "assessment_date": assessment.assessment_date.isoformat(),
            "assessor": assessment.assessor,
            "summary": {
                "total_controls": assessment.total_controls,
                "implemented": assessment.implemented,
                "partially_implemented": assessment.partially_implemented,
                "not_implemented": assessment.not_implemented,
                "not_applicable": assessment.not_applicable,
                "compliance_score": assessment.compliance_score,
            },
            "gaps": assessment.gaps,
            "recommendations": assessment.recommendations,
            "controls_assessed": assessment.controls_assessed,
        }

        # Generate output based on format
        if format == ReportFormat.JSON:
            report.output_path = self._generate_json_report(report)

        elif format == ReportFormat.HTML:
            report.output_path = self._generate_html_compliance_report(report)

        elif format == ReportFormat.MARKDOWN:
            report.output_path = self._generate_markdown_compliance_report(report)

        elif format == ReportFormat.CSV:
            report.output_path = self._generate_csv_compliance_report(report)

        # Register report
        self.reports.append(report)

        logger.info(
            f"Generated compliance assessment report: {report.id} "
            f"({format.value})"
        )

        return report

    def generate_gap_analysis_report(
        self,
        gap_analysis: Dict[str, Any],
        framework: str,
        format: ReportFormat = ReportFormat.HTML,
        generated_by: str = "system",
    ) -> Report:
        """
        Gera relatório de gap analysis

        Args:
            gap_analysis: Gap analysis dict
            framework: Framework name
            format: Output format
            generated_by: Who generated

        Returns:
            Report object
        """
        import uuid

        report = Report(
            id=f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            report_type=ReportType.GAP_ANALYSIS,
            title=f"Gap Analysis: {framework.upper()}",
            generated_at=datetime.now(),
            generated_by=generated_by,
            format=format,
        )

        report.data = gap_analysis

        # Generate output
        if format == ReportFormat.JSON:
            report.output_path = self._generate_json_report(report)

        elif format == ReportFormat.HTML:
            report.output_path = self._generate_html_gap_report(report)

        elif format == ReportFormat.MARKDOWN:
            report.output_path = self._generate_markdown_gap_report(report)

        self.reports.append(report)

        logger.info(f"Generated gap analysis report: {report.id}")

        return report

    def generate_audit_trail_report(
        self,
        events: List[Any],  # AuditEvent list
        period_start: datetime,
        period_end: datetime,
        format: ReportFormat = ReportFormat.HTML,
        generated_by: str = "system",
    ) -> Report:
        """
        Gera relatório de audit trail

        Args:
            events: List of audit events
            period_start: Start of reporting period
            period_end: End of reporting period
            format: Output format
            generated_by: Who generated

        Returns:
            Report object
        """
        import uuid

        report = Report(
            id=f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            report_type=ReportType.AUDIT_TRAIL,
            title=f"Audit Trail Report: {period_start.date()} to {period_end.date()}",
            generated_at=datetime.now(),
            generated_by=generated_by,
            period_start=period_start,
            period_end=period_end,
            format=format,
        )

        # Aggregate event data
        by_event_type = {}
        by_actor = {}
        by_result = {}
        by_severity = {}

        for event in events:
            # By event type
            et = event.event_type.value
            by_event_type[et] = by_event_type.get(et, 0) + 1

            # By actor
            by_actor[event.actor] = by_actor.get(event.actor, 0) + 1

            # By result
            by_result[event.result] = by_result.get(event.result, 0) + 1

            # By severity
            sev = event.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        report.data = {
            "total_events": len(events),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "by_event_type": by_event_type,
            "by_actor": by_actor,
            "by_result": by_result,
            "by_severity": by_severity,
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type.value,
                    "timestamp": e.timestamp.isoformat(),
                    "actor": e.actor,
                    "resource": e.resource,
                    "action": e.action,
                    "result": e.result,
                    "severity": e.severity.value,
                }
                for e in events
            ]
        }

        # Generate output
        if format == ReportFormat.JSON:
            report.output_path = self._generate_json_report(report)

        elif format == ReportFormat.HTML:
            report.output_path = self._generate_html_audit_report(report)

        elif format == ReportFormat.CSV:
            report.output_path = self._generate_csv_audit_report(report)

        self.reports.append(report)

        logger.info(f"Generated audit trail report: {report.id}")

        return report

    def generate_metrics_dashboard_report(
        self,
        metrics: Dict[str, Any],
        format: ReportFormat = ReportFormat.HTML,
        generated_by: str = "system",
    ) -> Report:
        """
        Gera relatório de métricas e KPIs

        Args:
            metrics: Metrics data
            format: Output format
            generated_by: Who generated

        Returns:
            Report object
        """
        import uuid

        report = Report(
            id=f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            report_type=ReportType.METRICS_DASHBOARD,
            title="Metrics & KPI Dashboard",
            generated_at=datetime.now(),
            generated_by=generated_by,
            format=format,
        )

        report.data = metrics

        # Generate output
        if format == ReportFormat.JSON:
            report.output_path = self._generate_json_report(report)

        elif format == ReportFormat.HTML:
            report.output_path = self._generate_html_metrics_report(report)

        self.reports.append(report)

        logger.info(f"Generated metrics dashboard report: {report.id}")

        return report

    def generate_executive_summary(
        self,
        summary_data: Dict[str, Any],
        format: ReportFormat = ReportFormat.HTML,
        generated_by: str = "system",
    ) -> Report:
        """
        Gera executive summary

        Args:
            summary_data: Summary data
            format: Output format
            generated_by: Who generated

        Returns:
            Report object
        """
        import uuid

        report = Report(
            id=f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            report_type=ReportType.EXECUTIVE_SUMMARY,
            title="Executive Summary - Security Posture",
            generated_at=datetime.now(),
            generated_by=generated_by,
            format=format,
        )

        report.data = summary_data

        # Generate output
        if format == ReportFormat.HTML:
            report.output_path = self._generate_html_executive_summary(report)

        elif format == ReportFormat.MARKDOWN:
            report.output_path = self._generate_markdown_executive_summary(report)

        elif format == ReportFormat.JSON:
            report.output_path = self._generate_json_report(report)

        self.reports.append(report)

        logger.info(f"Generated executive summary: {report.id}")

        return report

    # ==================== Format Generators ====================

    def _generate_json_report(self, report: Report) -> str:
        """Gera relatório JSON"""
        output_file = self.output_dir / f"{report.id}.json"

        report_dict = {
            "id": report.id,
            "report_type": report.report_type.value,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "generated_by": report.generated_by,
            "period_start": report.period_start.isoformat() if report.period_start else None,
            "period_end": report.period_end.isoformat() if report.period_end else None,
            "data": report.data,
            "metadata": report.metadata,
        }

        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"JSON report saved: {output_file}")

        return str(output_file)

    def _generate_html_compliance_report(self, report: Report) -> str:
        """Gera relatório HTML de compliance"""
        output_file = self.output_dir / f"{report.id}.html"

        data = report.data
        summary = data.get("summary", {})

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 30px; border-radius: 8px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px;
                    border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .score {{ font-size: 48px; font-weight: bold; color: #667eea; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ color: #666; }}
        .gap {{ background: #fff3cd; padding: 10px; margin: 5px 0;
                border-left: 4px solid #ffc107; }}
        .recommendation {{ background: #d1ecf1; padding: 10px; margin: 5px 0;
                           border-left: 4px solid #17a2b8; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.title}</h1>
        <p>Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Assessor: {data.get('assessor', 'N/A')}</p>
    </div>

    <div class="section">
        <h2>Compliance Score</h2>
        <div class="score">{summary.get('compliance_score', 0):.1f}%</div>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-value">{summary.get('total_controls', 0)}</div>
            <div class="metric-label">Total Controls</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #28a745;">{summary.get('implemented', 0)}</div>
            <div class="metric-label">Implemented</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #ffc107;">{summary.get('partially_implemented', 0)}</div>
            <div class="metric-label">Partial</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #dc3545;">{summary.get('not_implemented', 0)}</div>
            <div class="metric-label">Not Implemented</div>
        </div>
    </div>

    <div class="section">
        <h2>Gaps Identified ({len(data.get('gaps', []))})</h2>
        {''.join(f'<div class="gap">{gap}</div>' for gap in data.get('gaps', []))}
    </div>

    <div class="section">
        <h2>Recommendations ({len(data.get('recommendations', []))})</h2>
        {''.join(f'<div class="recommendation">{rec}</div>' for rec in data.get('recommendations', []))}
    </div>

    <div class="section">
        <h2>Controls Assessed</h2>
        <p>{len(data.get('controls_assessed', []))} controls assessed</p>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html)

        logger.info(f"HTML compliance report saved: {output_file}")

        return str(output_file)

    def _generate_html_gap_report(self, report: Report) -> str:
        """Gera relatório HTML de gap analysis"""
        output_file = self.output_dir / f"{report.id}.html"

        data = report.data

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 30px; border-radius: 8px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px;
                    border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .gap {{ background: #fff3cd; padding: 15px; margin: 10px 0;
                border-left: 4px solid #ffc107; border-radius: 4px; }}
        .critical {{ border-left-color: #dc3545; background: #f8d7da; }}
        .gap-header {{ font-weight: bold; color: #333; }}
        .gap-status {{ color: #666; font-size: 14px; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.title}</h1>
        <p>Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-value">{data.get('total_gaps', 0)}</div>
            <div>Total Gaps</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #dc3545;">{data.get('critical_gaps', 0)}</div>
            <div>Critical Gaps</div>
        </div>
    </div>

    <div class="section">
        <h2>Critical Gaps</h2>
        {''.join(f'''<div class="gap critical">
            <div class="gap-header">{gap['control_id']}: {gap['title']}</div>
            <div class="gap-status">Status: {gap['status']} | Priority: {gap['priority']}</div>
        </div>''' for gap in data.get('critical_gaps_list', []))}
    </div>

    <div class="section">
        <h2>All Gaps</h2>
        {''.join(f'''<div class="gap">
            <div class="gap-header">{gap['control_id']}: {gap['title']}</div>
            <div class="gap-status">Status: {gap['status']} | Priority: {gap['priority']}</div>
        </div>''' for gap in data.get('gaps', []))}
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html)

        logger.info(f"HTML gap report saved: {output_file}")

        return str(output_file)

    def _generate_html_audit_report(self, report: Report) -> str:
        """Gera relatório HTML de audit trail"""
        output_file = self.output_dir / f"{report.id}.html"

        data = report.data

        events_table = ""
        for event in data.get('events', [])[:100]:  # Limit to 100 for display
            events_table += f"""
            <tr>
                <td>{event['timestamp'][:19]}</td>
                <td>{event['event_type']}</td>
                <td>{event['actor']}</td>
                <td>{event['resource']}</td>
                <td>{event['action']}</td>
                <td>{event['result']}</td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 30px; border-radius: 8px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px;
                    border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; position: sticky; top: 0; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.title}</h1>
        <p>Period: {data.get('period_start', '')[:10]} to {data.get('period_end', '')[:10]}</p>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-value">{data.get('total_events', 0)}</div>
            <div>Total Events</div>
        </div>
    </div>

    <div class="section">
        <h2>Events</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Event Type</th>
                    <th>Actor</th>
                    <th>Resource</th>
                    <th>Action</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody>
                {events_table}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html)

        logger.info(f"HTML audit report saved: {output_file}")

        return str(output_file)

    def _generate_html_metrics_report(self, report: Report) -> str:
        """Gera relatório HTML de métricas"""
        output_file = self.output_dir / f"{report.id}.html"

        # Simple metrics display
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 30px; border-radius: 8px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px;
                    border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.title}</h1>
        <p>Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>Metrics Data</h2>
        <pre>{json.dumps(report.data, indent=2)}</pre>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html)

        logger.info(f"HTML metrics report saved: {output_file}")

        return str(output_file)

    def _generate_html_executive_summary(self, report: Report) -> str:
        """Gera executive summary HTML"""
        output_file = self.output_dir / f"{report.id}.html"

        data = report.data

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report.title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 40px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 40px; border-radius: 8px; }}
        .section {{ background: white; margin: 20px 0; padding: 30px;
                    border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .highlight {{ font-size: 18px; color: #667eea; font-weight: bold; }}
        .summary-item {{ margin: 15px 0; line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.title}</h1>
        <p style="font-size: 18px;">Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <pre>{json.dumps(data, indent=2)}</pre>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html)

        logger.info(f"HTML executive summary saved: {output_file}")

        return str(output_file)

    def _generate_markdown_compliance_report(self, report: Report) -> str:
        """Gera relatório Markdown de compliance"""
        output_file = self.output_dir / f"{report.id}.md"

        data = report.data
        summary = data.get("summary", {})

        markdown = f"""# {report.title}

**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Assessor:** {data.get('assessor', 'N/A')}

## Compliance Score

**{summary.get('compliance_score', 0):.1f}%**

## Summary

- **Total Controls:** {summary.get('total_controls', 0)}
- **Implemented:** {summary.get('implemented', 0)}
- **Partially Implemented:** {summary.get('partially_implemented', 0)}
- **Not Implemented:** {summary.get('not_implemented', 0)}
- **Not Applicable:** {summary.get('not_applicable', 0)}

## Gaps Identified

{chr(10).join(f'- {gap}' for gap in data.get('gaps', []))}

## Recommendations

{chr(10).join(f'- {rec}' for rec in data.get('recommendations', []))}

## Controls Assessed

{len(data.get('controls_assessed', []))} controls assessed
"""

        with open(output_file, 'w') as f:
            f.write(markdown)

        logger.info(f"Markdown compliance report saved: {output_file}")

        return str(output_file)

    def _generate_markdown_gap_report(self, report: Report) -> str:
        """Gera relatório Markdown de gap analysis"""
        output_file = self.output_dir / f"{report.id}.md"

        data = report.data

        markdown = f"""# {report.title}

**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Gaps:** {data.get('total_gaps', 0)}
- **Critical Gaps:** {data.get('critical_gaps', 0)}

## Critical Gaps

{chr(10).join(f"- **{gap['control_id']}**: {gap['title']} (Status: {gap['status']}, Priority: {gap['priority']})" for gap in data.get('critical_gaps_list', []))}

## All Gaps

{chr(10).join(f"- **{gap['control_id']}**: {gap['title']} (Status: {gap['status']}, Priority: {gap['priority']})" for gap in data.get('gaps', []))}
"""

        with open(output_file, 'w') as f:
            f.write(markdown)

        logger.info(f"Markdown gap report saved: {output_file}")

        return str(output_file)

    def _generate_markdown_executive_summary(self, report: Report) -> str:
        """Gera executive summary Markdown"""
        output_file = self.output_dir / f"{report.id}.md"

        markdown = f"""# {report.title}

**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

```json
{json.dumps(report.data, indent=2)}
```
"""

        with open(output_file, 'w') as f:
            f.write(markdown)

        logger.info(f"Markdown executive summary saved: {output_file}")

        return str(output_file)

    def _generate_csv_compliance_report(self, report: Report) -> str:
        """Gera relatório CSV de compliance"""
        output_file = self.output_dir / f"{report.id}.csv"

        data = report.data

        # Simple CSV with gaps
        with open(output_file, 'w') as f:
            f.write("Gap\n")
            for gap in data.get('gaps', []):
                f.write(f'"{gap}"\n')

        logger.info(f"CSV compliance report saved: {output_file}")

        return str(output_file)

    def _generate_csv_audit_report(self, report: Report) -> str:
        """Gera relatório CSV de audit"""
        output_file = self.output_dir / f"{report.id}.csv"

        data = report.data

        # CSV with events
        with open(output_file, 'w') as f:
            f.write("Timestamp,Event Type,Actor,Resource,Action,Result\n")
            for event in data.get('events', []):
                f.write(
                    f"{event['timestamp']},{event['event_type']},{event['actor']},"
                    f"{event['resource']},{event['action']},{event['result']}\n"
                )

        logger.info(f"CSV audit report saved: {output_file}")

        return str(output_file)

    def get_report(self, report_id: str) -> Optional[Report]:
        """Retorna relatório por ID"""
        for report in self.reports:
            if report.id == report_id:
                return report

        return None

    def list_reports(
        self,
        report_type: Optional[ReportType] = None,
        limit: int = 50,
    ) -> List[Report]:
        """Lista relatórios"""
        reports = self.reports

        if report_type:
            reports = [r for r in reports if r.report_type == report_type]

        # Sort by generation date (most recent first)
        reports = sorted(reports, key=lambda r: r.generated_at, reverse=True)

        return reports[:limit]
