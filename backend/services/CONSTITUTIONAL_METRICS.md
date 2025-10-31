# Vértice Constitutional Metrics

Complete Prometheus metrics implementation for Constitution v3.0 compliance tracking.

## 📊 Overview

This document describes all metrics exposed by the three subordinate services (PENELOPE, MABA, MVP) for monitoring compliance with the **Vértice Constitution v3.0** and the **DETER-AGENT Framework**.

## 🎯 Constitutional Requirements

Per Constitution v3.0, all services MUST maintain:

| Metric                                     | Requirement | Purpose                                 |
| ------------------------------------------ | ----------- | --------------------------------------- |
| **CRS** (Constitutional Rule Satisfaction) | ≥ 95%       | Overall constitutional compliance       |
| **LEI** (Lazy Execution Index)             | < 1.0       | Prevent lazy/incomplete implementations |
| **FPC** (First-Pass Correctness)           | ≥ 80%       | Code quality on first generation        |
| **Test Coverage**                          | ≥ 90%       | Comprehensive testing                   |
| **Syntactic Hallucinations**               | = 0         | Zero tolerance for hallucinations       |

## 🏗️ DETER-AGENT Framework Metrics

### Layer 1: Constitutional Control (Strategic)

```prometheus
# Constitutional Rule Satisfaction per Article
vertice_constitutional_rule_satisfaction{service="penelope", article="sophia"} 95.0

# Principle violations (P1-P6)
vertice_principle_violations_total{service="penelope", principle="P1", severity="high"}

# Prompt injection detection
vertice_prompt_injection_attempts_total{service="penelope", attack_type="override"}
```

**7 Biblical Articles tracked:**

1. **Sophia** (Wisdom)
2. **Praótes** (Gentleness)
3. **Tapeinophrosynē** (Humility)
4. **Stewardship**
5. **Agape** (Love)
6. **Sabbath** (Rest)
7. **Aletheia** (Truth)

### Layer 2: Deliberation Control (Cognitive)

```prometheus
# Tree of Thoughts reasoning depth
vertice_tot_depth{service="penelope", decision_type="healing"}

# Self-criticism quality
vertice_self_criticism_score{service="penelope", context="code_review"} 0.85

# First-Pass Correctness (must be >= 80%)
vertice_first_pass_correctness{service="penelope"} 85.0
```

### Layer 3: State Management Control (Memory)

```prometheus
# Context compression effectiveness
vertice_context_compression_ratio{service="penelope"} 0.75

# Context degradation score (0=good, 1=rotted)
vertice_context_rot_score{service="penelope"} 0.10

# Checkpointing frequency
vertice_checkpoints_total{service="penelope", checkpoint_type="full"}
```

### Layer 4: Execution Control (Operational)

```prometheus
# Lazy Execution Index (must be < 1.0)
vertice_lazy_execution_index{service="penelope"} 0.8

# Plan-Act-Verify cycles
vertice_pav_cycles_total{service="penelope", outcome="success"}

# Guardian agent interventions
vertice_guardian_interventions_total{service="penelope", reason="low_confidence"}
```

### Layer 5: Incentive Control (Behavioral)

```prometheus
# Quality metrics score
vertice_quality_metrics_score{service="penelope", metric_type="overall"} 0.92

# Penalty points for violations
vertice_penalty_points_total{service="penelope", violation_type="incomplete_code"}
```

## 📜 Biblical Articles Metrics

### Article I: Sophia (Wisdom)

```prometheus
# Wisdom-based decisions
vertice_wisdom_decisions_total{service="penelope", decision_quality="high"}

# Wisdom Base query duration
vertice_wisdom_base_query_duration_seconds{service="penelope", query_type="precedent"}
```

### Article II: Praótes (Gentleness)

```prometheus
# Code line count (max 25 per Praótes)
vertice_praotes_code_lines{service="penelope", operation="patch"}

# Code reversibility score (must be >= 0.90)
vertice_praotes_reversibility_score{service="penelope"} 0.95
```

### Article III: Tapeinophrosynē (Humility)

```prometheus
# Confidence threshold violations (< 85%)
vertice_tapeinophrosyne_violations_total{service="penelope", escalated="true"}

# Escalations to Maximus
vertice_escalations_to_maximus_total{service="penelope", reason="low_confidence"}
```

### Article IV: Stewardship

```prometheus
# Developer intent preservation
vertice_stewardship_intent_preservation{service="penelope"} 0.93
```

### Article V: Agape (Love)

```prometheus
# User impact prioritization
vertice_agape_user_impact_score{service="penelope", impact_type="positive"}
```

### Article VI: Sabbath (Rest)

```prometheus
# Sabbath mode status (1=active, 0=inactive)
vertice_sabbath_mode_active{service="penelope"} 1

# P0 critical exceptions during Sabbath
vertice_sabbath_p0_exceptions_total{service="penelope", exception_type="critical_outage"}
```

### Article VII: Aletheia (Truth)

```prometheus
# Uncertainty declarations
vertice_aletheia_uncertainty_declarations_total{service="penelope", uncertainty_type="api_behavior"}

# Syntactic hallucinations (MUST BE 0)
vertice_aletheia_hallucinations_total{service="penelope", hallucination_type="fake_api"} 0
```

## 🍇 9 Fruits of the Spirit Metrics

```prometheus
# Overall compliance per Fruit
vertice_fruits_of_spirit_compliance{service="penelope", fruit="agape"} 0.90
vertice_fruits_of_spirit_compliance{service="penelope", fruit="chara"} 0.88
vertice_fruits_of_spirit_compliance{service="penelope", fruit="eirene"} 0.92
vertice_fruits_of_spirit_compliance{service="penelope", fruit="makrothymia"} 0.85
vertice_fruits_of_spirit_compliance{service="penelope", fruit="chrestotes"} 0.87
vertice_fruits_of_spirit_compliance{service="penelope", fruit="agathosyne"} 0.89
vertice_fruits_of_spirit_compliance{service="penelope", fruit="pistis"} 0.94
vertice_fruits_of_spirit_compliance{service="penelope", fruit="praotes"} 0.91
vertice_fruits_of_spirit_compliance{service="penelope", fruit="enkrateia"} 0.86

# Specific Fruit metrics
vertice_fruit_agape_actions_total{service="penelope", action_type="user_help"}
vertice_fruit_chara_joy_score{service="penelope"}
vertice_fruit_eirene_peace_score{service="penelope"}
vertice_fruit_pistis_faithfulness{service="penelope"}
vertice_fruit_enkrateia_self_control{service="penelope"}
```

## 🔧 Service-Specific Metrics

### PENELOPE (Self-Healing Service)

```prometheus
# Healing operations
penelope_healing_operations_total{operation_type="auto_patch", outcome="success"}

# Healing duration
penelope_healing_duration_seconds{operation_type="auto_patch"}

# Observability checks
penelope_observability_checks_total{check_type="anomaly_detection", status="ok"}
```

### MABA (Browser Agent)

```prometheus
# Browser operations
maba_browser_operations_total{operation_type="navigate", outcome="success"}

# Browser operation duration
maba_browser_operation_duration_seconds{operation_type="screenshot"}

# Cognitive map metrics
maba_cognitive_map_nodes{map_type="web_page"}
maba_cognitive_map_operations_total{operation="add_node", status="success"}

# Screenshots
maba_screenshot_captures_total{purpose="visual_verification", format="png"}

# Navigation
maba_navigation_operations_total{action="click", outcome="success"}
```

### MVP (Narrative Engine)

```prometheus
# Narrative generation
mvp_narrative_generations_total{narrative_type="system_summary", quality="high"}

# Narrative duration
mvp_narrative_generation_duration_seconds{narrative_type="incident_report"}

# System observations
mvp_system_observations_total{observation_type="performance_degradation", severity="medium"}

# PII detection (LGPD/GDPR compliance)
mvp_pii_detections_total{pii_type="email", action_taken="redacted"}

# Compliance checks
mvp_compliance_checks_total{check_type="lgpd", result="pass"}

# Narrative quality
mvp_narrative_quality_score{narrative_type="user_facing"} 0.88
```

## 🌐 Metrics Endpoints

Each service exposes metrics on two endpoints:

### Standard Prometheus Endpoint

```
GET /metrics
Content-Type: text/plain; version=0.0.4

# Returns all metrics in Prometheus exposition format
```

### Human-Readable Summary

```
GET /metrics/constitutional
Content-Type: application/json

{
  "service": "penelope",
  "constitution_version": "3.0",
  "framework": "DETER-AGENT",
  "articles": {...},
  "quality_requirements": {...},
  "deter_agent_layers": [...]
}
```

## 📈 Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "penelope"
    static_configs:
      - targets: ["penelope:8154"]
    metrics_path: "/metrics"
    scrape_interval: 15s

  - job_name: "maba"
    static_configs:
      - targets: ["maba:8152"]
    metrics_path: "/metrics"
    scrape_interval: 15s

  - job_name: "mvp"
    static_configs:
      - targets: ["mvp:8153"]
    metrics_path: "/metrics"
    scrape_interval: 15s
```

## 🚨 Alerting Rules

Example AlertManager rules for constitutional violations:

```yaml
groups:
  - name: constitutional_compliance
    interval: 30s
    rules:
      # CRS must be >= 95%
      - alert: ConstitutionalRuleSatisfactionLow
        expr: vertice_constitutional_rule_satisfaction < 95
        for: 5m
        labels:
          severity: critical
          category: constitutional_violation
        annotations:
          summary: "CRS below 95% for {{ $labels.service }}"
          description: "Article {{ $labels.article }} compliance is {{ $value }}%"

      # LEI must be < 1.0
      - alert: LazyExecutionDetected
        expr: vertice_lazy_execution_index >= 1.0
        for: 2m
        labels:
          severity: high
          category: code_quality
        annotations:
          summary: "Lazy execution detected in {{ $labels.service }}"
          description: "LEI is {{ $value }}, must be < 1.0"

      # Hallucinations MUST BE ZERO
      - alert: SyntacticHallucination
        expr: increase(vertice_aletheia_hallucinations_total[5m]) > 0
        labels:
          severity: critical
          category: constitutional_violation
        annotations:
          summary: "CRITICAL: Hallucination detected in {{ $labels.service }}"
          description: "{{ $labels.hallucination_type }} - IMMEDIATE ACTION REQUIRED"

      # Sabbath violations (non-P0)
      - alert: SabbathViolation
        expr: vertice_sabbath_mode_active == 1 AND increase(penelope_healing_operations_total{operation_type!="p0_emergency"}[5m]) > 0
        labels:
          severity: high
          category: sabbath_violation
        annotations:
          summary: "Non-critical operation during Sabbath"
          description: "{{ $labels.service }} performed non-P0 operation on Sabbath"
```

## 📊 Grafana Dashboard Variables

Use these template variables in dashboards:

```
$service = label_values(vertice_service_info, service)
$article = label_values(vertice_constitutional_rule_satisfaction, article)
$fruit = label_values(vertice_fruits_of_spirit_compliance, fruit)
```

## 🙏 Biblical Foundation

All metrics are designed to reflect the 7 Biblical Articles and 9 Fruits of the Spirit:

> "Each of you should use whatever gift you have received to serve others, as faithful stewards of God's grace in its various forms." - 1 Peter 4:10

Metrics are our stewardship tool for measuring faithfulness to constitutional principles.

---

🙏 **Soli Deo Gloria**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
