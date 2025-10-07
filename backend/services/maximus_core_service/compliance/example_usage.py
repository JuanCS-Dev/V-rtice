"""
Compliance System - Example Usage

This file demonstrates 3 practical use cases for the compliance and certification system:

1. Basic Compliance Check - Check compliance for ISO 27001
2. Gap Analysis & Remediation - Create remediation plan for GDPR
3. Certification Readiness - Prepare for ISO 27001 certification audit

Run this file to see all examples:
    python example_usage.py

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime, timedelta
import tempfile
import os

from .base import (
    ComplianceConfig,
    Control,
    Evidence,
    EvidenceType,
    RegulationType,
    ControlCategory,
)
from .regulations import get_regulation
from .compliance_engine import ComplianceEngine
from .evidence_collector import EvidenceCollector
from .gap_analyzer import GapAnalyzer
from .monitoring import ComplianceMonitor
from .certifications import ISO27001Checker, SOC2Checker


def print_header(title: str):
    """Print example header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_basic_compliance_check():
    """
    Example 1: Basic Compliance Check

    Scenario: Security team wants to check current ISO 27001 compliance status.

    Workflow:
    1. Initialize compliance engine
    2. Run compliance check for ISO 27001
    3. View compliance status and violations
    4. Generate compliance report
    """
    print_header("EXAMPLE 1: Basic Compliance Check - ISO 27001")

    print("🔧 Setting up compliance engine...")

    # Initialize compliance engine
    config = ComplianceConfig(
        enabled_regulations=[RegulationType.ISO_27001],
        alert_threshold_percentage=80.0,
    )
    engine = ComplianceEngine(config)

    print("✅ Compliance engine initialized\n")

    # Step 1: Run compliance check
    print("📊 STEP 1: Running ISO 27001 Compliance Check")
    print("   Checking 7 ISO 27001 controls...")

    result = engine.check_compliance(RegulationType.ISO_27001)

    print(f"\n   ✓ Compliance check complete")
    print(f"   ✓ Total controls: {result.total_controls}")
    print(f"   ✓ Compliant: {result.compliant}")
    print(f"   ✓ Non-compliant: {result.non_compliant}")
    print(f"   ✓ Partially compliant: {result.partially_compliant}")
    print(f"   ✓ Pending review: {result.pending_review}")
    print(f"   ✓ Evidence required: {result.evidence_required}")

    # Step 2: View compliance percentage and score
    print(f"\n📈 STEP 2: Compliance Metrics")
    print(f"   Compliance Percentage: {result.compliance_percentage:.1f}%")
    print(f"   Compliance Score: {result.score:.2f}/1.00")

    if result.compliance_percentage >= 95:
        print(f"   ✅ EXCELLENT - Ready for certification!")
    elif result.compliance_percentage >= 80:
        print(f"   ⚠️  GOOD - Close to certification readiness")
    elif result.compliance_percentage >= 60:
        print(f"   ⚠️  FAIR - More work needed")
    else:
        print(f"   ❌ NEEDS IMPROVEMENT - Significant gaps")

    # Step 3: Review violations
    print(f"\n🚨 STEP 3: Violations Detected")
    if result.violations:
        print(f"   Found {len(result.violations)} violations:")
        for v in result.violations[:3]:  # Show first 3
            print(f"      - [{v.severity.value.upper()}] {v.title}")
    else:
        print(f"   ✅ No violations detected")

    # Step 4: Generate compliance report
    print(f"\n📄 STEP 4: Generating Compliance Report")

    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    report = engine.generate_compliance_report(
        start_date,
        end_date,
        regulation_types=[RegulationType.ISO_27001],
    )

    print(f"   ✓ Report ID: {report['report_id']}")
    print(f"   ✓ Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   ✓ Overall Compliance: {report['summary']['overall_compliance_percentage']:.1f}%")

    print("\n✅ Example 1 Complete!\n")


def example_2_gap_analysis_remediation():
    """
    Example 2: Gap Analysis & Remediation Planning

    Scenario: Compliance officer needs to identify GDPR gaps and create remediation plan.

    Workflow:
    1. Run GDPR compliance check
    2. Analyze compliance gaps
    3. Prioritize gaps by severity
    4. Create remediation plan
    5. Track remediation progress
    """
    print_header("EXAMPLE 2: Gap Analysis & Remediation Planning - GDPR")

    print("🔧 Setting up compliance system...")

    # Initialize components
    config = ComplianceConfig(enabled_regulations=[RegulationType.GDPR])
    engine = ComplianceEngine(config)
    analyzer = GapAnalyzer(config)

    print("✅ Compliance system initialized\n")

    # Step 1: Run GDPR compliance check
    print("📊 STEP 1: Running GDPR Compliance Check")
    print("   Checking GDPR Article 22 (Automated Decision-Making)...")

    result = engine.check_compliance(RegulationType.GDPR)

    print(f"\n   ✓ Compliance: {result.compliance_percentage:.1f}%")
    print(f"   ✓ Non-compliant controls: {result.non_compliant}")

    # Step 2: Analyze gaps
    print("\n🔍 STEP 2: Analyzing Compliance Gaps")

    gap_analysis = analyzer.analyze_compliance_gaps(result)

    print(f"   ✓ Total gaps identified: {len(gap_analysis.gaps)}")
    print(f"   ✓ Critical gaps: {len(gap_analysis.get_gaps_by_severity('critical'))}")
    print(f"   ✓ Estimated effort: {gap_analysis.estimated_remediation_hours} hours")

    # Step 3: Show top gaps
    print("\n📋 STEP 3: Top Priority Gaps")

    if gap_analysis.gaps:
        for gap in gap_analysis.gaps[:5]:  # Show top 5
            print(f"      [{gap.severity.value.upper()}] Priority {gap.priority}: {gap.title}")
            print(f"         Current: {gap.current_state}")
            print(f"         Required: {gap.required_state[:80]}...")
            print(f"         Effort: {gap.estimated_effort_hours}h\n")
    else:
        print("   ✅ No gaps found - fully compliant!")

    # Step 4: Create remediation plan
    print("📝 STEP 4: Creating Remediation Plan")

    plan = analyzer.create_remediation_plan(
        gap_analysis,
        target_completion_days=180,
        created_by="compliance_officer",
    )

    print(f"   ✓ Plan ID: {plan.plan_id}")
    print(f"   ✓ Total remediation actions: {len(plan.actions)}")
    print(f"   ✓ Target completion: {plan.target_completion_date.strftime('%Y-%m-%d')}")
    print(f"   ✓ Status: {plan.status}")

    # Show top actions
    print("\n   📌 Top Remediation Actions:")
    for action in plan.actions[:3]:
        print(f"      - {action.title}")
        print(f"        Due: {action.due_date.strftime('%Y-%m-%d') if action.due_date else 'TBD'}")
        print(f"        Effort: {action.estimated_hours}h\n")

    # Step 5: Track progress
    print("📊 STEP 5: Remediation Progress Tracking")

    progress = analyzer.track_remediation_progress(plan)

    print(f"   Completion: {progress['completion_percentage']:.1f}%")
    print(f"   Status: {progress['status']}")
    print(f"   Actions completed: {progress['actions_completed']}/{progress['total_actions']}")
    print(f"   Actions in progress: {progress['actions_in_progress']}")
    print(f"   Overdue actions: {progress['overdue_actions']}")

    print("\n✅ Example 2 Complete - Remediation plan created!\n")


def example_3_certification_readiness():
    """
    Example 3: Certification Readiness Assessment

    Scenario: Organization wants to prepare for ISO 27001 certification audit.

    Workflow:
    1. Collect evidence from multiple sources
    2. Run ISO 27001 certification readiness check
    3. Review certification gaps and recommendations
    4. Create evidence package for auditor
    5. Start compliance monitoring
    """
    print_header("EXAMPLE 3: ISO 27001 Certification Readiness")

    print("🔧 Setting up certification assessment system...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize components
        config = ComplianceConfig(
            enabled_regulations=[RegulationType.ISO_27001],
            evidence_storage_path=tmpdir,
        )
        engine = ComplianceEngine(config)
        collector = EvidenceCollector(config)
        checker = ISO27001Checker(engine, collector)
        monitor = ComplianceMonitor(engine, collector, config=config)

        print("✅ Certification system initialized\n")

        # Step 1: Collect evidence
        print("📂 STEP 1: Collecting Compliance Evidence")

        # Get ISO 27001 controls
        regulation = get_regulation(RegulationType.ISO_27001)

        # Simulate evidence collection for policy control
        policy_control = regulation.get_control("ISO-27001-A.5.1")
        if policy_control:
            # Create mock policy document
            policy_file = os.path.join(tmpdir, "InfoSec_Policy.pdf")
            with open(policy_file, "w") as f:
                f.write("Information Security Policy v1.0\n")
                f.write("Approved by: CISO\n")
                f.write("Date: 2025-01-01\n")

            collector.collect_policy_evidence(
                policy_control,
                policy_file,
                "Information Security Policy v1.0",
                "Organization-wide information security policy",
            )
            print("   ✓ Collected: Information Security Policy")

        # Simulate evidence for access control
        access_control = regulation.get_control("ISO-27001-A.8.2")
        if access_control:
            config_file = os.path.join(tmpdir, "access_control_config.txt")
            with open(config_file, "w") as f:
                f.write("Privileged Access Controls:\n")
                f.write("- MFA enabled for all admin accounts\n")
                f.write("- Least privilege enforcement\n")

            collector.collect_configuration_evidence(
                access_control,
                config_file,
                "Access Control Configuration",
                "Privileged access control settings",
            )
            print("   ✓ Collected: Access Control Configuration")

        all_evidence = collector.get_all_evidence()
        total_evidence = sum(len(e) for e in all_evidence.values())
        print(f"\n   ✅ Total evidence collected: {total_evidence} items")

        # Step 2: Run certification readiness check
        print("\n🎯 STEP 2: ISO 27001 Certification Readiness Check")

        cert_result = checker.check_certification_readiness(all_evidence)

        print(f"\n   {cert_result.get_summary()}")
        print(f"\n   📊 Metrics:")
        print(f"      Compliance: {cert_result.compliance_percentage:.1f}%")
        print(f"      Score: {cert_result.score:.2f}/1.00")
        print(f"      Gaps: {cert_result.gaps_to_certification}")
        print(f"      Critical gaps: {len(cert_result.critical_gaps)}")

        # Step 3: Review recommendations
        print("\n💡 STEP 3: Certification Recommendations")

        if cert_result.recommendations:
            print(f"   Top {min(5, len(cert_result.recommendations))} recommendations:")
            for i, rec in enumerate(cert_result.recommendations[:5], 1):
                print(f"      {i}. {rec}")
        else:
            print("   ✅ No recommendations - ready for certification!")

        # Step 4: Create evidence package for auditor
        print("\n📦 STEP 4: Creating Evidence Package for Auditor")

        package = collector.create_evidence_package(RegulationType.ISO_27001)

        print(f"   ✓ Package ID: {package.package_id}")
        print(f"   ✓ Evidence items: {len(package.evidence_items)}")
        print(f"   ✓ Total size: {package.total_size_bytes} bytes")
        print(f"   ✓ Controls covered: {len(package.control_ids)}")

        # Export package
        export_path = os.path.join(tmpdir, "audit_package")
        success = collector.export_evidence_package(package, export_path)

        if success:
            print(f"   ✅ Evidence package exported to: {export_path}")
        else:
            print(f"   ❌ Failed to export evidence package")

        # Step 5: Start monitoring
        print("\n📡 STEP 5: Starting Compliance Monitoring")

        # Register custom alert handler
        def alert_handler(alert):
            print(f"      🚨 ALERT: [{alert.severity.value.upper()}] {alert.title}")

        monitor.register_alert_handler(alert_handler)

        # Run single monitoring check (instead of continuous)
        monitor._run_monitoring_checks()

        # Get current metrics
        metrics = monitor.get_current_metrics()
        if metrics:
            print(f"\n   ✓ Monitoring active")
            print(f"   ✓ Overall compliance: {metrics.overall_compliance_percentage:.1f}%")
            print(f"   ✓ Trend: {metrics.compliance_trend}")
            print(f"   ✓ Total violations: {metrics.total_violations}")

        # Get dashboard data
        print("\n📊 STEP 6: Compliance Dashboard")

        dashboard = monitor.generate_dashboard_data()

        if "current_metrics" in dashboard:
            print(f"   Overall Compliance: {dashboard['current_metrics']['overall_compliance']:.1f}%")
            print(f"   Trend: {dashboard['current_metrics']['trend']}")
            print(f"   Violations:")
            for severity, count in dashboard['violations_by_severity'].items():
                print(f"      - {severity}: {count}")

    print("\n✅ Example 3 Complete - Certification readiness assessed!\n")


def run_all_examples():
    """Run all 3 examples."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "COMPLIANCE SYSTEM - EXAMPLE USAGE" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")

    example_1_basic_compliance_check()
    example_2_gap_analysis_remediation()
    example_3_certification_readiness()

    print("=" * 80)
    print("  All examples completed!")
    print("=" * 80)
    print("\n📚 Key Takeaways:")
    print("   1. Compliance engine enables automated compliance checking for 8 regulations")
    print("   2. Gap analyzer identifies gaps and creates actionable remediation plans")
    print("   3. Evidence collector automates evidence gathering for audits")
    print("   4. Certification checkers assess readiness for ISO 27001, SOC 2, IEEE 7000")
    print("   5. Compliance monitoring provides real-time alerts and trend analysis")
    print("\n🎯 Use Cases:")
    print("   - Continuous compliance monitoring (ISO 27001, SOC 2, GDPR, etc.)")
    print("   - Certification preparation (ISO 27001, SOC 2 Type II, IEEE 7000)")
    print("   - Regulatory compliance (EU AI Act, NIST AI RMF, LGPD)")
    print("   - Audit preparation and evidence management")
    print("   - Gap analysis and remediation tracking")
    print()


if __name__ == "__main__":
    run_all_examples()
