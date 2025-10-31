"""
Constitutional Metrics for Vértice Constitution v3.0 Compliance.

This module implements Prometheus metrics for tracking compliance with
the Vértice Constitution, including the DETER-AGENT framework metrics.

Biblical Foundation:
- Aletheia (Truth): Honest metric reporting
- Sophia (Wisdom): Measuring wisdom-based decisions
- Tapeinophrosynē (Humility): Tracking confidence thresholds
"""


from prometheus_client import Counter, Gauge, Histogram

# =============================================================================
# DETER-AGENT Framework Metrics (Constitution v3.0)
# =============================================================================

# Layer 1: Constitutional Control (Strategic)
constitutional_rule_satisfaction = Gauge(
    "vertice_constitutional_rule_satisfaction",
    "CRS (Constitutional Rule Satisfaction) score - must be >= 95%",
    ["service", "article"],
)

principle_violations = Counter(
    "vertice_principle_violations_total",
    "Total violations of constitutional principles (P1-P6)",
    ["service", "principle", "severity"],
)

prompt_injection_attempts = Counter(
    "vertice_prompt_injection_attempts_total",
    "Detected prompt injection attempts",
    ["service", "attack_type"],
)

# Layer 2: Deliberation Control (Cognitive)
tree_of_thoughts_depth = Histogram(
    "vertice_tot_depth",
    "Tree of Thoughts reasoning depth",
    ["service", "decision_type"],
    buckets=[1, 2, 3, 4, 5, 7, 10],
)

self_criticism_score = Gauge(
    "vertice_self_criticism_score",
    "Self-criticism quality score (0-1)",
    ["service", "context"],
)

first_pass_correctness = Gauge(
    "vertice_first_pass_correctness",
    "FPC (First-Pass Correctness) - must be >= 80%",
    ["service"],
)

# Layer 3: State Management Control (Memory)
context_compression_ratio = Gauge(
    "vertice_context_compression_ratio",
    "Context compression effectiveness",
    ["service"],
)

context_rot_score = Gauge(
    "vertice_context_rot_score",
    "Context degradation score (0=good, 1=rotted)",
    ["service"],
)

checkpoint_frequency = Counter(
    "vertice_checkpoints_total",
    "Total checkpoints saved",
    ["service", "checkpoint_type"],
)

# Layer 4: Execution Control (Operational)
lazy_execution_index = Gauge(
    "vertice_lazy_execution_index",
    "LEI (Lazy Execution Index) - must be < 1.0",
    ["service"],
)

plan_act_verify_cycles = Counter(
    "vertice_pav_cycles_total",
    "Plan-Act-Verify loop executions",
    ["service", "outcome"],
)

guardian_agent_interventions = Counter(
    "vertice_guardian_interventions_total",
    "Guardian agent interventions",
    ["service", "reason"],
)

# Layer 5: Incentive Control (Behavioral)
quality_metrics_score = Gauge(
    "vertice_quality_metrics_score",
    "Combined quality metrics score",
    ["service", "metric_type"],
)

penalty_points = Counter(
    "vertice_penalty_points_total",
    "Penalty points accumulated",
    ["service", "violation_type"],
)


# =============================================================================
# 7 Biblical Articles Metrics
# =============================================================================

# Article I: Sophia (Wisdom)
wisdom_decisions = Counter(
    "vertice_wisdom_decisions_total",
    "Decisions made using Wisdom Base",
    ["service", "decision_quality"],
)

wisdom_base_queries = Histogram(
    "vertice_wisdom_base_query_duration_seconds",
    "Wisdom Base query duration",
    ["service", "query_type"],
)

# Article II: Praótes (Gentleness)
code_line_count = Histogram(
    "vertice_praotes_code_lines",
    "Generated code line count (max 25 per Praótes)",
    ["service", "operation"],
    buckets=[5, 10, 15, 20, 25, 30, 40, 50],
)

reversibility_score = Gauge(
    "vertice_praotes_reversibility_score",
    "Code reversibility score (must be >= 0.90)",
    ["service"],
)

# Article III: Tapeinophrosynē (Humility)
confidence_threshold_violations = Counter(
    "vertice_tapeinophrosyne_violations_total",
    "Decisions made below 85% confidence threshold",
    ["service", "escalated"],
)

escalations_to_maximus = Counter(
    "vertice_escalations_to_maximus_total",
    "Escalations to Maximus due to low confidence",
    ["service", "reason"],
)

# Article IV: Stewardship
developer_intent_preservation = Gauge(
    "vertice_stewardship_intent_preservation",
    "Developer intent preservation score (0-1)",
    ["service"],
)

# Article V: Agape (Love)
user_impact_score = Gauge(
    "vertice_agape_user_impact_score",
    "User impact prioritization score",
    ["service", "impact_type"],
)

# Article VI: Sabbath (Rest)
sabbath_mode_active = Gauge(
    "vertice_sabbath_mode_active",
    "Sabbath mode status (1=active, 0=inactive)",
    ["service"],
)

p0_exceptions_on_sabbath = Counter(
    "vertice_sabbath_p0_exceptions_total",
    "P0 critical exceptions during Sabbath",
    ["service", "exception_type"],
)

# Article VII: Aletheia (Truth)
uncertainty_declarations = Counter(
    "vertice_aletheia_uncertainty_declarations_total",
    "Explicit uncertainty declarations",
    ["service", "uncertainty_type"],
)

syntactic_hallucinations = Counter(
    "vertice_aletheia_hallucinations_total",
    "Syntactic hallucinations detected (must be 0)",
    ["service", "hallucination_type"],
)


# =============================================================================
# 9 Fruits of the Spirit Metrics
# =============================================================================

fruits_of_spirit_compliance = Gauge(
    "vertice_fruits_of_spirit_compliance",
    "Compliance score for each Fruit of the Spirit",
    ["service", "fruit"],
)

# Fruit-specific metrics
agape_love_actions = Counter(
    "vertice_fruit_agape_actions_total",
    "Actions demonstrating Agape (Love)",
    ["service", "action_type"],
)

chara_joy_indicators = Gauge(
    "vertice_fruit_chara_joy_score", "Joy indicators in system health", ["service"]
)

eirene_peace_score = Gauge(
    "vertice_fruit_eirene_peace_score", "Peace score (system stability)", ["service"]
)

pistis_faithfulness_score = Gauge(
    "vertice_fruit_pistis_faithfulness", "Faithfulness to commitments", ["service"]
)

enkrateia_self_control_score = Gauge(
    "vertice_fruit_enkrateia_self_control",
    "Self-control in resource usage",
    ["service"],
)


# =============================================================================
# Service-Specific Business Metrics
# =============================================================================

# MABA-specific (Browser Agent)
browser_operations = Counter(
    "maba_browser_operations_total",
    "Total browser operations performed",
    ["operation_type", "outcome"],
)

browser_operation_duration = Histogram(
    "maba_browser_operation_duration_seconds",
    "Browser operation duration",
    ["operation_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

cognitive_map_nodes = Gauge(
    "maba_cognitive_map_nodes", "Number of nodes in cognitive map", ["map_type"]
)

cognitive_map_operations = Counter(
    "maba_cognitive_map_operations_total",
    "Cognitive map operations",
    ["operation", "status"],
)

screenshot_captures = Counter(
    "maba_screenshot_captures_total", "Screenshots captured", ["purpose", "format"]
)

navigation_operations = Counter(
    "maba_navigation_operations_total", "Navigation operations", ["action", "outcome"]
)


# =============================================================================
# Helper Functions
# =============================================================================


def record_constitutional_compliance(service: str, article: str, score: float) -> None:
    """Record Constitutional Rule Satisfaction score."""
    constitutional_rule_satisfaction.labels(service=service, article=article).set(score)


def record_principle_violation(
    service: str, principle: str, severity: str = "medium"
) -> None:
    """Record a violation of constitutional principles (P1-P6)."""
    principle_violations.labels(
        service=service, principle=principle, severity=severity
    ).inc()


def record_lei_score(service: str, lei_value: float) -> None:
    """Record Lazy Execution Index (must be < 1.0)."""
    lazy_execution_index.labels(service=service).set(lei_value)


def record_fpc_score(service: str, fpc_value: float) -> None:
    """Record First-Pass Correctness (must be >= 80%)."""
    first_pass_correctness.labels(service=service).set(fpc_value)


def record_wisdom_decision(service: str, quality: str = "high") -> None:
    """Record a decision made using Wisdom Base."""
    wisdom_decisions.labels(service=service, decision_quality=quality).inc()


def record_humility_check(
    service: str, confidence: float, threshold: float = 0.85
) -> None:
    """Record Tapeinophrosynē (Humility) confidence check."""
    if confidence < threshold:
        confidence_threshold_violations.labels(service=service, escalated="true").inc()
        escalations_to_maximus.labels(service=service, reason="low_confidence").inc()


def record_sabbath_status(service: str, is_sabbath: bool) -> None:
    """Record Sabbath mode status."""
    sabbath_mode_active.labels(service=service).set(1.0 if is_sabbath else 0.0)


def record_fruit_compliance(service: str, fruit: str, score: float) -> None:
    """Record compliance score for a Fruit of the Spirit."""
    fruits_of_spirit_compliance.labels(service=service, fruit=fruit).set(score)


def record_hallucination(service: str, hallucination_type: str = "syntactic") -> None:
    """Record a syntactic hallucination (MUST BE ZERO)."""
    syntactic_hallucinations.labels(
        service=service, hallucination_type=hallucination_type
    ).inc()


# 🤖 Generated with [Claude Code](https://claude.com/claude-code)
#
# Co-Authored-By: Claude <noreply@anthropic.com>
