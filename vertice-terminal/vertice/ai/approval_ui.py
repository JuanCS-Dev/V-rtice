"""
Plan Approval UI
================

Rich terminal UI for approving and editing execution plans before execution.
"""

from typing import Optional, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Prompt, Confirm

from .models import ExecutionPlan, ExecutionPhase, RiskLevel, PhaseStatus

console = Console()


class PlanApprovalUI:
    """
    Interactive UI for plan approval.

    Features:
    - Rich plan visualization
    - Phase-by-phase approval
    - Plan editing
    - Risk assessment display
    - Dry-run mode
    """

    def __init__(self):
        """Initialize approval UI."""
        self.console = Console()

    def show_plan(self, plan: ExecutionPlan) -> bool:
        """
        Display plan and get user approval.

        Args:
            plan: ExecutionPlan to display

        Returns:
            True if approved, False if cancelled

        Example:
            ui = PlanApprovalUI()
            approved = ui.show_plan(plan)

            if approved:
                engine.execute_plan(plan)
        """
        console.clear()

        # Display header
        self._display_header(plan)

        # Display phases
        self._display_phases(plan)

        # Display summary
        self._display_summary(plan)

        # Get user choice
        return self._get_approval(plan)

    def _display_header(self, plan: ExecutionPlan):
        """Display plan header with name, objective, and target."""
        risk_colors = {
            RiskLevel.LOW: "green",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "bold red"
        }

        risk_symbols = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴"
        }

        risk_color = risk_colors.get(plan.risk_level, "white")
        risk_symbol = risk_symbols.get(plan.risk_level, "")

        header_text = Text()
        header_text.append("🤖 Maximus AI: ", style="bold cyan")
        header_text.append("Execution Plan Generated\n\n", style="bold white")

        header_text.append("📋 EXECUTION PLAN: ", style="bold white")
        header_text.append(f"{plan.name}\n", style="bold cyan")

        header_text.append("━" * 60 + "\n", style="dim")

        header_text.append("Objective: ", style="bold")
        header_text.append(f"{plan.objective.value}\n", style="cyan")

        header_text.append("Target: ", style="bold")
        header_text.append(f"{plan.target}\n", style="yellow")

        header_text.append("Workspace: ", style="bold")
        header_text.append(f"{plan.workspace}\n", style="green")

        header_text.append("Risk Level: ", style="bold")
        header_text.append(f"{risk_symbol} {plan.risk_level.value}\n", style=risk_color)

        if plan.description:
            header_text.append("\nDescription:\n", style="bold")
            header_text.append(f"{plan.description}\n", style="dim")

        console.print(Panel(header_text, border_style="cyan", box=box.ROUNDED))
        console.print()

    def _display_phases(self, plan: ExecutionPlan):
        """Display all phases with steps."""
        for phase in plan.phases:
            self._display_phase(phase)
            console.print()

    def _display_phase(self, phase: ExecutionPhase):
        """Display single phase with its steps."""
        # Phase header
        risk_symbol = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴"
        }.get(phase.risk_level, "")

        approval_text = ""
        if phase.requires_approval:
            approval_text = " ⚠️  REQUIRES APPROVAL"

        console.print(
            f"Phase {phase.id}: {phase.name} {risk_symbol}{approval_text}",
            style="bold yellow"
        )
        console.print(f"  {phase.description}", style="dim")
        console.print(f"  Estimated time: {phase.estimated_time // 60} min", style="dim")
        console.print()

        # Steps table
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Step", style="white")
        table.add_column("Tool", style="green", width=12)
        table.add_column("Description", style="dim")

        for step in phase.steps:
            approval_icon = "⚠️ " if step.requires_approval else "✓"
            table.add_row(
                f"  {step.id}",
                f"{approval_icon} {step.name}",
                step.tool,
                step.description
            )

        console.print(table)

    def _display_summary(self, plan: ExecutionPlan):
        """Display execution summary with statistics."""
        est_time_min = plan.estimated_time // 60
        high_risk_phases = sum(
            1 for phase in plan.phases
            if phase.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )
        approval_phases = sum(1 for phase in plan.phases if phase.requires_approval)

        summary_text = Text()
        summary_text.append("━" * 60 + "\n", style="dim")
        summary_text.append(f"Estimated time: ", style="bold")
        summary_text.append(f"{est_time_min} minutes\n")

        summary_text.append(f"Total phases: ", style="bold")
        summary_text.append(f"{len(plan.phases)}\n")

        summary_text.append(f"Total steps: ", style="bold")
        summary_text.append(f"{plan.total_steps}\n")

        if approval_phases > 0:
            summary_text.append(f"Phases requiring approval: ", style="bold red")
            summary_text.append(f"{approval_phases}\n", style="red")

        if high_risk_phases > 0:
            summary_text.append(f"High-risk phases: ", style="bold yellow")
            summary_text.append(f"{high_risk_phases}\n", style="yellow")

        summary_text.append(f"\nWorkspace: ", style="bold")
        summary_text.append(f"{plan.workspace}\n", style="green")

        summary_text.append(f"Output: ", style="bold")
        summary_text.append("Real-time updates + final report\n")

        console.print(summary_text)

    def _get_approval(self, plan: ExecutionPlan) -> bool:
        """
        Get user approval choice.

        Returns:
            True if plan should execute, False if cancelled
        """
        console.print("\n[bold cyan]Actions:[/bold cyan]")
        console.print("  [A] Approve all (phases 1-3 only, others require separate approval)")
        console.print("  [E] Edit plan (modify/remove steps)")
        console.print("  [S] Step-by-step (approve each phase individually)")
        console.print("  [R] Run simulation (dry-run, no actual execution)")
        console.print("  [C] Cancel")
        console.print()

        choice = Prompt.ask(
            "Your choice",
            choices=["A", "E", "S", "R", "C", "a", "e", "s", "r", "c"],
            default="C"
        ).upper()

        if choice == "A":
            return self._approve_all(plan)
        elif choice == "E":
            return self._edit_plan(plan)
        elif choice == "S":
            return self._step_by_step(plan)
        elif choice == "R":
            return self._dry_run(plan)
        else:
            console.print("\n[yellow]Plan cancelled by user[/yellow]")
            return False

    def _approve_all(self, plan: ExecutionPlan) -> bool:
        """
        Approve all non-requiring-approval phases.

        Phases that require approval remain pending.
        """
        approved_count = 0

        for phase in plan.phases:
            if not phase.requires_approval:
                phase.status = PhaseStatus.APPROVED
                approved_count += 1

        console.print(f"\n[green]✓ Approved {approved_count} phases for execution[/green]")
        console.print(f"[yellow]⚠️  {len(plan.phases) - approved_count} phases will require separate approval[/yellow]")

        plan.approved_by_user = True
        return True

    def _edit_plan(self, plan: ExecutionPlan) -> bool:
        """Allow user to edit the plan."""
        console.print("\n[yellow]Plan editing not yet implemented[/yellow]")
        console.print("Returning to approval menu...")
        return self.show_plan(plan)

    def _step_by_step(self, plan: ExecutionPlan) -> bool:
        """Approve each phase individually."""
        console.print("\n[bold]Step-by-Step Approval:[/bold]\n")

        for phase in plan.phases:
            console.print(f"\n[bold yellow]Phase {phase.id}: {phase.name}[/bold yellow]")
            console.print(f"  {phase.description}")
            console.print(f"  Estimated time: {phase.estimated_time // 60} min")
            console.print(f"  Risk level: {phase.risk_level.value}")

            if Confirm.ask(f"  Approve phase {phase.id}?", default=True):
                phase.status = PhaseStatus.APPROVED
                console.print(f"  [green]✓ Phase {phase.id} approved[/green]")
            else:
                phase.status = PhaseStatus.SKIPPED
                console.print(f"  [yellow]⚠ Phase {phase.id} skipped[/yellow]")

        approved_count = sum(1 for p in plan.phases if p.status == PhaseStatus.APPROVED)
        console.print(f"\n[green]✓ {approved_count}/{len(plan.phases)} phases approved[/green]")

        plan.approved_by_user = True
        return True

    def _dry_run(self, plan: ExecutionPlan) -> bool:
        """Execute plan in dry-run mode (simulation)."""
        console.print("\n[bold cyan]Dry-Run Mode:[/bold cyan]")
        console.print("This will simulate execution without running actual commands.\n")

        if Confirm.ask("Start dry-run?", default=True):
            # Mark all phases for dry-run
            for phase in plan.phases:
                phase.status = PhaseStatus.APPROVED
                phase.metadata["dry_run"] = True

            plan.approved_by_user = True
            plan.metadata["dry_run"] = True

            console.print("[green]✓ Dry-run approved - no commands will execute[/green]")
            return True

        return False

    def show_progress(self, plan: ExecutionPlan):
        """
        Display real-time execution progress.

        Args:
            plan: ExecutionPlan being executed
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            # Add task for each phase
            phase_tasks = {}
            for phase in plan.phases:
                task_id = progress.add_task(
                    f"Phase {phase.id}: {phase.name}",
                    total=len(phase.steps)
                )
                phase_tasks[phase.id] = task_id

            # Update progress as phases execute
            # (This would be called from AutopilotEngine during execution)
            for phase in plan.phases:
                for step in phase.steps:
                    progress.update(phase_tasks[phase.id], advance=1)
