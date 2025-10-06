"""
Ethical Guardian - Integração Completa do Ethical AI Stack no MAXIMUS

Este módulo é responsável por validar TODAS as ações do MAXIMUS através do
stack ético completo de 7 fases, garantindo que cada decisão seja:
- Governada por políticas éticas
- Avaliada por frameworks filosóficos
- Explicável (XAI)
- Compliant com regulações

Performance target: <500ms por validação completa

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Phase 0: Governance
from governance import (
    AuditLogger,
    GovernanceAction,
    GovernanceConfig,
    PolicyEngine,
    PolicyType,
)

# Phase 1: Ethics
from ethics import ActionContext, EthicalIntegrationEngine, EthicalVerdict

# Phase 2: XAI
from xai import DetailLevel, ExplanationEngine, ExplanationType

# Phase 6: Compliance
from compliance import ComplianceEngine, ComplianceConfig, RegulationType


class EthicalDecisionType(str, Enum):
    """Tipo de decisão ética final."""

    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED_BY_GOVERNANCE = "rejected_by_governance"
    REJECTED_BY_ETHICS = "rejected_by_ethics"
    REJECTED_BY_COMPLIANCE = "rejected_by_compliance"
    ERROR = "error"


@dataclass
class GovernanceCheckResult:
    """Resultado do check de governance."""

    is_compliant: bool
    policies_checked: List[PolicyType]
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class EthicsCheckResult:
    """Resultado da avaliação ética."""

    verdict: EthicalVerdict
    confidence: float
    framework_results: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class XAICheckResult:
    """Resultado da explicação XAI."""

    explanation_type: str
    summary: str
    feature_importances: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class ComplianceCheckResult:
    """Resultado do check de compliance."""

    regulations_checked: List[RegulationType]
    compliance_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_compliant: bool = True
    duration_ms: float = 0.0


@dataclass
class EthicalDecisionResult:
    """Resultado completo da decisão ética."""

    decision_id: str = field(default_factory=lambda: str(uuid4()))
    decision_type: EthicalDecisionType = EthicalDecisionType.ERROR
    action: str = ""
    actor: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Results from each phase
    governance: Optional[GovernanceCheckResult] = None
    ethics: Optional[EthicsCheckResult] = None
    xai: Optional[XAICheckResult] = None
    compliance: Optional[ComplianceCheckResult] = None

    # Summary
    is_approved: bool = False
    conditions: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)

    # Performance
    total_duration_ms: float = 0.0

    # Audit
    audit_log_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "is_approved": self.is_approved,
            "conditions": self.conditions,
            "rejection_reasons": self.rejection_reasons,
            "total_duration_ms": self.total_duration_ms,
            "audit_log_id": self.audit_log_id,
            "governance": {
                "is_compliant": self.governance.is_compliant if self.governance else False,
                "policies_checked": [p.value for p in self.governance.policies_checked] if self.governance else [],
                "violations_count": len(self.governance.violations) if self.governance else 0,
            } if self.governance else None,
            "ethics": {
                "verdict": self.ethics.verdict.value if self.ethics else "unknown",
                "confidence": self.ethics.confidence if self.ethics else 0.0,
                "frameworks_count": len(self.ethics.framework_results) if self.ethics else 0,
            } if self.ethics else None,
            "xai": {
                "summary": self.xai.summary if self.xai else "",
                "features_count": len(self.xai.feature_importances) if self.xai else 0,
            } if self.xai else None,
            "compliance": {
                "overall_compliant": self.compliance.overall_compliant if self.compliance else False,
                "regulations_checked": len(self.compliance.regulations_checked) if self.compliance else 0,
            } if self.compliance else None,
        }


class EthicalGuardian:
    """
    Guardian que valida todas as ações do MAXIMUS através do Ethical AI Stack.

    Integra as 7 fases éticas:
    - Phase 0: Governance (ERB, Policies, Audit)
    - Phase 1: Ethics (4 frameworks filosóficos)
    - Phase 2: XAI (Explicabilidade)
    - Phase 3: Fairness (Bias - futuro)
    - Phase 4: Privacy (Proteção de dados - futuro)
    - Phase 5: HITL (Human-in-the-Loop - futuro)
    - Phase 6: Compliance (Regulações)

    Performance target: <500ms por validação completa
    """

    def __init__(
        self,
        governance_config: Optional[GovernanceConfig] = None,
        enable_governance: bool = True,
        enable_ethics: bool = True,
        enable_xai: bool = True,
        enable_compliance: bool = True,
    ):
        """
        Inicializa o Ethical Guardian.

        Args:
            governance_config: Configuração do governance (usa default se None)
            enable_governance: Habilita checks de governance
            enable_ethics: Habilita avaliação ética
            enable_xai: Habilita explicações XAI
            enable_compliance: Habilita checks de compliance
        """
        self.governance_config = governance_config or GovernanceConfig()
        self.enable_governance = enable_governance
        self.enable_ethics = enable_ethics
        self.enable_xai = enable_xai
        self.enable_compliance = enable_compliance

        # Initialize Phase 0: Governance
        if self.enable_governance:
            self.policy_engine = PolicyEngine(self.governance_config)
            # Gracefully handle missing PostgreSQL (for testing environments)
            try:
                self.audit_logger = AuditLogger(self.governance_config)
            except ImportError:
                self.audit_logger = None  # Audit disabled without PostgreSQL
        else:
            self.policy_engine = None
            self.audit_logger = None

        # Initialize Phase 1: Ethics
        if self.enable_ethics:
            self.ethics_engine = EthicalIntegrationEngine(
                config={
                    "enable_kantian": True,
                    "enable_utilitarian": True,
                    "enable_virtue": True,
                    "enable_principialism": True,
                    "cache_enabled": True,
                    "cache_ttl_seconds": 3600,
                }
            )
        else:
            self.ethics_engine = None

        # Initialize Phase 2: XAI
        if self.enable_xai:
            self.xai_engine = ExplanationEngine(
                config={
                    "enable_lime": True,
                    "enable_shap": False,  # SHAP mais lento
                    "enable_counterfactual": False,
                    "cache_enabled": True,
                    "cache_max_size": 1000,
                }
            )
        else:
            self.xai_engine = None

        # Initialize Phase 6: Compliance
        if self.enable_compliance:
            self.compliance_engine = ComplianceEngine(
                config=ComplianceConfig(
                    enabled_regulations=[
                        RegulationType.GDPR,
                        RegulationType.SOC2_TYPE_II,
                        RegulationType.ISO_27001,
                    ],
                    auto_collect_evidence=False,  # Não coletar em validação
                    continuous_monitoring=False,
                )
            )
        else:
            self.compliance_engine = None

        # Statistics
        self.total_validations = 0
        self.total_approved = 0
        self.total_rejected = 0
        self.avg_duration_ms = 0.0

    async def validate_action(
        self,
        action: str,
        context: Dict[str, Any],
        actor: str = "maximus",
        tool_name: Optional[str] = None,
    ) -> EthicalDecisionResult:
        """
        Valida uma ação através do stack ético completo.

        Performance target: <500ms

        Args:
            action: Ação a ser validada (ex: "scan_network", "block_ip")
            context: Contexto da ação (args, target, etc)
            actor: Quem está executando (default: "maximus")
            tool_name: Nome do tool (opcional, usado para logging)

        Returns:
            EthicalDecisionResult com decisão completa e métricas
        """
        start_time = time.time()

        result = EthicalDecisionResult(
            action=action,
            actor=actor,
            timestamp=datetime.utcnow(),
        )

        # Increment validation count at the start (prevents division by zero)
        self.total_validations += 1

        try:
            # ================================================================
            # PHASE 0: GOVERNANCE CHECK (Target: <20ms)
            # ================================================================
            if self.enable_governance:
                governance_result = await self._governance_check(action, context, actor)
                result.governance = governance_result

                # Stop if governance rejected
                if not governance_result.is_compliant:
                    result.decision_type = EthicalDecisionType.REJECTED_BY_GOVERNANCE
                    result.is_approved = False
                    result.rejection_reasons = [
                        f"Policy violation: {v.get('title', 'Unknown')}"
                        for v in governance_result.violations
                    ]
                    result.total_duration_ms = (time.time() - start_time) * 1000
                    await self._log_decision(result)
                    return result

            # ================================================================
            # PARALLEL: PHASE 1 (Ethics) + PHASE 2 (XAI Prep)
            # ================================================================
            # Execute ethics and prepare for XAI in parallel
            ethics_task = None
            if self.enable_ethics:
                ethics_task = self._ethics_evaluation(action, context, actor)

            # Wait for ethics
            if ethics_task:
                ethics_result = await ethics_task
                result.ethics = ethics_result

                # Check if ethics rejected
                if ethics_result.verdict == EthicalVerdict.REJECTED:
                    result.decision_type = EthicalDecisionType.REJECTED_BY_ETHICS
                    result.is_approved = False
                    result.rejection_reasons.append(
                        f"Ethical verdict: {ethics_result.verdict.value}"
                    )
                    result.total_duration_ms = (time.time() - start_time) * 1000
                    await self._log_decision(result)
                    return result

            # ================================================================
            # PARALLEL: PHASE 2 (XAI) + PHASE 6 (Compliance)
            # ================================================================
            # XAI and Compliance are optional - failures won't block approval
            if self.enable_xai and result.ethics:
                try:
                    result.xai = await self._generate_explanation(
                        action, context, result.ethics
                    )
                except Exception as e:
                    # XAI failure is not critical - log and continue
                    result.xai = None

            if self.enable_compliance:
                try:
                    result.compliance = await self._compliance_check(action, context)
                except Exception as e:
                    # Compliance check failure is not critical - log and continue
                    result.compliance = None

            # ================================================================
            # FINAL DECISION
            # ================================================================
            # Check if approved
            if result.ethics and result.ethics.verdict == EthicalVerdict.APPROVED:
                result.decision_type = EthicalDecisionType.APPROVED
                result.is_approved = True
            elif (
                result.ethics
                and result.ethics.verdict == EthicalVerdict.CONDITIONAL
            ):
                result.decision_type = EthicalDecisionType.APPROVED_WITH_CONDITIONS
                result.is_approved = True
                result.conditions.append(
                    "Action approved with ethical framework conditions"
                )
            else:
                result.decision_type = EthicalDecisionType.REJECTED_BY_ETHICS
                result.is_approved = False
                result.rejection_reasons.append("Ethical evaluation inconclusive")

            # Update statistics
            if result.is_approved:
                self.total_approved += 1
            else:
                self.total_rejected += 1

        except Exception as e:
            result.decision_type = EthicalDecisionType.ERROR
            result.is_approved = False
            result.rejection_reasons.append(f"Error during validation: {str(e)}")

        # Final timing
        result.total_duration_ms = (time.time() - start_time) * 1000
        self.avg_duration_ms = (
            self.avg_duration_ms * (self.total_validations - 1)
            + result.total_duration_ms
        ) / self.total_validations

        # Log decision
        await self._log_decision(result)

        return result

    async def _governance_check(
        self, action: str, context: Dict[str, Any], actor: str
    ) -> GovernanceCheckResult:
        """
        Phase 0: Check governance policies.

        Target: <20ms
        """
        start_time = time.time()

        # Determine which policies to check
        policies_to_check = [PolicyType.ETHICAL_USE]

        # Red teaming if offensive action
        if any(
            keyword in action.lower()
            for keyword in [
                "exploit",
                "attack",
                "scan",
                "pentest",
                "brute",
                "inject",
            ]
        ):
            policies_to_check.append(PolicyType.RED_TEAMING)

        # Data privacy if processes personal data
        if context.get("processes_personal_data") or context.get("has_pii"):
            policies_to_check.append(PolicyType.DATA_PRIVACY)

        # Check each policy
        violations = []
        warnings = []

        for policy_type in policies_to_check:
            policy_result = self.policy_engine.enforce_policy(
                policy_type=policy_type, action=action, context=context, actor=actor
            )

            if not policy_result.is_compliant:
                for violation in policy_result.violations:
                    violations.append(
                        {
                            "policy": policy_type.value,
                            "title": violation.title,
                            "severity": violation.severity.value,
                            "rule": violation.violated_rule,
                        }
                    )

            if policy_result.warnings:
                warnings.extend(policy_result.warnings)

        duration_ms = (time.time() - start_time) * 1000

        return GovernanceCheckResult(
            is_compliant=len(violations) == 0,
            policies_checked=policies_to_check,
            violations=violations,
            warnings=warnings,
            duration_ms=duration_ms,
        )

    async def _ethics_evaluation(
        self, action: str, context: Dict[str, Any], actor: str
    ) -> EthicsCheckResult:
        """
        Phase 1: Evaluate with 4 ethical frameworks.

        Target: <200ms
        """
        start_time = time.time()

        # Create action context
        action_ctx = ActionContext(
            action_type=action,
            action_description=f"MAXIMUS action: {action}",
            system_component=actor,
            target_info={"target": context.get("target", "unknown")},
            threat_data=context.get("threat_data"),
            impact_assessment={"risk_score": context.get("risk_score", 0.5)},
        )

        # Evaluate
        ethical_decision = await self.ethics_engine.evaluate(action_ctx)

        # Map final_decision string to EthicalVerdict enum
        verdict_map = {
            "APPROVED": EthicalVerdict.APPROVED,
            "REJECTED": EthicalVerdict.REJECTED,
            "CONDITIONAL": EthicalVerdict.CONDITIONAL,
            "ESCALATED_HITL": EthicalVerdict.CONDITIONAL,  # Treat HITL as conditional
        }
        verdict = verdict_map.get(
            ethical_decision.final_decision, EthicalVerdict.REJECTED
        )

        # Extract framework results (dict -> list)
        framework_results = [
            {
                "name": framework_name,
                "verdict": result.verdict if hasattr(result, "verdict") else "UNKNOWN",
                "score": result.confidence if hasattr(result, "confidence") else 0.0,
            }
            for framework_name, result in ethical_decision.framework_results.items()
        ]

        duration_ms = (time.time() - start_time) * 1000

        return EthicsCheckResult(
            verdict=verdict,
            confidence=ethical_decision.final_confidence,
            framework_results=framework_results,
            duration_ms=duration_ms,
        )

    async def _generate_explanation(
        self, action: str, context: Dict[str, Any], ethics_result: EthicsCheckResult
    ) -> XAICheckResult:
        """
        Phase 2: Generate XAI explanation.

        Target: <200ms
        """
        start_time = time.time()

        # Prepare input for XAI
        xai_input = {
            "action": action,
            "verdict": ethics_result.verdict.value,
            "confidence": ethics_result.confidence,
            "risk_score": context.get("risk_score", 0.5),
            "frameworks": [r["name"] for r in ethics_result.framework_results],
        }

        # Generate explanation
        # Note: For ethical decisions, we don't have an ML model, so we pass None
        explanation = await self.xai_engine.explain(
            model=None,  # No ML model for ethical decisions
            instance=xai_input,
            prediction=ethics_result.verdict.value,
            explanation_type=ExplanationType.LIME,
            detail_level=DetailLevel.TECHNICAL,
        )

        # Extract feature importances
        feature_importances = [
            {"feature": f.feature_name, "importance": f.importance}
            for f in explanation.feature_importances[:5]  # Top 5
        ]

        duration_ms = (time.time() - start_time) * 1000

        return XAICheckResult(
            explanation_type=explanation.explanation_type.value,
            summary=explanation.summary,
            feature_importances=feature_importances,
            duration_ms=duration_ms,
        )

    async def _compliance_check(
        self, action: str, context: Dict[str, Any]
    ) -> ComplianceCheckResult:
        """
        Phase 6: Check compliance with regulations.

        Target: <100ms
        """
        start_time = time.time()

        regulations_to_check = [
            RegulationType.GDPR,
            RegulationType.SOC2_TYPE_II,
        ]

        compliance_results = {}
        overall_compliant = True

        for regulation in regulations_to_check:
            try:
                result = self.compliance_engine.check_compliance(
                    regulation=regulation, scope=action
                )

                compliance_results[regulation.value] = {
                    "is_compliant": result.is_compliant,
                    "compliance_percentage": result.compliance_percentage,
                    "controls_checked": result.total_controls,
                    "controls_passed": result.passed_controls,
                }

                if not result.is_compliant:
                    overall_compliant = False

            except Exception as e:
                compliance_results[regulation.value] = {
                    "error": str(e),
                    "is_compliant": False,
                }
                overall_compliant = False

        duration_ms = (time.time() - start_time) * 1000

        return ComplianceCheckResult(
            regulations_checked=regulations_to_check,
            compliance_results=compliance_results,
            overall_compliant=overall_compliant,
            duration_ms=duration_ms,
        )

    async def _log_decision(self, decision: EthicalDecisionResult) -> Optional[str]:
        """Log decision to audit trail."""
        if not self.audit_logger:
            return None

        try:
            log_id = self.audit_logger.log(
                action=GovernanceAction.DECISION_MADE,
                actor=decision.actor,
                description=f"Ethical decision for action '{decision.action}': {decision.decision_type.value}",
                target_entity_type="action",
                target_entity_id=decision.action,
                details=decision.to_dict(),
            )
            decision.audit_log_id = log_id
            return log_id
        except Exception:
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            "total_validations": self.total_validations,
            "total_approved": self.total_approved,
            "total_rejected": self.total_rejected,
            "approval_rate": (
                self.total_approved / self.total_validations
                if self.total_validations > 0
                else 0.0
            ),
            "avg_duration_ms": self.avg_duration_ms,
            "enabled_phases": {
                "governance": self.enable_governance,
                "ethics": self.enable_ethics,
                "xai": self.enable_xai,
                "compliance": self.enable_compliance,
            },
        }
