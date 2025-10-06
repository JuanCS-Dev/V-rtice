"""
Governance Module - Ethical Policies

Defines and implements the 5 core ethical policies for the VÉRTICE platform:
1. Ethical Use Policy
2. Red Teaming Policy
3. Data Privacy Policy
4. Incident Response Policy
5. Whistleblower Protection Policy

Each policy includes specific rules, validation logic, and enforcement guidelines.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime, timedelta
from typing import Dict, List

from .base import Policy, PolicySeverity, PolicyType


# ============================================================================
# POLICY DEFINITIONS
# ============================================================================


def create_ethical_use_policy() -> Policy:
    """
    Create Ethical Use Policy.

    Defines acceptable use of VÉRTICE's autonomous capabilities,
    focusing on preventing misuse and ensuring ethical operation.

    Scope: All systems (MAXIMUS, Immunis, RTE)
    """
    rules = [
        "RULE-EU-001: AI systems MUST NOT be used to cause harm to individuals or organizations without legal authorization",
        "RULE-EU-002: Offensive capabilities (red teaming, exploit development) MUST only be used in authorized environments",
        "RULE-EU-003: All autonomous actions MUST be logged and auditable",
        "RULE-EU-004: AI systems MUST NOT make life-or-death decisions without human oversight",
        "RULE-EU-005: Discrimination based on protected attributes is PROHIBITED",
        "RULE-EU-006: AI systems MUST provide explanations for critical decisions (XAI requirement)",
        "RULE-EU-007: Users MUST be informed when interacting with AI systems",
        "RULE-EU-008: AI systems MUST respect intellectual property and licensing",
        "RULE-EU-009: Deceptive practices (fake identities, social engineering against non-authorized targets) are PROHIBITED",
        "RULE-EU-010: AI autonomy level MUST be appropriate for task criticality (HITL for high-risk)",
    ]

    policy = Policy(
        policy_type=PolicyType.ETHICAL_USE,
        version="1.0",
        title="VÉRTICE Ethical Use Policy",
        description=(
            "Defines ethical boundaries for using VÉRTICE's autonomous cybersecurity capabilities. "
            "Ensures AI systems operate within legal and moral constraints, preventing misuse "
            "while enabling legitimate security operations."
        ),
        rules=rules,
        scope="all",
        enforcement_level=PolicySeverity.CRITICAL,
        auto_enforce=True,
        created_date=datetime.utcnow(),
        next_review_date=datetime.utcnow() + timedelta(days=365),
        approved_by_erb=False,  # Requires ERB approval
        stakeholders=[
            "Security Operations Team",
            "Legal Department",
            "Ethics Review Board",
            "Development Team",
        ],
        metadata={
            "policy_owner": "Chief Ethics Officer",
            "compliance_frameworks": ["EU AI Act", "NIST AI RMF", "IEEE 7000"],
            "related_regulations": ["GDPR", "LGPD"],
        },
    )

    return policy


def create_red_teaming_policy() -> Policy:
    """
    Create Red Teaming Policy.

    Governs the use of offensive security capabilities, ensuring they are
    used responsibly and only in authorized contexts.

    Scope: Offensive capabilities (C2, exploit development, network attacks)
    """
    rules = [
        "RULE-RT-001: Red team operations MUST have written authorization from target organization",
        "RULE-RT-002: Rules of Engagement (RoE) MUST be defined and approved before operations",
        "RULE-RT-003: Offensive tools MUST NOT target production systems without explicit approval",
        "RULE-RT-004: Data exfiltrated during red team ops MUST be handled per data classification policy",
        "RULE-RT-005: Social engineering attacks MUST be approved by ERB for each campaign",
        "RULE-RT-006: Exploits MUST NOT be weaponized against real targets without authorization",
        "RULE-RT-007: Third-party targets (vendors, partners) REQUIRE separate authorization",
        "RULE-RT-008: Red team findings MUST be reported within 48 hours of discovery",
        "RULE-RT-009: Exploits discovered MUST be responsibly disclosed per disclosure policy",
        "RULE-RT-010: Autonomous red team actions REQUIRE human approval (HITL) for destructive operations",
        "RULE-RT-011: Red team operations MUST comply with all applicable laws and regulations",
        "RULE-RT-012: Credentials obtained during ops MUST be secured and destroyed after exercise",
    ]

    policy = Policy(
        policy_type=PolicyType.RED_TEAMING,
        version="1.0",
        title="VÉRTICE Red Teaming & Offensive Security Policy",
        description=(
            "Governs the use of VÉRTICE's offensive capabilities including C2 orchestration, "
            "exploit development, and adversarial testing. Ensures offensive operations are "
            "authorized, controlled, and legally compliant."
        ),
        rules=rules,
        scope="offensive_gateway,c2_orchestration_service,web_attack_service,network_recon_service",
        enforcement_level=PolicySeverity.CRITICAL,
        auto_enforce=True,
        created_date=datetime.utcnow(),
        next_review_date=datetime.utcnow() + timedelta(days=365),
        approved_by_erb=False,
        stakeholders=[
            "Red Team",
            "Legal Department",
            "Security Leadership",
            "Ethics Review Board",
            "Clients (for authorized ops)",
        ],
        metadata={
            "policy_owner": "Red Team Lead",
            "legal_review_required": True,
            "insurance_requirements": ["Cyber liability coverage", "E&O insurance"],
            "training_requirements": ["Red team certification", "Legal & ethics training"],
        },
    )

    return policy


def create_data_privacy_policy() -> Policy:
    """
    Create Data Privacy Policy.

    Ensures VÉRTICE platform complies with GDPR, LGPD, and other privacy regulations.
    Governs data collection, processing, retention, and subject rights.

    Scope: All data processing activities
    """
    rules = [
        "RULE-DP-001: Personal data MUST only be collected with valid legal basis (GDPR Art. 6)",
        "RULE-DP-002: Data minimization principle MUST be applied (collect only necessary data)",
        "RULE-DP-003: Data subjects MUST be informed of processing activities (transparency)",
        "RULE-DP-004: Consent MUST be explicit, informed, and revocable",
        "RULE-DP-005: Data retention periods MUST be defined and enforced (max 7 years for audit logs)",
        "RULE-DP-006: Data subject rights MUST be honored within regulatory timelines (30 days GDPR)",
        "RULE-DP-007: Personal data MUST be encrypted at rest and in transit",
        "RULE-DP-008: Data transfers outside EU/Brazil REQUIRE adequacy decision or safeguards",
        "RULE-DP-009: Data breaches MUST be reported within 72 hours (GDPR Art. 33)",
        "RULE-DP-010: Data Protection Impact Assessments (DPIA) REQUIRED for high-risk processing",
        "RULE-DP-011: Automated decision-making MUST allow for human intervention (GDPR Art. 22)",
        "RULE-DP-012: Pseudonymization and anonymization MUST be used where possible",
        "RULE-DP-013: Third-party processors MUST have Data Processing Agreements (DPA)",
        "RULE-DP-014: Privacy by Design and by Default principles MUST be implemented",
    ]

    policy = Policy(
        policy_type=PolicyType.DATA_PRIVACY,
        version="1.0",
        title="VÉRTICE Data Privacy & Protection Policy",
        description=(
            "Ensures VÉRTICE platform complies with GDPR, LGPD, and international data privacy "
            "regulations. Governs data lifecycle management, subject rights, and privacy-preserving "
            "techniques including differential privacy and federated learning."
        ),
        rules=rules,
        scope="all",
        enforcement_level=PolicySeverity.CRITICAL,
        auto_enforce=True,
        created_date=datetime.utcnow(),
        next_review_date=datetime.utcnow() + timedelta(days=365),
        approved_by_erb=False,
        stakeholders=[
            "Data Protection Officer (DPO)",
            "Legal Department",
            "Security Team",
            "Development Team",
            "Data Subjects",
        ],
        metadata={
            "policy_owner": "Data Protection Officer",
            "compliance_frameworks": ["GDPR", "LGPD", "CCPA", "PIPEDA"],
            "dpo_contact": "dpo@vertice.ai",
            "supervisory_authority": "ANPD (Brazil) / EDPB (EU)",
            "dpia_threshold": "Processing personal data of >10,000 individuals",
        },
    )

    return policy


def create_incident_response_policy() -> Policy:
    """
    Create Incident Response Policy.

    Defines procedures for handling ethical violations, security incidents,
    and AI system failures.

    Scope: All incident response procedures
    """
    rules = [
        "RULE-IR-001: Incidents MUST be reported within 1 hour of discovery",
        "RULE-IR-002: Critical incidents REQUIRE immediate ERB notification",
        "RULE-IR-003: Incident severity MUST be assessed within 2 hours",
        "RULE-IR-004: Root cause analysis MUST be completed within 7 days",
        "RULE-IR-005: Affected parties MUST be notified per regulatory requirements (72h for GDPR)",
        "RULE-IR-006: Incident response team MUST be activated for MEDIUM+ severity",
        "RULE-IR-007: Evidence preservation REQUIRED for forensic analysis",
        "RULE-IR-008: Post-incident review REQUIRED within 14 days",
        "RULE-IR-009: Lessons learned MUST be incorporated into policies and systems",
        "RULE-IR-010: AI system behavior leading to incident MUST be logged and analyzed",
        "RULE-IR-011: Containment actions MUST be documented and justified",
        "RULE-IR-012: External authorities MUST be notified per legal requirements",
        "RULE-IR-013: Communication plan MUST be executed for public incidents",
    ]

    policy = Policy(
        policy_type=PolicyType.INCIDENT_RESPONSE,
        version="1.0",
        title="VÉRTICE Incident Response & Management Policy",
        description=(
            "Defines procedures for detecting, responding to, and recovering from incidents "
            "including ethical violations, security breaches, AI failures, and policy violations. "
            "Ensures rapid response, proper escalation, and continuous improvement."
        ),
        rules=rules,
        scope="all",
        enforcement_level=PolicySeverity.HIGH,
        auto_enforce=True,
        created_date=datetime.utcnow(),
        next_review_date=datetime.utcnow() + timedelta(days=365),
        approved_by_erb=False,
        stakeholders=[
            "Incident Response Team",
            "Security Operations Center (SOC)",
            "Legal Department",
            "Public Relations",
            "Ethics Review Board",
        ],
        metadata={
            "policy_owner": "Chief Information Security Officer (CISO)",
            "escalation_contacts": {
                "critical": ["CISO", "CEO", "ERB Chair"],
                "high": ["CISO", "Security Lead"],
                "medium": ["SOC Manager"],
            },
            "regulatory_notification": {
                "GDPR": "72 hours",
                "LGPD": "reasonable timeframe",
                "SEC": "4 days (material incidents)",
            },
            "runbook_location": "docs/incident_response/playbooks/",
        },
    )

    return policy


def create_whistleblower_policy() -> Policy:
    """
    Create Whistleblower Protection Policy.

    Provides safe channels for reporting ethical concerns, violations,
    and misconduct, with protection against retaliation.

    Scope: All employees, contractors, and stakeholders
    """
    rules = [
        "RULE-WB-001: Anonymous reporting MUST be supported and protected",
        "RULE-WB-002: Retaliation against whistleblowers is STRICTLY PROHIBITED",
        "RULE-WB-003: Reports MUST be investigated within 30 days",
        "RULE-WB-004: Whistleblower identity MUST be kept confidential unless legally required",
        "RULE-WB-005: ERB MUST review all CRITICAL severity whistleblower reports",
        "RULE-WB-006: Reporters MUST receive status updates every 14 days during investigation",
        "RULE-WB-007: Good faith reports MUST NOT result in adverse employment actions",
        "RULE-WB-008: False or malicious reports MAY result in disciplinary action",
        "RULE-WB-009: External reporting channels MUST be available (e.g., ethics hotline)",
        "RULE-WB-010: Whistleblower protection extends 365 days after report submission",
        "RULE-WB-011: Legal protections MUST comply with local whistleblower laws",
        "RULE-WB-012: Training on whistleblower rights REQUIRED for all employees annually",
    ]

    policy = Policy(
        policy_type=PolicyType.WHISTLEBLOWER,
        version="1.0",
        title="VÉRTICE Whistleblower Protection Policy",
        description=(
            "Provides safe, confidential channels for reporting ethical concerns, policy violations, "
            "and misconduct within the VÉRTICE platform. Ensures whistleblowers are protected from "
            "retaliation and reports are handled professionally and confidentially."
        ),
        rules=rules,
        scope="all",
        enforcement_level=PolicySeverity.CRITICAL,
        auto_enforce=True,
        created_date=datetime.utcnow(),
        next_review_date=datetime.utcnow() + timedelta(days=365),
        approved_by_erb=False,
        stakeholders=[
            "All Employees",
            "Contractors",
            "Ethics Review Board",
            "Legal Department",
            "Human Resources",
        ],
        metadata={
            "policy_owner": "Chief Ethics Officer",
            "reporting_channels": [
                "Internal: ethics@vertice.ai",
                "Anonymous hotline: +55-XXX-XXXX-XXXX",
                "Web form: https://vertice.ai/whistleblower",
                "ERB Chair direct: erb-chair@vertice.ai",
            ],
            "legal_frameworks": [
                "SOX (Sarbanes-Oxley Act)",
                "Dodd-Frank Act",
                "EU Whistleblowing Directive 2019/1937",
                "Brazilian Anti-Corruption Law 12.846/2013",
            ],
            "protection_measures": [
                "Confidentiality of identity",
                "No adverse employment actions",
                "Legal support if needed",
                "Anonymous reporting option",
            ],
        },
    )

    return policy


# ============================================================================
# POLICY REGISTRY
# ============================================================================


class PolicyRegistry:
    """
    Central registry for all governance policies.

    Provides easy access to policy definitions and management.
    """

    def __init__(self):
        """Initialize policy registry."""
        self.policies: Dict[PolicyType, Policy] = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """Load all default policies."""
        self.policies[PolicyType.ETHICAL_USE] = create_ethical_use_policy()
        self.policies[PolicyType.RED_TEAMING] = create_red_teaming_policy()
        self.policies[PolicyType.DATA_PRIVACY] = create_data_privacy_policy()
        self.policies[PolicyType.INCIDENT_RESPONSE] = create_incident_response_policy()
        self.policies[PolicyType.WHISTLEBLOWER] = create_whistleblower_policy()

    def get_policy(self, policy_type: PolicyType) -> Policy:
        """Get policy by type."""
        if policy_type not in self.policies:
            raise ValueError(f"Policy type {policy_type} not found in registry")
        return self.policies[policy_type]

    def get_all_policies(self) -> List[Policy]:
        """Get all policies."""
        return list(self.policies.values())

    def get_policies_by_scope(self, scope: str) -> List[Policy]:
        """Get policies applicable to a specific scope."""
        return [p for p in self.policies.values() if p.scope == "all" or scope in p.scope]

    def get_policies_requiring_review(self) -> List[Policy]:
        """Get policies that are due for review."""
        return [p for p in self.policies.values() if p.is_due_for_review()]

    def get_unapproved_policies(self) -> List[Policy]:
        """Get policies pending ERB approval."""
        return [p for p in self.policies.values() if not p.approved_by_erb]

    def approve_policy(self, policy_type: PolicyType, erb_decision_id: str):
        """Mark policy as approved by ERB."""
        if policy_type not in self.policies:
            raise ValueError(f"Policy type {policy_type} not found")

        policy = self.policies[policy_type]
        policy.approved_by_erb = True
        policy.erb_decision_id = erb_decision_id
        policy.last_review_date = datetime.utcnow()
        policy.next_review_date = datetime.utcnow() + timedelta(days=365)

    def update_policy_version(
        self,
        policy_type: PolicyType,
        new_version: str,
        updated_rules: List[str],
        description: str,
    ):
        """Update policy to new version."""
        if policy_type not in self.policies:
            raise ValueError(f"Policy type {policy_type} not found")

        policy = self.policies[policy_type]
        policy.version = new_version
        policy.rules = updated_rules
        policy.description = description
        policy.last_review_date = datetime.utcnow()
        policy.next_review_date = datetime.utcnow() + timedelta(days=365)
        policy.approved_by_erb = False  # Requires re-approval

    def get_policy_summary(self) -> Dict[str, any]:
        """Get summary of all policies."""
        return {
            "total_policies": len(self.policies),
            "approved_policies": len([p for p in self.policies.values() if p.approved_by_erb]),
            "pending_approval": len([p for p in self.policies.values() if not p.approved_by_erb]),
            "due_for_review": len(self.get_policies_requiring_review()),
            "policies": {
                policy_type.value: {
                    "version": policy.version,
                    "approved": policy.approved_by_erb,
                    "enforcement_level": policy.enforcement_level.value,
                    "total_rules": len(policy.rules),
                    "days_until_review": policy.days_until_review(),
                }
                for policy_type, policy in self.policies.items()
            },
        }
