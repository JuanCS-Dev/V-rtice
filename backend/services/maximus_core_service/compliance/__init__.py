"""
Compliance & Certification Module

Multi-jurisdictional regulatory compliance engine for the VÉRTICE platform.
Provides automated compliance checking, evidence collection, gap analysis, and
certification readiness assessment.

Supported Regulations:
- EU AI Act (High-Risk AI System - Tier I)
- GDPR Article 22 (Automated Decision-Making)
- NIST AI RMF 1.0 (AI Risk Management Framework)
- US Executive Order 14110 (Safe, Secure AI)
- Brazil LGPD (Lei Geral de Proteção de Dados)
- ISO/IEC 27001:2022 (Information Security)
- SOC 2 Type II (Security, Availability, Confidentiality)
- IEEE 7000-2021 (Ethical AI Design)

Key Features:
- Automated compliance checks across multiple jurisdictions
- Real-time violation detection and alerting
- Evidence collection and storage
- Gap analysis and remediation tracking
- Certification readiness assessment
- Compliance dashboard and reporting

Architecture:
    Compliance Engine → Regulation Checks → Evidence Collection
                              ↓
                        Gap Analysis → Remediation
                              ↓
                    Compliance Monitoring → Alerts

Usage:
    from compliance import (
        ComplianceEngine,
        RegulationType,
        ComplianceCheck,
        EvidenceCollector,
        GapAnalyzer,
    )

    # Initialize engine
    engine = ComplianceEngine()

    # Run compliance check
    result = engine.check_compliance(
        regulation=RegulationType.EU_AI_ACT,
        scope="threat_detection_ai"
    )

    # Generate compliance report
    report = engine.generate_compliance_report(
        regulations=[RegulationType.GDPR, RegulationType.LGPD],
        period_days=30
    )

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from .base import (
    # Core data structures
    Regulation,
    Control,
    Evidence,
    ComplianceResult,
    ComplianceViolation,
    GapAnalysisResult,

    # Enums
    RegulationType,
    ControlCategory,
    ComplianceStatus,
    ViolationSeverity,
    EvidenceType,

    # Configuration
    ComplianceConfig,
)

from .regulations import (
    # Regulation definitions
    EU_AI_ACT,
    GDPR,
    NIST_AI_RMF,
    US_EO_14110,
    BRAZIL_LGPD,
    ISO_27001,
    SOC2_TYPE_II,
    IEEE_7000,

    # Regulation registry
    REGULATION_REGISTRY,
    get_regulation,
)

from .compliance_engine import (
    ComplianceEngine,
    ComplianceCheckResult,
)

from .evidence_collector import (
    EvidenceCollector,
    EvidenceItem,
    EvidencePackage,
)

from .gap_analyzer import (
    GapAnalyzer,
    Gap,
    RemediationPlan,
)

from .monitoring import (
    ComplianceMonitor,
    ComplianceAlert,
    MonitoringMetrics,
)

# Certification modules
from .certifications import (
    ISO27001Checker,
    SOC2Checker,
    IEEE7000Checker,
    CertificationResult,
)

# Version information
__version__ = "1.0.0"
__author__ = "Claude Code + JuanCS-Dev"
__all__ = [
    # Base classes
    "Regulation",
    "Control",
    "Evidence",
    "ComplianceResult",
    "ComplianceViolation",
    "GapAnalysisResult",
    "RegulationType",
    "ControlCategory",
    "ComplianceStatus",
    "ViolationSeverity",
    "EvidenceType",
    "ComplianceConfig",

    # Regulations
    "EU_AI_ACT",
    "GDPR",
    "NIST_AI_RMF",
    "US_EO_14110",
    "BRAZIL_LGPD",
    "ISO_27001",
    "SOC2_TYPE_II",
    "IEEE_7000",
    "REGULATION_REGISTRY",
    "get_regulation",

    # Compliance engine
    "ComplianceEngine",
    "ComplianceCheckResult",

    # Evidence collection
    "EvidenceCollector",
    "EvidenceItem",
    "EvidencePackage",

    # Gap analysis
    "GapAnalyzer",
    "Gap",
    "RemediationPlan",

    # Monitoring
    "ComplianceMonitor",
    "ComplianceAlert",
    "MonitoringMetrics",

    # Certifications
    "ISO27001Checker",
    "SOC2Checker",
    "IEEE7000Checker",
    "CertificationResult",
]
