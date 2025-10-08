# Active Immune Core - Kubernetes Deployment

Production-grade Kubernetes deployment manifests for Active Immune Core.

**REGRA DE OURO**: NO MOCK, NO PLACEHOLDER, NO TODO - 100% Production-Ready.

---

## 📋 Prerequisites

### Required
- Kubernetes cluster (v1.24+)
- kubectl configured
- Storage provisioner (for PersistentVolumes)
- Dependencies running:
  - Kafka cluster
  - Redis cluster
  - PostgreSQL database

### Optional
- Metrics Server (for HPA)
- Ingress Controller (nginx, traefik, etc.)
- Cert-Manager (for TLS certificates)
- CNI with NetworkPolicy support (Calico, Cilium, Weave)

---

## 🚀 Quick Start

### 1. Create Namespace
```bash
kubectl apply -f k8s/00-namespace.yaml
```

### 2. Create ConfigMap and Secrets
```bash
# Edit secrets BEFORE applying!
# Change ACTIVE_IMMUNE_POSTGRES_PASSWORD and JWT_SECRET
vim k8s/02-secret.yaml

# Apply configuration
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
```

### 3. Create Storage
```bash
kubectl apply -f k8s/05-pvc.yaml

# Verify PVCs are bound
kubectl get pvc -n active-immune
```

### 4. Deploy Application
```bash
kubectl apply -f k8s/03-deployment.yaml
kubectl apply -f k8s/04-service.yaml

# Watch deployment
kubectl rollout status deployment/active-immune-core -n active-immune

# Check pods
kubectl get pods -n active-immune
```

### 5. (Optional) Enable Auto-Scaling
```bash
# Requires metrics-server
kubectl apply -f k8s/06-hpa.yaml

# Check HPA status
kubectl get hpa -n active-immune
```

### 6. (Optional) Enable Network Policies
```bash
# Requires CNI with NetworkPolicy support
kubectl apply -f k8s/07-networkpolicy.yaml

# Verify policies
kubectl get networkpolicy -n active-immune
```

### 7. (Optional) External Access via Ingress
```bash
# Edit hostname in 08-ingress.yaml
vim k8s/08-ingress.yaml

# Apply ingress
kubectl apply -f k8s/08-ingress.yaml

# Get ingress IP
kubectl get ingress -n active-immune
```

---

## 📦 Manifest Files

| File | Purpose | Required |
|------|---------|----------|
| `00-namespace.yaml` | Namespace isolation | ✅ Yes |
| `01-configmap.yaml` | Non-sensitive config | ✅ Yes |
| `02-secret.yaml` | Passwords, tokens | ✅ Yes |
| `03-deployment.yaml` | Application deployment | ✅ Yes |
| `04-service.yaml` | Load balancing | ✅ Yes |
| `05-pvc.yaml` | Persistent storage | ✅ Yes |
| `06-hpa.yaml` | Auto-scaling | ⚠️ Optional |
| `07-networkpolicy.yaml` | Network security | ⚠️ Optional |
| `08-ingress.yaml` | External access | ⚠️ Optional |

---

## 🔍 Verification

### Check Health
```bash
# Port-forward to access locally
kubectl port-forward svc/active-immune-core 8200:8200 -n active-immune

# Test health endpoint
curl http://localhost:8200/health
```

### Check Logs
```bash
# Real-time logs
kubectl logs -f deployment/active-immune-core -n active-immune

# Last 100 lines
kubectl logs --tail=100 deployment/active-immune-core -n active-immune

# All pods
kubectl logs -l app=active-immune-core -n active-immune
```

### Check Events
```bash
kubectl get events -n active-immune --sort-by='.lastTimestamp'
```

### Check Resources
```bash
# Pod resource usage
kubectl top pods -n active-immune

# Deployment status
kubectl get deployment active-immune-core -n active-immune -o wide
```

---

## ⚙️ Configuration

### Environment Variables (ConfigMap)

Modify `k8s/01-configmap.yaml` to adjust:

- **Service Config**: Port, log level, debug mode
- **Kafka**: Bootstrap servers, topics, compression
- **Redis**: URL, TTL, max connections
- **PostgreSQL**: Host, port, database, pool size
- **External Services**: URLs for Treg, Memory, Adaptive, etc.
- **Homeostasis**: Temperature thresholds, energy decay
- **Agent Limits**: Max agents, clones, lifespans

### Secrets (Secret)

⚠️ **CRITICAL**: Change these in `k8s/02-secret.yaml` BEFORE production deployment:

- `ACTIVE_IMMUNE_POSTGRES_PASSWORD`: PostgreSQL password
- `ACTIVE_IMMUNE_API_KEY`: API key (if needed)
- `JWT_SECRET`: JWT signing secret

**Best Practice**: Use a secrets management tool:
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager
- Sealed Secrets

### Resource Limits

In `k8s/03-deployment.yaml`:

```yaml
resources:
  requests:
    cpu: "500m"      # 0.5 CPU cores
    memory: "512Mi"  # 512 MB RAM
  limits:
    cpu: "2000m"     # 2 CPU cores max
    memory: "2Gi"    # 2 GB RAM max
```

Adjust based on your workload and cluster capacity.

### Scaling

#### Manual Scaling
```bash
# Scale to 5 replicas
kubectl scale deployment/active-immune-core --replicas=5 -n active-immune
```

#### Auto-Scaling (HPA)
Edit `k8s/06-hpa.yaml`:
- `minReplicas`: Minimum pods (default: 3)
- `maxReplicas`: Maximum pods (default: 10)
- `averageUtilization`: CPU/Memory threshold (default: 70%/80%)

---

## 🔄 Updates & Rollouts

### Rolling Update
```bash
# Update image
kubectl set image deployment/active-immune-core \
  active-immune-core=active-immune-core:2.0.0 \
  -n active-immune

# Watch rollout
kubectl rollout status deployment/active-immune-core -n active-immune
```

### Rollback
```bash
# Undo last deployment
kubectl rollout undo deployment/active-immune-core -n active-immune

# Rollback to specific revision
kubectl rollout undo deployment/active-immune-core --to-revision=2 -n active-immune
```

### Rollout History
```bash
kubectl rollout history deployment/active-immune-core -n active-immune
```

---

## 🛡️ Security

### Pod Security Context
- `runAsNonRoot: true` - Runs as user 1000
- `readOnlyRootFilesystem: false` - Allows writes to volumes
- `allowPrivilegeEscalation: false` - No privilege escalation
- `capabilities.drop: ALL` - Drops all Linux capabilities

### Network Policies
Network policies (if enabled) restrict:
- **Ingress**: Only from API Gateway, Prometheus, same namespace
- **Egress**: Only to Kafka, Redis, PostgreSQL, DNS, Vertice services

### TLS/HTTPS
For external access, configure TLS in `k8s/08-ingress.yaml` with:
- Valid TLS certificate (Let's Encrypt recommended)
- HTTPS redirect enabled
- Security headers configured

---

## 📊 Monitoring

### Prometheus Metrics
Service automatically exposes Prometheus metrics at `/metrics`:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8200"
  prometheus.io/path: "/metrics"
```

### Grafana Dashboards
Import dashboards from `monitoring/grafana/dashboards/` for:
- Agent lifecycle metrics
- Cytokine signaling stats
- Homeostatic control metrics
- External service circuit breaker states

---

## 🐛 Troubleshooting

### Pod Not Starting

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n active-immune

# Check init containers
kubectl logs <pod-name> -c wait-for-kafka -n active-immune
kubectl logs <pod-name> -c wait-for-redis -n active-immune
kubectl logs <pod-name> -c wait-for-postgres -n active-immune
```

### CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n active-immune --previous

# Check liveness/readiness probes
kubectl describe pod <pod-name> -n active-immune | grep -A 10 "Liveness\|Readiness"
```

### Service Not Reachable

```bash
# Check service endpoints
kubectl get endpoints active-immune-core -n active-immune

# Check network policies
kubectl describe networkpolicy -n active-immune

# Test from another pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n active-immune \
  -- curl http://active-immune-core:8200/health
```

### PVC Pending

```bash
# Check PVC status
kubectl describe pvc active-immune-data-pvc -n active-immune

# Check storage classes
kubectl get storageclass

# Check if provisioner is running
kubectl get pods -n kube-system | grep provisioner
```

---

## 🧹 Cleanup

### Delete Everything
```bash
# Delete all resources (keeps PVCs)
kubectl delete -f k8s/08-ingress.yaml
kubectl delete -f k8s/07-networkpolicy.yaml
kubectl delete -f k8s/06-hpa.yaml
kubectl delete -f k8s/04-service.yaml
kubectl delete -f k8s/03-deployment.yaml
kubectl delete -f k8s/02-secret.yaml
kubectl delete -f k8s/01-configmap.yaml

# Delete PVCs (THIS DELETES DATA!)
kubectl delete -f k8s/05-pvc.yaml

# Delete namespace
kubectl delete -f k8s/00-namespace.yaml
```

### Quick Delete
```bash
# Delete namespace (cascading delete)
kubectl delete namespace active-immune

# WARNING: This deletes ALL resources in the namespace including PVCs!
```

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

---

**NO MOCK, NO PLACEHOLDER, NO TODO** - Production-ready deployment.
