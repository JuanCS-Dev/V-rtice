"""Maximus BAS Service - Purple Team Engine.

This module implements the Purple Team Engine for the Breach and Attack
Simulation (BAS) service. It orchestrates simulated attacks (red team actions)
and simultaneously monitors the defensive responses (blue team actions) of the
Maximus AI system.

By combining offensive and defensive perspectives, the Purple Team Engine provides
a holistic view of the AI's security posture, identifies gaps in detection and
response capabilities, and facilitates continuous improvement of security controls.
It is crucial for validating the effectiveness of the AI Immune System and ADR
Core Service.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from atomic_executor import AtomicExecutor
from metrics import MetricsCollector
from models import AttackResult, AttackSimulation, AttackTechnique, SimulationStatus


class PurpleTeamEngine:
    """Orchestrates simulated attacks (red team actions) and simultaneously monitors
    the defensive responses (blue team actions) of the Maximus AI system.

    Provides a holistic view of the AI's security posture, identifies gaps in
    detection and response capabilities, and facilitates continuous improvement.
    """

    def __init__(self, atomic_executor: AtomicExecutor, metrics_collector: MetricsCollector):
        """Initializes the PurpleTeamEngine.

        Args:
            atomic_executor (AtomicExecutor): The executor for atomic attack techniques.
            metrics_collector (MetricsCollector): The collector for BAS metrics.
        """
        self.atomic_executor = atomic_executor
        self.metrics_collector = metrics_collector
        self.active_simulations: Dict[str, AttackSimulation] = {}
        print("[PurpleTeamEngine] Initialized Purple Team Engine.")

    async def run_simulation(self, simulation: AttackSimulation):
        """Runs a full attack simulation, executing techniques and monitoring responses.

        Args:
            simulation (AttackSimulation): The attack simulation object to run.
        """
        self.active_simulations[simulation.id] = simulation
        print(f"[PurpleTeamEngine] Running simulation {simulation.id}: {simulation.attack_scenario}")
        self.metrics_collector.record_metric("bas_simulations_started")

        simulation.status = SimulationStatus.RUNNING
        simulation.results = []

        # Simulate execution of attack techniques
        for technique_name in simulation.techniques_used:
            technique = AttackTechnique(
                id=technique_name,
                name=technique_name,
                description=f"Simulated technique {technique_name}",
            )
            print(f"[PurpleTeamEngine] Executing technique: {technique.name}")
            try:
                attack_output = await self.atomic_executor.execute_technique(technique, simulation.target_service)
                # Simulate blue team detection/response here
                detection_status = (
                    "detected" if "malicious" in attack_output.get("status", "").lower() else "not_detected"
                )
                response_status = "responded" if detection_status == "detected" else "no_response"

                result = AttackResult(
                    id=str(uuid.uuid4()),
                    technique_id=technique.id,
                    timestamp=datetime.now().isoformat(),
                    attack_status="success",
                    detection_status=detection_status,
                    response_status=response_status,
                    attack_output=attack_output,
                    detection_details=({"simulated_detection": True} if detection_status == "detected" else {}),
                    response_details=({"simulated_response": True} if response_status == "responded" else {}),
                )
                simulation.results.append(result)
                self.metrics_collector.record_metric(f"technique_executed_{technique.id}")
                if detection_status == "detected":
                    self.metrics_collector.record_metric("attack_detected")
                else:
                    self.metrics_collector.record_metric("attack_not_detected")

            except Exception as e:
                print(f"[PurpleTeamEngine] Error executing technique {technique.name}: {e}")
                result = AttackResult(
                    id=str(uuid.uuid4()),
                    technique_id=technique.id,
                    timestamp=datetime.now().isoformat(),
                    attack_status="failed",
                    detection_status="N/A",
                    response_status="N/A",
                    attack_output={"error": str(e)},
                    detection_details={},
                    response_details={},
                )
                simulation.results.append(result)
                self.metrics_collector.record_metric(f"technique_failed_{technique.id}")

            await asyncio.sleep(1)  # Simulate time between techniques

        simulation.status = SimulationStatus.COMPLETED
        simulation.end_time = datetime.now().isoformat()
        print(f"[PurpleTeamEngine] Simulation {simulation.id} completed.")
        self.metrics_collector.record_metric("bas_simulations_completed")

    def get_simulation(self, simulation_id: str) -> Optional[AttackSimulation]:
        """Retrieves an active or completed simulation by its ID.

        Args:
            simulation_id (str): The ID of the simulation.

        Returns:
            Optional[AttackSimulation]: The AttackSimulation object, or None if not found.
        """
        return self.active_simulations.get(simulation_id)

    def list_active_simulations(self) -> List[AttackSimulation]:
        """Lists all currently active simulations.

        Returns:
            List[AttackSimulation]: A list of active AttackSimulation objects.
        """
        return [s for s in self.active_simulations.values() if s.status == SimulationStatus.RUNNING]
