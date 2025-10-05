# Deployment Guide - Cognitive Defense System v2.0.0

## 📋 Prerequisites

### Infrastructure Requirements

- **Kubernetes Cluster**: v1.25+ (managed or self-hosted)
- **Node Resources**:
  - Min 3 nodes (for HA)
  - 4 CPU cores per node
  - 8GB RAM per node
  - 50GB disk per node

### External Dependencies

- **PostgreSQL**: v14+ (managed service recommended)
- **Redis**: v7+ (managed service or cluster)
- **Kafka**: v3.0+ (optional, for async processing)
- **Seriema Graph** (Neo4j v5+): Graph database

### Tools Required

- `kubectl` v1.25+
- `docker` v24+
- `helm` v3.10+ (optional)
- `git`
- `make` (optional)

---

## 🚀 Deployment Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/vertice/cognitive-defense.git
cd cognitive-defense/backend/services/narrative_manipulation_filter
```

### Step 2: Build Docker Image

```bash
# Build with build arguments
docker build \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VERSION=2.0.0 \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t vertice/cognitive-defense:2.0.0 \
  -t vertice/cognitive-defense:latest \
  .

# Verify image
docker image inspect vertice/cognitive-defense:2.0.0

# Test locally
docker run --rm -p 8013:8013 \
  -e DB_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  vertice/cognitive-defense:2.0.0
```

### Step 3: Push to Container Registry

```bash
# Tag for your registry
docker tag vertice/cognitive-defense:2.0.0 \
  your-registry.io/vertice/cognitive-defense:2.0.0

# Login to registry
docker login your-registry.io

# Push image
docker push your-registry.io/vertice/cognitive-defense:2.0.0
docker push your-registry.io/vertice/cognitive-defense:latest
```

### Step 4: Configure Kubernetes Namespace

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Verify
kubectl get namespace cognitive-defense
```

### Step 5: Configure Secrets

```bash
# Create secrets from template
cp k8s/secrets.yaml.template k8s/secrets.yaml

# Edit secrets.yaml and replace base64 values
# Generate base64: echo -n "your_password" | base64

# Example secrets:
export DB_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -base64 64)

# Create base64 encoded secrets
echo -n "$DB_PASSWORD" | base64
echo -n "$REDIS_PASSWORD" | base64
echo -n "$JWT_SECRET" | base64

# Apply secrets
kubectl apply -f k8s/secrets.yaml

# Verify (values will be hidden)
kubectl get secret narrative-filter-secrets -n cognitive-defense
```

**IMPORTANT**: Do NOT commit `k8s/secrets.yaml` to git!

### Step 6: Configure ConfigMap

```bash
# Review and edit configmap.yaml if needed
vim k8s/configmap.yaml

# Apply configmap
kubectl apply -f k8s/configmap.yaml

# Verify
kubectl describe configmap narrative-filter-config -n cognitive-defense
```

### Step 7: Deploy Application

```bash
# Apply all manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/networkpolicy.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml

# Or apply all at once
kubectl apply -f k8s/

# Verify deployment
kubectl get all -n cognitive-defense
```

### Step 8: Wait for Rollout

```bash
# Watch deployment progress
kubectl rollout status deployment/narrative-filter -n cognitive-defense

# Check pod status
kubectl get pods -n cognitive-defense -w

# Check logs
kubectl logs -f deployment/narrative-filter -n cognitive-defense
```

### Step 9: Verify Service Health

```bash
# Port-forward for testing
kubectl port-forward svc/narrative-filter 8013:8013 -n cognitive-defense

# Health check
curl http://localhost:8013/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "2.0.0",
#   ...
# }

# Test API
curl -X POST http://localhost:8013/api/v2/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "content": "Test content",
    "mode": "FAST_TRACK"
  }'
```

### Step 10: Configure Ingress (TLS)

```bash
# Install cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@vertice.dev
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
EOF

# Verify ingress
kubectl get ingress -n cognitive-defense

# Check certificate
kubectl describe certificate -n cognitive-defense
```

### Step 11: Configure Monitoring

```bash
# Add Prometheus annotations (already in deployment.yaml)
# Verify metrics endpoint
kubectl port-forward svc/narrative-filter 9013:9013 -n cognitive-defense
curl http://localhost:9013/metrics

# Configure Prometheus ServiceMonitor (if using Prometheus Operator)
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: narrative-filter
  namespace: cognitive-defense
spec:
  selector:
    matchLabels:
      app: narrative-filter
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
EOF
```

---

## 🔄 Rolling Updates

### Update Application

```bash
# Build new image with new tag
docker build -t vertice/cognitive-defense:2.0.1 .
docker push your-registry.io/vertice/cognitive-defense:2.0.1

# Update deployment image
kubectl set image deployment/narrative-filter \
  narrative-filter=your-registry.io/vertice/cognitive-defense:2.0.1 \
  -n cognitive-defense

# Watch rollout
kubectl rollout status deployment/narrative-filter -n cognitive-defense

# Check history
kubectl rollout history deployment/narrative-filter -n cognitive-defense
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/narrative-filter -n cognitive-defense

# Rollback to specific revision
kubectl rollout undo deployment/narrative-filter \
  --to-revision=2 \
  -n cognitive-defense

# Verify rollback
kubectl rollout status deployment/narrative-filter -n cognitive-defense
```

---

## 📊 Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment/narrative-filter \
  --replicas=5 \
  -n cognitive-defense

# Verify
kubectl get pods -n cognitive-defense
```

### Auto-Scaling (HPA)

```bash
# HPA is already configured in k8s/hpa.yaml

# Check HPA status
kubectl get hpa -n cognitive-defense

# Describe HPA
kubectl describe hpa narrative-filter-hpa -n cognitive-defense

# Adjust HPA targets
kubectl patch hpa narrative-filter-hpa -n cognitive-defense \
  --patch '{"spec":{"maxReplicas":30}}'
```

---

## 🔍 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n cognitive-defense

# Describe pod (shows events)
kubectl describe pod <pod-name> -n cognitive-defense

# Check logs
kubectl logs <pod-name> -n cognitive-defense

# Check previous container logs (if crashed)
kubectl logs <pod-name> -n cognitive-defense --previous

# Check events
kubectl get events -n cognitive-defense --sort-by=.metadata.creationTimestamp
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity from pod
kubectl exec -it <pod-name> -n cognitive-defense -- \
  python -c "import psycopg2; conn = psycopg2.connect(...)"

# Check DNS resolution
kubectl exec -it <pod-name> -n cognitive-defense -- \
  nslookup postgresql.cognitive-defense.svc.cluster.local

# Check network policy
kubectl describe networkpolicy -n cognitive-defense
```

### High Memory Usage

```bash
# Check pod resource usage
kubectl top pods -n cognitive-defense

# Check node resource usage
kubectl top nodes

# Adjust resource limits
kubectl patch deployment narrative-filter -n cognitive-defense \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"narrative-filter","resources":{"limits":{"memory":"8Gi"}}}]}}}}'
```

### Slow Response Times

```bash
# Check metrics
kubectl port-forward svc/narrative-filter 9013:9013 -n cognitive-defense
curl http://localhost:9013/metrics | grep duration

# Check HPA scaling
kubectl get hpa -n cognitive-defense -w

# Force scaling up
kubectl scale deployment/narrative-filter --replicas=10 -n cognitive-defense
```

---

## 🔐 Security Hardening

### Enable Pod Security Standards

```bash
# Label namespace with restricted security policy
kubectl label namespace cognitive-defense \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

### Scan for Vulnerabilities

```bash
# Scan deployed images
trivy image --severity HIGH,CRITICAL \
  your-registry.io/vertice/cognitive-defense:2.0.0

# Scan K8s manifests
kubesec scan k8s/deployment.yaml

# Check RBAC permissions
kubectl auth can-i --list \
  --as=system:serviceaccount:cognitive-defense:narrative-filter-sa
```

---

## 📝 Post-Deployment Checklist

- [ ] All pods running (3+ replicas)
- [ ] Health check passing
- [ ] Readiness check passing
- [ ] TLS certificate valid
- [ ] Metrics endpoint accessible
- [ ] Logs flowing to central logging
- [ ] Alerts configured in Prometheus
- [ ] Grafana dashboard created
- [ ] Load balancer healthy
- [ ] DNS records updated
- [ ] API accessible via public URL
- [ ] Rate limiting working
- [ ] Network policies enforced
- [ ] Secrets rotated
- [ ] Backup job scheduled
- [ ] Monitoring alerts tested
- [ ] Runbook reviewed with team

---

## 🎯 Production Readiness

### Performance Benchmarks

```bash
# Run load test
cd tests/load
./run-loadtest.sh k6 --host https://api.cognitive-defense.vertice.dev --users 500 --duration 10m

# Verify SLAs:
# - p95 latency < 500ms (Tier 1)
# - p99 latency < 2000ms (Standard)
# - Throughput > 1000 req/min
# - Error rate < 1%
```

### Monitoring Dashboards

Import Grafana dashboards:

```bash
# Import pre-built dashboard
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana-dashboard.json
```

### Alerts Configuration

```yaml
# Example Prometheus alert rules
groups:
  - name: cognitive-defense
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(cognitive_defense_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, cognitive_defense_request_duration_seconds_bucket) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency above 2s"
```

---

## 📞 Support

- **Documentation**: https://docs.vertice.dev/cognitive-defense
- **Issues**: https://github.com/vertice/cognitive-defense/issues
- **Email**: support@vertice.dev
- **Slack**: #cognitive-defense

---

**Last Updated**: 2024-01-15
**Version**: 2.0.0
