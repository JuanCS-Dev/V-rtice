"""
Autopilot Engine
=================

AI-powered autonomous workflow execution with human oversight.

Workflow:
1. Parse user objective
2. Create multi-phase execution plan (via ExecutionPlanner)
3. Get user approval (via PlanApprovalUI)
4. Execute phases sequentially
5. Adapt plan based on results
6. Populate workspace automatically
7. Generate final report
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

from .models import (
    ExecutionPlan,
    ExecutionPhase,
    ExecutionStep,
    ObjectiveType,
    PhaseStatus,
    StepStatus,
    PlanResult
)
from .planner import ExecutionPlanner

logger = logging.getLogger(__name__)


class AutopilotEngine:
    """
    Autonomous workflow execution engine.

    Manages plan execution with:
    - Phase-by-phase progression
    - Step-by-step tool execution
    - Real-time progress tracking
    - Error handling & recovery
    - Workspace auto-population
    - Report generation
    """

    def __init__(
        self,
        workspace_manager=None,
        tool_orchestrator=None,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize autopilot engine.

        Args:
            workspace_manager: WorkspaceManager instance for data storage
            tool_orchestrator: ToolOrchestrator instance for tool execution
            progress_callback: Callback function for progress updates
        """
        self.planner = ExecutionPlanner()
        self.workspace_manager = workspace_manager
        self.tool_orchestrator = tool_orchestrator
        self.progress_callback = progress_callback

        # Execution state
        self.current_plan: Optional[ExecutionPlan] = None
        self.is_running = False
        self.paused = False
        self.stop_requested = False

    async def execute_plan(self, plan: ExecutionPlan) -> PlanResult:
        """
        Execute complete plan autonomously.

        Args:
            plan: ExecutionPlan to execute

        Returns:
            PlanResult with execution statistics and findings

        Example:
            engine = AutopilotEngine(workspace_manager, tool_orchestrator)
            result = await engine.execute_plan(plan)

            if result.success:
                print(f"Plan completed: {result.summary}")
            else:
                print(f"Plan failed: {result.errors}")
        """
        if self.is_running:
            raise RuntimeError("Autopilot is already running")

        self.current_plan = plan
        self.is_running = True
        self.stop_requested = False

        plan.started_at = datetime.now()
        errors = []
        findings = {}

        logger.info(f"Starting autopilot execution: {plan.name}")

        try:
            # Execute each phase sequentially
            for phase in plan.phases:
                if self.stop_requested:
                    logger.warning("Execution stopped by user")
                    break

                # Skip phases that don't require approval or are already approved
                if phase.requires_approval and phase.status != PhaseStatus.APPROVED:
                    logger.info(f"Skipping phase '{phase.name}' - requires approval")
                    phase.status = PhaseStatus.SKIPPED
                    continue

                # Execute phase
                try:
                    phase_findings = await self._execute_phase(phase)
                    findings.update(phase_findings)
                except Exception as e:
                    error_msg = f"Phase '{phase.name}' failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    phase.status = PhaseStatus.FAILED

                    # Continue to next phase or stop?
                    if phase.risk_level.value in ["high", "critical"]:
                        logger.error("High-risk phase failed, stopping execution")
                        break

            plan.completed_at = datetime.now()

            # Generate result
            success = not errors and plan.is_complete
            result = PlanResult(
                plan=plan,
                success=success,
                total_duration=plan.duration or 0,
                findings=findings,
                errors=errors
            )

            logger.info(f"Autopilot execution completed: {result.summary}")

            return result

        except Exception as e:
            logger.exception(f"Autopilot execution failed: {e}")
            plan.completed_at = datetime.now()

            return PlanResult(
                plan=plan,
                success=False,
                total_duration=plan.duration or 0,
                errors=[str(e)]
            )

        finally:
            self.is_running = False
            self.current_plan = None

    async def _execute_phase(self, phase: ExecutionPhase) -> Dict[str, Any]:
        """
        Execute single phase.

        Args:
            phase: ExecutionPhase to execute

        Returns:
            Findings dict from phase execution
        """
        phase.status = PhaseStatus.RUNNING
        phase.started_at = datetime.now()

        logger.info(f"Executing phase: {phase.name}")
        self._notify_progress(f"Phase: {phase.name}")

        findings = {}

        try:
            # Execute each step sequentially
            for step in phase.steps:
                if self.stop_requested:
                    break

                # Wait if paused
                while self.paused and not self.stop_requested:
                    await asyncio.sleep(0.5)

                if self.stop_requested:
                    break

                # Execute step
                try:
                    step_findings = await self._execute_step(step)
                    findings.update(step_findings)

                except Exception as e:
                    error_msg = f"Step '{step.name}' failed: {e}"
                    logger.error(error_msg)
                    step.status = StepStatus.FAILED
                    step.error = str(e)

                    # Continue or stop?
                    if step.requires_approval:
                        # Critical step failed, stop phase
                        raise

            phase.status = PhaseStatus.COMPLETED
            phase.completed_at = datetime.now()

            logger.info(f"Phase completed: {phase.name} ({phase.duration}s)")

            return findings

        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.completed_at = datetime.now()
            raise

    async def _execute_step(self, step: ExecutionStep) -> Dict[str, Any]:
        """
        Execute single step.

        Args:
            step: ExecutionStep to execute

        Returns:
            Findings dict from step execution
        """
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()

        logger.info(f"Executing step: {step.name}")
        self._notify_progress(f"  Step: {step.name}")

        findings = {}

        try:
            # Execute tool command
            if self.tool_orchestrator:
                # Use ToolOrchestrator for proper tool execution
                result = await self._execute_tool(step.tool, step.command)
                step.output = result.get("output", "")

                # Parse output for findings
                if result.get("success"):
                    findings = self._parse_findings(step.tool, step.output)

                    # Store in workspace if available
                    if self.workspace_manager and findings:
                        await self._store_findings(findings)

                else:
                    step.error = result.get("error", "Unknown error")
                    raise RuntimeError(step.error)

            else:
                # Dry-run mode (no actual execution)
                logger.info(f"DRY-RUN: {step.command}")
                step.output = "[DRY-RUN] No actual execution"

            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()

            logger.info(f"Step completed: {step.name} ({step.duration}s)")

            return findings

        except Exception as e:
            step.status = StepStatus.FAILED
            step.completed_at = datetime.now()
            step.error = str(e)
            raise

    async def _execute_tool(self, tool: str, command: str) -> Dict[str, Any]:
        """
        Execute tool command.

        Args:
            tool: Tool name (nmap, nuclei, nikto, etc.)
            command: Command to execute

        Returns:
            Execution result dict
        """
        # Map tool names to orchestrator methods
        tool_map = {
            "nmap": "execute_nmap",
            "nuclei": "execute_nuclei",
            "nikto": "execute_nikto",
            "whois": "execute_whois",
            "sslscan": "execute_sslscan",
            "curl": "execute_curl"
        }

        if tool not in tool_map:
            # Generic command execution
            return {
                "success": False,
                "error": f"Tool '{tool}' not supported yet"
            }

        # Call appropriate orchestrator method
        try:
            # For now, return mock success
            # TODO: Integrate with actual ToolOrchestrator
            return {
                "success": True,
                "output": f"[MOCK] Executed {tool}: {command}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_findings(self, tool: str, output: str) -> Dict[str, Any]:
        """
        Parse tool output into structured findings.

        Args:
            tool: Tool that produced the output
            output: Raw tool output

        Returns:
            Findings dict
        """
        # Tool-specific parsers
        parsers = {
            "nmap": self._parse_nmap_findings,
            "nuclei": self._parse_nuclei_findings,
            "nikto": self._parse_nikto_findings
        }

        parser = parsers.get(tool, lambda x: {})
        return parser(output)

    def _parse_nmap_findings(self, output: str) -> Dict[str, Any]:
        """Parse Nmap output into findings."""
        # TODO: Integrate with NmapParser from core.parsers
        return {"hosts": [], "ports": []}

    def _parse_nuclei_findings(self, output: str) -> Dict[str, Any]:
        """Parse Nuclei output into findings."""
        # TODO: Integrate with NucleiParser from core.parsers
        return {"vulnerabilities": []}

    def _parse_nikto_findings(self, output: str) -> Dict[str, Any]:
        """Parse Nikto output into findings."""
        # TODO: Integrate with NiktoParser from core.parsers
        return {"web_vulns": []}

    async def _store_findings(self, findings: Dict[str, Any]):
        """
        Store findings in workspace.

        Args:
            findings: Findings dict to store
        """
        if not self.workspace_manager:
            return

        # TODO: Integrate with WorkspaceManager
        # workspace_manager.add_hosts(findings.get("hosts", []))
        # workspace_manager.add_vulnerabilities(findings.get("vulnerabilities", []))
        pass

    def _notify_progress(self, message: str):
        """
        Notify progress callback.

        Args:
            message: Progress message
        """
        if self.progress_callback:
            self.progress_callback(message)

    def pause(self):
        """Pause execution (can be resumed)."""
        self.paused = True
        logger.info("Autopilot execution paused")

    def resume(self):
        """Resume paused execution."""
        self.paused = False
        logger.info("Autopilot execution resumed")

    def stop(self):
        """Stop execution gracefully."""
        self.stop_requested = True
        logger.info("Autopilot stop requested")

    @property
    def progress(self) -> float:
        """Get current execution progress (0.0 to 1.0)."""
        if not self.current_plan:
            return 0.0
        return self.current_plan.progress
