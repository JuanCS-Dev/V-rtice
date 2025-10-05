"""Maximus Network Reconnaissance Service - Reconnaissance Engine.

This module implements the core Reconnaissance Engine for the Maximus AI's
Network Reconnaissance Service. It is responsible for orchestrating various
reconnaissance techniques to gather information about target networks, systems,
and services.

Key functionalities include:
- Utilizing specialized tools (e.g., Nmap, Masscan) for port scanning, service
  detection, and OS fingerprinting.
- Discovering network topology, active hosts, and open services.
- Identifying potential attack surfaces and vulnerabilities.
- Providing detailed reconnaissance reports to other Maximus AI services for
  threat assessment, vulnerability management, and offensive operations.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from nmap_wrapper import NmapWrapper
from masscan_wrapper import MasscanWrapper
from metrics import MetricsCollector
from models import ReconTask, ReconResult, ReconStatus


class ReconEngine:
    """Orchestrates various reconnaissance techniques to gather information about
    target networks, systems, and services.

    Utilizes specialized tools (e.g., Nmap, Masscan) for port scanning, service
    detection, and OS fingerprinting.
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """Initializes the ReconEngine.

        Args:
            metrics_collector (MetricsCollector): The collector for reconnaissance metrics.
        """
        self.metrics_collector = metrics_collector
        self.nmap_wrapper = NmapWrapper()
        self.masscan_wrapper = MasscanWrapper()
        self.active_tasks: Dict[str, ReconTask] = {}
        self.task_results: Dict[str, ReconResult] = {}
        print("[ReconEngine] Initialized Reconnaissance Engine.")

    async def start_recon_task(self, task: ReconTask):
        """Starts a new reconnaissance task.

        Args:
            task (ReconTask): The reconnaissance task object to execute.
        """
        self.active_tasks[task.id] = task
        task.status = ReconStatus.RUNNING
        self.metrics_collector.record_metric("recon_tasks_started")
        print(f"[ReconEngine] Starting recon task {task.id}: {task.target}")

        try:
            results_data: Dict[str, Any] = {}
            if task.scan_type == "nmap_full":
                results_data = await self.nmap_wrapper.full_scan(task.target)
            elif task.scan_type == "masscan_ports":
                results_data = await self.masscan_wrapper.port_scan(task.target, task.parameters.get("ports", []))
            else:
                raise ValueError(f"Unsupported scan type: {task.scan_type}")

            task.status = ReconStatus.COMPLETED
            task.end_time = datetime.now().isoformat()
            self.metrics_collector.record_metric("recon_tasks_completed")
            self.task_results[task.id] = ReconResult(
                task_id=task.id,
                status="success",
                output=results_data,
                timestamp=datetime.now().isoformat()
            )
            print(f"[ReconEngine] Recon task {task.id} completed successfully.")

        except Exception as e:
            task.status = ReconStatus.FAILED
            task.end_time = datetime.now().isoformat()
            self.metrics_collector.record_metric("recon_tasks_failed")
            self.task_results[task.id] = ReconResult(
                task_id=task.id,
                status="failed",
                output={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
            print(f"[ReconEngine] Recon task {task.id} failed: {e}")

    def get_task(self, task_id: str) -> Optional[ReconTask]:
        """Retrieves a reconnaissance task by its ID.

        Args:
            task_id (str): The ID of the task.

        Returns:
            Optional[ReconTask]: The ReconTask object, or None if not found.
        """
        return self.active_tasks.get(task_id)

    def get_task_results(self, task_id: str) -> Optional[ReconResult]:
        """Retrieves the results of a reconnaissance task by its ID.

        Args:
            task_id (str): The ID of the task.

        Returns:
            Optional[ReconResult]: The ReconResult object, or None if not found or not completed.
        """
        return self.task_results.get(task_id)

    def list_active_tasks(self) -> List[ReconTask]:
        """Lists all currently active reconnaissance tasks.

        Returns:
            List[ReconTask]: A list of active ReconTask objects.
        """
        return [task for task in self.active_tasks.values() if task.status == ReconStatus.RUNNING]