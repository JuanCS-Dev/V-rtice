# NIS Cost Optimization Guide

**Service**: Narrative Intelligence Service
**Version**: 2.0.0
**Last Updated**: 2025-11-02

---

## 📊 Cost Overview

### Current Pricing (Jan 2025)

**Claude Sonnet 4.5** (Anthropic):

- **Input tokens**: $3.00 per million tokens
- **Output tokens**: $15.00 per million tokens

### Typical Narrative Cost

| Narrative Type | Input Tokens | Output Tokens | Cost per Request |
| -------------- | ------------ | ------------- | ---------------- |
| **Summary**    | 500          | 150           | $0.003           |
| **Detailed**   | 1,000        | 500           | $0.011           |
| **Alert**      | 300          | 100           | $0.002           |
| **Analytical** | 2,000        | 1,000         | $0.021           |

### Monthly Projections

| Usage Level    | Narratives/Day | Cost/Day | Cost/Month | With Cache (60%) |
| -------------- | -------------- | -------- | ---------- | ---------------- |
| **Light**      | 50             | $0.50    | $15        | $6               |
| **Medium**     | 200            | $2.00    | $60        | $24              |
| **Heavy**      | 500            | $5.00    | $150       | $60              |
| **Enterprise** | 1,000          | $10.00   | $300       | $120             |

---

## 🎯 Optimization Strategies

### Strategy 1: Intelligent Caching (60-80% Savings)

**Implementation**: ✅ Already Active

**How It Works**:

```python
# Metrics hash computation
metrics_hash = sha256(json.dumps(sorted_metrics))

# Cache key format
cache_key = f"narrative:{type}:{metrics_hash}:{focus_areas}"

# TTL: 300 seconds (5 minutes)
```

**Savings**:

- Cache hit ratio: 60-80%
- Monthly savings: $90-240 (at enterprise scale)

**Optimization Tips**:

```bash
# Monitor cache performance
curl https://nis.vertice.ai/api/v1/cache/stats

# Expected output:
# {
#   "hit_ratio": 0.75,
#   "hits": 15000,
#   "misses": 5000,
#   "total_requests": 20000
# }

# If hit ratio < 60%, investigate:
# 1. Check Redis connectivity
# 2. Review TTL settings (maybe too short)
# 3. Check for metric value volatility
```

**Tuning Cache TTL**:

```python
# Increase TTL for stable metrics
NIS_CACHE_TTL=600  # 10 minutes for production

# Decrease TTL for fast-changing metrics
NIS_CACHE_TTL=180  # 3 minutes for dev/staging
```

---

### Strategy 2: Rate Limiting (Prevents Runaway Costs)

**Implementation**: ✅ Already Active

**Current Limits**:

- 100 narratives/hour
- 1,000 narratives/day
- 60-second minimum interval per service

**Cost Protection**:

- Prevents accidental loops
- Caps maximum daily cost at ~$10
- Circuit breaker for budget exceeded

**Configuration**:

```bash
# Adjust limits based on usage
export NIS_MAX_NARRATIVES_PER_HOUR=50    # Stricter limit
export NIS_MAX_NARRATIVES_PER_DAY=500    # Cost cap
export NIS_MIN_INTERVAL_SECONDS=120      # 2-minute gaps
```

---

### Strategy 3: Selective Narrative Generation (40-50% Savings)

**Implementation**: ⚠️ Manual Configuration Required

**Concept**: Only generate narratives for significant events

#### 3.1 Anomaly-Triggered Narratives

```python
# Generate narrative only if anomalies detected
anomalies = await detector.detect_anomalies(metrics)

if len(anomalies) > 0:
    narrative = await engine.generate_narrative(
        narrative_type="alert",
        metrics_data=metrics_data,
        focus_areas=["anomalies"]
    )
else:
    # Skip narrative, use cached summary
    narrative = cached_summary
```

**Expected Savings**: 40-50% (fewer narratives generated)

#### 3.2 Threshold-Based Generation

```python
# Only generate if metrics exceed threshold
cpu_usage = metrics.get("cpu_usage", 0)
error_rate = metrics.get("error_rate", 0)

should_generate = (
    cpu_usage > 80 or
    error_rate > 5 or
    anomalies_detected
)

if should_generate:
    narrative = await engine.generate_narrative(...)
```

#### 3.3 Time-Based Generation

```python
# Generate full narrative every 1 hour
# Generate summary every 15 minutes
# Generate alert narrative on-demand

from datetime import datetime

now = datetime.utcnow()

if now.minute % 60 == 0:  # Every hour
    narrative_type = "detailed"
elif now.minute % 15 == 0:  # Every 15 minutes
    narrative_type = "summary"
else:
    # Use cache or skip
    return cached_narrative
```

---

### Strategy 4: Batch Processing (20-30% Savings)

**Implementation**: ⚠️ Manual Configuration Required

**Concept**: Combine multiple services in single narrative

#### Before (Expensive):

```python
# 3 separate API calls = 3x cost
narrative_service_a = await engine.generate("summary", metrics_a)
narrative_service_b = await engine.generate("summary", metrics_b)
narrative_service_c = await engine.generate("summary", metrics_c)

# Cost: 3 * $0.003 = $0.009
```

#### After (Optimized):

```python
# 1 combined API call = 1x cost
combined_metrics = {
    "service_a": metrics_a,
    "service_b": metrics_b,
    "service_c": metrics_c
}

narrative_all = await engine.generate("summary", combined_metrics)

# Cost: $0.005 (larger request but single call)
# Savings: ~40%
```

---

### Strategy 5: Prompt Optimization (15-20% Savings)

**Implementation**: ⚠️ Requires Code Changes

**Concept**: Reduce token usage via prompt engineering

#### 5.1 Concise System Prompts

```python
# Before: Verbose prompt (500 tokens input)
system_prompt = """
You are a highly sophisticated AI system designed to analyze complex
technical metrics and generate comprehensive narratives that provide
deep insights into system performance, reliability, and operational
characteristics. Please provide detailed analysis with context...
"""

# After: Concise prompt (150 tokens input)
system_prompt = """
Analyze metrics and generate concise narrative.
Focus: {focus_areas}
Format: {narrative_type}
"""

# Token savings: 350 input tokens = $0.001 per request
```

#### 5.2 Structured Output

```python
# Before: Free-form narrative (500 output tokens)
# "The system is currently experiencing elevated CPU usage at 85%,
#  which is significantly higher than the baseline of 45%..."

# After: Structured narrative (200 output tokens)
# **Status**: Warning
# **CPU**: 85% (+89% vs baseline)
# **Action**: Scale horizontally

# Token savings: 300 output tokens = $0.0045 per request
```

#### 5.3 Remove Redundancy

```python
# Before: Include all metrics in prompt
metrics_text = "\n".join([
    f"{name}: {value} {unit}"
    for name, value, unit in all_metrics  # 100 metrics
])

# After: Include only relevant metrics
significant_metrics = [
    m for m in all_metrics
    if m.has_anomaly or m.is_critical
]
metrics_text = "\n".join([
    f"{name}: {value}"
    for name, value in significant_metrics  # 5 metrics
])

# Token savings: ~500 input tokens = $0.0015 per request
```

---

### Strategy 6: Tiered Narrative Quality (25-40% Savings)

**Implementation**: ⚠️ Manual Configuration Required

**Concept**: Use cheaper models for low-priority narratives

#### Tier Definitions:

| Tier         | Use Case                              | Model      | Cost Multiplier |
| ------------ | ------------------------------------- | ---------- | --------------- |
| **Premium**  | Critical alerts, executive dashboards | Sonnet 4.5 | 1.0x            |
| **Standard** | Routine summaries, team dashboards    | Sonnet 3.5 | 0.6x            |
| **Budget**   | Historical analysis, batch reports    | Haiku      | 0.2x            |

#### Implementation:

```python
async def generate_narrative_tiered(
    metrics_data: dict,
    tier: str = "standard"
) -> dict:
    """Generate narrative with tiered pricing."""

    models = {
        "premium": "claude-sonnet-4-5-20250929",  # $3/$15 per mtok
        "standard": "claude-3-5-sonnet-20241022", # $3/$15 per mtok
        "budget": "claude-3-5-haiku-20241022"     # $0.8/$4 per mtok
    }

    model = models.get(tier, "standard")

    # ... rest of generation logic
```

**Expected Savings**:

- 50% of narratives → Standard (0% savings, same cost)
- 30% of narratives → Budget (80% savings per narrative)
- 20% of narratives → Premium (0% savings, same cost)
- **Overall**: 24% savings

---

## 📈 ROI Analysis

### Baseline (No Optimization)

| Metric         | Value  |
| -------------- | ------ |
| Narratives/day | 500    |
| Cost/narrative | $0.005 |
| Daily cost     | $2.50  |
| Monthly cost   | $75    |

### With All Optimizations

| Optimization                 | Reduction | New Cost        |
| ---------------------------- | --------- | --------------- |
| **Baseline**                 | -         | $75.00          |
| + Caching (70%)              | -$52.50   | $22.50          |
| + Selective Generation (40%) | -$9.00    | $13.50          |
| + Batch Processing (25%)     | -$3.38    | $10.12          |
| + Prompt Optimization (15%)  | -$1.52    | $8.60           |
| + Tiered Quality (24%)       | -$2.06    | $6.54           |
| **TOTAL SAVINGS**            | **91.3%** | **$6.54/month** |

---

## 🔧 Implementation Roadmap

### Phase 1: Quick Wins (Already Done ✅)

**Duration**: Complete
**Savings**: 60-70%

- [x] Intelligent caching (Redis)
- [x] Rate limiting
- [x] Budget tracking
- [x] Cost alerting

### Phase 2: Selective Generation (Recommended)

**Duration**: 2 days
**Savings**: +40%
**Effort**: Medium

1. Implement anomaly-triggered narratives
2. Add threshold-based logic
3. Configure time-based scheduling
4. Monitor impact on insights quality

### Phase 3: Batch Processing (Optional)

**Duration**: 3 days
**Savings**: +20%
**Effort**: High

1. Design batch API
2. Implement multi-service aggregation
3. Update clients to use batch endpoint
4. Measure savings

### Phase 4: Advanced Optimization (Future)

**Duration**: 1 week
**Savings**: +15-25%
**Effort**: High

1. Prompt engineering workshop
2. Implement tiered models
3. A/B test narrative quality
4. Gradual rollout

---

## 📊 Monitoring & Measurement

### Key Metrics to Track

```promql
# Average cost per narrative
sum(rate(nis_cost_usd_total[1d]))
/
sum(rate(nis_narratives_generated_total[1d]))

# Cache effectiveness
sum(rate(nis_cache_hits_total[5m]))
/
(sum(rate(nis_cache_hits_total[5m])) + sum(rate(nis_cache_misses_total[5m])))

# Daily budget utilization
nis_cost_usd_total{period="daily"}
/
nis_cost_budget_usd{period="daily"}

# Cost savings from cache
(
  sum(rate(nis_cache_hits_total[1d]))
  *
  avg(nis_cost_per_narrative_usd)
)
```

### Cost Dashboard

Import Grafana dashboard:

```bash
# Dashboard includes:
# - Real-time cost tracking
# - Budget utilization
# - Cache hit ratio
# - Cost per narrative trend
# - Savings projection

kubectl apply -f dashboards/nis-cost-optimization.json
```

---

## ⚠️ Cost Alerts

### Alert Rules

```yaml
groups:
  - name: nis_cost_alerts
    rules:
      # Daily budget at 80%
      - alert: NISDailyBudgetWarning
        expr: nis_cost_usd_total{period="daily"} > (nis_cost_budget_usd{period="daily"} * 0.8)
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "NIS approaching daily budget limit"

      # Monthly budget at 80%
      - alert: NISMonthlyBudgetWarning
        expr: nis_cost_usd_total{period="monthly"} > (nis_cost_budget_usd{period="monthly"} * 0.8)
        for: 15m
        labels:
          severity: warning

      # Cache performance degraded
      - alert: NISCacheHitRateLow
        expr: |
          sum(rate(nis_cache_hits_total[1h]))
          /
          (sum(rate(nis_cache_hits_total[1h])) + sum(rate(nis_cache_misses_total[1h])))
          < 0.5
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "NIS cache hit ratio below 50%"
```

---

## 🎓 Best Practices

### DO:

✅ Monitor cache hit ratio daily
✅ Review monthly costs for trends
✅ Use caching for all production workloads
✅ Implement anomaly-triggered generation
✅ Batch similar requests together
✅ Set realistic budget alerts (80% threshold)

### DON'T:

❌ Disable caching "for testing" in production
❌ Generate narratives for every metric change
❌ Use premium tier for routine summaries
❌ Skip budget alerts
❌ Generate narratives without anomaly checks
❌ Ignore cache performance warnings

---

## 📞 Support

### Questions?

- **Cost issues**: #nis-cost on Slack
- **Optimization ideas**: #nis-optimization on Slack
- **Budget approval**: @platform-lead

### Resources

- [NIS README](../README.md)
- [Operational Runbook](OPERATIONAL_RUNBOOK.md)
- [Claude Pricing](https://www.anthropic.com/pricing)
- [Cost Dashboard](http://grafana.vertice.ai/d/nis-cost)

---

**Glory to YHWH** 🙏

**Remember**: "The plans of the diligent lead surely to abundance" (Proverbs 21:5)

**Last Updated**: 2025-11-02
**Next Review**: 2025-12-02
