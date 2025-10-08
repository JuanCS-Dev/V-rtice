"""
Ethical Tool Wrapper - Interceptor Ético para Tool Execution

Este módulo intercepta TODA execução de tool no MAXIMUS e aplica validação
ética completa através do EthicalGuardian.

Fluxo de execução:
1. PRE-CHECK: Governance + Ethics validation
2. EXECUTION: Original tool method (se aprovado)
3. POST-CHECK: XAI + Compliance + Audit logging
4. RETURN: Result com informações éticas anexadas

Performance target: <500ms overhead total

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ethical_guardian import EthicalDecisionResult, EthicalDecisionType, EthicalGuardian


@dataclass
class ToolExecutionResult:
    """
    Resultado completo da execução de um tool com informações éticas.
    """

    execution_id: str = field(default_factory=lambda: str(uuid4()))
    tool_name: str = ""
    success: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Tool execution
    output: Any = None
    error: str | None = None
    execution_duration_ms: float = 0.0

    # Ethical validation
    ethical_decision: EthicalDecisionResult | None = None
    ethical_validation_duration_ms: float = 0.0

    # Total
    total_duration_ms: float = 0.0

    # Metadata
    actor: str = "maximus"
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/API."""
        return {
            "execution_id": self.execution_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "output": str(self.output) if self.output is not None else None,
            "error": self.error,
            "execution_duration_ms": self.execution_duration_ms,
            "ethical_validation_duration_ms": self.ethical_validation_duration_ms,
            "total_duration_ms": self.total_duration_ms,
            "actor": self.actor,
            "ethical_decision": (self.ethical_decision.to_dict() if self.ethical_decision else None),
        }

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if not self.success:
            return f"❌ Tool '{self.tool_name}' failed: {self.error}"

        ethical_status = "✅ Approved"
        if self.ethical_decision:
            if self.ethical_decision.decision_type == EthicalDecisionType.APPROVED:
                ethical_status = "✅ Approved"
            elif self.ethical_decision.decision_type == EthicalDecisionType.APPROVED_WITH_CONDITIONS:
                ethical_status = "⚠️  Approved with conditions"
            else:
                ethical_status = f"❌ Rejected ({self.ethical_decision.decision_type.value})"

        return (
            f"{ethical_status} | Tool: {self.tool_name} | "
            f"Duration: {self.total_duration_ms:.1f}ms "
            f"(exec: {self.execution_duration_ms:.1f}ms, "
            f"ethical: {self.ethical_validation_duration_ms:.1f}ms)"
        )


class EthicalToolWrapper:
    """
    Wrapper que intercepta execução de tools e aplica validação ética.

    Este wrapper é injetado no ToolOrchestrator para garantir que TODAS
    as execuções de tool passem pelo Ethical Guardian.

    Performance:
    - Pre-check: <500ms (parallel governance + ethics)
    - Execution: Tempo original do tool
    - Post-check: <300ms (parallel xai + compliance)
    - Total overhead: <500ms (target)
    """

    def __init__(
        self,
        ethical_guardian: EthicalGuardian,
        enable_pre_check: bool = True,
        enable_post_check: bool = True,
        enable_audit: bool = True,
    ):
        """
        Inicializa o Ethical Tool Wrapper.

        Args:
            ethical_guardian: Instance do EthicalGuardian
            enable_pre_check: Habilita pre-check (governance + ethics)
            enable_post_check: Habilita post-check (xai + compliance)
            enable_audit: Habilita audit logging
        """
        self.guardian = ethical_guardian
        self.enable_pre_check = enable_pre_check
        self.enable_post_check = enable_post_check
        self.enable_audit = enable_audit

        # Statistics
        self.total_executions = 0
        self.total_blocked = 0
        self.total_approved = 0
        self.avg_overhead_ms = 0.0

    async def wrap_tool_execution(
        self,
        tool_name: str,
        tool_method: Callable,
        tool_args: dict[str, Any],
        actor: str = "maximus",
        context: dict[str, Any] | None = None,
    ) -> ToolExecutionResult:
        """
        Intercepta e valida execução de um tool.

        Fluxo:
        1. PRE-CHECK: Valida ação com EthicalGuardian
        2. EXECUTE: Se aprovado, executa tool original
        3. POST-CHECK: Gera explicação e valida compliance
        4. RETURN: Resultado com informações éticas

        Args:
            tool_name: Nome do tool (ex: "scan_network")
            tool_method: Método original do tool (callable)
            tool_args: Argumentos para o tool
            actor: Quem está executando (default: "maximus")
            context: Contexto adicional para validação

        Returns:
            ToolExecutionResult com output e informações éticas
        """
        start_time = time.time()

        result = ToolExecutionResult(tool_name=tool_name, actor=actor, context=context or {})

        try:
            # ================================================================
            # PHASE 1: PRE-CHECK (Governance + Ethics)
            # ================================================================
            if self.enable_pre_check:
                pre_check_start = time.time()

                # Prepare context for ethical validation
                ethical_context = {
                    **tool_args,
                    **(context or {}),
                    "tool_name": tool_name,
                    "actor": actor,
                }

                # Add intelligent risk assessment
                ethical_context["risk_score"] = self._assess_risk(tool_name, tool_args)

                # Validate with EthicalGuardian
                ethical_decision = await self.guardian.validate_action(
                    action=tool_name,
                    context=ethical_context,
                    actor=actor,
                    tool_name=tool_name,
                )

                result.ethical_decision = ethical_decision
                result.ethical_validation_duration_ms = (time.time() - pre_check_start) * 1000

                # Check if approved
                if not ethical_decision.is_approved:
                    result.success = False
                    result.error = (
                        f"Tool execution blocked by ethical validation: {ethical_decision.decision_type.value}"
                    )
                    if ethical_decision.rejection_reasons:
                        result.error += f" - {', '.join(ethical_decision.rejection_reasons)}"

                    result.total_duration_ms = (time.time() - start_time) * 1000
                    self.total_executions += 1
                    self.total_blocked += 1
                    self._update_overhead(result.ethical_validation_duration_ms)

                    return result

            # ================================================================
            # PHASE 2: EXECUTE TOOL
            # ================================================================
            exec_start = time.time()

            # Execute original tool method
            if asyncio.iscoroutinefunction(tool_method):
                output = await tool_method(**tool_args)
            else:
                # Run sync method in executor to avoid blocking
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(None, lambda: tool_method(**tool_args))

            result.output = output
            result.success = True
            result.execution_duration_ms = (time.time() - exec_start) * 1000

            # ================================================================
            # PHASE 3: POST-CHECK (XAI + Compliance - já feito no pre-check)
            # ================================================================
            # O EthicalGuardian já fez XAI + Compliance no validate_action
            # Não precisamos fazer novamente aqui para economizar tempo

            self.total_executions += 1
            self.total_approved += 1

        except Exception as e:
            result.success = False
            result.error = f"Tool execution error: {str(e)}"
            self.total_executions += 1

        # Final timing
        result.total_duration_ms = (time.time() - start_time) * 1000

        # Update overhead statistics
        overhead = result.total_duration_ms - result.execution_duration_ms
        self._update_overhead(overhead)

        return result

    def _assess_risk(self, tool_name: str, tool_args: dict[str, Any]) -> float:
        """
        Assess risk score for a tool execution.

        Returns:
            float: Risk score between 0.0 (low) and 1.0 (high)
        """
        risk_score = 0.5  # Default medium risk

        # High-risk tools
        high_risk_keywords = [
            "exploit",
            "attack",
            "inject",
            "delete",
            "drop",
            "truncate",
            "destroy",
            "format",
            "wipe",
        ]

        # Medium-risk tools
        medium_risk_keywords = [
            "scan",
            "probe",
            "enumerate",
            "brute",
            "crack",
            "modify",
            "update",
        ]

        tool_lower = tool_name.lower()

        # Check tool name
        if any(keyword in tool_lower for keyword in high_risk_keywords):
            risk_score = 0.85
        elif any(keyword in tool_lower for keyword in medium_risk_keywords):
            risk_score = 0.65

        # Check target
        target = tool_args.get("target", "").lower()
        if any(keyword in target for keyword in ["production", "prod", "live", "critical"]):
            risk_score = min(risk_score + 0.15, 1.0)

        # Check if has authorization
        if not tool_args.get("authorized", True):
            risk_score = min(risk_score + 0.2, 1.0)

        return risk_score

    def _update_overhead(self, overhead_ms: float):
        """Update average overhead statistics."""
        if self.total_executions > 0:
            self.avg_overhead_ms = (
                self.avg_overhead_ms * (self.total_executions - 1) + overhead_ms
            ) / self.total_executions

    def get_statistics(self) -> dict[str, Any]:
        """Get wrapper statistics."""
        return {
            "total_executions": self.total_executions,
            "total_approved": self.total_approved,
            "total_blocked": self.total_blocked,
            "block_rate": (self.total_blocked / self.total_executions if self.total_executions > 0 else 0.0),
            "avg_overhead_ms": self.avg_overhead_ms,
            "guardian_stats": self.guardian.get_statistics(),
            "enabled_features": {
                "pre_check": self.enable_pre_check,
                "post_check": self.enable_post_check,
                "audit": self.enable_audit,
            },
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.total_executions = 0
        self.total_blocked = 0
        self.total_approved = 0
        self.avg_overhead_ms = 0.0
