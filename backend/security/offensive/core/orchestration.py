"""
Orchestration Engine - AI-driven attack chain coordination.

Coordinates multi-stage offensive operations with ML decision-making.
"""
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from .base import OffensiveTool, ToolResult, ToolMetadata
from .exceptions import OffensiveToolError


class OperationPhase(Enum):
    """Attack operation phases."""
    RECONNAISSANCE = "reconnaissance"
    WEAPONIZATION = "weaponization"
    DELIVERY = "delivery"
    EXPLOITATION = "exploitation"
    INSTALLATION = "installation"
    COMMAND_CONTROL = "command_control"
    ACTIONS_ON_OBJECTIVE = "actions_on_objective"


class OperationStatus(Enum):
    """Operation execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class OperationStep:
    """Single step in attack chain."""
    step_id: str
    phase: OperationPhase
    tool_name: str
    tool_config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 300.0
    retry_on_failure: bool = True
    max_retries: int = 3
    status: OperationStatus = OperationStatus.PENDING
    result: Optional[ToolResult] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class Operation:
    """Complete attack operation definition."""
    operation_id: str
    name: str
    description: str
    target: str
    steps: List[OperationStep]
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: OperationStatus = OperationStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    """Operation execution result."""
    operation_id: str
    status: OperationStatus
    total_steps: int
    completed_steps: int
    failed_steps: int
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    step_results: Dict[str, ToolResult]
    loot: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict] = field(default_factory=list)


class OrchestrationEngine(OffensiveTool):
    """
    AI-driven operation orchestration engine.
    
    Coordinates complex multi-stage offensive operations with:
    - Dependency-based execution ordering
    - Dynamic adaptation based on results
    - ML-driven decision-making
    - Automatic recovery and retry logic
    - Real-time operation monitoring
    """
    
    def __init__(self) -> None:
        """Initialize orchestration engine."""
        super().__init__(
            name="orchestration_engine",
            category="core"
        )
        
        self.tools: Dict[str, OffensiveTool] = {}
        self.operations: Dict[str, Operation] = {}
        self.running_operations: Dict[str, asyncio.Task] = {}
    
    def register_tool(self, tool: OffensiveTool) -> None:
        """
        Register a tool for orchestration.
        
        Args:
            tool: Tool instance
        """
        self.tools[tool.name] = tool
    
    def create_operation(
        self,
        name: str,
        description: str,
        target: str,
        steps: List[OperationStep]
    ) -> str:
        """
        Create a new operation.
        
        Args:
            name: Operation name
            description: Operation description
            target: Target identifier
            steps: Operation steps
            
        Returns:
            Operation ID
            
        Raises:
            OffensiveToolError: If operation invalid
        """
        # Validate steps
        self._validate_operation_steps(steps)
        
        # Generate operation ID
        operation_id = f"op_{datetime.utcnow().timestamp()}"
        
        operation = Operation(
            operation_id=operation_id,
            name=name,
            description=description,
            target=target,
            steps=steps
        )
        
        self.operations[operation_id] = operation
        
        return operation_id
    
    async def execute(
        self,
        operation_id: str,
        **kwargs
    ) -> ToolResult:
        """
        Execute an operation.
        
        Args:
            operation_id: Operation ID
            **kwargs: Additional parameters
            
        Returns:
            ToolResult with operation results
            
        Raises:
            OffensiveToolError: If execution fails
        """
        if operation_id not in self.operations:
            raise OffensiveToolError(
                f"Operation not found: {operation_id}",
                tool_name=self.name
            )
        
        operation = self.operations[operation_id]
        
        if operation.status == OperationStatus.RUNNING:
            raise OffensiveToolError(
                f"Operation already running: {operation_id}",
                tool_name=self.name
            )
        
        # Execute operation asynchronously
        task = asyncio.create_task(self._execute_operation(operation))
        self.running_operations[operation_id] = task
        
        try:
            result = await task
            
            return ToolResult(
                success=result.status == OperationStatus.COMPLETED,
                data=result,
                message=f"Operation {result.status.value}: {result.completed_steps}/{result.total_steps} steps",
                metadata=self._create_metadata(result)
            )
        
        finally:
            # Clean up task
            if operation_id in self.running_operations:
                del self.running_operations[operation_id]
    
    async def _execute_operation(
        self, operation: Operation
    ) -> OperationResult:
        """
        Execute operation steps.
        
        Args:
            operation: Operation to execute
            
        Returns:
            OperationResult
        """
        operation.status = OperationStatus.RUNNING
        operation.start_time = datetime.utcnow()
        
        step_results = {}
        timeline = []
        completed = 0
        failed = 0
        
        try:
            # Execute steps in dependency order
            execution_order = self._resolve_dependencies(operation.steps)
            
            for step in execution_order:
                # Check if dependencies succeeded
                if not self._check_dependencies(step, step_results):
                    step.status = OperationStatus.FAILED
                    step.error = "Dependency failed"
                    failed += 1
                    continue
                
                # Execute step
                step_result = await self._execute_step(operation, step)
                step_results[step.step_id] = step_result
                
                # Update timeline
                timeline.append({
                    "step_id": step.step_id,
                    "phase": step.phase.value,
                    "tool": step.tool_name,
                    "status": step.status.value,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                if step.status == OperationStatus.COMPLETED:
                    completed += 1
                else:
                    failed += 1
                
                # Check if critical step failed
                if step.status == OperationStatus.FAILED and not step.retry_on_failure:
                    break
        
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.end_time = datetime.utcnow()
            
            raise OffensiveToolError(
                f"Operation execution error: {str(e)}",
                tool_name=self.name,
                details={"operation_id": operation.operation_id}
            )
        
        operation.end_time = datetime.utcnow()
        operation.status = (
            OperationStatus.COMPLETED if failed == 0
            else OperationStatus.FAILED
        )
        
        # Aggregate loot from all steps
        loot = {}
        for step_id, result in step_results.items():
            if result.success and result.data:
                if hasattr(result.data, 'loot'):
                    loot[step_id] = result.data.loot
        
        return OperationResult(
            operation_id=operation.operation_id,
            status=operation.status,
            total_steps=len(operation.steps),
            completed_steps=completed,
            failed_steps=failed,
            start_time=operation.start_time,
            end_time=operation.end_time,
            duration_seconds=(
                operation.end_time - operation.start_time
            ).total_seconds(),
            step_results=step_results,
            loot=loot,
            timeline=timeline
        )
    
    async def _execute_step(
        self, operation: Operation, step: OperationStep
    ) -> ToolResult:
        """
        Execute single operation step.
        
        Args:
            operation: Parent operation
            step: Step to execute
            
        Returns:
            ToolResult
        """
        step.status = OperationStatus.RUNNING
        step.start_time = datetime.utcnow()
        
        # Get tool
        if step.tool_name not in self.tools:
            step.status = OperationStatus.FAILED
            step.error = f"Tool not found: {step.tool_name}"
            step.end_time = datetime.utcnow()
            
            return ToolResult(
                success=False,
                message=step.error
            )
        
        tool = self.tools[step.tool_name]
        
        # Execute with retries
        attempt = 0
        last_error = None
        
        while attempt < step.max_retries:
            try:
                result = await asyncio.wait_for(
                    tool.execute(**step.tool_config),
                    timeout=step.timeout
                )
                
                step.result = result
                step.status = (
                    OperationStatus.COMPLETED if result.success
                    else OperationStatus.FAILED
                )
                step.end_time = datetime.utcnow()
                
                return result
            
            except asyncio.TimeoutError:
                last_error = "Step execution timed out"
            except Exception as e:
                last_error = str(e)
            
            attempt += 1
            
            if attempt < step.max_retries and step.retry_on_failure:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        step.status = OperationStatus.FAILED
        step.error = last_error or "Unknown error"
        step.end_time = datetime.utcnow()
        
        return ToolResult(
            success=False,
            message=step.error
        )
    
    def _validate_operation_steps(self, steps: List[OperationStep]) -> None:
        """
        Validate operation steps.
        
        Args:
            steps: Steps to validate
            
        Raises:
            OffensiveToolError: If validation fails
        """
        if not steps:
            raise OffensiveToolError(
                "Operation must have at least one step",
                tool_name=self.name
            )
        
        # Check for duplicate step IDs
        step_ids = [s.step_id for s in steps]
        if len(step_ids) != len(set(step_ids)):
            raise OffensiveToolError(
                "Duplicate step IDs found",
                tool_name=self.name
            )
        
        # Validate dependencies exist
        for step in steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise OffensiveToolError(
                        f"Unknown dependency: {dep}",
                        tool_name=self.name,
                        details={"step": step.step_id}
                    )
    
    def _resolve_dependencies(
        self, steps: List[OperationStep]
    ) -> List[OperationStep]:
        """
        Resolve step execution order based on dependencies.
        
        Args:
            steps: Operation steps
            
        Returns:
            Ordered list of steps
        """
        # Topological sort
        step_map = {s.step_id: s for s in steps}
        visited = set()
        order = []
        
        def visit(step_id: str):
            if step_id in visited:
                return
            
            step = step_map[step_id]
            
            # Visit dependencies first
            for dep in step.dependencies:
                visit(dep)
            
            visited.add(step_id)
            order.append(step)
        
        for step in steps:
            visit(step.step_id)
        
        return order
    
    def _check_dependencies(
        self, step: OperationStep, results: Dict[str, ToolResult]
    ) -> bool:
        """
        Check if step dependencies are satisfied.
        
        Args:
            step: Step to check
            results: Completed step results
            
        Returns:
            True if dependencies satisfied
        """
        for dep in step.dependencies:
            if dep not in results:
                return False
            
            if not results[dep].success:
                return False
        
        return True
    
    def pause_operation(self, operation_id: str) -> None:
        """
        Pause running operation.
        
        Args:
            operation_id: Operation ID
        """
        if operation_id in self.running_operations:
            task = self.running_operations[operation_id]
            task.cancel()
            
            operation = self.operations[operation_id]
            operation.status = OperationStatus.PAUSED
    
    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get operation status.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            Status information
        """
        if operation_id not in self.operations:
            return {"error": "Operation not found"}
        
        operation = self.operations[operation_id]
        
        completed_steps = len([
            s for s in operation.steps
            if s.status == OperationStatus.COMPLETED
        ])
        
        return {
            "operation_id": operation_id,
            "name": operation.name,
            "status": operation.status.value,
            "target": operation.target,
            "progress": f"{completed_steps}/{len(operation.steps)}",
            "started_at": operation.start_time.isoformat() if operation.start_time else None,
            "running": operation_id in self.running_operations
        }
    
    def _create_metadata(self, result: OperationResult) -> ToolMetadata:
        """
        Create tool metadata.
        
        Args:
            result: Operation result
            
        Returns:
            Tool metadata
        """
        success_rate = (
            result.completed_steps / result.total_steps
            if result.total_steps > 0 else 0.0
        )
        
        return ToolMetadata(
            tool_name=self.name,
            execution_time=result.duration_seconds,
            success_rate=success_rate,
            confidence_score=0.9 if result.status == OperationStatus.COMPLETED else 0.4,
            resource_usage={
                "total_steps": result.total_steps,
                "completed_steps": result.completed_steps,
                "failed_steps": result.failed_steps
            }
        )
    
    async def validate(self) -> bool:
        """
        Validate orchestration engine.
        
        Returns:
            True if validation passes
        """
        try:
            # Test simple operation creation
            steps = [
                OperationStep(
                    step_id="test_step",
                    phase=OperationPhase.RECONNAISSANCE,
                    tool_name="test_tool",
                    tool_config={}
                )
            ]
            
            op_id = self.create_operation(
                name="validation_test",
                description="Test operation",
                target="test",
                steps=steps
            )
            
            return op_id in self.operations
        
        except Exception:
            return False
