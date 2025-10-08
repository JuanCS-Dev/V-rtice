"""Maximus Strategic Planning Service - Demo Module.

This module provides a demonstration of the Maximus AI's Strategic Planning
Service capabilities. It showcases how high-level objectives can be set,
scenarios analyzed, and strategic plans generated.

Key functionalities include:
- Illustrating the process of defining strategic objectives.
- Simulating scenario analysis with various contextual factors and risk factors.
- Presenting a simplified strategic plan with actionable recommendations.

This demo is intended to provide a quick overview of the service's functionality
and its role in enabling Maximus AI to make coherent, goal-oriented decisions
and align its actions with overarching missions.
"""

import asyncio

from strategic_planning_core import StrategicPlanningCore


async def run_strategic_planning_demo():
    """Runs a demonstration of the Strategic Planning Service."""
    print("\n--- Maximus Strategic Planning Service Demo ---")
    core = StrategicPlanningCore()

    # 1. Set a strategic objective
    print("\n1. Setting a strategic objective...")
    await core.set_objective(
        objective_name="Global Cyber Dominance",
        description="Achieve and maintain unparalleled cybersecurity superiority across all digital domains.",
        priority=10,
        target_date="2028-12-31",
    )
    print("Objective set.")

    # 2. Analyze a scenario
    print("\n2. Analyzing a critical scenario: Zero-Day Exploit Discovery...")
    scenario_context = {
        "threat_level": "critical",
        "affected_systems": ["core_network", "data_center_A"],
        "discovery_source": "Maximus Eureka Service",
    }
    risk_factors = ["data_loss", "system_downtime", "reputation_damage"]
    analysis_result = await core.analyze_scenario(
        scenario_name="Zero-Day Exploit Response",
        context=scenario_context,
        risk_factors=risk_factors,
    )
    print("Scenario Analysis Result:")
    print(analysis_result)

    # 3. Generate a strategic plan based on the analysis and objective
    print("\n3. Generating a strategic plan...")
    strategic_plan = await core.generate_strategic_plan(analysis_result)
    print("Generated Strategic Plan:")
    print(strategic_plan)

    # 4. Get current strategic plan status
    print("\n4. Getting current strategic plan status...")
    status = await core.get_strategic_plan()
    print("Current Strategic Plan Status:")
    print(status)

    print("\n--- Demo Complete ---")


if __name__ == "__main__":
    asyncio.run(run_strategic_planning_demo())
