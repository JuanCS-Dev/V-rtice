"""
📋 Compliance & Reporting
Frameworks de compliance, auditoria e relatórios

Componentes:
- ComplianceEngine: Engine de compliance com múltiplos frameworks
- AuditLogger: Logging imutável para auditoria
- ReportGenerator: Geração de relatórios de compliance
- MetricsCollector: Coleta de métricas e KPIs
"""

from .compliance_engine import (
    ComplianceEngine,
    ComplianceFramework,
    Control,
    ControlStatus,
    Assessment,
)
from .audit_logger import AuditLogger, AuditEvent, AuditEventType
from .report_generator import ReportGenerator, Report, ReportFormat
from .metrics import MetricsCollector, Metric, MetricType

__all__ = [
    "ComplianceEngine",
    "ComplianceFramework",
    "Control",
    "ControlStatus",
    "Assessment",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "ReportGenerator",
    "Report",
    "ReportFormat",
    "MetricsCollector",
    "Metric",
    "MetricType",
]
