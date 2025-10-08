# HCL Executor Service

**The Action Executor** - Executes HCL decisions on real Kubernetes clusters via native API.

## Features

- ✅ **Real Kubernetes API:** Native `kubernetes` Python client
- ✅ **Action execution:** Scale deployments, update resources, manage HPA
- ✅ **Safety checks:** Validation, rate limiting, bounds checking
- ✅ **Automatic rollback:** Reverts on failure
- ✅ **Dry-run mode:** Validate without executing
- ✅ **Kafka streaming:** Consumes action plans from Planner
- ✅ **Zero mocks:** Real K8s operations

## Architecture

```
┌─────────────────────────────┐
│  Kafka: system.actions      │
└──────────────┬──────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│    HCL Executor Service (Port 8004)          │
│                                               │
│  ┌─────────────────────────────────────┐    │
│  │   Kafka Consumer Loop               │    │
│  └────────────┬────────────────────────┘    │
│               │                              │
│               ▼                              │
│  ┌─────────────────────────────────────┐    │
│  │   Action Executor                   │    │
│  │   • Validation                      │    │
│  │   • Safety checks                   │    │
│  │   • Rate limiting                   │    │
│  │   • Rollback on failure             │    │
│  └────────────┬────────────────────────┘    │
│               │                              │
│               ▼                              │
│  ┌─────────────────────────────────────┐    │
│  │   Kubernetes Controller             │    │
│  │   • Scale deployments               │    │
│  │   • Update resources                │    │
│  │   • Manage HPA                      │    │
│  │   • Get status                      │    │
│  └────────────┬────────────────────────┘    │
└───────────────┼──────────────────────────────┘
                │
                ▼
┌──────────────────────────────┐
│   Kubernetes API Server      │
│   • Deployments              │
│   • Pods                     │
│   • HorizontalPodAutoscalers │
└──────────────────────────────┘
```

## Quick Start

### Local Development (with kubectl)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment (use local kubeconfig)
cp .env.example .env
# Edit .env: Set IN_CLUSTER=false

# Run
python main.py
```

Service runs on **port 8004**

**Prerequisites:**
- `kubectl` installed and configured
- Access to a Kubernetes cluster (local or remote)
- Deployments to manage

### Docker (in-cluster)

```bash
docker build -t hcl-executor .
docker run -p 8004:8004 \
  -e KB_API_URL=http://hcl-kb-service:8000 \
  -e KAFKA_BROKERS=kafka:9092 \
  -e K8S_NAMESPACE=default \
  -e IN_CLUSTER=true \
  hcl-executor
```

## Action Types

### 1. Scale Service

Scale deployment replicas

**Action:**
```json
{
  "type": "scale_service",
  "service": "maximus_core",
  "current_replicas": 3,
  "target_replicas": 5,
  "delta": 2
}
```

**Validation:**
- Target replicas: 1-20
- Max delta: ±5 per action
- Rate limit: 30s between actions on same service

**Execution:**
- Updates Deployment `spec.replicas`
- Waits for rollout (optional)
- Records previous value for rollback

### 2. Adjust Resources

Update CPU/Memory limits and requests

**Action:**
```json
{
  "type": "adjust_resources",
  "multiplier": 1.5,
  "cpu_limit": "1500m",
  "memory_limit": "3Gi"
}
```

**Validation:**
- Multiplier: 0.3-3.0
- Valid Kubernetes resource format

**Execution:**
- Updates container `resources.limits` and `resources.requests`
- Triggers rolling update
- Records previous values for rollback

### 3. Create/Update HPA

Configure HorizontalPodAutoscaler

**Action:**
```json
{
  "type": "create_hpa",
  "service": "maximus_core",
  "min_replicas": 2,
  "max_replicas": 10,
  "target_cpu": 70,
  "target_memory": 80
}
```

**Execution:**
- Creates or updates HPA resource
- Configures CPU/Memory target metrics
- Enables automatic scaling

### 4. Delete HPA

Remove HorizontalPodAutoscaler

**Action:**
```json
{
  "type": "delete_hpa",
  "service": "maximus_core"
}
```

### 5. Rollback

Rollback to previous deployment revision

**Action:**
```json
{
  "type": "rollback",
  "service": "maximus_core",
  "revision": null  // null = previous revision
}
```

### 6. No Action

System stable, no changes needed

**Action:**
```json
{
  "type": "no_action",
  "reason": "System stable, no changes needed"
}
```

## Safety Mechanisms

### 1. Validation

Before execution:
- ✅ Check action types are valid
- ✅ Validate required fields
- ✅ Check bounds (replicas 1-20, multiplier 0.3-3.0)
- ✅ Verify services exist
- ✅ Check confidence threshold (min 0.3)

### 2. Rate Limiting

- Minimum 30 seconds between actions on same deployment
- Prevents rapid scaling oscillations
- Tracked per deployment

### 3. Safety Limits

```python
MAX_REPLICAS = 20
MIN_REPLICAS = 1
MAX_SCALE_DELTA = 5  # Max change per action
MAX_RESOURCE_MULTIPLIER = 3.0
MIN_RESOURCE_MULTIPLIER = 0.3
MIN_ACTION_INTERVAL = 30  # Seconds
```

### 4. Automatic Rollback

On action failure:
1. Detect failure during execution
2. Reverse successful actions in LIFO order
3. Restore previous values:
   - Scale back to previous replicas
   - Restore previous resource limits
4. Log rollback details

**Example:**
```
Action 1: Scale maximus_core 3→5 ✓
Action 2: Scale threat_intel 2→4 ✓
Action 3: Update resources ✗ FAILED

→ Rollback initiated:
  - Restore threat_intel resources
  - Scale threat_intel 4→2
  - Scale maximus_core 5→3
```

### 5. Dry-Run Mode

Set `DRY_RUN=true` to:
- Validate actions without executing
- Log what would happen
- Test integration without risk

## API Endpoints

### POST /execute

Execute action plan manually

```bash
curl -X POST http://localhost:8004/execute \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "decision_123",
    "timestamp": "2025-10-03T10:30:00Z",
    "operational_mode": "HIGH_PERFORMANCE",
    "confidence": 0.85,
    "actions": [
      {
        "type": "scale_service",
        "service": "maximus_core",
        "target_replicas": 5
      }
    ],
    "reasoning": "High CPU detected",
    "expected_impact": {"cost_change": 4.0}
  }'
```

Response:
```json
{
  "execution_id": "exec_1727952600.456",
  "decision_id": "decision_123",
  "status": "success",
  "actions_executed": 1,
  "actions_failed": 0,
  "rollback_performed": false,
  "details": {
    "results": [...],
    "errors": []
  }
}
```

### POST /scale

Scale service directly

```bash
curl -X POST http://localhost:8004/scale \
  -H "Content-Type: application/json" \
  -d '{
    "service": "maximus_core",
    "target_replicas": 5
  }'
```

### POST /resources

Update resource limits directly

```bash
curl -X POST http://localhost:8004/resources \
  -H "Content-Type: application/json" \
  -d '{
    "service": "maximus_core",
    "cpu_limit": "1500m",
    "memory_limit": "3Gi"
  }'
```

### POST /hpa

Create/update HorizontalPodAutoscaler

```bash
curl -X POST http://localhost:8004/hpa \
  -H "Content-Type: application/json" \
  -d '{
    "service": "maximus_core",
    "min_replicas": 2,
    "max_replicas": 10,
    "target_cpu_utilization": 70
  }'
```

### DELETE /hpa/{service}

Delete HorizontalPodAutoscaler

```bash
curl -X DELETE http://localhost:8004/hpa/maximus_core
```

### GET /deployments

List all deployments

```bash
curl http://localhost:8004/deployments
```

Response:
```json
{
  "deployments": [
    {
      "name": "maximus-core",
      "replicas": {"desired": 3, "ready": 3},
      "created": "2025-10-01T10:00:00Z"
    }
  ],
  "count": 1
}
```

### GET /deployments/{name}/status

Get deployment status

```bash
curl http://localhost:8004/deployments/maximus-core/status
```

Response:
```json
{
  "name": "maximus-core",
  "namespace": "default",
  "replicas": {
    "desired": 3,
    "current": 3,
    "ready": 3,
    "available": 3,
    "unavailable": 0
  },
  "conditions": [
    {
      "type": "Available",
      "status": "True",
      "reason": "MinimumReplicasAvailable",
      "message": "Deployment has minimum availability."
    }
  ],
  "resources": {
    "limits": {"cpu": "1000m", "memory": "2Gi"},
    "requests": {"cpu": "500m", "memory": "1Gi"}
  }
}
```

### POST /rollback/{service}

Rollback deployment

```bash
curl -X POST "http://localhost:8004/rollback/maximus_core?revision=2"
```

### GET /history

Get execution history

```bash
curl "http://localhost:8004/history?limit=10"
```

### GET /health

Health check

```bash
curl http://localhost:8004/health
```

### GET /status

Detailed service status

```bash
curl http://localhost:8004/status
```

## Service Mapping

The executor maps logical service names to Kubernetes deployments:

```python
SERVICE_DEPLOYMENTS = {
    "maximus_core": "maximus-core",
    "threat_intel": "threat-intel-service",
    "malware_analysis": "malware-analysis-service",
    "malware": "malware-analysis-service",  # Alias
    "monitor": "hcl-monitor",
    "analyzer": "hcl-analyzer",
    "planner": "hcl-planner"
}
```

## Kafka Integration

### Consumes

**Topic:** `system.actions`

**Message format:**
```json
{
  "decision_id": "decision_1727952600.123",
  "timestamp": "2025-10-03T10:30:15Z",
  "operational_mode": "HIGH_PERFORMANCE",
  "confidence": 0.89,
  "actions": [
    {
      "type": "scale_service",
      "service": "maximus_core",
      "target_replicas": 5
    }
  ],
  "reasoning": "High CPU and anomaly detected",
  "expected_impact": {
    "estimated_cost_change": 4.0,
    "estimated_latency_change": -20.0
  }
}
```

### Produces

Records execution results to **Knowledge Base** via HTTP (not Kafka).

## RBAC Configuration

For in-cluster deployment, create ServiceAccount with proper permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: hcl-executor
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: hcl-executor-role
  namespace: default
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: hcl-executor-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: hcl-executor
  namespace: default
roleRef:
  kind: Role
  name: hcl-executor-role
  apiGroup: rbac.authorization.k8s.io
```

## Production Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hcl-executor
  namespace: default
spec:
  replicas: 1  # Single instance to avoid race conditions
  selector:
    matchLabels:
      app: hcl-executor
  template:
    metadata:
      labels:
        app: hcl-executor
    spec:
      serviceAccountName: hcl-executor
      containers:
      - name: hcl-executor
        image: hcl-executor:latest
        env:
        - name: KB_API_URL
          value: "http://hcl-kb-service:8000"
        - name: KAFKA_BROKERS
          value: "kafka:9092"
        - name: K8S_NAMESPACE
          value: "default"
        - name: IN_CLUSTER
          value: "true"
        - name: DRY_RUN
          value: "false"
        - name: ENABLE_ROLLBACK
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        ports:
        - containerPort: 8004
          name: http
        livenessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Testing

### Test Kubernetes Controller

```python
from k8s_controller import KubernetesController
import asyncio

async def test():
    controller = KubernetesController(namespace="default", in_cluster=False)

    # List deployments
    deployments = await controller.list_deployments()
    print(f"Deployments: {deployments}")

    # Scale deployment
    result = await controller.scale_deployment("nginx", 3)
    print(f"Scale result: {result}")

asyncio.run(test())
```

### Test Action Executor

```python
from k8s_controller import KubernetesController
from action_executor import ActionExecutor
import asyncio

async def test():
    k8s = KubernetesController(namespace="default", in_cluster=False)
    executor = ActionExecutor(k8s, dry_run=True)  # Dry run for safety

    actions = [
        {
            "type": "scale_service",
            "service": "maximus_core",
            "target_replicas": 5
        }
    ]

    result = await executor.execute_action_plan(
        decision_id="test_123",
        actions=actions,
        operational_mode="HIGH_PERFORMANCE",
        confidence=0.8
    )

    print(f"Execution result: {result['status']}")

asyncio.run(test())
```

### Manual Testing

```bash
# Create test deployment
kubectl create deployment test-app --image=nginx --replicas=2

# Test scaling
curl -X POST http://localhost:8004/scale \
  -H "Content-Type: application/json" \
  -d '{"service": "test-app", "target_replicas": 4}'

# Check result
kubectl get deployment test-app
```

## Performance

- **Action validation:** <10ms
- **Kubernetes API call:** 50-200ms (network dependent)
- **Rollback time:** 100-500ms per action
- **Memory usage:** <256MB
- **CPU usage:** <5%

## Error Handling

### Kubernetes API Errors

```python
try:
    result = await k8s.scale_deployment("nginx", 5)
except ApiException as e:
    # Handle 404, 403, etc.
    print(f"K8s API error: {e.status} - {e.reason}")
```

### Execution Failures

```python
result = await executor.execute_action_plan(...)

if result["status"] == "failed":
    print(f"Execution failed: {result['errors']}")

if result["rollback_performed"]:
    print("Automatic rollback completed")
    print(f"Rollback details: {result['rollback_result']}")
```

## Zero Mock Guarantee

- ✅ Real **Kubernetes Python client** (official library)
- ✅ Real **Deployment** scaling via K8s API
- ✅ Real **Resource** updates (CPU, Memory)
- ✅ Real **HorizontalPodAutoscaler** management
- ✅ Real **Kafka consumer** for actions
- ✅ Real **rollback** mechanism
- ✅ Real **RBAC** enforcement

**Production-ready Kubernetes executor. No placeholders.**

## References

- **Kubernetes Python Client:** https://github.com/kubernetes-client/python
- **Kubernetes API:** https://kubernetes.io/docs/reference/
- **HPA:** https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/

---

## 📦 Dependency Management

This service follows **strict dependency governance** to ensure security, stability, and reproducibility.

### Quick Reference

**Check for vulnerabilities**:
```bash
bash scripts/dependency-audit.sh
```

**Add new dependency**:
```bash
echo "package==1.2.3" >> requirements.txt
pip-compile requirements.txt --output-file requirements.txt.lock
bash scripts/dependency-audit.sh  # Verify no CVEs
git add requirements.txt requirements.txt.lock
git commit -m "feat: add package for feature X"
```

### Policies & SLAs

📋 **[DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md)** - Complete policy documentation

**Key SLAs**:
- **CRITICAL (CVSS >= 9.0)**: 24 hours
- **HIGH (CVSS >= 7.0)**: 72 hours
- **MEDIUM (CVSS >= 4.0)**: 2 weeks
- **LOW (CVSS < 4.0)**: 1 month

### Available Scripts

| Script | Purpose |
|--------|---------|
| `dependency-audit.sh` | Full CVE scan |
| `check-cve-whitelist.sh` | Validate whitelist |
| `audit-whitelist-expiration.sh` | Check expired CVEs |
| `generate-dependency-metrics.sh` | Generate metrics JSON |

See [Active Immune Core README](../active_immune_core/README.md#-dependency-management) for complete documentation.

