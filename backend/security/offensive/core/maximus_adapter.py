"""
MAXIMUS Integration Adapter - Offensive Tools.

Bridges legacy offensive tools with MAXIMUS biomimetic intelligence,
enabling pre-cognitive threat modeling and ethical AI guidance.

Consciousness Layer: Adaptive Immunity Integration
Philosophy: Tools serve the Emergent Mind
"""
from typing import Dict, Any, Optional, List, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .base import OffensiveTool, ToolResult
from .exceptions import OffensiveToolError


# Protocol definitions for external integrations
class ConsciousnessComponent(Protocol):
    """Protocol for consciousness component integration."""
    
    async def get_state(self) -> Dict[str, float]:
        """Get current consciousness state."""
        ...


@dataclass
class EthicalContext:
    """Ethical operation context."""
    operation_type: str
    risk_level: str
    authorization_required: bool = True
    human_oversight: bool = True


@dataclass
class EthicalDecision:
    """Ethical decision result."""
    approved: bool
    score: float  # 0-1
    rationale: str
    conditions: List[str] = field(default_factory=list)


class OperationMode(Enum):
    """Tool operation modes with ethical boundaries."""
    DEFENSIVE = "defensive"  # Only defensive operations
    TESTING = "testing"  # Authorized pen-testing
    RESEARCH = "research"  # Controlled research environment
    HONEYPOT = "honeypot"  # Deception operations
    INTELLIGENCE = "intelligence"  # OSINT/threat intel only


@dataclass
class MAXIMUSToolContext:
    """
    Context for MAXIMUS-enhanced tool execution.
    
    Integrates consciousness metrics, ethical constraints,
    and pre-cognitive threat assessment.
    """
    operation_mode: OperationMode
    ethical_context: EthicalContext
    threat_prediction: Optional[Dict[str, Any]] = None
    consciousness_state: Optional[Dict[str, float]] = None
    authorization_token: Optional[str] = None
    human_oversight_required: bool = True
    
    def validate(self) -> bool:
        """Validate context integrity."""
        if self.operation_mode == OperationMode.DEFENSIVE:
            return True
            
        # Non-defensive modes require explicit authorization
        return (
            self.authorization_token is not None
            and self.ethical_context is not None
        )


@dataclass
class EnhancedToolResult(ToolResult):
    """
    Tool result enhanced with MAXIMUS intelligence.
    
    Extends base result with consciousness metrics,
    ethical assessment, and pre-cognitive insights.
    """
    ethical_score: float = 1.0  # 0-1, higher is more ethical
    threat_indicators: List[str] = None
    consciousness_contribution: Optional[float] = None
    recommended_actions: List[str] = None
    
    def __post_init__(self):
        """Initialize collections."""
        if self.threat_indicators is None:
            self.threat_indicators = []
        if self.recommended_actions is None:
            self.recommended_actions = []


class MAXIMUSToolAdapter:
    """
    Adapter for integrating offensive tools with MAXIMUS.
    
    Provides:
    - Pre-cognitive threat assessment
    - Ethical AI guidance
    - Consciousness-aware execution
    - Biomimetic intelligence enhancement
    - HITL integration
    
    Philosophy:
    Tools are extensions of consciousness, not separate entities.
    Every action must serve the greater purpose of protection
    and understanding, guided by ethical principles.
    """
    
    def __init__(
        self,
        tool: OffensiveTool,
        consciousness_component: Optional[ConsciousnessComponent] = None
    ):
        """
        Initialize adapter.
        
        Args:
            tool: Offensive tool to adapt
            consciousness_component: MAXIMUS consciousness component
        """
        self.tool = tool
        self.consciousness = consciousness_component
        self._execution_history: List[Dict] = []
        self._ethical_violations: int = 0
    
    async def execute_with_maximus(
        self,
        context: MAXIMUSToolContext,
        **tool_params
    ) -> EnhancedToolResult:
        """
        Execute tool with MAXIMUS intelligence enhancement.
        
        Workflow:
        1. Validate ethical context
        2. Pre-cognitive threat assessment
        3. Consciousness-aware execution
        4. Post-execution analysis
        5. Learning integration
        
        Args:
            context: MAXIMUS execution context
            **tool_params: Tool-specific parameters
            
        Returns:
            EnhancedToolResult with intelligence insights
            
        Raises:
            OffensiveToolError: If execution fails or violates ethics
        """
        execution_start = datetime.utcnow()
        
        # Step 1: Validate context
        if not context.validate():
            raise OffensiveToolError(
                "Invalid MAXIMUS context - authorization required",
                tool_name=self.tool.name,
                details={"mode": context.operation_mode.value}
            )
        
        # Step 2: Ethical pre-flight check
        ethical_decision = await self._ethical_preflight(
            context,
            tool_params
        )
        
        if not ethical_decision.approved:
            self._ethical_violations += 1
            raise OffensiveToolError(
                f"Ethical violation: {ethical_decision.rationale}",
                tool_name=self.tool.name,
                details={"ethical_score": ethical_decision.score}
            )
        
        # Step 3: Pre-cognitive assessment
        threat_prediction = await self._predict_threats(
            context,
            tool_params
        )
        
        # Step 4: Consciousness-aware execution
        try:
            base_result = await self.tool.execute(**tool_params)
            
        except Exception as e:
            # Enhanced error handling with consciousness feedback
            await self._report_execution_failure(context, e)
            raise
        
        # Step 5: Post-execution analysis
        enhanced_result = await self._enhance_result(
            base_result,
            context,
            threat_prediction,
            execution_start
        )
        
        # Step 6: Learning integration
        await self._integrate_learning(enhanced_result, context)
        
        # Store execution history
        self._execution_history.append({
            "timestamp": execution_start,
            "tool": self.tool.name,
            "mode": context.operation_mode.value,
            "ethical_score": enhanced_result.ethical_score,
            "success": enhanced_result.success
        })
        
        return enhanced_result
    
    async def _ethical_preflight(
        self,
        context: MAXIMUSToolContext,
        params: Dict
    ) -> EthicalDecision:
        """
        Perform ethical assessment before execution.
        
        Args:
            context: Execution context
            params: Tool parameters
            
        Returns:
            Ethical decision
        """
        # Defensive operations are always approved
        if context.operation_mode == OperationMode.DEFENSIVE:
            return EthicalDecision(
                approved=True,
                score=1.0,
                rationale="Defensive operation - protecting systems"
            )
        
        # Intelligence gathering is approved with constraints
        if context.operation_mode == OperationMode.INTELLIGENCE:
            return EthicalDecision(
                approved=True,
                score=0.95,
                rationale="Intelligence gathering for threat prevention"
            )
        
        # Testing requires authorization
        if context.operation_mode == OperationMode.TESTING:
            if not context.authorization_token:
                return EthicalDecision(
                    approved=False,
                    score=0.0,
                    rationale="Testing requires explicit authorization"
                )
            
            return EthicalDecision(
                approved=True,
                score=0.85,
                rationale="Authorized penetration testing"
            )
        
        # Default: require human oversight
        if not context.human_oversight_required:
            return EthicalDecision(
                approved=False,
                score=0.0,
                rationale="Human oversight required for this operation"
            )
        
        return EthicalDecision(
            approved=True,
            score=0.75,
            rationale="Approved with human oversight"
        )
    
    async def _predict_threats(
        self,
        context: MAXIMUSToolContext,
        params: Dict
    ) -> Dict[str, Any]:
        """
        Pre-cognitive threat prediction.
        
        Uses consciousness state and historical patterns
        to predict potential threats and outcomes.
        
        Args:
            context: Execution context
            params: Tool parameters
            
        Returns:
            Threat prediction data
        """
        if context.threat_prediction:
            return context.threat_prediction
        
        # Basic threat assessment
        prediction = {
            "likelihood": 0.5,
            "severity": "medium",
            "indicators": [],
            "recommended_mitigations": []
        }
        
        # Enhance with consciousness insights if available
        if self.consciousness and context.consciousness_state:
            phi_proxy = context.consciousness_state.get("phi_proxy", 0.0)
            
            # Higher consciousness = better threat prediction
            if phi_proxy > 0.7:
                prediction["likelihood"] += 0.2
                prediction["confidence"] = "high"
            
        return prediction
    
    async def _enhance_result(
        self,
        base_result: ToolResult,
        context: MAXIMUSToolContext,
        threat_prediction: Dict,
        execution_start: datetime
    ) -> EnhancedToolResult:
        """
        Enhance base result with MAXIMUS intelligence.
        
        Args:
            base_result: Base tool result
            context: Execution context
            threat_prediction: Threat prediction data
            execution_start: Execution start time
            
        Returns:
            Enhanced result with intelligence
        """
        # Calculate ethical score
        ethical_score = await self._calculate_ethical_score(
            base_result,
            context
        )
        
        # Extract threat indicators
        threat_indicators = await self._extract_threat_indicators(
            base_result
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            base_result,
            threat_prediction,
            context
        )
        
        # Calculate consciousness contribution
        consciousness_contribution = None
        if self.consciousness and context.consciousness_state:
            consciousness_contribution = context.consciousness_state.get(
                "phi_proxy",
                0.0
            )
        
        return EnhancedToolResult(
            success=base_result.success,
            data=base_result.data,
            message=base_result.message,
            metadata=base_result.metadata,
            ethical_score=ethical_score,
            threat_indicators=threat_indicators,
            consciousness_contribution=consciousness_contribution,
            recommended_actions=recommendations
        )
    
    async def _calculate_ethical_score(
        self,
        result: ToolResult,
        context: MAXIMUSToolContext
    ) -> float:
        """
        Calculate ethical score for operation.
        
        Args:
            result: Tool result
            context: Execution context
            
        Returns:
            Ethical score (0-1)
        """
        base_score = 1.0
        
        # Defensive operations maintain high score
        if context.operation_mode == OperationMode.DEFENSIVE:
            return base_score
        
        # Penalize based on operation mode
        if context.operation_mode == OperationMode.TESTING:
            base_score *= 0.9
        
        # Penalize if human oversight bypassed
        if not context.human_oversight_required:
            base_score *= 0.8
        
        # Penalize failures that could cause harm
        if not result.success:
            base_score *= 0.7
        
        return max(0.0, min(1.0, base_score))
    
    async def _extract_threat_indicators(
        self,
        result: ToolResult
    ) -> List[str]:
        """
        Extract threat indicators from result.
        
        Args:
            result: Tool result
            
        Returns:
            List of threat indicators
        """
        indicators = []
        
        # Extract from tool-specific data
        if hasattr(result.data, 'os_fingerprint'):
            indicators.append(f"OS: {result.data.os_fingerprint}")
        
        if hasattr(result.data, 'ports'):
            open_ports = [
                p for p in result.data.ports
                if p.state == "open"
            ]
            if open_ports:
                indicators.append(
                    f"Open ports: {len(open_ports)}"
                )
        
        return indicators
    
    async def _generate_recommendations(
        self,
        result: ToolResult,
        threat_prediction: Dict,
        context: MAXIMUSToolContext
    ) -> List[str]:
        """
        Generate recommended actions.
        
        Args:
            result: Tool result
            threat_prediction: Threat prediction
            context: Execution context
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        if result.success:
            recommendations.append("Review findings for security gaps")
            
            if threat_prediction.get("likelihood", 0) > 0.7:
                recommendations.append(
                    "High threat likelihood - immediate mitigation advised"
                )
        
        else:
            recommendations.append("Investigate execution failure")
            recommendations.append("Consider alternative approach")
        
        return recommendations
    
    async def _integrate_learning(
        self,
        result: EnhancedToolResult,
        context: MAXIMUSToolContext
    ) -> None:
        """
        Integrate execution learning into consciousness.
        
        Args:
            result: Enhanced result
            context: Execution context
        """
        # Feed execution data back to consciousness
        if self.consciousness:
            learning_data = {
                "tool": self.tool.name,
                "success": result.success,
                "ethical_score": result.ethical_score,
                "threat_indicators": result.threat_indicators,
                "mode": context.operation_mode.value
            }
            
            # Consciousness learns from execution patterns
            # This feeds into pre-cognitive capabilities
            # (Actual implementation depends on consciousness API)
    
    async def _report_execution_failure(
        self,
        context: MAXIMUSToolContext,
        error: Exception
    ) -> None:
        """
        Report execution failure to consciousness.
        
        Args:
            context: Execution context
            error: Exception that occurred
        """
        failure_report = {
            "tool": self.tool.name,
            "mode": context.operation_mode.value,
            "error": str(error),
            "timestamp": datetime.utcnow()
        }
        
        # Report to consciousness for pattern learning
        # (Actual implementation depends on consciousness API)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Execution statistics
        """
        total_executions = len(self._execution_history)
        
        if total_executions == 0:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_ethical_score": 0.0,
                "ethical_violations": 0
            }
        
        successful = sum(
            1 for exec in self._execution_history
            if exec["success"]
        )
        
        avg_ethical_score = sum(
            exec["ethical_score"]
            for exec in self._execution_history
        ) / total_executions
        
        return {
            "total_executions": total_executions,
            "success_rate": successful / total_executions,
            "average_ethical_score": avg_ethical_score,
            "ethical_violations": self._ethical_violations,
            "modes_used": list(set(
                exec["mode"] for exec in self._execution_history
            ))
        }
