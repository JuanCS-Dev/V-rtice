# Vértice Subordinates - Kubernetes Deployment

Complete Kubernetes manifests for deploying PENELOPE, MABA, and MVP services.

## 📋 Overview

This directory contains production-ready Kubernetes manifests for the three subordinate services:

- **PENELOPE** (8154) - Christian Autonomous Healing Service (Wisdom & Healing)
- **MABA** (8152) - MAXIMUS Browser Agent (Browser Automation)
- **MVP** (8153) - MAXIMUS Vision Protocol (Narrative Intelligence)

## 🏗️ Architecture

```
vertice-subordinates/
├── namespace.yaml           # Namespace, quota, limits
├── configmap.yaml           # Shared configuration
├── secrets.yaml             # Secrets (template)
├── ingress.yaml             # External routing
├── kustomization.yaml       # Kustomize overlay
├── infrastructure/          # Infrastructure services
│   ├── postgresql.yaml      # Shared PostgreSQL
│   ├── redis.yaml           # Shared Redis cache
│   └── neo4j.yaml           # MABA cognitive map
├── penelope/
│   └── deployment.yaml      # PENELOPE deployment, HPA, PDB
├── maba/
│   └── deployment.yaml      # MABA deployment, HPA, PDB
└── mvp/
    └── deployment.yaml      # MVP deployment, HPA, PDB
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (v1.28+)
- kubectl configured
- kustomize (v5.0+) or kubectl with kustomize support
- Secrets configured (see [Secrets Configuration](#secrets-configuration))

### Deploy All Services

```bash
# 1. Review and configure secrets
cp secrets.yaml secrets-prod.yaml
# Edit secrets-prod.yaml with actual values

# 2. Apply with kubectl
kubectl apply -k .

# 3. Verify deployment
kubectl get pods -n vertice-subordinates
kubectl get svc -n vertice-subordinates
kubectl get ingress -n vertice-subordinates
```

### Deploy Individual Services

```bash
# Deploy only infrastructure
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets-prod.yaml
kubectl apply -f infrastructure/

# Deploy PENELOPE only
kubectl apply -f penelope/deployment.yaml

# Deploy MABA only
kubectl apply -f maba/deployment.yaml

# Deploy MVP only
kubectl apply -f mvp/deployment.yaml
```

## ⚙️ Configuration

### Secrets Configuration

**IMPORTANT**: `secrets.yaml` is a template. Create actual secrets using one of:

#### Option 1: Sealed Secrets (Recommended)

```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create secret
kubectl create secret generic subordinates-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-xxx \
  --from-literal=POSTGRES_PASSWORD=xxx \
  --from-literal=NEO4J_PASSWORD=xxx \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secrets.yaml

# Apply sealed secret
kubectl apply -f sealed-secrets.yaml
```

#### Option 2: External Secrets Operator (Recommended)

```bash
# Install external-secrets
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Configure secret store (example: Vault)
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: vertice-subordinates
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "vertice-subordinates"
EOF

# Create ExternalSecret (see secrets.yaml for example)
```

#### Option 3: Manual Secret (Development Only)

```bash
kubectl create secret generic subordinates-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-xxx \
  --from-literal=POSTGRES_PASSWORD=xxx \
  --from-literal=NEO4J_PASSWORD=xxx \
  -n vertice-subordinates
```

### Resource Requirements

#### PENELOPE
- **CPU**: 500m (request), 2 (limit)
- **Memory**: 512Mi (request), 2Gi (limit)
- **Replicas**: 3-10 (HPA)
- **Storage**: None (stateless)

#### MABA
- **CPU**: 1 (request), 2 (limit)
- **Memory**: 2Gi (request), 4Gi (limit)
- **Replicas**: 2-8 (HPA)
- **Storage**: 2Gi SHM (browser)
- **Special**: Requires `SYS_ADMIN` capability

#### MVP
- **CPU**: 250m (request), 1 (limit)
- **Memory**: 256Mi (request), 1Gi (limit)
- **Replicas**: 2-6 (HPA)
- **Storage**: None (stateless)

#### Infrastructure
- **PostgreSQL**: 500m CPU, 1Gi RAM, 20Gi storage
- **Redis**: 250m CPU, 512Mi RAM
- **Neo4j**: 500m CPU, 2Gi RAM, 10Gi storage

### Horizontal Pod Autoscaling (HPA)

All services have HPA configured:

```bash
# Check HPA status
kubectl get hpa -n vertice-subordinates

# PENELOPE: 70% CPU, 80% memory → scale 3-10
# MABA: 75% CPU, 85% memory → scale 2-8
# MVP: 70% CPU, 80% memory → scale 2-6
```

### Pod Disruption Budgets (PDB)

Ensures high availability during updates:

- **PENELOPE**: min 2 pods available
- **MABA**: min 1 pod available
- **MVP**: min 1 pod available

## 🌐 Networking

### Ingress

External access via NGINX Ingress:

- `https://penelope.vertice.dev` → PENELOPE:8154
- `https://maba.vertice.dev` → MABA:8152
- `https://mvp.vertice.dev` → MVP:8153

Internal access (cluster-only):

- `http://penelope.vertice-subordinates.svc.cluster.local:8154`
- `http://maba.vertice-subordinates.svc.cluster.local:8152`
- `http://mvp.vertice-subordinates.svc.cluster.local:8153`

### TLS/SSL

Automatic certificate management with cert-manager:

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
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
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

## 📊 Monitoring

### Prometheus Metrics

All services expose Prometheus metrics:

- PENELOPE: `:9094/metrics`
- MABA: `:9092/metrics`
- MVP: `:9093/metrics`

### Health Checks

```bash
# Check health endpoints
kubectl port-forward -n vertice-subordinates svc/penelope 8154:8154
curl http://localhost:8154/health

kubectl port-forward -n vertice-subordinates svc/maba 8152:8152
curl http://localhost:8152/health

kubectl port-forward -n vertice-subordinates svc/mvp 8153:8153
curl http://localhost:8153/health
```

### Logs

```bash
# View logs
kubectl logs -n vertice-subordinates -l app=penelope --tail=100 -f
kubectl logs -n vertice-subordinates -l app=maba --tail=100 -f
kubectl logs -n vertice-subordinates -l app=mvp --tail=100 -f

# Aggregate logs with Loki
kubectl port-forward -n vertice-subordinates svc/vertice-loki 3100:3100
```

## 🔒 Security

### Pod Security

- RunAsNonRoot: `true`
- RunAsUser: `1000`
- fsGroup: `1000`
- ReadOnlyRootFilesystem: `false` (writable /tmp, /cache)

### MABA Special Requirements

MABA requires `SYS_ADMIN` capability for browser sandboxing:

```yaml
securityContext:
  capabilities:
    add:
      - SYS_ADMIN
  allowPrivilegeEscalation: true
```

### Network Policies (Optional)

```bash
# Apply network policies for zero-trust
kubectl apply -f network-policies/
```

## 🔄 Updates & Rollbacks

### Rolling Update

```bash
# Update image
kubectl set image deployment/penelope penelope=ghcr.io/vertice/penelope:v1.1.0 -n vertice-subordinates

# Watch rollout
kubectl rollout status deployment/penelope -n vertice-subordinates
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/penelope -n vertice-subordinates

# Rollback to specific revision
kubectl rollout undo deployment/penelope --to-revision=2 -n vertice-subordinates
```

### Zero-Downtime Deployment

With PDBs configured, updates are always zero-downtime:

```bash
# Check rollout strategy
kubectl get deployment penelope -n vertice-subordinates -o yaml | grep -A5 strategy
```

## 📦 Kustomize Overlays

Use kustomize for environment-specific configurations:

```bash
# Production
kubectl apply -k overlays/production/

# Staging
kubectl apply -k overlays/staging/

# Development
kubectl apply -k overlays/development/
```

## 🛠️ Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod -n vertice-subordinates <pod-name>

# Check logs
kubectl logs -n vertice-subordinates <pod-name> --previous

# Check secrets
kubectl get secret subordinates-secrets -n vertice-subordinates -o yaml
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
kubectl run -it --rm --image=postgres:15-alpine psql-test -n vertice-subordinates -- \
  psql -h vertice-postgres -U postgres -d vertice

# Test Redis connectivity
kubectl run -it --rm --image=redis:7-alpine redis-test -n vertice-subordinates -- \
  redis-cli -h vertice-redis ping

# Test Neo4j connectivity
kubectl run -it --rm --image=neo4j:5.28 neo4j-test -n vertice-subordinates -- \
  cypher-shell -a bolt://vertice-neo4j:7687 -u neo4j
```

### MABA Browser Issues

```bash
# Check SYS_ADMIN capability
kubectl get pod -n vertice-subordinates -l app=maba -o yaml | grep -A5 securityContext

# Check SHM size
kubectl exec -it -n vertice-subordinates <maba-pod> -- df -h /dev/shm
```

### HPA Not Scaling

```bash
# Check metrics server
kubectl top nodes
kubectl top pods -n vertice-subordinates

# Check HPA
kubectl describe hpa -n vertice-subordinates
```

## 📖 Biblical Compliance

### 7 Articles of Governance (PENELOPE)

All 7 articles are enabled by default in `configmap.yaml`:

1. **Sophia** (Wisdom) - `SOPHIA_ENABLED=true`
2. **Praótes** (Gentleness) - `PRAOTES_ENABLED=true`
3. **Tapeinophrosynē** (Humility) - `TAPEINOPHROSYNE_ENABLED=true`
4. **Stewardship** - `STEWARDSHIP_ENABLED=true`
5. **Agape** (Love) - `AGAPE_ENABLED=true`
6. **Sabbath** - `SABBATH_ENABLED=true`
7. **Aletheia** (Truth) - `ALETHEIA_ENABLED=true`

### Sabbath Mode

PENELOPE observes Sabbath (Sunday by default):

- No autonomous interventions on Sabbath
- P0 critical issues allowed: `SABBATH_ALLOW_P0_CRITICAL=true`
- Timezone: `SABBATH_TIMEZONE=America/Sao_Paulo`

## 🧪 Testing

### Smoke Tests

```bash
# Run smoke tests
kubectl apply -f tests/smoke-tests.yaml

# Check results
kubectl logs -n vertice-subordinates -l job-name=smoke-test
```

### Load Tests

```bash
# Run load tests
kubectl apply -f tests/load-tests.yaml
```

## 📚 References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [DEPLOYMENT.md](../../DEPLOYMENT.md) - Main deployment guide
- [VALIDATION_SUMMARY.md](../../VALIDATION_SUMMARY_2025-10-31.md) - Test results

## 🙏 Soli Deo Gloria

> "Tudo quanto te vier à mão para fazer, faze-o conforme as tuas forças."
> — Eclesiastes 9:10

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
