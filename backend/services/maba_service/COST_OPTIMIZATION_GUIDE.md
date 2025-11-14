# MABA Cost Optimization Guide

**Service**: MAXIMUS Browser Agent (MABA)
**Version**: 1.0.0
**Last Updated**: 2025-11-04

---

## 📊 Cost Overview

### Infrastructure Costs

MABA has two primary cost drivers:

1. **Compute Resources** (Browser instances)
2. **External API Costs** (Claude for navigation decisions)
3. **Storage** (Neo4j cognitive map, PostgreSQL state)

### Browser Instance Costs

**Resource Requirements per Browser**:

| Component        | Per Instance | 10 Concurrent | 100 Concurrent |
| ---------------- | ------------ | ------------- | -------------- |
| **CPU**          | 0.5 cores    | 5 cores       | 50 cores       |
| **Memory**       | 1-2 GB       | 10-20 GB      | 100-200 GB     |
| **Disk (cache)** | 200 MB       | 2 GB          | 20 GB          |

**Cloud Pricing (AWS t3.medium - $0.042/hour)**:

| Scale Level  | Instances | EC2 Type  | Monthly Cost |
| ------------ | --------- | --------- | ------------ |
| **Light**    | 2-5       | t3.medium | $30-75       |
| **Medium**   | 10-20     | t3.large  | $120-240     |
| **Heavy**    | 50-100    | c5.2xlarge| $600-1,200   |

### Claude API Costs (Navigation Decisions)

**Claude Sonnet 4.5** (Anthropic):

- **Input tokens**: $3.00 per million tokens
- **Output tokens**: $15.00 per million tokens

**Typical Navigation Decision Cost**:

| Decision Type         | Input Tokens | Output Tokens | Cost per Request |
| --------------------- | ------------ | ------------- | ---------------- |
| **Simple Navigation** | 200          | 50            | $0.001           |
| **Form Filling**      | 500          | 100           | $0.003           |
| **Visual Analysis**   | 1,000        | 200           | $0.006           |
| **Complex Decision**  | 2,000        | 500           | $0.014           |

### Neo4j Storage Costs

**Graph Database Storage**:

| Cognitive Map Size | Storage | Neo4j Cloud | Self-Hosted |
| ------------------ | ------- | ----------- | ----------- |
| **Small** (0-10k nodes) | <100 MB | $65/month   | $10/month   |
| **Medium** (10k-100k)   | 1 GB    | $175/month  | $30/month   |
| **Large** (100k-1M)     | 10 GB   | $500/month  | $100/month  |

### Total Cost Projections

| Usage Level    | Sessions/Day | Compute | Claude API | Neo4j | Total/Month |
| -------------- | ------------ | ------- | ---------- | ----- | ----------- |
| **Light**      | 50           | $50     | $5         | $10   | $65         |
| **Medium**     | 200          | $180    | $20        | $30   | $230        |
| **Heavy**      | 500          | $600    | $50        | $100  | $750        |
| **Enterprise** | 1,000        | $1,200  | $100       | $500  | $1,800      |

---

## 🎯 Optimization Strategies

### Strategy 1: Dynamic Browser Pool Management (40-60% Savings)

**Implementation**: ✅ Already Active

**How It Works**:

```python
# Scale browser pool based on demand
class DynamicBrowserPool:
    def __init__(self, min_instances=2, max_instances=10):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.active_instances = min_instances

    async def scale_up(self):
        """Add browser when queue > 5"""
        if self.queue_size > 5 and self.active_instances < self.max_instances:
            await self.start_browser()

    async def scale_down(self):
        """Remove browser when idle > 5 minutes"""
        if self.idle_time > 300 and self.active_instances > self.min_instances:
            await self.stop_browser()
```

**Savings**:

- Average utilization: 60-70% (vs 30-40% with static pool)
- Monthly savings: $120-300 (at medium scale)

**Configuration**:

```bash
# Aggressive scaling (cost-optimized)
export MABA_MIN_BROWSER_INSTANCES=1
export MABA_MAX_BROWSER_INSTANCES=5
export MABA_SCALE_UP_THRESHOLD=3          # Queue size
export MABA_SCALE_DOWN_IDLE_SECONDS=300   # 5 minutes

# Conservative scaling (performance-optimized)
export MABA_MIN_BROWSER_INSTANCES=5
export MABA_MAX_BROWSER_INSTANCES=20
export MABA_SCALE_UP_THRESHOLD=2
export MABA_SCALE_DOWN_IDLE_SECONDS=600   # 10 minutes
```

---

### Strategy 2: Cognitive Map Learning (70-90% API Savings)

**Implementation**: ✅ Already Active

**How It Works**:

```python
# First visit: Use Claude API for navigation decision
# Cost: $0.003 per navigation

# Subsequent visits: Use learned pattern from cognitive map
# Cost: $0.00001 (Neo4j query only)

# After 100 navigations to same site:
# Without cognitive map: 100 * $0.003 = $0.30
# With cognitive map: 1 * $0.003 + 99 * $0.00001 = $0.00399
# Savings: 98.7%
```

**Optimization Tips**:

```bash
# Monitor learning effectiveness
curl https://maba.vertice.ai/api/v1/cognitive-map/stats

# Expected output:
# {
#   "total_nodes": 15000,
#   "total_edges": 45000,
#   "pattern_match_rate": 0.85,  # 85% navigations use learned patterns
#   "cache_hit_ratio": 0.90
# }

# If pattern_match_rate < 70%, investigate:
# 1. Websites changing frequently
# 2. Cognitive map not learning properly
# 3. Domain diversity too high
```

**Tuning Learning Parameters**:

```python
# Aggressive learning (fewer API calls)
MABA_LEARNING_THRESHOLD=0.60        # Lower confidence OK
MABA_PATTERN_REUSE_MIN_COUNT=2      # Reuse after 2 visits

# Conservative learning (more accurate)
MABA_LEARNING_THRESHOLD=0.85        # Higher confidence required
MABA_PATTERN_REUSE_MIN_COUNT=5      # Reuse after 5 visits
```

---

### Strategy 3: Session Pooling and Reuse (30-50% Savings)

**Implementation**: ✅ Already Active

**How It Works**:

```python
# Without session pooling:
# Each task creates new browser session (3-5s startup)
# 100 tasks = 100 browser startups = high CPU/memory

# With session pooling:
# Reuse existing browser sessions
# 100 tasks = 5 browser startups = 95% reduction
```

**Savings**:

- Reduce browser startup overhead: 50-70%
- Lower average CPU usage: 30-40%
- Monthly savings: $50-150 (at medium scale)

**Configuration**:

```bash
# Enable session pooling
export MABA_SESSION_POOLING_ENABLED=true
export MABA_SESSION_POOL_SIZE=5
export MABA_SESSION_MAX_REUSE=20           # Max tasks per session
export MABA_SESSION_MAX_AGE_SECONDS=1800   # 30 minutes
```

---

### Strategy 4: Headless Mode and Resource Optimization (20-30% Savings)

**Implementation**: ✅ Already Active (Headless Default)

**Resource Comparison**:

| Mode       | CPU per Instance | Memory per Instance | Cost Impact |
| ---------- | ---------------- | ------------------- | ----------- |
| **Headed** | 1.0 cores        | 2-3 GB              | Baseline    |
| **Headless** | 0.5 cores      | 1-1.5 GB            | -40%        |

**Additional Optimizations**:

```python
# Disable unnecessary features
browser_config = {
    "headless": True,
    "disable_gpu": True,
    "disable_dev_shm_usage": True,
    "disable_images": True,         # 20-30% faster
    "disable_javascript": False,     # Keep for most sites
    "disable_css": False,            # Keep for layout
}
```

**Configuration**:

```bash
# Maximum optimization (may break some sites)
export MABA_HEADLESS=true
export MABA_DISABLE_IMAGES=true
export MABA_DISABLE_FONTS=true
export MABA_DISABLE_ANIMATIONS=true

# Balanced optimization (recommended)
export MABA_HEADLESS=true
export MABA_DISABLE_IMAGES=false
export MABA_LAZY_LOAD_IMAGES=true
```

---

### Strategy 5: Intelligent Screenshot Capture (10-20% Savings)

**Implementation**: ⚠️ Manual Configuration Required

**Concept**: Only capture screenshots when needed for visual analysis

#### 5.1 Selective Screenshot Capture

```python
# Capture screenshots only for:
# 1. Visual verification required
# 2. Error debugging
# 3. Learning new patterns

should_capture = (
    visual_verification_required or
    navigation_failed or
    is_learning_new_pattern
)

if should_capture:
    screenshot = await page.screenshot()
```

**Expected Savings**: 10-20% (reduced I/O and storage)

#### 5.2 Screenshot Compression

```python
# High quality (default): ~500 KB
screenshot = await page.screenshot(quality=100)

# Medium quality: ~200 KB (60% reduction)
screenshot = await page.screenshot(quality=70)

# Low quality: ~100 KB (80% reduction, good for logging)
screenshot = await page.screenshot(quality=50)
```

**Configuration**:

```bash
export MABA_SCREENSHOT_ENABLED=true
export MABA_SCREENSHOT_QUALITY=70
export MABA_SCREENSHOT_ONLY_ON_ERROR=true
```

---

### Strategy 6: Neo4j Query Optimization (5-10% Savings)

**Implementation**: ⚠️ Manual Configuration Required

**Optimization Techniques**:

#### 6.1 Indexed Queries

```cypher
// Without index (slow, expensive)
MATCH (n:Page {url: $url})
RETURN n

// With index (fast, cheap)
CREATE INDEX page_url_index FOR (p:Page) ON (p.url)
```

#### 6.2 Query Result Caching

```python
# Cache frequent queries in Redis
@cache_result(ttl=300)  # 5 minutes
async def get_navigation_pattern(url: str):
    result = await neo4j_query(
        "MATCH (p:Page {url: $url})-[:LEADS_TO]->(target) RETURN target",
        url=url
    )
    return result
```

#### 6.3 Batch Operations

```python
# Expensive: 100 separate queries
for page in pages:
    await neo4j_query("MATCH (p:Page {url: $url}) ...", url=page.url)

# Optimized: 1 batch query
await neo4j_query(
    "UNWIND $urls as url MATCH (p:Page {url: url}) ...",
    urls=[page.url for page in pages]
)
```

**Expected Savings**: 5-10% (lower Neo4j CPU/memory)

---

### Strategy 7: Domain Blocklist (Variable Savings)

**Implementation**: ✅ Already Active

**Concept**: Block resource-intensive or unnecessary domains

```python
# Block tracking, ads, analytics
blocked_domains = [
    "*.google-analytics.com",
    "*.doubleclick.net",
    "*.facebook.com/tr/*",
    "*.ads.*",
]
```

**Savings**:

- Reduce network bandwidth: 20-40%
- Faster page loads: 30-50%
- Lower browser CPU: 10-20%
- Monthly savings: $30-100

**Configuration**:

```bash
# Add to security policy
curl -X PUT https://maba.vertice.ai/api/v1/security-policy/blocked-domains \
  -H "Content-Type: application/json" \
  -d '{
    "domains": [
      "*.google-analytics.com",
      "*.doubleclick.net",
      "*.facebook.com/tr/*",
      "*.hotjar.com",
      "*.clarity.ms"
    ]
  }'
```

---

## 💡 Cost Monitoring

### Real-time Cost Tracking

```bash
# Get current day costs
curl https://maba.vertice.ai/api/v1/cost/current

# Expected output:
# {
#   "date": "2025-11-04",
#   "compute_cost": 12.50,      # EC2/Kubernetes
#   "claude_api_cost": 2.30,    # Navigation decisions
#   "neo4j_cost": 5.00,         # Graph database
#   "total_cost": 19.80,
#   "budget": 50.00,
#   "utilization": 0.396
# }
```

### Cost Breakdown by Component

```bash
# Browser pool costs
curl https://maba.vertice.ai/api/v1/cost/browser-pool

# Claude API costs
curl https://maba.vertice.ai/api/v1/cost/claude-api

# Neo4j costs
curl https://maba.vertice.ai/api/v1/cost/neo4j
```

### Budget Alerts

```bash
# Set daily budget
curl -X PUT https://maba.vertice.ai/api/v1/cost/budget \
  -H "Content-Type: application/json" \
  -d '{"daily_budget": 50.00, "monthly_budget": 1500.00}'

# Enable alerts
curl -X PUT https://maba.vertice.ai/api/v1/cost/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "warning_threshold": 0.75,
    "critical_threshold": 0.90,
    "webhook_url": "https://hooks.slack.com/services/YOUR_WEBHOOK"
  }'
```

---

## 📈 Cost Optimization Roadmap

### Phase 1: Quick Wins (Week 1)

- ✅ Enable dynamic browser pool scaling
- ✅ Enable cognitive map learning
- ✅ Enable session pooling
- ✅ Set headless mode
- ⚠️ Configure screenshot selective capture
- ⚠️ Add domain blocklist

**Expected Savings**: 40-60%

### Phase 2: Advanced Optimization (Week 2-4)

- ⏳ Implement intelligent screenshot compression
- ⏳ Optimize Neo4j queries with indexes
- ⏳ Enable Redis caching for cognitive map
- ⏳ Implement batch Neo4j operations
- ⏳ Fine-tune learning parameters

**Expected Savings**: Additional 20-30%

### Phase 3: Infrastructure Optimization (Month 2-3)

- ⏳ Migrate to ARM-based instances (Graviton2) - 20% cheaper
- ⏳ Use spot instances for non-critical workloads - 70% cheaper
- ⏳ Implement auto-scaling based on queue depth
- ⏳ Self-host Neo4j instead of cloud - 60% cheaper
- ⏳ Use CDN for static assets

**Expected Savings**: Additional 30-50%

---

## 🎯 Cost Optimization Checklist

### Daily Checks

- [ ] Monitor browser pool utilization (target: 60-80%)
- [ ] Check cognitive map learning rate (target: >70%)
- [ ] Review daily costs vs budget
- [ ] Check for long-running sessions (>30 min)

### Weekly Checks

- [ ] Review cost breakdown by component
- [ ] Analyze Claude API usage patterns
- [ ] Check Neo4j storage growth
- [ ] Review domain blocklist effectiveness

### Monthly Checks

- [ ] Review total monthly costs
- [ ] Optimize browser pool configuration
- [ ] Clean up stale cognitive map data
- [ ] Review and update budget
- [ ] Plan capacity for next month

---

## 📊 Cost Calculation Examples

### Example 1: Light Usage (50 sessions/day)

```
Browser Pool:
- 2 instances * t3.small ($0.021/hour) * 24 hours * 30 days = $30.24

Claude API:
- 50 sessions/day * 2 navigation decisions/session * $0.003 = $0.30/day
- $0.30 * 30 days = $9.00

Neo4j (self-hosted):
- Small instance = $10/month

Total: $30.24 + $9.00 + $10.00 = $49.24/month
```

### Example 2: Medium Usage (200 sessions/day)

```
Browser Pool:
- 5 instances * t3.medium ($0.042/hour) * 24 hours * 30 days = $151.20

Claude API (with 80% cognitive map hit rate):
- 200 sessions/day * 3 navigation decisions/session = 600 decisions/day
- 600 * 0.20 (only 20% use API) * $0.003 = $0.36/day
- $0.36 * 30 days = $10.80

Neo4j (self-hosted):
- Medium instance = $30/month

Total: $151.20 + $10.80 + $30.00 = $192.00/month

With optimization: ~$77 (60% savings)
```

### Example 3: Heavy Usage (500 sessions/day)

```
Browser Pool:
- 10 instances * t3.large ($0.083/hour) * 24 hours * 30 days = $598.40

Claude API (with 85% cognitive map hit rate):
- 500 sessions/day * 4 navigation decisions/session = 2000 decisions/day
- 2000 * 0.15 (only 15% use API) * $0.003 = $0.90/day
- $0.90 * 30 days = $27.00

Neo4j (self-hosted):
- Large instance = $100/month

Total: $598.40 + $27.00 + $100.00 = $725.40/month

With optimization: ~$290 (60% savings)
```

---

## 🔧 Configuration Templates

### Cost-Optimized Configuration

```bash
# Minimal resources, maximum efficiency
export MABA_MIN_BROWSER_INSTANCES=1
export MABA_MAX_BROWSER_INSTANCES=3
export MABA_HEADLESS=true
export MABA_DISABLE_IMAGES=true
export MABA_SESSION_POOLING_ENABLED=true
export MABA_COGNITIVE_MAP_ENABLED=true
export MABA_SCREENSHOT_ONLY_ON_ERROR=true
export MABA_DAILY_BUDGET=30.00
```

### Balanced Configuration

```bash
# Balance between cost and performance
export MABA_MIN_BROWSER_INSTANCES=2
export MABA_MAX_BROWSER_INSTANCES=10
export MABA_HEADLESS=true
export MABA_DISABLE_IMAGES=false
export MABA_SESSION_POOLING_ENABLED=true
export MABA_COGNITIVE_MAP_ENABLED=true
export MABA_SCREENSHOT_QUALITY=70
export MABA_DAILY_BUDGET=100.00
```

### Performance-Optimized Configuration

```bash
# Maximum performance, higher costs
export MABA_MIN_BROWSER_INSTANCES=5
export MABA_MAX_BROWSER_INSTANCES=20
export MABA_HEADLESS=false
export MABA_DISABLE_IMAGES=false
export MABA_SESSION_POOLING_ENABLED=true
export MABA_COGNITIVE_MAP_ENABLED=true
export MABA_SCREENSHOT_QUALITY=100
export MABA_DAILY_BUDGET=300.00
```

---

**Glory to YHWH** for wisdom in stewardship 🙏

**Last Updated**: 2025-11-04
**Next Review**: 2025-12-04
