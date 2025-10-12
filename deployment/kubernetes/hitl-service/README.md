# HITL Patch Service - Kubernetes Deployment

Complete Kubernetes deployment configuration for the Human-in-the-Loop Patch Approval Service.

## 📁 Files

```
hitl-service/
├── deployment.yaml      - Deployment, Service, HPA, PDB, NetworkPolicy
├── ingress.yaml         - Ingress configuration + TLS
├── config.yaml          - ConfigMap, Secrets, RBAC
├── monitoring.yaml      - ServiceMonitor, PrometheusRule, Grafana Dashboard
├── kustomization.yaml   - Kustomize configuration
├── deploy.sh            - Automated deployment script
└── README.md            - This file
```

## 🚀 Quick Start

### Prerequisites

- kubectl configured and connected to cluster
- Docker installed
- Namespace `maximus-immunity` (created automatically)
- PostgreSQL deployed (`postgres-immunity-service`)

### Deploy to Staging

```bash
./deploy.sh staging
```

### Deploy to Production

```bash
./deploy.sh production
```

## 📊 Architecture

### Components

1. **Deployment**: 2 replicas with rolling updates
2. **Service**: ClusterIP with session affinity
3. **HPA**: Auto-scaling 2-5 replicas based on CPU/Memory
4. **PDB**: Ensures at least 1 pod available during disruptions
5. **NetworkPolicy**: Restricts traffic to/from approved sources
6. **Ingress**: TLS termination + rate limiting
7. **ServiceMonitor**: Prometheus metrics scraping
8. **PrometheusRule**: Alerting rules

### Resource Limits

```yaml
Requests:
  CPU: 250m
  Memory: 256Mi

Limits:
  CPU: 500m
  Memory: 512Mi
```

### Auto-Scaling

- **Min Replicas**: 2
- **Max Replicas**: 5
- **CPU Target**: 70%
- **Memory Target**: 80%

## 🔒 Security

### RBAC

- ServiceAccount: `maximus-immunity-sa`
- Role: Limited to reading ConfigMaps/Secrets
- RoleBinding: Binds SA to Role

### NetworkPolicy

**Ingress**:
- Allow from `maximus-frontend` namespace
- Allow from `monitoring` namespace (Prometheus)

**Egress**:
- Allow to PostgreSQL pods
- Allow to Wargaming Crisol pods
- Allow DNS (UDP 53)

### Secrets

⚠️ **IMPORTANT**: Replace default secrets before production!

```bash
# Generate strong passwords
kubectl create secret generic postgres-immunity-secret \
  -n maximus-immunity \
  --from-literal=username=maximus \
  --from-literal=password=$(openssl rand -base64 32)

kubectl create secret generic hitl-api-keys \
  -n maximus-immunity \
  --from-literal=jwt-secret=$(openssl rand -base64 64) \
  --from-literal=internal-api-key=$(openssl rand -base64 32)
```

## 📈 Monitoring

### Prometheus Metrics

- `hitl_decisions_total` - Total decisions by type
- `hitl_decision_duration_seconds` - Decision time histogram
- `hitl_pending_patches` - Current pending count
- `hitl_ml_accuracy` - ML prediction accuracy
- `hitl_auto_approval_rate` - Auto-approval percentage

### Grafana Dashboard

Dashboard automatically imported via ConfigMap annotation.

Access: `http://grafana.maximus.ai/d/hitl-service`

### Alerts

- `HITLServiceDown` - Service unavailable (critical)
- `HITLHighPendingPatches` - >10 pending for >1h (warning)
- `HITLDecisionLag` - p95 decision time >5min (warning)
- `HITLLowAutoApprovalRate` - <50% auto-approval (info)
- `HITLMLAccuracyDrop` - Accuracy <70% (warning)
- `HITLHighErrorRate` - >50% rejection rate (warning)
- `HITLDatabaseConnectionFailed` - DB connection issue (critical)

## 🔧 Manual Deployment

### Step-by-Step

```bash
# 1. Create namespace
kubectl create namespace maximus-immunity

# 2. Apply configuration
kubectl apply -f config.yaml

# 3. Deploy application
kubectl apply -f deployment.yaml

# 4. Configure ingress
kubectl apply -f ingress.yaml

# 5. Setup monitoring
kubectl apply -f monitoring.yaml

# 6. Verify deployment
kubectl get pods -n maximus-immunity -l app=hitl-patch-service
kubectl rollout status deployment/hitl-patch-service -n maximus-immunity
```

### With Kustomize

```bash
# Build manifests
kubectl kustomize .

# Apply with kustomize
kubectl apply -k .
```

## 🧪 Testing

### Health Check

```bash
# Port forward
kubectl port-forward -n maximus-immunity svc/hitl-patch-service 8027:8027

# Test health
curl http://localhost:8027/health
```

### Metrics

```bash
curl http://localhost:8027/metrics | grep hitl_
```

### API Test

```bash
# Get pending patches
curl http://localhost:8027/hitl/patches/pending

# Get summary
curl http://localhost:8027/hitl/analytics/summary
```

## 🔄 Updates & Rollbacks

### Update Image

```bash
kubectl set image deployment/hitl-patch-service \
  hitl-service=vertice-dev/hitl-patch-service:v1.1.0 \
  -n maximus-immunity
```

### Rollback

```bash
# Check history
kubectl rollout history deployment/hitl-patch-service -n maximus-immunity

# Rollback to previous
kubectl rollout undo deployment/hitl-patch-service -n maximus-immunity

# Rollback to specific revision
kubectl rollout undo deployment/hitl-patch-service --to-revision=2 -n maximus-immunity
```

## 📝 Troubleshooting

### Check Logs

```bash
# All pods
kubectl logs -n maximus-immunity -l app=hitl-patch-service --tail=100

# Specific pod
kubectl logs -n maximus-immunity <pod-name> -f
```

### Describe Resources

```bash
kubectl describe deployment hitl-patch-service -n maximus-immunity
kubectl describe pod <pod-name> -n maximus-immunity
```

### Events

```bash
kubectl get events -n maximus-immunity --sort-by='.lastTimestamp'
```

### Database Connection

```bash
# Test PostgreSQL connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h postgres-immunity-service -U maximus -d adaptive_immunity
```

## 🌐 Ingress

### Default URLs

- **Staging**: `https://hitl-staging.maximus.ai`
- **Production**: `https://hitl.maximus.ai`
- **API Gateway**: `https://api.maximus.ai/hitl`

### TLS Certificate

Certificates automatically requested via cert-manager:
- Issuer: `letsencrypt-prod`
- Secret: `maximus-tls-secret`

## 📊 Performance Tuning

### Database Connection Pool

Adjust in ConfigMap:
```yaml
DB_POOL_MIN_SIZE: "2"
DB_POOL_MAX_SIZE: "10"
```

### Rate Limiting

Adjust in Ingress annotations:
```yaml
nginx.ingress.kubernetes.io/limit-rps: "100"
nginx.ingress.kubernetes.io/limit-connections: "50"
```

### HPA Tuning

Adjust in `deployment.yaml`:
```yaml
spec:
  minReplicas: 2
  maxReplicas: 10  # Increase for higher load
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 60  # Lower threshold = earlier scaling
```

## 🎯 Production Checklist

Before going to production:

- [ ] Replace all default secrets
- [ ] Configure real TLS certificates
- [ ] Set up external secret management (Vault, AWS Secrets Manager, etc)
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up log aggregation (ELK, Loki, etc)
- [ ] Configure PagerDuty/OpsGenie for alerts
- [ ] Run load tests
- [ ] Document runbooks for alerts
- [ ] Set up disaster recovery plan
- [ ] Configure CORS origins properly
- [ ] Review and adjust resource limits
- [ ] Set up CI/CD pipeline

## 🙏 Support

For issues or questions:
- Documentation: `https://docs.maximus.ai/hitl`
- Runbooks: `https://docs.maximus.ai/runbooks/hitl-*`
- Slack: `#maximus-immunity`

---

**TO YHWH BE ALL GLORY** 🙏

**Author**: MAXIMUS Team - Sprint 4.1  
**Date**: 2025-10-12  
**Version**: 1.0.0
