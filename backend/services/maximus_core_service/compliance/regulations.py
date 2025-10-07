"""
Regulatory Definitions

Complete definitions of 8 major regulations with controls, requirements,
and test procedures. Based on official regulatory documentation.

Regulations:
1. EU AI Act - High-Risk AI System (Tier I)
2. GDPR - Article 22 Automated Decision-Making
3. NIST AI RMF 1.0 - AI Risk Management Framework
4. US Executive Order 14110 - Safe, Secure AI
5. Brazil LGPD - Lei Geral de Proteção de Dados
6. ISO/IEC 27001:2022 - Information Security Management
7. SOC 2 Type II - Trust Services Criteria
8. IEEE 7000-2021 - Ethical AI Design

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from datetime import datetime
from typing import Dict

from .base import (
    Regulation,
    Control,
    RegulationType,
    ControlCategory,
    EvidenceType,
)


# ============================================================================
# EU AI ACT - High-Risk AI System (Tier I)
# ============================================================================

EU_AI_ACT = Regulation(
    regulation_type=RegulationType.EU_AI_ACT,
    name="EU Artificial Intelligence Act - High-Risk AI Systems",
    version="1.0",
    effective_date=datetime(2026, 1, 1),
    jurisdiction="European Union",
    description="Regulation on Artificial Intelligence. VÉRTICE qualifies as High-Risk AI (Tier I) due to use in law enforcement, critical infrastructure protection, and biometric systems.",
    authority="European Commission",
    url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206",
    penalties="Up to €30 million or 6% of global annual turnover",
    scope="High-Risk AI systems as defined in Annex III",
    controls=[
        Control(
            control_id="EU-AI-ACT-ART-9",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.GOVERNANCE,
            title="Risk Management System",
            description="Establish, implement, document and maintain a risk management system throughout the AI system's lifecycle. Must identify and analyze known and foreseeable risks, estimate and evaluate risks arising from intended use and reasonably foreseeable misuse.",
            mandatory=True,
            test_procedure="Review risk management documentation, verify continuous risk assessment process, validate risk mitigation measures",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.RISK_ASSESSMENT,
                EvidenceType.POLICY,
            ],
            reference="Article 9",
            tags={"risk", "governance", "lifecycle"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-10",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.TECHNICAL,
            title="Data and Data Governance",
            description="Training, validation and testing data sets shall be subject to appropriate data governance and management practices. Data must be relevant, representative, free of errors and complete. Account for characteristics/elements particular to geographic, behavioral or functional setting.",
            mandatory=True,
            test_procedure="Audit training data provenance, verify data quality metrics, validate data governance policies",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Article 10",
            tags={"data", "quality", "bias"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-11",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.DOCUMENTATION,
            title="Technical Documentation",
            description="Technical documentation must be drawn up before AI system is placed on market. Must include: general description, detailed description of elements, data requirements, information on monitoring/logging, risk management, changes to the system.",
            mandatory=True,
            test_procedure="Review technical documentation for completeness per Annex IV requirements",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 11, Annex IV",
            tags={"documentation", "transparency"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-12",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.MONITORING,
            title="Record-Keeping and Logging",
            description="High-risk AI systems shall be designed with automatic recording of events (logs) throughout operation. Logging capabilities must enable traceability, monitoring and auditability.",
            mandatory=True,
            test_procedure="Verify automatic logging system, test log retention, validate log completeness",
            evidence_required=[
                EvidenceType.LOG,
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 12",
            tags={"logging", "auditability", "traceability"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-13",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.TECHNICAL,
            title="Transparency and Information to Users",
            description="High-risk AI systems shall be designed and developed with appropriate transparency to enable users to interpret system output and use it appropriately. Instructions for use must include intended purpose, accuracy level, robustness, known limitations.",
            mandatory=True,
            test_procedure="Review user documentation, verify transparency of AI decisions, validate user training materials",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TRAINING_RECORD,
            ],
            reference="Article 13",
            tags={"transparency", "explainability", "users"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-14",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.ORGANIZATIONAL,
            title="Human Oversight",
            description="High-risk AI systems must be designed to enable effective oversight by natural persons during use. Human oversight measures must enable humans to: fully understand AI system capacities and limitations, remain aware of automation bias, interpret system outputs, decide not to use system, intervene or interrupt system.",
            mandatory=True,
            test_procedure="Verify HITL (Human-in-the-Loop) framework implementation, test override capabilities, validate oversight effectiveness",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="Article 14",
            tags={"hitl", "oversight", "human-control"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-15",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.TECHNICAL,
            title="Accuracy, Robustness and Cybersecurity",
            description="High-risk AI systems shall be designed and developed to achieve appropriate levels of accuracy, robustness and cybersecurity. Must be resilient to errors, faults, inconsistencies, attempts to manipulate the system. Technical solutions to address AI specific vulnerabilities.",
            mandatory=True,
            test_procedure="Execute accuracy testing, perform adversarial testing, conduct penetration testing",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Article 15",
            tags={"accuracy", "robustness", "security"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-61",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.MONITORING,
            title="Post-Market Monitoring",
            description="Providers shall establish and document a post-market monitoring system proportionate to the nature of the AI technologies and risks. Must actively and systematically collect, document and analyze data on performance throughout lifetime.",
            mandatory=True,
            test_procedure="Review post-market monitoring plan, verify incident collection system, validate reporting process",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.LOG,
                EvidenceType.INCIDENT_REPORT,
            ],
            reference="Article 61",
            tags={"monitoring", "incident-management"},
        ),
    ],
)


# ============================================================================
# GDPR - Article 22 Automated Decision-Making
# ============================================================================

GDPR = Regulation(
    regulation_type=RegulationType.GDPR,
    name="General Data Protection Regulation - Article 22 (Automated Decision-Making)",
    version="2016/679",
    effective_date=datetime(2018, 5, 25),
    jurisdiction="European Union",
    description="Regulation on automated individual decision-making, including profiling. VÉRTICE processes personal data for threat detection and automated response decisions.",
    authority="European Data Protection Board (EDPB)",
    url="https://gdpr-info.eu/",
    penalties="Up to €20 million or 4% of global annual turnover",
    scope="Automated decision-making with legal or similarly significant effects",
    controls=[
        Control(
            control_id="GDPR-ART-22",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.GOVERNANCE,
            title="Right to Human Review of Automated Decisions",
            description="Data subject has the right not to be subject to decision based solely on automated processing which produces legal effects or similarly significantly affects them. Must provide: right to obtain human intervention, right to express point of view, right to contest decision.",
            mandatory=True,
            test_procedure="Verify HITL implementation for decisions affecting individuals, test human review process, validate appeal mechanism",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 22",
            tags={"automated-decision", "human-review", "rights"},
        ),
        Control(
            control_id="GDPR-ART-25",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.TECHNICAL,
            title="Data Protection by Design and by Default",
            description="Implement appropriate technical and organizational measures to ensure data processing meets GDPR requirements. Must implement data minimization, pseudonymization where possible, transparency, enable data subject rights.",
            mandatory=True,
            test_procedure="Review system architecture for privacy-by-design, verify data minimization, test pseudonymization",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CODE_REVIEW,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 25",
            tags={"privacy-by-design", "data-minimization"},
        ),
        Control(
            control_id="GDPR-ART-30",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.DOCUMENTATION,
            title="Records of Processing Activities",
            description="Maintain records of all processing activities under controller's responsibility. Must include: purposes of processing, categories of data subjects, categories of personal data, categories of recipients, transfers to third countries, retention periods, security measures.",
            mandatory=True,
            test_procedure="Review processing activity records (ROPA), verify completeness and accuracy",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Article 30",
            tags={"documentation", "ropa"},
        ),
        Control(
            control_id="GDPR-ART-32",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.SECURITY,
            title="Security of Processing",
            description="Implement appropriate technical and organizational measures to ensure security appropriate to the risk. Must include: pseudonymization and encryption, ongoing confidentiality/integrity/availability/resilience, ability to restore availability after incident, regular testing of measures.",
            mandatory=True,
            test_procedure="Conduct security audit, test encryption, verify access controls, validate incident response",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 32",
            tags={"security", "encryption", "access-control"},
        ),
        Control(
            control_id="GDPR-ART-35",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.ORGANIZATIONAL,
            title="Data Protection Impact Assessment (DPIA)",
            description="Conduct DPIA when processing is likely to result in high risk to rights and freedoms. Required for: systematic and extensive automated decision-making, large scale processing of special categories of data, systematic monitoring of publicly accessible areas.",
            mandatory=True,
            test_procedure="Review DPIA documentation, verify risk assessment methodology, validate mitigation measures",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.RISK_ASSESSMENT,
            ],
            reference="Article 35",
            tags={"dpia", "risk-assessment", "privacy"},
        ),
    ],
)


# ============================================================================
# NIST AI RMF 1.0 - AI Risk Management Framework
# ============================================================================

NIST_AI_RMF = Regulation(
    regulation_type=RegulationType.NIST_AI_RMF,
    name="NIST AI Risk Management Framework 1.0",
    version="1.0",
    effective_date=datetime(2023, 1, 26),
    jurisdiction="United States (voluntary)",
    description="Framework for managing risks to individuals, organizations and society from AI systems. Four core functions: GOVERN, MAP, MEASURE, MANAGE.",
    authority="National Institute of Standards and Technology (NIST)",
    url="https://www.nist.gov/itl/ai-risk-management-framework",
    penalties="N/A - Voluntary framework",
    scope="All AI systems",
    controls=[
        Control(
            control_id="NIST-GOVERN-1.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.GOVERNANCE,
            title="AI Risk Management Strategy",
            description="Legal and regulatory requirements involving AI are understood, managed, and documented. Organizational policies and practices for AI system development and deployment.",
            mandatory=True,
            test_procedure="Review AI governance documentation, verify regulatory compliance tracking",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="GOVERN-1.1",
            tags={"governance", "strategy"},
        ),
        Control(
            control_id="NIST-GOVERN-1.7",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.GOVERNANCE,
            title="AI Risk Accountability",
            description="Processes and procedures are in place for the workforce to raise and communicate AI risks, performance issues, and emergent risks. Accountability structures established.",
            mandatory=True,
            test_procedure="Verify incident reporting process, validate escalation procedures",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="GOVERN-1.7",
            tags={"accountability", "reporting"},
        ),
        Control(
            control_id="NIST-MAP-1.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.ORGANIZATIONAL,
            title="AI System Context and Purpose",
            description="Context is established and documented. Purpose and intended use of AI system are defined and understood by relevant AI actors.",
            mandatory=True,
            test_procedure="Review system documentation for context and purpose definition",
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="MAP-1.1",
            tags={"context", "purpose"},
        ),
        Control(
            control_id="NIST-MAP-3.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.TECHNICAL,
            title="AI System Requirements and Design",
            description="AI system requirements are elicited from and understood by relevant AI actors. Design decisions are documented.",
            mandatory=True,
            test_procedure="Review requirements documentation, verify traceability to design",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="MAP-3.1",
            tags={"requirements", "design"},
        ),
        Control(
            control_id="NIST-MEASURE-2.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.TESTING,
            title="Test, Evaluation, Validation and Verification (TEVV)",
            description="AI systems are evaluated for trustworthy characteristics using domain-specific approaches. Metrics for performance, fairness, safety, security are defined and measured.",
            mandatory=True,
            test_procedure="Execute TEVV plan, measure defined metrics, validate against thresholds",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="MEASURE-2.1",
            tags={"testing", "metrics", "validation"},
        ),
        Control(
            control_id="NIST-MEASURE-2.7",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.TESTING,
            title="Bias Testing and Mitigation",
            description="AI systems are evaluated for harmful bias. Bias testing and mitigation approaches are documented and applied.",
            mandatory=True,
            test_procedure="Execute bias testing suite, measure fairness metrics, verify mitigation effectiveness",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="MEASURE-2.7",
            tags={"bias", "fairness", "testing"},
        ),
        Control(
            control_id="NIST-MANAGE-1.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.MONITORING,
            title="AI Risk Response and Monitoring",
            description="Risk response plans are implemented and monitored. AI systems are routinely reviewed and updated based on deployment context and evolving risks.",
            mandatory=True,
            test_procedure="Review risk response plans, verify monitoring implementation, validate update procedures",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.LOG,
                EvidenceType.INCIDENT_REPORT,
            ],
            reference="MANAGE-1.1",
            tags={"risk-management", "monitoring"},
        ),
    ],
)


# ============================================================================
# US EXECUTIVE ORDER 14110 - Safe, Secure AI
# ============================================================================

US_EO_14110 = Regulation(
    regulation_type=RegulationType.US_EO_14110,
    name="US Executive Order 14110 - Safe, Secure, and Trustworthy AI",
    version="2023",
    effective_date=datetime(2023, 10, 30),
    jurisdiction="United States",
    description="Executive Order on Safe, Secure, and Trustworthy Development and Use of Artificial Intelligence. Applies to dual-use foundation models and AI systems affecting critical infrastructure or national security.",
    authority="White House Office of Science and Technology Policy (OSTP)",
    url="https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/executive-order-on-the-safe-secure-and-trustworthy-development-and-use-of-artificial-intelligence/",
    penalties="Federal enforcement actions",
    scope="Dual-use foundation models, critical infrastructure AI",
    controls=[
        Control(
            control_id="US-EO-14110-SEC-4.2-A",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.TESTING,
            title="Safety Testing and Red-Team Testing",
            description="Developers of dual-use foundation models must conduct extensive red-team testing to identify and address potential risks. Must test for: chemical, biological, radiological, nuclear risks; cybersecurity vulnerabilities; harmful biases and discrimination.",
            mandatory=True,
            test_procedure="Execute red-team testing program, document vulnerabilities, verify remediation",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Section 4.2(a)",
            tags={"red-team", "safety", "testing"},
        ),
        Control(
            control_id="US-EO-14110-SEC-4.2-B",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.SECURITY,
            title="Cybersecurity and Supply Chain Security",
            description="AI systems must implement robust cybersecurity measures. Secure development practices, vulnerability management, supply chain security for AI models and data.",
            mandatory=True,
            test_procedure="Conduct cybersecurity audit, verify secure development lifecycle, test vulnerability management",
            evidence_required=[
                EvidenceType.AUDIT_REPORT,
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 4.2(b)",
            tags={"cybersecurity", "supply-chain"},
        ),
        Control(
            control_id="US-EO-14110-SEC-5.1",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.GOVERNANCE,
            title="AI Risk Management for Critical Infrastructure",
            description="AI systems affecting critical infrastructure must implement comprehensive risk management. Identify and mitigate risks to safety, security, and resilience.",
            mandatory=True,
            test_procedure="Review critical infrastructure risk assessment, verify mitigation controls",
            evidence_required=[
                EvidenceType.RISK_ASSESSMENT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.1",
            tags={"critical-infrastructure", "risk"},
        ),
        Control(
            control_id="US-EO-14110-SEC-10.1-B",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.TESTING,
            title="Bias and Discrimination Testing",
            description="AI systems must be tested for harmful bias and discrimination. Implement measures to prevent algorithmic discrimination in areas such as housing, employment, credit, healthcare.",
            mandatory=True,
            test_procedure="Execute bias testing across protected classes, measure fairness metrics, validate mitigation",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 10.1(b)",
            tags={"bias", "fairness", "discrimination"},
        ),
    ],
)


# ============================================================================
# BRAZIL LGPD - Lei Geral de Proteção de Dados
# ============================================================================

BRAZIL_LGPD = Regulation(
    regulation_type=RegulationType.BRAZIL_LGPD,
    name="Lei Geral de Proteção de Dados Pessoais (LGPD)",
    version="Lei nº 13.709/2018",
    effective_date=datetime(2020, 9, 18),
    jurisdiction="Brazil",
    description="Brazilian General Data Protection Law. Regulates processing of personal data. Similar to GDPR with specific requirements for automated decision-making.",
    authority="Autoridade Nacional de Proteção de Dados (ANPD)",
    url="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
    penalties="Up to 2% of revenue (max R$ 50 million per infraction)",
    scope="Processing of personal data in Brazil",
    controls=[
        Control(
            control_id="LGPD-ART-7",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.GOVERNANCE,
            title="Legal Basis for Processing",
            description="Personal data processing must have legal basis. For sensitive data, requires explicit consent or legal obligation. Must document legal basis for each processing activity.",
            mandatory=True,
            test_procedure="Review legal basis documentation for all processing activities",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="Article 7",
            tags={"legal-basis", "consent"},
        ),
        Control(
            control_id="LGPD-ART-18",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.ORGANIZATIONAL,
            title="Data Subject Rights",
            description="Data subjects have rights to: confirmation of processing, access to data, correction, anonymization/blocking/deletion, portability, information about sharing, information about possibility of not providing consent, revocation of consent.",
            mandatory=True,
            test_procedure="Verify implementation of data subject rights request process, test request fulfillment",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 18",
            tags={"data-subject-rights", "access"},
        ),
        Control(
            control_id="LGPD-ART-20",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.GOVERNANCE,
            title="Right to Review Automated Decisions",
            description="Data subject has right to request review of decisions made solely based on automated processing that affect their interests. Must provide: information about automated decision-making criteria, right to contest.",
            mandatory=True,
            test_procedure="Verify human review process for automated decisions, test review request handling",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 20",
            tags={"automated-decision", "review", "transparency"},
        ),
        Control(
            control_id="LGPD-ART-38",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.ORGANIZATIONAL,
            title="Data Protection Impact Assessment (RIPD)",
            description="Controller must prepare Data Protection Impact Assessment (Relatório de Impacto à Proteção de Dados Pessoais - RIPD) when requested by ANPD. Must include: description of processing, legal basis, assessment of necessity and proportionality, security measures, risk mitigation.",
            mandatory=True,
            test_procedure="Review RIPD documentation, verify risk assessment methodology",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.RISK_ASSESSMENT,
            ],
            reference="Article 38",
            tags={"ripd", "impact-assessment", "privacy"},
        ),
        Control(
            control_id="LGPD-ART-46",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.SECURITY,
            title="Security and Preventive Measures",
            description="Controllers and operators must adopt security, technical and administrative measures to protect personal data. Must prevent: unauthorized access, accidental or unlawful destruction, loss, alteration, communication or diffusion.",
            mandatory=True,
            test_procedure="Conduct security audit, test access controls, verify encryption, validate incident response",
            evidence_required=[
                EvidenceType.AUDIT_REPORT,
                EvidenceType.TEST_RESULT,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 46",
            tags={"security", "encryption", "access-control"},
        ),
    ],
)


# ============================================================================
# ISO/IEC 27001:2022 - Information Security Management
# ============================================================================

ISO_27001 = Regulation(
    regulation_type=RegulationType.ISO_27001,
    name="ISO/IEC 27001:2022 - Information Security Management System",
    version="2022",
    effective_date=datetime(2022, 10, 25),
    jurisdiction="International",
    description="International standard for Information Security Management Systems (ISMS). Provides requirements for establishing, implementing, maintaining and continually improving an ISMS.",
    authority="International Organization for Standardization (ISO)",
    url="https://www.iso.org/standard/27001",
    penalties="N/A - Certification standard",
    scope="Information security management",
    controls=[
        Control(
            control_id="ISO-27001-A.5.1",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.GOVERNANCE,
            title="Information Security Policies",
            description="Information security policy and topic-specific policies shall be defined, approved by management, published, communicated and acknowledged by relevant personnel.",
            mandatory=True,
            test_procedure="Review information security policies, verify approval and communication",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="A.5.1",
            tags={"policy", "governance"},
        ),
        Control(
            control_id="ISO-27001-A.8.1",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.TECHNICAL,
            title="User Endpoint Devices",
            description="Information stored on, processed by or accessible via user endpoint devices shall be protected. Implement controls for: device registration, encryption, remote wipe, secure configuration.",
            mandatory=True,
            test_procedure="Test endpoint security controls, verify encryption, validate device management",
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.1",
            tags={"endpoint", "encryption"},
        ),
        Control(
            control_id="ISO-27001-A.8.2",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.SECURITY,
            title="Privileged Access Rights",
            description="Allocation and use of privileged access rights shall be restricted and managed. Implement: least privilege, separation of duties, privileged access monitoring, MFA for privileged accounts.",
            mandatory=True,
            test_procedure="Review privileged access controls, test access restrictions, verify monitoring",
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.LOG,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="A.8.2",
            tags={"access-control", "privilege"},
        ),
        Control(
            control_id="ISO-27001-A.8.10",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.SECURITY,
            title="Information Deletion",
            description="Information stored in information systems, devices or any other storage media shall be deleted when no longer required. Implement secure deletion procedures.",
            mandatory=True,
            test_procedure="Verify secure deletion procedures, test data sanitization",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.10",
            tags={"data-deletion", "sanitization"},
        ),
        Control(
            control_id="ISO-27001-A.8.16",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.MONITORING,
            title="Monitoring Activities",
            description="Networks, systems and applications shall be monitored for anomalous behavior. Security events shall be recorded. Logs shall be protected and analyzed.",
            mandatory=True,
            test_procedure="Verify monitoring implementation, test log collection, validate log protection",
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.LOG,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.16",
            tags={"monitoring", "logging", "siem"},
        ),
        Control(
            control_id="ISO-27001-A.8.23",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.TECHNICAL,
            title="Web Filtering",
            description="Access to external websites shall be managed to reduce exposure to malicious content. Implement web filtering and categorization.",
            mandatory=False,
            test_procedure="Test web filtering implementation, verify categorization rules",
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.23",
            tags={"web-filtering", "security"},
        ),
        Control(
            control_id="ISO-27001-A.8.24",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.SECURITY,
            title="Use of Cryptography",
            description="Rules for the effective use of cryptography shall be defined and implemented. Include: encryption algorithms, key management, secure protocols.",
            mandatory=True,
            test_procedure="Review cryptographic standards, verify algorithm strength, test key management",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.24",
            tags={"cryptography", "encryption"},
        ),
    ],
)


# ============================================================================
# SOC 2 TYPE II - Trust Services Criteria
# ============================================================================

SOC2_TYPE_II = Regulation(
    regulation_type=RegulationType.SOC2_TYPE_II,
    name="SOC 2 Type II - Trust Services Criteria",
    version="2017",
    effective_date=datetime(2017, 1, 1),
    jurisdiction="United States (accepted globally)",
    description="Service Organization Control 2 Type II audit. Evaluates controls over: Security (required), Availability, Processing Integrity, Confidentiality, Privacy. Type II evaluates effectiveness over time (6-12 months).",
    authority="American Institute of Certified Public Accountants (AICPA)",
    url="https://www.aicpa.org/soc4so",
    penalties="N/A - Audit report standard",
    scope="Service organizations and SaaS providers",
    controls=[
        Control(
            control_id="SOC2-CC6.1",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.SECURITY,
            title="Logical and Physical Access Controls",
            description="Entity implements logical and physical access controls to meet security commitments. Controls include: authentication, authorization, physical security, network security.",
            mandatory=True,
            test_procedure="Test access control implementation, verify MFA, validate physical security",
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="CC6.1 (Common Criteria)",
            tags={"access-control", "security", "mfa"},
        ),
        Control(
            control_id="SOC2-CC6.6",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.MONITORING,
            title="Security Event Logging and Monitoring",
            description="Entity implements logging and monitoring to detect anomalous behavior. Logs are protected from tampering and reviewed regularly.",
            mandatory=True,
            test_procedure="Verify log collection, test log protection, validate monitoring alerts",
            evidence_required=[
                EvidenceType.LOG,
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="CC6.6",
            tags={"logging", "monitoring", "siem"},
        ),
        Control(
            control_id="SOC2-CC6.7",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.SECURITY,
            title="Security Incident Management",
            description="Entity has incident response plan. Security incidents are identified, reported, assessed, responded to and resolved in timely manner.",
            mandatory=True,
            test_procedure="Review incident response plan, test incident detection and response",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.INCIDENT_REPORT,
                EvidenceType.TEST_RESULT,
            ],
            reference="CC6.7",
            tags={"incident-response", "security"},
        ),
        Control(
            control_id="SOC2-CC7.2",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.MONITORING,
            title="System Monitoring and Alerting",
            description="Entity monitors system performance and availability. Capacity planning is performed. Alerts are configured for performance degradation.",
            mandatory=True,
            test_procedure="Verify system monitoring, test alerting, review capacity planning",
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.LOG,
                EvidenceType.DOCUMENT,
            ],
            reference="CC7.2 (Availability)",
            tags={"monitoring", "availability", "alerting"},
        ),
        Control(
            control_id="SOC2-PI1.4",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.TESTING,
            title="Processing Integrity - Data Validation",
            description="Entity implements controls to ensure complete, valid, accurate, timely and authorized processing. Input validation, error handling, reconciliation.",
            mandatory=True,
            test_procedure="Test input validation, verify error handling, validate data integrity controls",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="PI1.4 (Processing Integrity)",
            tags={"data-validation", "integrity"},
        ),
        Control(
            control_id="SOC2-C1.1",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.SECURITY,
            title="Confidentiality - Encryption",
            description="Entity protects confidential information through encryption in transit and at rest. Encryption keys are properly managed.",
            mandatory=True,
            test_procedure="Verify encryption implementation, test key management, validate cipher strength",
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="C1.1 (Confidentiality)",
            tags={"encryption", "confidentiality"},
        ),
    ],
)


# ============================================================================
# IEEE 7000-2021 - Ethical AI Design
# ============================================================================

IEEE_7000 = Regulation(
    regulation_type=RegulationType.IEEE_7000,
    name="IEEE 7000-2021 - Model Process for Addressing Ethical Concerns",
    version="2021",
    effective_date=datetime(2021, 9, 9),
    jurisdiction="International",
    description="Standard for addressing ethical concerns during system design. Value-based engineering approach. Applicable to AI systems with societal impact.",
    authority="IEEE Standards Association",
    url="https://standards.ieee.org/standard/7000-2021.html",
    penalties="N/A - Voluntary standard",
    scope="Systems with ethical implications",
    controls=[
        Control(
            control_id="IEEE-7000-5.2",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Stakeholder Analysis",
            description="Identify and analyze all stakeholders who may be affected by the system. Document stakeholder values, concerns, and potential impacts. Include: direct users, indirect users, affected communities.",
            mandatory=True,
            test_procedure="Review stakeholder analysis documentation, verify completeness of stakeholder identification",
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.2",
            tags={"stakeholders", "ethics"},
        ),
        Control(
            control_id="IEEE-7000-5.3",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Value Elicitation",
            description="Elicit values from stakeholders through structured methodology. Document: core values, value conflicts, value priorities. Values must be specific, measurable, and actionable.",
            mandatory=True,
            test_procedure="Review value elicitation process, verify stakeholder participation, validate value documentation",
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.3",
            tags={"values", "stakeholders", "ethics"},
        ),
        Control(
            control_id="IEEE-7000-5.4",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Value-Based Requirements",
            description="Translate stakeholder values into verifiable system requirements. Requirements must be: traceable to values, testable, prioritized. Include acceptance criteria.",
            mandatory=True,
            test_procedure="Review requirements traceability matrix, verify value linkage, validate testability",
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.4",
            tags={"requirements", "values", "traceability"},
        ),
        Control(
            control_id="IEEE-7000-5.5",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Ethical Risk Assessment",
            description="Conduct ethical risk assessment throughout system lifecycle. Identify: value conflicts, unintended consequences, potential harms to stakeholders. Document mitigation strategies.",
            mandatory=True,
            test_procedure="Review ethical risk assessment, verify mitigation strategies, validate stakeholder review",
            evidence_required=[
                EvidenceType.RISK_ASSESSMENT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.5",
            tags={"ethics", "risk-assessment"},
        ),
        Control(
            control_id="IEEE-7000-5.7",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.TECHNICAL,
            title="Transparency and Explainability",
            description="System design must incorporate transparency and explainability appropriate to stakeholder needs. Users must understand: how system works, why decisions were made, limitations of system.",
            mandatory=True,
            test_procedure="Test explainability features, verify transparency documentation, validate user understanding",
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="Section 5.7",
            tags={"transparency", "explainability", "xai"},
        ),
        Control(
            control_id="IEEE-7000-6.1",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.TESTING,
            title="Value Verification and Validation",
            description="Verify that system requirements align with stakeholder values. Validate that implemented system meets value-based requirements. Conduct stakeholder acceptance testing.",
            mandatory=True,
            test_procedure="Execute value validation tests, conduct stakeholder acceptance testing, verify requirement satisfaction",
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 6.1",
            tags={"testing", "validation", "values"},
        ),
    ],
)


# ============================================================================
# REGULATION REGISTRY
# ============================================================================

REGULATION_REGISTRY: Dict[RegulationType, Regulation] = {
    RegulationType.EU_AI_ACT: EU_AI_ACT,
    RegulationType.GDPR: GDPR,
    RegulationType.NIST_AI_RMF: NIST_AI_RMF,
    RegulationType.US_EO_14110: US_EO_14110,
    RegulationType.BRAZIL_LGPD: BRAZIL_LGPD,
    RegulationType.ISO_27001: ISO_27001,
    RegulationType.SOC2_TYPE_II: SOC2_TYPE_II,
    RegulationType.IEEE_7000: IEEE_7000,
}


def get_regulation(regulation_type: RegulationType) -> Regulation:
    """
    Get regulation definition by type.

    Args:
        regulation_type: Type of regulation to retrieve

    Returns:
        Regulation object

    Raises:
        ValueError: If regulation type not found
    """
    if regulation_type not in REGULATION_REGISTRY:
        raise ValueError(f"Regulation {regulation_type} not found in registry")
    return REGULATION_REGISTRY[regulation_type]
