"""Example usage of the Ethical AI system.

This script demonstrates how to use the ethical frameworks to evaluate
cybersecurity actions.
"""

import asyncio
from typing import Any, Dict

from .base import ActionContext
from .config import get_config, get_config_for_risk
from .integration_engine import EthicalIntegrationEngine


async def example_1_threat_mitigation():
    """Example: Automated threat mitigation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Automated Threat Mitigation (High Confidence)")
    print("=" * 80)

    # Create action context
    action_context = ActionContext(
        action_type="auto_response",
        action_description="Block IP 192.168.1.100 attacking web server with SQL injection attempts",
        system_component="immunis_neutrophil_service",
        threat_data={
            "severity": 0.85,
            "confidence": 0.95,
            "people_protected": 1000,
            "part_of_campaign": True,
        },
        impact_assessment={
            "disruption_level": 0.1,
            "people_impacted": 1,
            "improves_defenses": True,
        },
        urgency="high",
    )

    # Initialize ethical engine
    config = get_config("production")
    engine = EthicalIntegrationEngine(config)

    # Evaluate
    decision = await engine.evaluate(action_context)

    # Print results
    print(f"\n📋 Action: {action_context.action_description}")
    print(f"🎯 Final Decision: {decision.final_decision}")
    print(f"📊 Confidence: {decision.final_confidence:.2%}")
    print(f"🤝 Framework Agreement: {decision.framework_agreement_rate:.1%}")
    print(f"⏱️  Total Latency: {decision.total_latency_ms}ms")
    print(f"\n💡 Explanation: {decision.explanation}")

    print("\n📊 Individual Framework Results:")
    for name, result in decision.framework_results.items():
        status = "✅ APPROVED" if result.approved else "❌ REJECTED"
        print(
            f"  {name}: {status} (confidence: {result.confidence:.2%}, {result.latency_ms}ms)"
        )


async def example_2_offensive_action():
    """Example: Offensive red team operation (requires human approval)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Offensive Red Team Operation (High Stakes)")
    print("=" * 80)

    action_context = ActionContext(
        action_type="offensive_action",
        action_description="Execute exploit against target.com to test defenses (authorized pentest)",
        system_component="offensive_gateway",
        threat_data={"severity": 0.6, "confidence": 0.7, "people_protected": 50},
        target_info={"target": "target.com", "precision_targeting": True},
        impact_assessment={
            "disruption_level": 0.3,
            "people_impacted": 10,
            "side_effects": [
                {"severity": "medium", "description": "Temporary service degradation"}
            ],
        },
        operator_context={"operator_id": "operator_123", "authorized_pentest": True},
        urgency="medium",
    )

    # Use offensive configuration (stricter)
    config = get_config("offensive")
    engine = EthicalIntegrationEngine(config)

    decision = await engine.evaluate(action_context)

    print(f"\n📋 Action: {action_context.action_description}")
    print(f"🎯 Final Decision: {decision.final_decision}")
    print(f"📊 Confidence: {decision.final_confidence:.2%}")
    print(f"🤝 Framework Agreement: {decision.framework_agreement_rate:.1%}")
    print(f"⏱️  Total Latency: {decision.total_latency_ms}ms")
    print(f"\n💡 Explanation: {decision.explanation}")

    print("\n📊 Individual Framework Results:")
    for name, result in decision.framework_results.items():
        status = "✅ APPROVED" if result.approved else "❌ REJECTED"
        print(f"  {name}: {status} (confidence: {result.confidence:.2%})")


async def example_3_kantian_veto():
    """Example: Action that violates Kantian principles (gets vetoed)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Kantian Veto - Violates Human Dignity")
    print("=" * 80)

    action_context = ActionContext(
        action_type="offensive_action",
        action_description="Deploy social engineering attack against employees without consent (violates dignity)",
        system_component="social_eng_service",
        threat_data={"severity": 0.8, "confidence": 0.9},
        operator_context=None,  # No human authorization
        urgency="low",
    )

    config = get_config("production")
    engine = EthicalIntegrationEngine(config)

    decision = await engine.evaluate(action_context)

    print(f"\n📋 Action: {action_context.action_description}")
    print(f"🎯 Final Decision: {decision.final_decision}")
    print(f"📊 Confidence: {decision.final_confidence:.2%}")
    print(f"🚨 Veto Applied: {decision.veto_applied}")
    print(f"⏱️  Total Latency: {decision.total_latency_ms}ms")
    print(f"\n💡 Explanation: {decision.explanation}")


async def example_4_hitl_escalation():
    """Example: Ambiguous case that escalates to HITL."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: HITL Escalation - Framework Disagreement")
    print("=" * 80)

    action_context = ActionContext(
        action_type="auto_response",
        action_description="Preemptively block IP based on threat intelligence (medium confidence)",
        system_component="immunis_neutrophil",
        threat_data={
            "severity": 0.7,
            "confidence": 0.65,  # Medium confidence
            "people_protected": 500,
        },
        impact_assessment={
            "disruption_level": 0.4,
            "people_impacted": 50,
            "false_positive_risk": 0.35,
        },
        urgency="medium",
    )

    config = get_config("production")
    engine = EthicalIntegrationEngine(config)

    decision = await engine.evaluate(action_context)

    print(f"\n📋 Action: {action_context.action_description}")
    print(f"🎯 Final Decision: {decision.final_decision}")
    print(f"📊 Confidence: {decision.final_confidence:.2%}")
    print(f"🤝 Framework Agreement: {decision.framework_agreement_rate:.1%}")
    print(f"⏱️  Total Latency: {decision.total_latency_ms}ms")
    print(f"\n💡 Explanation: {decision.explanation}")

    if decision.final_decision == "ESCALATED_HITL":
        print("\n⚠️  This decision requires human review!")
        print("   Reason: Framework disagreement or ambiguous ethical situation")


async def example_5_risk_adjusted():
    """Example: Risk-adjusted configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Critical Risk Level - Stricter Thresholds")
    print("=" * 80)

    action_context = ActionContext(
        action_type="policy_update",
        action_description="Update firewall rules to block entire subnet (critical infrastructure)",
        system_component="hcl_executor_service",
        threat_data={"severity": 0.9, "confidence": 0.85, "people_protected": 10000},
        impact_assessment={
            "disruption_level": 0.6,
            "people_impacted": 500,
            "critical_infrastructure": True,
        },
        urgency="critical",
    )

    # Use critical risk configuration
    config = get_config_for_risk("critical", "production")
    engine = EthicalIntegrationEngine(config)

    decision = await engine.evaluate(action_context)

    print(f"\n📋 Action: {action_context.action_description}")
    print(f"🎯 Final Decision: {decision.final_decision}")
    print(f"📊 Confidence: {decision.final_confidence:.2%}")
    print(f"🚨 Risk Level: CRITICAL")
    print(f"⏱️  Total Latency: {decision.total_latency_ms}ms")
    print(f"\n💡 Explanation: {decision.explanation}")


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "VÉRTICE ETHICAL AI SYSTEM EXAMPLES" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")

    await example_1_threat_mitigation()
    await example_2_offensive_action()
    await example_3_kantian_veto()
    await example_4_hitl_escalation()
    await example_5_risk_adjusted()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
