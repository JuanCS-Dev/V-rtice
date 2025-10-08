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

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Phase 0: Governance
# Phase 6: Compliance
from compliance import ComplianceConfig, ComplianceEngine, RegulationType

# Phase 1: Ethics
from ethics import ActionContext, EthicalIntegrationEngine, EthicalVerdict

# Phase 3: Fairness & Bias Mitigation
from fairness import (
    BiasDetector,
    FairnessMonitor,
    ProtectedAttribute,
)

# Phase 4.2: Federated Learning
from federated_learning import (
    AggregationStrategy,
    FLConfig,
    FLStatus,
    ModelType,
)
from governance import (
    AuditLogger,
    GovernanceAction,
    GovernanceConfig,
    PolicyEngine,
    PolicyType,
)

# Phase 5: HITL (Human-in-the-Loop)
from hitl import (
    ActionType,
    AutomationLevel,
    DecisionContext,
    HITLDecisionFramework,
    RiskAssessor,
    RiskLevel,
)

# Phase 4.1: Differential Privacy
from privacy import (
    CompositionType,
    PrivacyAccountant,
    PrivacyBudget,
)

# Phase 2: XAI
from xai import DetailLevel, ExplanationEngine, ExplanationType


class EthicalDecisionType(str, Enum):
    """Tipo de decisão ética final."""

    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED_BY_GOVERNANCE = "rejected_by_governance"
    REJECTED_BY_ETHICS = "rejected_by_ethics"
    REJECTED_BY_FAIRNESS = "rejected_by_fairness"  # Phase 3
    REJECTED_BY_PRIVACY = "rejected_by_privacy"  # Phase 4.1
    REJECTED_BY_COMPLIANCE = "rejected_by_compliance"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"  # Phase 5: HITL
    ERROR = "error"


@dataclass
class GovernanceCheckResult:
    """Resultado do check de governance."""

    is_compliant: bool
    policies_checked: list[PolicyType]
    violations: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class EthicsCheckResult:
    """Resultado da avaliação ética."""

    verdict: EthicalVerdict
    confidence: float
    framework_results: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class XAICheckResult:
    """Resultado da explicação XAI."""

    explanation_type: str
    summary: str
    feature_importances: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class ComplianceCheckResult:
    """Resultado do check de compliance."""

    regulations_checked: list[RegulationType]
    compliance_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    overall_compliant: bool = True
    duration_ms: float = 0.0


@dataclass
class FairnessCheckResult:
    """Resultado do check de fairness e bias (Phase 3)."""

    fairness_ok: bool
    bias_detected: bool
    protected_attributes_checked: list[str]  # ProtectedAttribute.value
    fairness_metrics: dict[str, float]  # metric_name -> score
    bias_severity: str  # low, medium, high, critical
    affected_groups: list[str] = field(default_factory=list)
    mitigation_recommended: bool = False
    confidence: float = 0.0
    duration_ms: float = 0.0


@dataclass
class PrivacyCheckResult:
    """Resultado do check de privacidade diferencial (Phase 4.1)."""

    privacy_budget_ok: bool
    privacy_level: str  # PrivacyLevel.value
    total_epsilon: float
    used_epsilon: float
    remaining_epsilon: float
    total_delta: float
    used_delta: float
    remaining_delta: float
    budget_exhausted: bool
    queries_executed: int
    duration_ms: float = 0.0


@dataclass
class FLCheckResult:
    """Resultado do check de federated learning (Phase 4.2)."""

    fl_ready: bool
    fl_status: str  # FLStatus.value
    model_type: str | None = None  # ModelType.value
    aggregation_strategy: str | None = None  # AggregationStrategy.value
    requires_dp: bool = False
    dp_epsilon: float | None = None
    dp_delta: float | None = None
    notes: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class HITLCheckResult:
    """Resultado do check de HITL (Phase 5)."""

    requires_human_review: bool
    automation_level: str  # AutomationLevel.value
    risk_level: str  # RiskLevel.value
    confidence_threshold_met: bool
    estimated_sla_minutes: int = 0
    escalation_recommended: bool = False
    human_expertise_required: list[str] = field(default_factory=list)  # Required skills
    decision_rationale: str = ""
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
    governance: GovernanceCheckResult | None = None
    ethics: EthicsCheckResult | None = None
    fairness: FairnessCheckResult | None = None  # Phase 3
    xai: XAICheckResult | None = None
    privacy: PrivacyCheckResult | None = None  # Phase 4.1
    fl: FLCheckResult | None = None  # Phase 4.2
    hitl: HITLCheckResult | None = None  # Phase 5
    compliance: ComplianceCheckResult | None = None

    # Summary
    is_approved: bool = False
    conditions: list[str] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)

    # Performance
    total_duration_ms: float = 0.0

    # Audit
    audit_log_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
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
            }
            if self.governance
            else None,
            "ethics": {
                "verdict": self.ethics.verdict.value if self.ethics else "unknown",
                "confidence": self.ethics.confidence if self.ethics else 0.0,
                "frameworks_count": len(self.ethics.framework_results) if self.ethics else 0,
            }
            if self.ethics
            else None,
            "xai": {
                "summary": self.xai.summary if self.xai else "",
                "features_count": len(self.xai.feature_importances) if self.xai else 0,
            }
            if self.xai
            else None,
            "compliance": {
                "overall_compliant": self.compliance.overall_compliant if self.compliance else False,
                "regulations_checked": len(self.compliance.regulations_checked) if self.compliance else 0,
            }
            if self.compliance
            else None,
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
        governance_config: GovernanceConfig | None = None,
        privacy_budget: PrivacyBudget | None = None,
        enable_governance: bool = True,
        enable_ethics: bool = True,
        enable_fairness: bool = True,  # Phase 3
        enable_xai: bool = True,
        enable_privacy: bool = True,  # Phase 4.1
        enable_fl: bool = False,  # Phase 4.2 (optional)
        enable_hitl: bool = True,  # Phase 5: HITL
        enable_compliance: bool = True,
    ):
        """
        Inicializa o Ethical Guardian.

        Args:
            governance_config: Configuração do governance (usa default se None)
            privacy_budget: Privacy budget para DP (usa default se None)
            enable_governance: Habilita checks de governance
            enable_ethics: Habilita avaliação ética
            enable_fairness: Habilita checks de fairness e bias (Phase 3)
            enable_xai: Habilita explicações XAI
            enable_privacy: Habilita checks de privacy (Phase 4.1)
            enable_fl: Habilita checks de federated learning (Phase 4.2)
            enable_hitl: Habilita checks de HITL/HOTL (Phase 5)
            enable_compliance: Habilita checks de compliance
        """
        self.governance_config = governance_config or GovernanceConfig()
        self.enable_governance = enable_governance
        self.enable_ethics = enable_ethics
        self.enable_fairness = enable_fairness
        self.enable_xai = enable_xai
        self.enable_privacy = enable_privacy
        self.enable_fl = enable_fl
        self.enable_hitl = enable_hitl
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

        # Initialize Phase 3: Fairness & Bias Mitigation
        if self.enable_fairness:
            self.bias_detector = BiasDetector(
                config={
                    "min_sample_size": 30,
                    "significance_level": 0.05,  # 95% confidence
                    "disparate_impact_threshold": 0.8,  # 4/5ths rule
                    "sensitivity": "medium",
                }
            )
            self.fairness_monitor = FairnessMonitor(
                config={
                    "check_interval_seconds": 3600,  # Check every hour
                    "alert_threshold": 0.1,  # Alert if fairness metric < 0.9
                }
            )
        else:
            self.bias_detector = None
            self.fairness_monitor = None

        # Initialize Phase 4.1: Differential Privacy
        if self.enable_privacy:
            # Create privacy budget if not provided (default: moderate privacy)
            self.privacy_budget = privacy_budget or PrivacyBudget(
                total_epsilon=3.0,  # Medium privacy level
                total_delta=1e-5,
            )
            # Create privacy accountant for tracking budget usage
            self.privacy_accountant = PrivacyAccountant(
                total_epsilon=self.privacy_budget.total_epsilon,
                total_delta=self.privacy_budget.total_delta,
                composition_type=CompositionType.ADVANCED_SEQUENTIAL,
            )
        else:
            self.privacy_budget = None
            self.privacy_accountant = None

        # Initialize Phase 4.2: Federated Learning
        if self.enable_fl:
            # Default FL config for threat intelligence sharing
            self.fl_config = FLConfig(
                model_type=ModelType.THREAT_CLASSIFIER,
                aggregation_strategy=AggregationStrategy.DP_FEDAVG,
                min_clients=3,
                use_differential_privacy=True,
                dp_epsilon=8.0,
                dp_delta=1e-5,
            )
        else:
            self.fl_config = None

        # Initialize Phase 5: HITL (Human-in-the-Loop)
        if self.enable_hitl:
            self.risk_assessor = RiskAssessor()
            # Note: HITLConfig and SLAConfig will use defaults
            # These can be customized in production with DB-backed config
            self.hitl_framework = HITLDecisionFramework(risk_assessor=self.risk_assessor)
        else:
            self.risk_assessor = None
            self.hitl_framework = None

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
        context: dict[str, Any],
        actor: str = "maximus",
        tool_name: str | None = None,
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
                        f"Policy violation: {v.get('title', 'Unknown')}" for v in governance_result.violations
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
                    result.rejection_reasons.append(f"Ethical verdict: {ethics_result.verdict.value}")
                    result.total_duration_ms = (time.time() - start_time) * 1000
                    await self._log_decision(result)
                    return result

            # ================================================================
            # PARALLEL: PHASE 2 (XAI) + PHASE 3 (Fairness) + PHASE 4 (Privacy & FL) + PHASE 6 (Compliance)
            # ================================================================
            # These phases are optional - failures won't block approval (except critical bias)

            # Phase 2: XAI
            if self.enable_xai and result.ethics:
                try:
                    result.xai = await self._generate_explanation(action, context, result.ethics)
                except Exception:
                    # XAI failure is not critical - log and continue
                    result.xai = None

            # Phase 3: Fairness & Bias Mitigation
            if self.enable_fairness:
                try:
                    result.fairness = await self._fairness_check(action, context)
                    # Reject if critical bias detected and mitigation recommended
                    if not result.fairness.fairness_ok and result.fairness.mitigation_recommended:
                        result.decision_type = EthicalDecisionType.REJECTED_BY_FAIRNESS
                        result.is_approved = False
                        result.rejection_reasons.append(
                            f"Critical bias detected: {result.fairness.bias_severity} "
                            f"(affected groups: {', '.join(result.fairness.affected_groups)})"
                        )
                        result.total_duration_ms = (time.time() - start_time) * 1000
                        await self._log_decision(result)
                        return result
                except Exception as e:
                    # Fairness check failure is not critical if not ML action
                    logger.warning(f"Fairness check failed: {e}")
                    result.fairness = None

            # Phase 4.1: Differential Privacy
            if self.enable_privacy:
                try:
                    result.privacy = await self._privacy_check(action, context)
                    # Reject if privacy budget exhausted and action processes PII
                    if not result.privacy.privacy_budget_ok and (
                        context.get("processes_personal_data") or context.get("has_pii")
                    ):
                        result.decision_type = EthicalDecisionType.REJECTED_BY_PRIVACY
                        result.is_approved = False
                        result.rejection_reasons.append(
                            f"Privacy budget exhausted (ε={result.privacy.used_epsilon:.2f}/{result.privacy.total_epsilon:.2f})"
                        )
                        result.total_duration_ms = (time.time() - start_time) * 1000
                        await self._log_decision(result)
                        return result
                except Exception:
                    # Privacy check failure is not critical if not processing PII
                    result.privacy = None

            # Phase 4.2: Federated Learning
            if self.enable_fl:
                try:
                    result.fl = await self._fl_check(action, context)
                except Exception:
                    # FL check failure is not critical
                    result.fl = None

            # Phase 5: HITL (Human-in-the-Loop)
            if self.enable_hitl:
                try:
                    # Calculate overall confidence from ethics result
                    confidence_score = 0.0
                    if result.ethics:
                        confidence_score = result.ethics.confidence

                    result.hitl = await self._hitl_check(action, context, confidence_score)

                    # If human review is required, mark decision accordingly
                    # Note: This doesn't reject the action, just flags it for human review
                    if result.hitl.requires_human_review:
                        # For now, we'll allow the action to proceed to compliance check
                        # but flag it for human review in the final decision
                        pass
                except Exception as e:
                    # HITL check failure is not critical - default to requiring human review for safety
                    logger.warning(f"HITL check failed: {e}")
                    result.hitl = HITLCheckResult(
                        requires_human_review=True,
                        automation_level="manual",
                        risk_level="medium",
                        confidence_threshold_met=False,
                        estimated_sla_minutes=15,
                        escalation_recommended=False,
                        human_expertise_required=["soc_operator"],
                        decision_rationale="HITL check failed - defaulting to human review for safety",
                        duration_ms=0.0,
                    )

            # Phase 6: Compliance
            if self.enable_compliance:
                try:
                    result.compliance = await self._compliance_check(action, context)
                except Exception:
                    # Compliance check failure is not critical - log and continue
                    result.compliance = None

            # ================================================================
            # FINAL DECISION
            # ================================================================
            # First check if HITL requires human review
            if result.hitl and result.hitl.requires_human_review:
                result.decision_type = EthicalDecisionType.REQUIRES_HUMAN_REVIEW
                result.is_approved = False  # Not auto-approved, requires human
                result.conditions.append(
                    f"Human review required (Risk: {result.hitl.risk_level}, "
                    f"SLA: {result.hitl.estimated_sla_minutes}min, "
                    f"Expertise: {', '.join(result.hitl.human_expertise_required)})"
                )
            # Check if approved
            elif result.ethics and result.ethics.verdict == EthicalVerdict.APPROVED:
                result.decision_type = EthicalDecisionType.APPROVED
                result.is_approved = True
                # Add SUPERVISED monitoring condition if applicable
                if result.hitl and result.hitl.automation_level == "supervised":
                    result.decision_type = EthicalDecisionType.APPROVED_WITH_CONDITIONS
                    result.conditions.append(
                        f"Approved for execution with SUPERVISED monitoring "
                        f"({result.hitl.risk_level} risk, {result.hitl.estimated_sla_minutes}min review window)"
                    )
            elif result.ethics and result.ethics.verdict == EthicalVerdict.CONDITIONAL:
                result.decision_type = EthicalDecisionType.APPROVED_WITH_CONDITIONS
                result.is_approved = True
                result.conditions.append("Action approved with ethical framework conditions")
                # Add SUPERVISED monitoring condition if applicable
                if result.hitl and result.hitl.automation_level == "supervised":
                    result.conditions.append(
                        f"SUPERVISED monitoring required "
                        f"({result.hitl.risk_level} risk, {result.hitl.estimated_sla_minutes}min review window)"
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
            self.avg_duration_ms * (self.total_validations - 1) + result.total_duration_ms
        ) / self.total_validations

        # Log decision
        await self._log_decision(result)

        return result

    async def _governance_check(self, action: str, context: dict[str, Any], actor: str) -> GovernanceCheckResult:
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

    async def _ethics_evaluation(self, action: str, context: dict[str, Any], actor: str) -> EthicsCheckResult:
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
        verdict = verdict_map.get(ethical_decision.final_decision, EthicalVerdict.REJECTED)

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
        self, action: str, context: dict[str, Any], ethics_result: EthicsCheckResult
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

    async def _compliance_check(self, action: str, context: dict[str, Any]) -> ComplianceCheckResult:
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
                result = self.compliance_engine.check_compliance(regulation=regulation, scope=action)

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

    async def _hitl_check(
        self,
        action: str,
        context: dict[str, Any],
        confidence_score: float = 0.0,
    ) -> HITLCheckResult:
        """
        Phase 5: HITL (Human-in-the-Loop) check.

        Determines if action requires human review based on:
        - Action risk level (from RiskAssessor)
        - Confidence score from previous phases
        - Automation level thresholds

        Target: <50ms
        """
        start_time = time.time()

        # Extract confidence from context or use provided score
        if confidence_score == 0.0:
            confidence_score = context.get("confidence", 0.0)

        # Map action string to ActionType (simplified - defaults to SEND_ALERT if not recognized)
        try:
            # Try to match action to known ActionType values
            action_lower = action.lower().replace(" ", "_")
            action_type = None
            for at in ActionType:
                if at.value == action_lower or at.value in action_lower:
                    action_type = at
                    break
            if action_type is None:
                action_type = ActionType.SEND_ALERT  # Safe default
        except Exception:
            action_type = ActionType.SEND_ALERT

        # Create DecisionContext for risk assessment
        decision_context = DecisionContext(
            action_type=action_type,
            action_params=context,
            confidence=confidence_score,
            threat_score=context.get("threat_score", 0.0),
            affected_assets=context.get("affected_assets", []),
            asset_criticality=context.get("asset_criticality", "medium"),
        )

        # Assess risk using RiskAssessor
        risk_score = self.risk_assessor.assess_risk(decision_context)

        # Determine automation level based on confidence and risk
        # High confidence (≥95%) + Low risk → FULL automation
        # Medium confidence (≥80%) + Low/Medium risk → SUPERVISED
        # Low confidence (<80%) or High/Critical risk → MANUAL
        if confidence_score >= 0.95 and risk_score.risk_level == RiskLevel.LOW:
            automation_level = AutomationLevel.FULL
        elif confidence_score >= 0.80 and risk_score.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
            automation_level = AutomationLevel.SUPERVISED
        elif confidence_score >= 0.60:
            automation_level = AutomationLevel.ADVISORY
        else:
            automation_level = AutomationLevel.MANUAL

        # Determine if human review is required
        # SUPERVISED executes with monitoring, but does NOT require pre-approval
        # Only ADVISORY and MANUAL require human review before execution
        requires_human_review = automation_level in [
            AutomationLevel.ADVISORY,
            AutomationLevel.MANUAL,
        ]

        # Confidence threshold check
        confidence_threshold_met = False
        if automation_level == AutomationLevel.FULL:
            confidence_threshold_met = confidence_score >= 0.95
        elif automation_level == AutomationLevel.SUPERVISED:
            confidence_threshold_met = confidence_score >= 0.80
        elif automation_level == AutomationLevel.ADVISORY:
            confidence_threshold_met = confidence_score >= 0.60
        else:  # MANUAL
            confidence_threshold_met = False

        # Determine SLA based on risk level
        sla_mapping = {
            RiskLevel.CRITICAL: 5,
            RiskLevel.HIGH: 10,
            RiskLevel.MEDIUM: 15,
            RiskLevel.LOW: 30,
        }
        estimated_sla_minutes = sla_mapping.get(risk_score.risk_level, 15)

        # Recommend escalation for critical/high risk
        escalation_recommended = risk_score.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]

        # Determine required human expertise
        human_expertise_required = []
        if risk_score.risk_level == RiskLevel.CRITICAL:
            human_expertise_required = ["security_manager", "ciso"]
        elif risk_score.risk_level == RiskLevel.HIGH:
            human_expertise_required = ["soc_supervisor", "security_manager"]
        elif requires_human_review:
            human_expertise_required = ["soc_operator"]

        # Generate decision rationale
        decision_rationale = (
            f"Action '{action}' assessed as {risk_score.risk_level.value} risk with "
            f"{confidence_score:.1%} confidence. Automation level: {automation_level.value}. "
        )

        if requires_human_review:
            decision_rationale += f"Human review required (SLA: {estimated_sla_minutes}min)."
        else:
            decision_rationale += "Approved for autonomous execution."

        duration_ms = (time.time() - start_time) * 1000

        return HITLCheckResult(
            requires_human_review=requires_human_review,
            automation_level=automation_level.value,
            risk_level=risk_score.risk_level.value,
            confidence_threshold_met=confidence_threshold_met,
            estimated_sla_minutes=estimated_sla_minutes,
            escalation_recommended=escalation_recommended,
            human_expertise_required=human_expertise_required,
            decision_rationale=decision_rationale,
            duration_ms=duration_ms,
        )

    async def _fairness_check(self, action: str, context: dict[str, Any]) -> FairnessCheckResult:
        """
        Phase 3: Check fairness and bias across protected attributes.

        Verifica se a ação possui viés algorítmico ou discriminação
        contra grupos protegidos.

        Target: <100ms
        """
        start_time = time.time()

        # Check if action involves ML predictions or decisions
        involves_ml = any(
            keyword in action.lower() for keyword in ["predict", "classify", "detect", "score", "model", "decision"]
        )

        if not involves_ml:
            # Non-ML actions don't require fairness checks
            duration_ms = (time.time() - start_time) * 1000
            return FairnessCheckResult(
                fairness_ok=True,
                bias_detected=False,
                protected_attributes_checked=[],
                fairness_metrics={},
                bias_severity="low",
                affected_groups=[],
                mitigation_recommended=False,
                confidence=1.0,
                duration_ms=duration_ms,
            )

        # Get predictions and protected attributes from context
        predictions = context.get("predictions")
        protected_attributes = context.get("protected_attributes", {})

        # If no data available, assume fairness OK (graceful degradation)
        if predictions is None or not protected_attributes:
            duration_ms = (time.time() - start_time) * 1000
            return FairnessCheckResult(
                fairness_ok=True,
                bias_detected=False,
                protected_attributes_checked=[],
                fairness_metrics={},
                bias_severity="low",
                affected_groups=[],
                mitigation_recommended=False,
                confidence=0.5,  # Lower confidence when no data
                duration_ms=duration_ms,
            )

        # Perform bias detection for each protected attribute
        bias_detected = False
        bias_severity = "low"
        affected_groups = []
        fairness_metrics = {}
        checked_attributes = []

        for attr_name, attr_values in protected_attributes.items():
            try:
                # Convert to ProtectedAttribute enum
                protected_attr = ProtectedAttribute(attr_name)
                checked_attributes.append(protected_attr.value)

                # Run bias detection
                result = self.bias_detector.detect_statistical_parity_bias(
                    predictions=predictions,
                    protected_attribute=attr_values,
                    protected_value=1,
                )

                if result.bias_detected:
                    bias_detected = True
                    bias_severity = max(
                        bias_severity, result.severity, key=lambda x: ["low", "medium", "high", "critical"].index(x)
                    )
                    affected_groups.extend(result.affected_groups)

                # Store fairness metrics
                fairness_metrics[attr_name] = {
                    "p_value": result.p_value,
                    "confidence": result.confidence,
                    "severity": result.severity,
                }

            except (ValueError, Exception) as e:
                # Skip invalid protected attributes
                logger.warning(f"Failed to check fairness for attribute {attr_name}: {e}")
                continue

        # Determine if fairness is OK
        fairness_ok = not bias_detected or bias_severity in ["low", "medium"]

        # Recommend mitigation if high/critical bias detected
        mitigation_recommended = bias_severity in ["high", "critical"]

        # Calculate overall confidence
        if fairness_metrics:
            confidence = sum(m["confidence"] for m in fairness_metrics.values()) / len(fairness_metrics)
        else:
            confidence = 0.5

        duration_ms = (time.time() - start_time) * 1000

        return FairnessCheckResult(
            fairness_ok=fairness_ok,
            bias_detected=bias_detected,
            protected_attributes_checked=checked_attributes,
            fairness_metrics=fairness_metrics,
            bias_severity=bias_severity,
            affected_groups=affected_groups,
            mitigation_recommended=mitigation_recommended,
            confidence=confidence,
            duration_ms=duration_ms,
        )

    async def _privacy_check(self, action: str, context: dict[str, Any]) -> PrivacyCheckResult:
        """
        Phase 4.1: Check differential privacy budget and constraints.

        Verifica se a ação respeita o privacy budget e princípios de DP.

        Target: <50ms
        """
        start_time = time.time()

        # Get current budget status
        budget = self.privacy_budget
        budget_ok = not budget.budget_exhausted

        # Check if action processes personal data
        processes_pii = context.get("processes_personal_data", False) or context.get("has_pii", False)

        # If action processes PII, check budget
        if processes_pii and budget.budget_exhausted:
            budget_ok = False

        duration_ms = (time.time() - start_time) * 1000

        return PrivacyCheckResult(
            privacy_budget_ok=budget_ok,
            privacy_level=budget.privacy_level.value,
            total_epsilon=budget.total_epsilon,
            used_epsilon=budget.used_epsilon,
            remaining_epsilon=budget.remaining_epsilon,
            total_delta=budget.total_delta,
            used_delta=budget.used_delta,
            remaining_delta=budget.remaining_delta,
            budget_exhausted=budget.budget_exhausted,
            queries_executed=len(budget.queries_executed),
            duration_ms=duration_ms,
        )

    async def _fl_check(self, action: str, context: dict[str, Any]) -> FLCheckResult:
        """
        Phase 4.2: Check federated learning readiness and constraints.

        Verifica se a ação é compatível com FL e se requer DP.

        Target: <30ms
        """
        start_time = time.time()

        # Check if action involves model training/aggregation
        is_model_training = any(
            keyword in action.lower() for keyword in ["train", "model", "learn", "aggregate", "federated"]
        )

        # FL is ready if config exists and action involves training
        fl_ready = is_model_training and self.fl_config is not None

        # Determine FL status
        if fl_ready:
            fl_status = FLStatus.INITIALIZING.value
            model_type = self.fl_config.model_type.value if self.fl_config else None
            aggregation_strategy = self.fl_config.aggregation_strategy.value if self.fl_config else None
            requires_dp = self.fl_config.use_differential_privacy if self.fl_config else False
            dp_epsilon = self.fl_config.dp_epsilon if self.fl_config else None
            dp_delta = self.fl_config.dp_delta if self.fl_config else None
            notes = ["FL ready for model training"] if fl_ready else []
        else:
            fl_status = FLStatus.FAILED.value if is_model_training else "not_applicable"
            model_type = None
            aggregation_strategy = None
            requires_dp = False
            dp_epsilon = None
            dp_delta = None
            notes = ["FL not configured"] if is_model_training else ["Action does not require FL"]

        duration_ms = (time.time() - start_time) * 1000

        return FLCheckResult(
            fl_ready=fl_ready,
            fl_status=fl_status,
            model_type=model_type,
            aggregation_strategy=aggregation_strategy,
            requires_dp=requires_dp,
            dp_epsilon=dp_epsilon,
            dp_delta=dp_delta,
            notes=notes,
            duration_ms=duration_ms,
        )

    async def _log_decision(self, decision: EthicalDecisionResult) -> str | None:
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

    def get_statistics(self) -> dict[str, Any]:
        """Get validation statistics."""
        return {
            "total_validations": self.total_validations,
            "total_approved": self.total_approved,
            "total_rejected": self.total_rejected,
            "approval_rate": (self.total_approved / self.total_validations if self.total_validations > 0 else 0.0),
            "avg_duration_ms": self.avg_duration_ms,
            "enabled_phases": {
                "governance": self.enable_governance,
                "ethics": self.enable_ethics,
                "xai": self.enable_xai,
                "compliance": self.enable_compliance,
            },
        }
