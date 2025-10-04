"""
Unit tests for Autopilot Mode
==============================

Tests for AI-powered autonomous workflow execution.

Coverage:
- ExecutionPlanner (plan generation)
- ExecutionPlan/Phase/Step models
- AutopilotEngine (mock execution)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from vertice.ai import (
    ExecutionPlanner,
    AutopilotEngine,
    ExecutionPlan,
    ExecutionPhase,
    ExecutionStep,
    ObjectiveType,
    RiskLevel,
    PhaseStatus,
    StepStatus,
    PlanResult
)


# ===== MODEL TESTS =====

class TestExecutionStep:
    """Test ExecutionStep model."""

    def test_step_creation(self):
        """Test creating an execution step."""
        step = ExecutionStep(
            id="1.1",
            name="Ping sweep",
            tool="nmap",
            command="nmap -sn 10.10.1.0/24",
            description="Find live hosts",
            estimated_time=60
        )

        assert step.id == "1.1"
        assert step.name == "Ping sweep"
        assert step.tool == "nmap"
        assert step.status == StepStatus.PENDING
        assert step.requires_approval is False

    def test_step_duration(self):
        """Test step duration calculation."""
        step = ExecutionStep(
            id="1.1",
            name="Test step",
            tool="nmap",
            command="nmap",
            description="Test"
        )

        # No duration yet
        assert step.duration is None

        # Set start and end times
        step.started_at = datetime(2024, 1, 1, 12, 0, 0)
        step.completed_at = datetime(2024, 1, 1, 12, 1, 30)

        assert step.duration == 90  # 90 seconds

    def test_step_is_complete(self):
        """Test is_complete property."""
        step = ExecutionStep(
            id="1.1",
            name="Test",
            tool="nmap",
            command="nmap",
            description="Test"
        )

        # Pending = not complete
        step.status = StepStatus.PENDING
        assert not step.is_complete

        # Running = not complete
        step.status = StepStatus.RUNNING
        assert not step.is_complete

        # Completed = complete
        step.status = StepStatus.COMPLETED
        assert step.is_complete

        # Failed = complete
        step.status = StepStatus.FAILED
        assert step.is_complete

        # Skipped = complete
        step.status = StepStatus.SKIPPED
        assert step.is_complete


class TestExecutionPhase:
    """Test ExecutionPhase model."""

    def test_phase_creation(self):
        """Test creating an execution phase."""
        steps = [
            ExecutionStep(
                id="1.1",
                name="Step 1",
                tool="nmap",
                command="nmap",
                description="Test"
            ),
            ExecutionStep(
                id="1.2",
                name="Step 2",
                tool="nuclei",
                command="nuclei",
                description="Test"
            )
        ]

        phase = ExecutionPhase(
            id="1",
            name="Reconnaissance",
            description="Discover hosts",
            steps=steps,
            estimated_time=300
        )

        assert phase.id == "1"
        assert phase.name == "Reconnaissance"
        assert len(phase.steps) == 2
        assert phase.status == PhaseStatus.PENDING
        assert phase.risk_level == RiskLevel.LOW

    def test_phase_progress(self):
        """Test phase progress calculation."""
        steps = [
            ExecutionStep(id="1.1", name="S1", tool="t", command="c", description="d"),
            ExecutionStep(id="1.2", name="S2", tool="t", command="c", description="d"),
            ExecutionStep(id="1.3", name="S3", tool="t", command="c", description="d"),
        ]

        phase = ExecutionPhase(
            id="1",
            name="Test",
            description="Test",
            steps=steps
        )

        # No steps complete
        assert phase.progress == 0.0

        # One step complete
        steps[0].status = StepStatus.COMPLETED
        assert phase.progress == 1.0 / 3.0

        # Two steps complete
        steps[1].status = StepStatus.FAILED
        assert phase.progress == 2.0 / 3.0

        # All steps complete
        steps[2].status = StepStatus.SKIPPED
        assert phase.progress == 1.0

    def test_phase_is_complete(self):
        """Test is_complete property."""
        steps = [
            ExecutionStep(id="1.1", name="S1", tool="t", command="c", description="d"),
            ExecutionStep(id="1.2", name="S2", tool="t", command="c", description="d"),
        ]

        phase = ExecutionPhase(
            id="1",
            name="Test",
            description="Test",
            steps=steps
        )

        assert not phase.is_complete

        # Complete first step
        steps[0].status = StepStatus.COMPLETED
        assert not phase.is_complete

        # Complete second step
        steps[1].status = StepStatus.COMPLETED
        assert phase.is_complete


class TestExecutionPlan:
    """Test ExecutionPlan model."""

    def test_plan_creation(self):
        """Test creating an execution plan."""
        phase1 = ExecutionPhase(
            id="1",
            name="Recon",
            description="Recon phase",
            steps=[
                ExecutionStep(id="1.1", name="S1", tool="t", command="c", description="d")
            ]
        )

        phase2 = ExecutionPhase(
            id="2",
            name="Scan",
            description="Scan phase",
            steps=[
                ExecutionStep(id="2.1", name="S2", tool="t", command="c", description="d"),
                ExecutionStep(id="2.2", name="S3", tool="t", command="c", description="d")
            ]
        )

        plan = ExecutionPlan(
            name="Test Pentest",
            objective=ObjectiveType.PENTEST,
            target="10.10.1.0/24",
            phases=[phase1, phase2],
            workspace="test-workspace"
        )

        assert plan.name == "Test Pentest"
        assert plan.objective == ObjectiveType.PENTEST
        assert plan.target == "10.10.1.0/24"
        assert len(plan.phases) == 2
        assert plan.total_steps == 3

    def test_plan_total_steps(self):
        """Test total_steps calculation."""
        phase1 = ExecutionPhase(
            id="1",
            name="P1",
            description="P1",
            steps=[
                ExecutionStep(id="1.1", name="S1", tool="t", command="c", description="d"),
                ExecutionStep(id="1.2", name="S2", tool="t", command="c", description="d")
            ]
        )

        phase2 = ExecutionPhase(
            id="2",
            name="P2",
            description="P2",
            steps=[
                ExecutionStep(id="2.1", name="S3", tool="t", command="c", description="d")
            ]
        )

        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[phase1, phase2],
            workspace="test"
        )

        assert plan.total_steps == 3

    def test_plan_progress(self):
        """Test overall plan progress."""
        phase = ExecutionPhase(
            id="1",
            name="P1",
            description="P1",
            steps=[
                ExecutionStep(id="1.1", name="S1", tool="t", command="c", description="d"),
                ExecutionStep(id="1.2", name="S2", tool="t", command="c", description="d")
            ]
        )

        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[phase],
            workspace="test"
        )

        assert plan.progress == 0.0

        # Complete first step
        phase.steps[0].status = StepStatus.COMPLETED
        assert plan.progress == 0.5

        # Complete second step
        phase.steps[1].status = StepStatus.COMPLETED
        assert plan.progress == 1.0

    def test_plan_get_phase_by_id(self):
        """Test get_phase_by_id method."""
        phase1 = ExecutionPhase(
            id="1",
            name="P1",
            description="P1",
            steps=[]
        )

        phase2 = ExecutionPhase(
            id="2",
            name="P2",
            description="P2",
            steps=[]
        )

        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[phase1, phase2],
            workspace="test"
        )

        assert plan.get_phase_by_id("1") == phase1
        assert plan.get_phase_by_id("2") == phase2
        assert plan.get_phase_by_id("3") is None

    def test_plan_to_dict(self):
        """Test to_dict serialization."""
        phase = ExecutionPhase(
            id="1",
            name="Recon",
            description="Test",
            steps=[
                ExecutionStep(id="1.1", name="S1", tool="nmap", command="nmap", description="Test")
            ]
        )

        plan = ExecutionPlan(
            name="Test Plan",
            objective=ObjectiveType.PENTEST,
            target="10.10.1.5",
            phases=[phase],
            workspace="test"
        )

        data = plan.to_dict()

        assert data["name"] == "Test Plan"
        assert data["objective"] == "pentest"
        assert data["target"] == "10.10.1.5"
        assert data["total_steps"] == 1
        assert len(data["phases"]) == 1
        assert data["phases"][0]["name"] == "Recon"


# ===== EXECUTION PLANNER TESTS =====

class TestExecutionPlanner:
    """Test ExecutionPlanner."""

    def test_planner_initialization(self):
        """Test planner initialization."""
        planner = ExecutionPlanner()
        assert planner is not None
        assert planner.templates is not None

    def test_create_pentest_plan(self):
        """Test creating a penetration testing plan."""
        planner = ExecutionPlanner()

        plan = planner.create_plan(
            objective=ObjectiveType.PENTEST,
            target="10.10.1.0/24",
            workspace="pentest-test"
        )

        assert plan.name == "Penetration Test - 10.10.1.0/24"
        assert plan.objective == ObjectiveType.PENTEST
        assert plan.target == "10.10.1.0/24"
        assert plan.workspace == "pentest-test"

        # Should have at least 3 phases (recon, scan, vuln)
        assert len(plan.phases) >= 3

        # Check phase names
        phase_names = [p.name for p in plan.phases]
        assert "Reconnaissance" in phase_names
        assert "Port Scanning" in phase_names
        assert "Vulnerability Assessment" in phase_names

    def test_pentest_plan_phases(self):
        """Test pentest plan phase structure."""
        planner = ExecutionPlanner()
        plan = planner.create_plan(
            objective=ObjectiveType.PENTEST,
            target="10.10.1.5",
            workspace="test"
        )

        # Phase 1: Reconnaissance
        recon_phase = plan.phases[0]
        assert recon_phase.id == "1"
        assert recon_phase.name == "Reconnaissance"
        assert recon_phase.risk_level == RiskLevel.LOW
        assert not recon_phase.requires_approval
        assert len(recon_phase.steps) >= 2

        # Phase 2: Port Scanning
        scan_phase = plan.phases[1]
        assert scan_phase.id == "2"
        assert scan_phase.name == "Port Scanning"
        assert scan_phase.risk_level == RiskLevel.LOW
        assert len(scan_phase.steps) >= 2

        # Phase 3: Vulnerability Assessment
        vuln_phase = plan.phases[2]
        assert vuln_phase.id == "3"
        assert vuln_phase.name == "Vulnerability Assessment"
        assert vuln_phase.risk_level == RiskLevel.MEDIUM
        assert len(vuln_phase.steps) >= 2

    def test_pentest_plan_with_exploitation(self):
        """Test pentest plan with exploitation enabled."""
        planner = ExecutionPlanner()
        plan = planner.create_plan(
            objective=ObjectiveType.PENTEST,
            target="10.10.1.5",
            workspace="test",
            scope={"allow_exploitation": True}
        )

        # Should have exploitation phases
        phase_names = [p.name for p in plan.phases]
        assert "Exploitation" in phase_names
        assert "Post-Exploitation" in phase_names

        # Exploitation phase should require approval
        exploit_phase = next(p for p in plan.phases if p.name == "Exploitation")
        assert exploit_phase.requires_approval
        assert exploit_phase.risk_level == RiskLevel.HIGH

    def test_create_defend_plan(self):
        """Test creating a defensive hardening plan."""
        planner = ExecutionPlanner()

        plan = planner.create_plan(
            objective=ObjectiveType.DEFEND,
            target="web-server-cluster",
            workspace="defend-test"
        )

        assert plan.name == "Security Hardening - web-server-cluster"
        assert plan.objective == ObjectiveType.DEFEND
        assert len(plan.phases) >= 3

        # Check phase names
        phase_names = [p.name for p in plan.phases]
        assert "Baseline Assessment" in phase_names
        assert "Vulnerability Detection" in phase_names
        assert "Automated Remediation" in phase_names

    def test_defend_plan_remediation_requires_approval(self):
        """Test that remediation phase requires approval."""
        planner = ExecutionPlanner()
        plan = planner.create_plan(
            objective=ObjectiveType.DEFEND,
            target="server",
            workspace="test"
        )

        remediation_phase = next(
            (p for p in plan.phases if "Remediation" in p.name),
            None
        )

        assert remediation_phase is not None
        assert remediation_phase.requires_approval
        assert remediation_phase.risk_level == RiskLevel.HIGH


# ===== AUTOPILOT ENGINE TESTS =====

class TestAutopilotEngine:
    """Test AutopilotEngine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = AutopilotEngine()

        assert engine is not None
        assert engine.planner is not None
        assert not engine.is_running
        assert not engine.paused
        assert not engine.stop_requested

    @pytest.mark.asyncio
    async def test_execute_simple_plan(self):
        """Test executing a simple plan (dry-run)."""
        # Create simple plan
        step = ExecutionStep(
            id="1.1",
            name="Test step",
            tool="echo",
            command="echo test",
            description="Test"
        )

        phase = ExecutionPhase(
            id="1",
            name="Test phase",
            description="Test",
            steps=[step],
            requires_approval=False
        )
        phase.status = PhaseStatus.APPROVED

        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[phase],
            workspace="test"
        )

        # Execute (without actual tool orchestrator = dry-run)
        engine = AutopilotEngine()
        result = await engine.execute_plan(plan)

        assert result is not None
        assert isinstance(result, PlanResult)
        assert result.plan == plan

    @pytest.mark.asyncio
    async def test_execute_plan_skips_unapproved_phases(self):
        """Test that unapproved phases are skipped."""
        phase1 = ExecutionPhase(
            id="1",
            name="Approved phase",
            description="Test",
            steps=[
                ExecutionStep(id="1.1", name="S1", tool="t", command="c", description="d")
            ],
            requires_approval=False
        )

        phase2 = ExecutionPhase(
            id="2",
            name="Unapproved phase",
            description="Test",
            steps=[
                ExecutionStep(id="2.1", name="S2", tool="t", command="c", description="d")
            ],
            requires_approval=True  # Requires approval but not approved
        )

        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[phase1, phase2],
            workspace="test"
        )

        engine = AutopilotEngine()
        result = await engine.execute_plan(plan)

        # Phase 2 should be skipped
        assert phase2.status == PhaseStatus.SKIPPED

    def test_engine_pause_resume(self):
        """Test pausing and resuming execution."""
        engine = AutopilotEngine()

        assert not engine.paused

        engine.pause()
        assert engine.paused

        engine.resume()
        assert not engine.paused

    def test_engine_stop(self):
        """Test stopping execution."""
        engine = AutopilotEngine()

        assert not engine.stop_requested

        engine.stop()
        assert engine.stop_requested

    def test_engine_progress(self):
        """Test progress tracking."""
        engine = AutopilotEngine()

        # No plan = 0% progress
        assert engine.progress == 0.0

        # Set current plan
        phase = ExecutionPhase(
            id="1",
            name="Test",
            description="Test",
            steps=[
                ExecutionStep(id="1.1", name="S1", tool="t", command="c", description="d"),
                ExecutionStep(id="1.2", name="S2", tool="t", command="c", description="d")
            ]
        )

        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[phase],
            workspace="test"
        )

        engine.current_plan = plan
        assert engine.progress == 0.0

        # Complete first step
        phase.steps[0].status = StepStatus.COMPLETED
        assert engine.progress == 0.5


# ===== PLAN RESULT TESTS =====

class TestPlanResult:
    """Test PlanResult model."""

    def test_result_creation(self):
        """Test creating a plan result."""
        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[],
            workspace="test"
        )

        result = PlanResult(
            plan=plan,
            success=True,
            total_duration=600,
            findings={"hosts": 5, "vulnerabilities": 3}
        )

        assert result.success
        assert result.total_duration == 600
        assert result.findings["hosts"] == 5

    def test_result_summary(self):
        """Test result summary generation."""
        plan = ExecutionPlan(
            name="Test",
            objective=ObjectiveType.PENTEST,
            target="test",
            phases=[],
            workspace="test-workspace"
        )

        result = PlanResult(
            plan=plan,
            success=True,
            total_duration=600
        )

        summary = result.summary
        assert "Success" in summary
        assert "test-workspace" in summary
        assert "10 minutes" in summary
