"""
Attack Chain - Multi-stage attack orchestration.

Coordinates reconnaissance, exploitation, and post-exploitation phases
with AI-driven decision making and adaptive strategies.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from ..core.base import OffensiveTool, ToolResult, ToolMetadata
from ..core.exceptions import OffensiveToolError


class StageType(Enum):
    """Attack chain stage types."""
    RECONNAISSANCE = "reconnaissance"
    WEAPONIZATION = "weaponization"
    DELIVERY = "delivery"
    EXPLOITATION = "exploitation"
    INSTALLATION = "installation"
    COMMAND_CONTROL = "command_control"
    ACTIONS_OBJECTIVES = "actions_objectives"


class StageStatus(Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AttackStage:
    """
    Single stage in attack chain.
    
    Represents one phase of a multi-stage attack with
    dependencies, prerequisites, and success criteria.
    """
    name: str
    stage_type: StageType
    tool_name: str
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    required: bool = True
    timeout: float = 300.0
    retry_count: int = 3
    
    # Runtime state
    status: StageStatus = StageStatus.PENDING
    result: Optional[ToolResult] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ChainResult:
    """Attack chain execution result."""
    chain_name: str
    target: str
    start_time: datetime
    end_time: datetime
    stages: List[AttackStage]
    success: bool
    loot: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AttackChain(OffensiveTool):
    """
    AI-enhanced attack chain orchestrator.
    
    Coordinates multi-stage attacks following cyber kill chain methodology.
    Uses ML to adapt strategy based on target responses and intermediate results.
    """
    
    def __init__(self, name: str) -> None:
        """
        Initialize attack chain.
        
        Args:
            name: Chain identifier
        """
        super().__init__(
            name=f"attack_chain_{name}",
            category="orchestration"
        )
        
        self.chain_name = name
        self.stages: List[AttackStage] = []
        self.tools: Dict[str, OffensiveTool] = {}
        self.decision_callbacks: List[Callable] = []
    
    def add_stage(self, stage: AttackStage) -> None:
        """
        Add stage to attack chain.
        
        Args:
            stage: Attack stage to add
        """
        # Validate dependencies exist
        for dep in stage.dependencies:
            if not any(s.name == dep for s in self.stages):
                raise OffensiveToolError(
                    f"Stage dependency not found: {dep}",
                    tool_name=self.name
                )
        
        self.stages.append(stage)
    
    def register_tool(self, tool: OffensiveTool) -> None:
        """
        Register tool for use in chain.
        
        Args:
            tool: Offensive tool instance
        """
        self.tools[tool.name] = tool
    
    def add_decision_callback(self, callback: Callable) -> None:
        """
        Add decision callback for adaptive behavior.
        
        Args:
            callback: Decision function called between stages
        """
        self.decision_callbacks.append(callback)
    
    async def execute(
        self,
        target: str,
        initial_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute complete attack chain.
        
        Args:
            target: Target identifier
            initial_context: Initial context data
            **kwargs: Additional parameters
            
        Returns:
            ToolResult with chain execution results
            
        Raises:
            OffensiveToolError: If chain execution fails
        """
        start_time = datetime.utcnow()
        context = initial_context or {}
        context["target"] = target
        
        try:
            # Execute stages in dependency order
            execution_order = self._get_execution_order()
            abort_execution = False
            
            for stage in execution_order:
                # Check if execution was aborted
                if abort_execution:
                    stage.status = StageStatus.SKIPPED
                    continue
                
                # Check if stage should be skipped
                if await self._should_skip_stage(stage, context):
                    stage.status = StageStatus.SKIPPED
                    continue
                
                # Execute stage
                await self._execute_stage(stage, context)
                
                # Run decision callbacks
                for callback in self.decision_callbacks:
                    decision = await self._run_callback(callback, stage, context)
                    if decision.get("abort"):
                        abort_execution = True
                        break
                
                # Stop on failed required stage
                if stage.status == StageStatus.FAILED and stage.required:
                    abort_execution = True
            
            end_time = datetime.utcnow()
            
            # Determine overall success
            success = all(
                s.status == StageStatus.SUCCESS or not s.required
                for s in self.stages
            )
            
            # Collect loot from successful stages
            loot = self._collect_loot()
            
            chain_result = ChainResult(
                chain_name=self.chain_name,
                target=target,
                start_time=start_time,
                end_time=end_time,
                stages=self.stages,
                success=success,
                loot=loot,
                metadata={
                    "total_stages": len(self.stages),
                    "successful_stages": len([
                        s for s in self.stages if s.status == StageStatus.SUCCESS
                    ]),
                    "failed_stages": len([
                        s for s in self.stages if s.status == StageStatus.FAILED
                    ]),
                    "duration_seconds": (end_time - start_time).total_seconds()
                }
            )
            
            return ToolResult(
                success=success,
                data=chain_result,
                message=f"Attack chain {'completed' if success else 'failed'}",
                metadata=self._create_metadata(chain_result)
            )
            
        except Exception as e:
            raise OffensiveToolError(
                f"Attack chain execution failed: {str(e)}",
                tool_name=self.name,
                details={"target": target}
            )
    
    async def _execute_stage(
        self,
        stage: AttackStage,
        context: Dict[str, Any]
    ) -> None:
        """
        Execute single stage.
        
        Args:
            stage: Stage to execute
            context: Execution context
        """
        stage.status = StageStatus.RUNNING
        stage.start_time = datetime.utcnow()
        
        try:
            # Get tool for stage
            tool = self.tools.get(stage.tool_name)
            if not tool:
                raise OffensiveToolError(
                    f"Tool not registered: {stage.tool_name}",
                    tool_name=self.name
                )
            
            # Prepare stage config with context
            config = self._prepare_config(stage.config, context)
            
            # Execute with retries
            last_error = None
            for attempt in range(stage.retry_count):
                try:
                    result = await asyncio.wait_for(
                        tool.execute(**config),
                        timeout=stage.timeout
                    )
                    
                    if result.success:
                        stage.result = result
                        stage.status = StageStatus.SUCCESS
                        
                        # Update context with results
                        self._update_context(context, stage, result)
                        break
                    
                    last_error = result.message
                    
                except asyncio.TimeoutError:
                    last_error = f"Stage timed out after {stage.timeout}s"
                except Exception as e:
                    last_error = str(e)
                
                # Wait before retry
                if attempt < stage.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
            
            # Mark as failed if all retries exhausted
            if stage.status != StageStatus.SUCCESS:
                stage.status = StageStatus.FAILED
                stage.error = last_error
        
        finally:
            stage.end_time = datetime.utcnow()
    
    def _get_execution_order(self) -> List[AttackStage]:
        """
        Get stages in dependency order.
        
        Returns:
            Ordered list of stages
        """
        ordered = []
        remaining = self.stages.copy()
        
        while remaining:
            # Find stages with satisfied dependencies
            ready = [
                s for s in remaining
                if all(dep in [x.name for x in ordered] for dep in s.dependencies)
            ]
            
            if not ready:
                raise OffensiveToolError(
                    "Circular dependency detected in attack chain",
                    tool_name=self.name
                )
            
            ordered.extend(ready)
            for stage in ready:
                remaining.remove(stage)
        
        return ordered
    
    async def _should_skip_stage(
        self,
        stage: AttackStage,
        context: Dict[str, Any]
    ) -> bool:
        """
        Determine if stage should be skipped.
        
        Args:
            stage: Stage to check
            context: Current context
            
        Returns:
            True if stage should be skipped
        """
        # Check if dependencies failed
        for dep_name in stage.dependencies:
            dep_stage = next((s for s in self.stages if s.name == dep_name), None)
            if dep_stage and dep_stage.status == StageStatus.FAILED:
                if dep_stage.required:
                    return True
        
        return False
    
    def _prepare_config(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare stage config with context substitution.
        
        Args:
            config: Stage configuration
            context: Execution context
            
        Returns:
            Prepared configuration
        """
        prepared = {}
        
        for key, value in config.items():
            # Substitute context variables
            if isinstance(value, str) and value.startswith("$"):
                context_key = value[1:]
                prepared[key] = context.get(context_key, value)
            else:
                prepared[key] = value
        
        return prepared
    
    def _update_context(
        self,
        context: Dict[str, Any],
        stage: AttackStage,
        result: ToolResult
    ) -> None:
        """
        Update context with stage results.
        
        Args:
            context: Execution context
            stage: Executed stage
            result: Stage result
        """
        # Store stage result in context
        context[f"{stage.name}_result"] = result.data
        
        # Extract specific data based on stage type
        if stage.stage_type == StageType.RECONNAISSANCE:
            if hasattr(result.data, "ports"):
                context["open_ports"] = [
                    p.number for p in result.data.ports if p.state == "open"
                ]
            if hasattr(result.data, "subdomains"):
                context["subdomains"] = [
                    s.subdomain for s in result.data.subdomains
                ]
        
        elif stage.stage_type == StageType.EXPLOITATION:
            if hasattr(result.data, "session_id"):
                context["session_id"] = result.data.session_id
            if hasattr(result.data, "loot"):
                context.update(result.data.loot)
    
    async def _run_callback(
        self,
        callback: Callable,
        stage: AttackStage,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run decision callback.
        
        Args:
            callback: Callback function
            stage: Current stage
            context: Execution context
            
        Returns:
            Decision dictionary
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                return await callback(stage, context)
            else:
                return callback(stage, context)
        except Exception as e:
            return {"error": str(e)}
    
    def _collect_loot(self) -> Dict[str, Any]:
        """
        Collect loot from successful stages.
        
        Returns:
            Aggregated loot data
        """
        loot = {}
        
        for stage in self.stages:
            if stage.status == StageStatus.SUCCESS and stage.result:
                if hasattr(stage.result.data, "loot"):
                    loot[stage.name] = stage.result.data.loot
                elif isinstance(stage.result.data, dict):
                    loot[stage.name] = stage.result.data
        
        return loot
    
    def _create_metadata(self, result: ChainResult) -> ToolMetadata:
        """
        Create tool metadata.
        
        Args:
            result: Chain result
            
        Returns:
            Tool metadata
        """
        total_stages = result.metadata["total_stages"]
        successful_stages = result.metadata["successful_stages"]
        
        return ToolMetadata(
            tool_name=self.name,
            execution_time=result.metadata["duration_seconds"],
            success_rate=successful_stages / total_stages if total_stages > 0 else 0.0,
            confidence_score=0.9 if result.success else 0.4,
            resource_usage={
                "stages_executed": total_stages,
                "tools_used": len(self.tools)
            }
        )
    
    async def validate(self) -> bool:
        """
        Validate attack chain.
        
        Returns:
            True if validation passes
        """
        # Validate all registered tools
        for tool in self.tools.values():
            if not await tool.validate():
                return False
        
        # Validate stage dependencies
        try:
            self._get_execution_order()
            return True
        except OffensiveToolError:
            return False
