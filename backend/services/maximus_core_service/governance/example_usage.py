"""
Governance Module - Example Usage

Demonstrates 3 practical use cases for the governance module:
1. ERB Meeting & Decision Making
2. Policy Enforcement
3. Whistleblower Report Handling

Run: python example_usage.py

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime, timedelta

from .base import (
    ERBMemberRole,
    GovernanceConfig,
    PolicySeverity,
    PolicyType,
    WhistleblowerReport,
)
from .ethics_review_board import ERBManager
from .policy_engine import PolicyEngine


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_erb_meeting_decision():
    """
    Example 1: ERB Meeting & Decision Making

    Scenario: ERB reviews and approves new Ethical Use Policy.
    """
    print_header("EXAMPLE 1: ERB Meeting & Decision Making")

    config = GovernanceConfig()
    erb = ERBManager(config)

    # Step 1: Add ERB members
    print("📋 STEP 1: Adding ERB Members")
    members = [
        ("Dr. Alice Chen", "alice@vertice.ai", ERBMemberRole.CHAIR, ["AI Ethics", "Philosophy"]),
        ("Bob Martinez", "bob@vertice.ai", ERBMemberRole.VICE_CHAIR, ["Legal", "Compliance"]),
        ("Carol Kim", "carol@vertice.ai", ERBMemberRole.TECHNICAL_MEMBER, ["Cybersecurity"]),
        ("David Brown", "david@external.com", ERBMemberRole.EXTERNAL_ADVISOR, ["AI Safety"]),
    ]

    for name, email, role, expertise in members:
        result = erb.add_member(
            name, email, role, "VÉRTICE" if role != ERBMemberRole.EXTERNAL_ADVISOR else "External", expertise
        )
        print(f"   ✓ Added: {name} ({role.value})")

    # Step 2: Schedule meeting
    print("\n📅 STEP 2: Scheduling ERB Meeting")
    meeting_date = datetime.utcnow() + timedelta(days=7)
    meeting_result = erb.schedule_meeting(
        scheduled_date=meeting_date,
        agenda=["Review Ethical Use Policy v1.0", "Q4 Ethics Audit Results"],
        duration_minutes=120,
    )
    meeting_id = meeting_result.entity_id
    print(f"   ✓ Meeting scheduled for {meeting_date.strftime('%Y-%m-%d %H:%M')}")

    # Step 3: Record attendance
    print("\n👥 STEP 3: Recording Attendance")
    attendee_ids = [m.member_id for m in erb.get_voting_members()]
    attendance_result = erb.record_attendance(meeting_id, attendee_ids[:3], attendee_ids[3:])
    print(f"   ✓ Quorum met: {attendance_result.metadata.get('quorum_met')}")
    print(f"   ✓ Voting attendees: {attendance_result.metadata.get('voting_attendees')}")

    # Step 4: Record decision
    print("\n🗳️  STEP 4: Recording Decision")
    decision_result = erb.record_decision(
        meeting_id=meeting_id,
        title="Approve Ethical Use Policy v1.0",
        description="Approve VÉRTICE Ethical Use Policy version 1.0",
        votes_for=3,
        votes_against=0,
        votes_abstain=0,
        rationale="Policy aligns with EU AI Act and organizational values",
        related_policies=[PolicyType.ETHICAL_USE],
    )
    print(f"   ✓ Decision: {erb.decisions[decision_result.entity_id].decision_type.value}")
    print(f"   ✓ Approval rate: {decision_result.metadata['approval_percentage']:.1f}%")

    print("\n✅ Example 1 Complete!\n")


def example_2_policy_enforcement():
    """
    Example 2: Policy Enforcement

    Scenario: Security analyst attempts to execute red team operation.
    Policy engine validates against all policies.
    """
    print_header("EXAMPLE 2: Policy Enforcement")

    config = GovernanceConfig()
    engine = PolicyEngine(config)

    # Scenario 1: Authorized red team operation
    print("🎯 SCENARIO 1: Authorized Red Team Operation")
    result1 = engine.enforce_policy(
        policy_type=PolicyType.RED_TEAMING,
        action="execute_exploit",
        context={
            "written_authorization": True,
            "target_environment": "test",
            "roe_defined": True,
            "logged": True,
        },
        actor="red_team_lead",
    )
    print(f"   Compliant: {result1.is_compliant}")
    print(f"   Checked rules: {result1.checked_rules}")
    print(f"   Violations: {len(result1.violations)}")

    # Scenario 2: Unauthorized action
    print("\n🚨 SCENARIO 2: Unauthorized Action (Should Fail)")
    result2 = engine.enforce_policy(
        policy_type=PolicyType.RED_TEAMING,
        action="execute_exploit",
        context={
            "written_authorization": False,
            "target_environment": "production",
        },
        actor="unauthorized_user",
    )
    print(f"   Compliant: {result2.is_compliant}")
    print(f"   Violations: {len(result2.violations)}")
    if result2.violations:
        print(f"   First violation: {result2.violations[0].title}")

    # Scenario 3: Data privacy check
    print("\n🔒 SCENARIO 3: Data Privacy Check")
    result3 = engine.enforce_policy(
        policy_type=PolicyType.DATA_PRIVACY,
        action="store_personal_data",
        context={
            "encrypted": True,
            "legal_basis": "consent",
            "logged": True,
        },
        actor="system",
    )
    print(f"   Compliant: {result3.is_compliant}")
    print(f"   Compliance: {result3.compliance_percentage():.1f}%")

    print("\n✅ Example 2 Complete!\n")


def example_3_whistleblower_report():
    """
    Example 3: Whistleblower Report Handling

    Scenario: Anonymous whistleblower reports ethical concern.
    """
    print_header("EXAMPLE 3: Whistleblower Report Handling")

    # Create anonymous whistleblower report
    print("📢 STEP 1: Submitting Anonymous Whistleblower Report")
    report = WhistleblowerReport(
        submission_date=datetime.utcnow(),
        reporter_id=None,  # Anonymous
        is_anonymous=True,
        title="Unauthorized use of offensive tools",
        description="Observed red team tools being used against non-authorized targets",
        alleged_violation_type=PolicyType.RED_TEAMING,
        severity=PolicySeverity.HIGH,
        affected_systems=["offensive_gateway", "c2_orchestration_service"],
        evidence=["logs/2025-10-06-suspicious-activity.log"],
        status="submitted",
        retaliation_concerns=True,
    )
    print(f"   ✓ Report ID: {report.report_id}")
    print(f"   ✓ Anonymous: {report.is_anonymous}")
    print(f"   ✓ Severity: {report.severity.value}")

    # Assign investigator
    print("\n🔍 STEP 2: Assigning Investigator")
    report.status = "under_review"
    report.assigned_investigator = "security_lead@vertice.ai"
    print(f"   ✓ Status: {report.status}")
    print(f"   ✓ Investigator: {report.assigned_investigator}")

    # Apply protection measures
    print("\n🛡️  STEP 3: Applying Whistleblower Protection")
    report.protection_measures = [
        "Anonymous identity maintained",
        "No retaliation monitoring active",
        "Legal support available if needed",
    ]
    for measure in report.protection_measures:
        print(f"   ✓ {measure}")

    # Resolve
    print("\n✅ STEP 4: Investigation Complete")
    report.status = "resolved"
    report.resolution = "Violation confirmed. Tools access revoked. Additional training mandated."
    report.resolution_date = datetime.utcnow()
    report.escalated_to_erb = True
    print(f"   ✓ Resolution: {report.resolution}")
    print(f"   ✓ Escalated to ERB: {report.escalated_to_erb}")

    print("\n✅ Example 3 Complete!\n")


def run_all_examples():
    """Run all examples."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "GOVERNANCE MODULE - EXAMPLES" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")

    example_1_erb_meeting_decision()
    example_2_policy_enforcement()
    example_3_whistleblower_report()

    print("=" * 80)
    print("  All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_examples()
