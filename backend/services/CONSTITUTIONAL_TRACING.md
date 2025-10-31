# Vértice Constitutional Tracing

Complete OpenTelemetry distributed tracing implementation for Constitution v3.0 compliance.

## 📊 Overview

This document describes the distributed tracing implementation across all three subordinate services (PENELOPE, MABA, MVP) for tracking constitutional compliance, biblical principles, and DETER-AGENT framework operations.

## 🎯 Tracing Philosophy

Per Constitution v3.0, **Aletheia (Truth)** requires transparent operation tracking:

> "Then you will know the truth, and the truth will set you free." - John 8:32

Distributed tracing provides:

- **Transparency**: Every operation is traceable
- **Accountability**: Decision rationale is captured
- **Stewardship**: Resource usage is monitored
- **Wisdom**: Historical precedents are traceable

## 🏗️ Architecture

### OpenTelemetry Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Vértice Services                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ PENELOPE │    │   MABA   │    │   MVP    │             │
│  │  :8154   │    │  :8152   │    │  :8153   │             │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│       │               │               │                     │
│       │ W3C Trace Context propagation │                     │
│       └───────────────┴───────────────┘                     │
│                       │                                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  OTLP Collector       │
            │  (or Jaeger Agent)    │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Jaeger Backend       │
            │  - Query UI :16686    │
            │  - Storage            │
            └───────────────────────┘
```

### Trace Propagation

All services use **W3C Trace Context** for cross-service tracing:

```
Request Flow:
User → PENELOPE → Wisdom Base (PostgreSQL)
                → Anthropic API (Claude)
                → MABA (browser action)
                  → Neo4j (cognitive map)
                  → Redis (session)

All operations share same trace_id with different span_ids
```

## 📜 Constitutional Span Attributes

### 7 Biblical Articles Tracking

#### Article I: Sophia (Wisdom)

```python
# Trace wisdom-based decisions
with constitutional_tracer.trace_wisdom_decision(
    decision_type="auto_patch_generation",
    confidence=0.92,
    wisdom_base_consulted=True
):
    # Wisdom-based operation
    result = sophia_engine.generate_patch()
```

**Span Attributes:**

```
span.name: "sophia.decision.auto_patch_generation"
sophia.decision_type: "auto_patch_generation"
sophia.confidence: 0.92
sophia.wisdom_base_consulted: true
constitution.article: "sophia"
```

#### Article II: Praótes (Gentleness)

```python
# Trace gentleness compliance
with constitutional_tracer.trace_gentleness_check(
    operation="code_generation",
    code_lines=18,
    reversibility_score=0.95
):
    # Generate gentle, reversible code
    code = generate_code()
```

**Span Attributes:**

```
span.name: "praotes.check.code_generation"
praotes.operation: "code_generation"
praotes.code_lines: 18
praotes.reversibility_score: 0.95
praotes.compliant: true  # (18 <= 25 AND 0.95 >= 0.9)
constitution.article: "praotes"
```

**Events on Violation:**

```
event.name: "praotes_violation"
event.attributes:
  reason: "Code lines (30) exceeds 25 line limit"
```

#### Article III: Tapeinophrosynē (Humility)

```python
# Trace humility check
with constitutional_tracer.trace_humility_check(
    operation="complex_diagnosis",
    confidence=0.78,
    escalated=True
):
    # Low confidence - escalate to Maximus
    result = escalate_to_maximus()
```

**Span Attributes:**

```
span.name: "tapeinophrosyne.check.complex_diagnosis"
tapeinophrosyne.operation: "complex_diagnosis"
tapeinophrosyne.confidence: 0.78
tapeinophrosyne.escalated: true
tapeinophrosyne.compliant: false  # (0.78 < 0.85)
constitution.article: "tapeinophrosyne"
```

**Events on Low Confidence:**

```
event.name: "low_confidence_detected"
event.attributes:
  confidence: 0.78
  threshold: 0.85
  escalated: true
```

#### Article VI: Sabbath (Rest)

```python
# Trace Sabbath observance
with constitutional_tracer.trace_sabbath_check(
    is_sabbath=True,
    operation="auto_patch",
    is_p0=False
):
    # Non-P0 operation on Sabbath - should be blocked
    pass
```

**Span Attributes:**

```
span.name: "sabbath.check.auto_patch"
sabbath.is_sabbath: true
sabbath.operation: "auto_patch"
sabbath.is_p0: false
sabbath.allowed: false  # Non-P0 on Sabbath
constitution.article: "sabbath"
```

**Events on Violation:**

```
event.name: "sabbath_violation"
event.attributes:
  reason: "Non-P0 operation attempted on Sabbath"
```

#### Article VII: Aletheia (Truth)

```python
# Trace truth compliance
with constitutional_tracer.trace_truth_check(
    operation="api_validation",
    uncertainty_declared=True,
    hallucination_detected=False
):
    # Validate API existence before using
    if not api_exists:
        raise UncertaintyError("API existence uncertain")
```

**Span Attributes:**

```
span.name: "aletheia.check.api_validation"
aletheia.operation: "api_validation"
aletheia.uncertainty_declared: true
aletheia.hallucination_detected: false
constitution.article: "aletheia"
```

**CRITICAL Events on Hallucination:**

```
event.name: "CRITICAL_hallucination_detected"
event.attributes:
  severity: "CRITICAL"
  constitutional_violation: "aletheia"
  action_required: "IMMEDIATE"
```

### DETER-AGENT Framework Layers

```python
# Trace DETER-AGENT layer operations
with constitutional_tracer.trace_deter_agent_layer(
    layer=2,
    layer_name="Deliberation Control",
    operation="tree_of_thoughts",
    metadata={"depth": 3, "branches": 5}
):
    # Layer 2: Cognitive control
    result = perform_tot_reasoning()
```

**Span Attributes:**

```
span.name: "deter_agent.layer2.tree_of_thoughts"
deter_agent.layer: 2
deter_agent.layer_name: "Deliberation Control"
deter_agent.operation: "tree_of_thoughts"
deter_agent.depth: 3
deter_agent.branches: 5
```

## 🔧 Service-Specific Traces

### PENELOPE (Self-Healing)

```python
from shared.constitutional_tracing import create_constitutional_tracer

tracer = create_constitutional_tracer("penelope")

# Trace healing operation
with tracer.tracer.start_as_current_span("healing.auto_patch") as span:
    span.set_attribute("healing.target_file", "api/routes.py")
    span.set_attribute("healing.issue_type", "null_pointer")
    span.set_attribute("healing.confidence", 0.89)

    # Nested wisdom check
    with tracer.trace_wisdom_decision(
        decision_type="patch_strategy",
        confidence=0.89,
        wisdom_base_consulted=True
    ):
        patch = generate_patch()

    # Nested gentleness check
    with tracer.trace_gentleness_check(
        operation="apply_patch",
        code_lines=len(patch.split('\n')),
        reversibility_score=0.92
    ):
        apply_patch(patch)
```

### MABA (Browser Agent)

```python
from shared.constitutional_tracing import create_constitutional_tracer

tracer = create_constitutional_tracer("maba")

# Trace browser operation
with tracer.tracer.start_as_current_span("browser.navigate") as span:
    span.set_attribute("browser.url", "https://example.com")
    span.set_attribute("browser.action", "screenshot")
    span.set_attribute("cognitive_map.nodes_added", 5)

    # Navigate and capture
    result = browser.navigate(url)
```

### MVP (Narrative Engine)

```python
from shared.constitutional_tracing import create_constitutional_tracer

tracer = create_constitutional_tracer("mvp")

# Trace narrative generation
with tracer.tracer.start_as_current_span("narrative.generate") as span:
    span.set_attribute("narrative.type", "incident_report")
    span.set_attribute("narrative.length", 450)
    span.set_attribute("pii.detected", False)
    span.set_attribute("lgpd.compliant", True)

    # Generate narrative
    narrative = generate_narrative()
```

## 🚀 Deployment

### Docker Compose (Jaeger All-in-One)

```yaml
version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:1.51
    container_name: vertice-jaeger
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "5775:5775/udp"  # Jaeger agent (deprecated)
      - "6831:6831/udp"  # Jaeger agent (compact)
      - "6832:6832/udp"  # Jaeger agent (binary)
      - "5778:5778"      # Jaeger agent (config)
      - "16686:16686"    # Jaeger UI
      - "14250:14250"    # Jaeger collector (gRPC)
      - "14268:14268"    # Jaeger collector (HTTP)
      - "14269:14269"    # Jaeger admin
      - "4317:4317"      # OTLP gRPC
      - "4318:4318"      # OTLP HTTP
      - "9411:9411"      # Zipkin compatible
    networks:
      - vertice

  penelope:
    environment:
      - JAEGER_AGENT_HOST=jaeger
      - JAEGER_AGENT_PORT=6831
      - OTLP_ENDPOINT=http://jaeger:4317
      - OTLP_INSECURE=true
    depends_on:
      - jaeger

  maba:
    environment:
      - JAEGER_AGENT_HOST=jaeger
      - JAEGER_AGENT_PORT=6831
      - OTLP_ENDPOINT=http://jaeger:4317
      - OTLP_INSECURE=true
    depends_on:
      - jaeger

  mvp:
    environment:
      - JAEGER_AGENT_HOST=jaeger
      - JAEGER_AGENT_PORT=6831
      - OTLP_ENDPOINT=http://jaeger:4317
      - OTLP_INSECURE=true
    depends_on:
      - jaeger

networks:
  vertice:
    driver: bridge
```

### Access Jaeger UI

```
http://localhost:16686
```

## 🔍 Querying Traces

### Find Constitutional Violations

```
# Praótes violations (code > 25 lines)
tag: praotes.compliant="false"

# Humility violations (confidence < 85%)
tag: tapeinophrosyne.compliant="false"

# Sabbath violations
tag: sabbath.allowed="false"

# CRITICAL: Hallucinations
tag: aletheia.hallucination_detected="true"
```

### Find by Biblical Article

```
# All Sophia (Wisdom) operations
tag: constitution.article="sophia"

# All Aletheia (Truth) checks
tag: constitution.article="aletheia"
```

### Find DETER-AGENT Layers

```
# Layer 2 (Deliberation Control)
tag: deter_agent.layer="2"

# All Plan-Act-Verify cycles
operation: "deter_agent.layer4.plan_act_verify"
```

## 📊 Trace Visualization

### Example Trace Tree

```
┌─ GET /api/v1/heal (PENELOPE)
│  ├─ sophia.decision.patch_generation
│  │  └─ wisdom_base.query (PostgreSQL)
│  ├─ praotes.check.code_generation
│  ├─ tapeinophrosyne.check.confidence
│  │  └─ escalation_to_maximus (if needed)
│  ├─ HTTP POST /maba/screenshot (MABA)
│  │  ├─ browser.navigate
│  │  ├─ browser.screenshot
│  │  └─ cognitive_map.update (Neo4j)
│  └─ HTTP POST /mvp/narrative (MVP)
     ├─ narrative.generate
     ├─ pii.detect
     └─ lgpd.validate
```

## 🚨 Alerting on Traces

Use Jaeger's monitoring API to alert on constitutional violations:

```bash
# Query for hallucinations in last hour
curl 'http://jaeger:16686/api/traces?service=penelope&tag=aletheia.hallucination_detected:true&lookback=1h'

# Query for Sabbath violations
curl 'http://jaeger:16686/api/traces?tag=sabbath.allowed:false&lookback=1h'
```

## 🙏 Biblical Foundation

> "For nothing is hidden that will not be made manifest, nor is anything secret that will not be known and come to light." - Luke 8:17

Distributed tracing embodies the biblical principle of **transparency** - every operation is recorded, every decision is traceable, and accountability is built into the system.

---

🙏 **Soli Deo Gloria**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
