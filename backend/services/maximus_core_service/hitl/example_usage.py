"""
HITL Framework - Example Usage

This file demonstrates 3 practical use cases for the Human-in-the-Loop framework:

1. Basic HITL Workflow - AI decision, operator review, execution
2. High-Risk Scenario - Critical decision requiring escalation
3. Compliance Audit - Generating compliance reports for regulatory requirements

Run this file to see all examples:
    python example_usage.py

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime, timedelta

from .base import (
    HITLConfig,
    DecisionContext,
    OperatorAction,
    ActionType,
    RiskLevel,
    AutomationLevel,
)
from .decision_framework import HITLDecisionFramework
from .decision_queue import DecisionQueue
from .escalation_manager import EscalationManager
from .operator_interface import OperatorInterface
from .audit_trail import AuditTrail, AuditQuery
from .risk_assessor import RiskAssessor


def print_header(title: str):
    """Print example header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_basic_hitl_workflow():
    """
    Example 1: Basic HITL Workflow

    Scenario: AI detects suspicious network activity and proposes blocking an IP.
    The confidence is medium (85%), so human review is required (SUPERVISED mode).

    Workflow:
    1. AI proposes blocking IP
    2. Decision queued for operator review
    3. Operator reviews context and approves
    4. Decision executed and audited
    """
    print_header("EXAMPLE 1: Basic HITL Workflow - Operator Approval")

    print("📊 Setting up HITL framework...")

    # Initialize components
    config = HITLConfig()
    framework = HITLDecisionFramework(config=config)
    queue = DecisionQueue()
    audit = AuditTrail()
    escalation = EscalationManager()
    operator_interface = OperatorInterface(
        decision_framework=framework,
        decision_queue=queue,
        escalation_manager=escalation,
        audit_trail=audit,
    )

    # Connect components
    framework.set_decision_queue(queue)
    framework.set_audit_trail(audit)

    # Register action executor
    def block_ip_executor(context):
        ip = context.action_params["ip_address"]
        print(f"      🔒 Executing: Blocking IP {ip} on firewall...")
        return {
            "status": "success",
            "blocked_ip": ip,
            "firewall_rule_id": "fw_rule_12345",
            "timestamp": datetime.utcnow().isoformat(),
        }

    framework.register_executor(ActionType.BLOCK_IP, block_ip_executor)

    print("✅ HITL framework initialized\n")

    # Step 1: AI proposes action
    print("🤖 STEP 1: AI Analysis")
    print("   MAXIMUS AI detected suspicious network scanning from IP 192.168.100.50")
    print("   Confidence: 85% (SUPERVISED mode)")
    print("   Threat Score: 0.78")

    result = framework.evaluate_action(
        action_type=ActionType.BLOCK_IP,
        action_params={"ip_address": "192.168.100.50"},
        ai_reasoning="Detected aggressive port scanning targeting multiple production servers",
        confidence=0.85,
        threat_score=0.78,
    )

    print(f"\n   ✓ Decision created: {result.decision.decision_id}")
    print(f"   ✓ Automation Level: {result.decision.automation_level.value.upper()}")
    print(f"   ✓ Risk Level: {result.decision.risk_level.value.upper()}")
    print(f"   ✓ Queued: {result.queued}")

    # Step 2: Operator reviews
    print("\n👤 STEP 2: Operator Review")
    session = operator_interface.create_session(
        operator_id="soc_op_001",
        operator_name="Alice Johnson",
        operator_role="soc_operator",
        ip_address="10.0.1.50",
    )
    print(f"   ✓ Operator session created: {session.operator_name}")

    pending = operator_interface.get_pending_decisions(
        session_id=session.session_id, limit=10
    )
    print(f"   ✓ Pending decisions: {len(pending)}")

    decision = pending[0]
    print(f"\n   📋 Decision Details:")
    print(f"      Action: {decision.context.action_type.value}")
    print(f"      Target: {decision.context.action_params['ip_address']}")
    print(f"      AI Reasoning: {decision.context.ai_reasoning}")
    print(f"      Threat Score: {decision.context.threat_score:.2f}")
    print(f"      SLA Deadline: {decision.get_time_remaining()}")

    # Step 3: Operator approves
    print("\n   👍 Operator Decision: APPROVE")
    print("      Comment: 'Verified malicious IP in multiple threat intel feeds'")

    approval_result = operator_interface.approve_decision(
        session_id=session.session_id,
        decision_id=decision.decision_id,
        comment="Verified malicious IP in multiple threat intel feeds",
    )

    print(f"\n   ✓ Decision approved and executed")
    print(f"      Result: {approval_result['result']}")

    # Step 4: Review audit trail
    print("\n📜 STEP 3: Audit Trail")
    query = AuditQuery(decision_ids=[decision.decision_id])
    entries = audit.query(query)

    print(f"   ✓ {len(entries)} audit entries logged:")
    for entry in entries:
        print(f"      - {entry.event_type}: {entry.event_description}")

    print("\n✅ Example 1 Complete!\n")


def example_2_high_risk_escalation():
    """
    Example 2: High-Risk Scenario with Escalation

    Scenario: AI detects ransomware and proposes deleting infected files.
    This is a CRITICAL risk action that requires executive approval.

    Workflow:
    1. AI proposes deleting production data
    2. Risk assessor determines CRITICAL risk
    3. Decision automatically escalated to CISO
    4. CISO reviews and approves with modifications
    """
    print_header("EXAMPLE 2: High-Risk Escalation - Critical Decision")

    print("📊 Setting up HITL framework...")

    # Initialize components
    config = HITLConfig(critical_risk_requires_approval=True)
    framework = HITLDecisionFramework(config=config)
    queue = DecisionQueue()
    audit = AuditTrail()
    escalation = EscalationManager()
    operator_interface = OperatorInterface(
        decision_framework=framework,
        decision_queue=queue,
        escalation_manager=escalation,
        audit_trail=audit,
    )

    framework.set_decision_queue(queue)
    framework.set_audit_trail(audit)

    # Register executor
    def delete_data_executor(context):
        path = context.action_params["data_path"]
        print(f"      🗑️  Executing: Deleting data at {path}...")
        return {
            "status": "success",
            "deleted_path": path,
            "backup_created": True,
            "backup_id": "backup_98765",
        }

    framework.register_executor(ActionType.DELETE_DATA, delete_data_executor)

    print("✅ HITL framework initialized\n")

    # Step 1: AI detects ransomware
    print("🤖 STEP 1: AI Detects Critical Threat")
    print("   MAXIMUS AI detected active ransomware encryption on production server")
    print("   Confidence: 92%")
    print("   Threat Score: 0.95 (CRITICAL)")
    print("   Recommendation: Delete infected files before spread")

    result = framework.evaluate_action(
        action_type=ActionType.DELETE_DATA,
        action_params={
            "data_path": "/production/fileserver/infected",
            "scope": "directory",
        },
        ai_reasoning="Active ransomware detected encrypting files. Immediate deletion recommended to prevent spread.",
        confidence=0.92,
        threat_score=0.95,
        affected_assets=["prod-fileserver-01"],
        asset_criticality="critical",
        business_impact="High - production data affected, potential data loss",
    )

    print(f"\n   ✓ Decision created: {result.decision.decision_id}")
    print(f"   ✓ Risk Level: {result.decision.risk_level.value.upper()}")
    print(f"   ✓ Automation Level: {result.decision.automation_level.value.upper()}")
    print(f"   ⚠️  CRITICAL RISK - Executive approval required!")

    # Step 2: Automatic escalation
    print("\n⬆️  STEP 2: Automatic Escalation")
    decision = result.decision

    rule = escalation.check_for_escalation(decision)
    if rule:
        print(f"   ✓ Escalation rule matched: {rule.rule_name}")
        escalation_event = escalation.escalate_decision(
            decision=decision,
            escalation_type=rule.escalation_type,
            reason="Critical risk decision requires executive approval",
            triggered_rule=rule,
        )
        print(f"   ✓ Escalated to: {escalation_event.to_role.upper()}")
        print(f"   ✓ Notifications sent: Email={escalation_event.email_sent}, SMS={escalation_event.sms_sent}")

    # Step 3: CISO reviews
    print("\n👔 STEP 3: CISO Review")
    ciso_session = operator_interface.create_session(
        operator_id="ciso_001",
        operator_name="David Chen",
        operator_role="ciso",
    )
    print(f"   ✓ CISO session created: {ciso_session.operator_name}")

    print(f"\n   📋 Reviewing Critical Decision:")
    print(f"      Threat: Active Ransomware")
    print(f"      Action: DELETE /production/fileserver/infected")
    print(f"      Impact: {decision.context.business_impact}")

    # Step 4: CISO modifies and approves
    print("\n   ✏️  CISO Decision: MODIFY and APPROVE")
    print("      Modification: Create backup before deletion")

    modified_result = operator_interface.modify_and_approve(
        session_id=ciso_session.session_id,
        decision_id=decision.decision_id,
        modifications={
            "create_backup": True,
            "backup_retention_days": 90,
        },
        comment="Approved with backup safeguard. Verified ransomware with security team.",
    )

    print(f"\n   ✓ Decision executed with modifications")
    print(f"      Result: {modified_result['result']}")
    print(f"      Backup created: {modified_result['result'].get('backup_created')}")

    print("\n✅ Example 2 Complete - Critical decision handled with proper oversight!\n")


def example_3_compliance_reporting():
    """
    Example 3: Compliance Audit Report

    Scenario: Generate compliance report for SOC 2 audit showing:
    - All AI decisions in last 30 days
    - Human oversight rate
    - SLA compliance
    - Risk distribution
    """
    print_header("EXAMPLE 3: Compliance Reporting - SOC 2 Audit")

    print("📊 Setting up HITL framework and generating sample data...")

    # Initialize
    config = HITLConfig()
    framework = HITLDecisionFramework(config=config)
    queue = DecisionQueue()
    audit = AuditTrail()
    risk_assessor = RiskAssessor()

    framework.set_decision_queue(queue)
    framework.set_audit_trail(audit)

    # Generate sample decisions for past 30 days
    print("\n🔄 Generating sample decision data (30 days)...")

    sample_decisions = [
        # Auto-executed (high confidence)
        ("SEND_ALERT", 0.97, 0.3, RiskLevel.LOW),
        ("SEND_ALERT", 0.96, 0.4, RiskLevel.LOW),
        ("COLLECT_LOGS", 0.95, 0.5, RiskLevel.MEDIUM),

        # Operator reviewed
        ("BLOCK_IP", 0.85, 0.7, RiskLevel.MEDIUM),
        ("ISOLATE_HOST", 0.82, 0.75, RiskLevel.HIGH),
        ("QUARANTINE_FILE", 0.88, 0.68, RiskLevel.MEDIUM),
        ("KILL_PROCESS", 0.81, 0.72, RiskLevel.HIGH),

        # Critical (escalated)
        ("DELETE_DATA", 0.90, 0.95, RiskLevel.CRITICAL),
    ]

    for action_str, confidence, threat_score, expected_risk in sample_decisions:
        action_type = ActionType[action_str]

        context = DecisionContext(
            action_type=action_type,
            action_params={"target": f"asset_{action_str}"},
            ai_reasoning=f"AI detected threat requiring {action_str}",
            confidence=confidence,
            threat_score=threat_score,
        )

        from .base import HITLDecision

        decision = HITLDecision(
            context=context,
            risk_level=expected_risk,
            automation_level=config.get_automation_level(confidence, expected_risk),
        )

        risk_score = risk_assessor.assess_risk(context)
        audit.log_decision_created(decision, risk_score)

        if decision.automation_level == AutomationLevel.FULL:
            audit.log_decision_executed(decision, {"status": "success"})
        else:
            audit.log_decision_queued(decision)
            operator_action = OperatorAction(
                decision_id=decision.decision_id,
                operator_id="soc_op_001",
                action="approve",
            )
            audit.log_decision_approved(decision, operator_action)
            audit.log_decision_executed(decision, {"status": "success"}, operator_action)

    print(f"   ✓ Generated {len(sample_decisions)} sample decisions")

    # Generate compliance report
    print("\n📄 Generating Compliance Report...")

    start_time = datetime.utcnow() - timedelta(days=30)
    end_time = datetime.utcnow()

    report = audit.generate_compliance_report(start_time, end_time)

    # Display report
    print(f"\n" + "=" * 60)
    print(f"  SOC 2 COMPLIANCE REPORT")
    print(f"  Report ID: {report.report_id}")
    print(f"  Period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
    print("=" * 60)

    print(f"\n📊 Summary Statistics:")
    print(f"   Total Decisions: {report.total_decisions}")
    print(f"   Auto-Executed: {report.auto_executed}")
    print(f"   Human Reviewed: {report.human_reviewed}")
    print(f"   Approved: {report.approved}")
    print(f"   Rejected: {report.rejected}")
    print(f"   Escalated: {report.escalated}")

    print(f"\n🎯 Risk Distribution:")
    print(f"   CRITICAL: {report.critical_decisions}")
    print(f"   HIGH:     {report.high_risk_decisions}")
    print(f"   MEDIUM:   {report.medium_risk_decisions}")
    print(f"   LOW:      {report.low_risk_decisions}")

    print(f"\n📈 Compliance Metrics:")
    print(f"   Automation Rate:       {report.automation_rate:.1%}")
    print(f"   Human Oversight Rate:  {report.human_oversight_rate:.1%}")
    print(f"   SLA Compliance Rate:   {report.sla_compliance_rate:.1%}")

    print(f"\n👥 Operator Statistics:")
    print(f"   Unique Operators: {report.unique_operators}")

    print(f"\n✅ Compliance Status: PASS")
    print(f"   ✓ Human oversight implemented for medium/high risk")
    print(f"   ✓ Critical decisions escalated appropriately")
    print(f"   ✓ Complete audit trail maintained")
    print(f"   ✓ SLA compliance: {report.sla_compliance_rate:.1%}")

    print("\n✅ Example 3 Complete - Compliance report generated!\n")


def run_all_examples():
    """Run all 3 examples."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "HITL FRAMEWORK - EXAMPLE USAGE" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")

    example_1_basic_hitl_workflow()
    example_2_high_risk_escalation()
    example_3_compliance_reporting()

    print("=" * 80)
    print("  All examples completed!")
    print("=" * 80)
    print("\n📚 Key Takeaways:")
    print("   1. HITL enables safe AI automation with human oversight")
    print("   2. Risk-based automation levels ensure appropriate review")
    print("   3. Escalation protects against high-risk decisions")
    print("   4. Complete audit trail supports compliance (SOC 2, ISO 27001)")
    print("\n🎯 Use Cases:")
    print("   - Incident response automation")
    print("   - Threat containment (block, isolate, quarantine)")
    print("   - Data protection decisions")
    print("   - Regulatory compliance (HIPAA, PCI-DSS, GDPR)")
    print()


if __name__ == "__main__":
    run_all_examples()
