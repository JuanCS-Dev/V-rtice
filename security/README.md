# Vértice Subordinates - Security Hardening

Complete security hardening for PENELOPE, MABA, and MVP services.

## 📋 Overview

This directory contains comprehensive security policies, RBAC configurations, and scanning tools for production-grade security.

## 🔒 Security Layers

### 1. Network Security (Zero Trust)
- **Network Policies**: Default deny-all with explicit allow rules
- **Service Mesh**: Ready for Istio/Linkerd integration
- **mTLS**: Mutual TLS between services
- **Ingress**: NGINX with rate limiting and TLS termination

### 2. Pod Security
- **Pod Security Standards**: Baseline for infrastructure, Restricted for services
- **Pod Security Policies**: Enforced via admission controllers
- **Security Contexts**: Non-root, read-only filesystem, capability dropping
- **OPA Gatekeeper**: Policy enforcement at admission time

### 3. Access Control (RBAC)
- **Service Accounts**: Dedicated SA for each service
- **Least Privilege**: Minimal permissions (read ConfigMaps, Secrets)
- **Role-Based Access**: Granular RBAC policies
- **Pod Security Policy**: Enforced via RBAC

### 4. Vulnerability Scanning
- **Trivy**: Container and filesystem scanning
- **Bandit**: Python code security analysis
- **Snyk**: Dependency vulnerability scanning
- **OWASP Dependency Check**: Known vulnerabilities

### 5. Secrets Management
- **Sealed Secrets**: Encrypted secrets in git
- **External Secrets Operator**: Integration with Vault/AWS Secrets Manager
- **Secret Rotation**: Automated rotation support
- **Encryption at Rest**: etcd encryption

## 🚀 Quick Start

### Apply Network Policies

```bash
# Apply zero-trust network policies
kubectl apply -f security/policies/network-policies.yaml

# Verify policies
kubectl get networkpolicies -n vertice-subordinates
```

### Apply Pod Security

```bash
# Apply Pod Security Policies
kubectl apply -f security/policies/pod-security.yaml

# Apply Pod Security Standards to namespace
kubectl label namespace vertice-subordinates \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

### Apply RBAC

```bash
# Apply RBAC configurations
kubectl apply -f security/rbac/rbac.yaml

# Verify service accounts
kubectl get sa -n vertice-subordinates
kubectl get roles -n vertice-subordinates
kubectl get rolebindings -n vertice-subordinates
```

### Install OPA Gatekeeper

```bash
# Install OPA Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml

# Apply constraints
kubectl apply -f security/policies/pod-security.yaml

# Verify constraints
kubectl get constraints
```

## 🛡️ Security Policies

### Network Policies

#### Default Deny All
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: vertice-subordinates
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

#### PENELOPE Allowed Traffic
- **Ingress**: NGINX Ingress (8154), Prometheus (9094), Internal services
- **Egress**: DNS (53), PostgreSQL (5432), Redis (6379), Anthropic API (443)

#### MABA Allowed Traffic
- **Ingress**: NGINX Ingress (8152), Prometheus (9092), Internal services
- **Egress**: DNS (53), PostgreSQL (5432), Redis (6379), Neo4j (7687), HTTP/HTTPS (80/443), Anthropic API (443)

#### MVP Allowed Traffic
- **Ingress**: NGINX Ingress (8153), Prometheus (9093), Internal services
- **Egress**: DNS (53), PostgreSQL (5432), Redis (6379), Prometheus (9090), Anthropic API (443)

### Pod Security Standards

| Service | Standard | RunAsNonRoot | Capabilities | Privilege Escalation |
|---------|----------|--------------|--------------|---------------------|
| PENELOPE | Restricted | ✅ | DROP ALL | ❌ |
| MABA | Privileged* | ✅ | +SYS_ADMIN | ✅** |
| MVP | Restricted | ✅ | DROP ALL | ❌ |

\* MABA requires SYS_ADMIN for browser sandboxing
\** Controlled privilege escalation only

### RBAC Permissions

All services have minimal permissions:

```yaml
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch"]
```

## 🔍 Vulnerability Scanning

### Trivy Scanner

```bash
# Scan container images
trivy image ghcr.io/vertice/penelope:latest
trivy image ghcr.io/vertice/maba:latest
trivy image ghcr.io/vertice/mvp:latest

# Scan filesystem
trivy fs backend/services/penelope_service/
trivy fs backend/services/maba_service/
trivy fs backend/services/mvp_service/

# Scan with config
trivy --config security/scanning/trivy-config.yaml fs .
```

### Bandit Python Security

```bash
# Scan PENELOPE
bandit -r backend/services/penelope_service/ \
  -c security/scanning/bandit-config.yaml \
  -f json -o bandit-penelope.json

# Scan MABA
bandit -r backend/services/maba_service/ \
  -c security/scanning/bandit-config.yaml \
  -f json -o bandit-maba.json

# Scan MVP
bandit -r backend/services/mvp_service/ \
  -c security/scanning/bandit-config.yaml \
  -f json -o bandit-mvp.json
```

### OWASP Dependency Check

```bash
# Install dependency-check
wget https://github.com/jeremylong/DependencyCheck/releases/download/v8.4.0/dependency-check-8.4.0-release.zip
unzip dependency-check-8.4.0-release.zip

# Scan Python dependencies
./dependency-check/bin/dependency-check.sh \
  --scan backend/services/penelope_service/requirements.txt \
  --format JSON \
  --out dependency-check-penelope.json
```

## 🔐 Secrets Management

### Option 1: Sealed Secrets (Recommended)

```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Seal a secret
kubectl create secret generic subordinates-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-xxx \
  --from-literal=POSTGRES_PASSWORD=xxx \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > k8s/subordinates/sealed-secrets.yaml

# Apply sealed secret
kubectl apply -f k8s/subordinates/sealed-secrets.yaml
```

### Option 2: External Secrets Operator

```bash
# Install external-secrets
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Configure Vault backend
kubectl apply -f - <<EOF
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

# Create ExternalSecret
kubectl apply -f k8s/subordinates/secrets.yaml
```

### Option 3: AWS Secrets Manager

```bash
# Install AWS Secrets Manager CSI driver
kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml

# Create SecretProviderClass
kubectl apply -f - <<EOF
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vertice-secrets
  namespace: vertice-subordinates
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "vertice/subordinates/anthropic-api-key"
        objectType: "secretsmanager"
      - objectName: "vertice/subordinates/postgres-password"
        objectType: "secretsmanager"
EOF
```

## 🌐 Service Mesh Integration

### Istio

```bash
# Install Istio
istioctl install --set profile=production -y

# Enable sidecar injection
kubectl label namespace vertice-subordinates istio-injection=enabled

# Apply Istio policies
kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: vertice-subordinates
spec:
  mtls:
    mode: STRICT
EOF
```

### Linkerd

```bash
# Install Linkerd
linkerd install | kubectl apply -f -

# Inject Linkerd
kubectl get deploy -n vertice-subordinates -o yaml | \
  linkerd inject - | \
  kubectl apply -f -

# Verify mTLS
linkerd viz stat deploy -n vertice-subordinates
```

## 📊 Security Monitoring

### Falco Runtime Security

```bash
# Install Falco
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set falco.grpc.enabled=true \
  --set falco.grpcOutput.enabled=true

# View Falco alerts
kubectl logs -n falco -l app.kubernetes.io/name=falco
```

### Kube-bench CIS Compliance

```bash
# Run kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# View results
kubectl logs job/kube-bench
```

## 🧪 Security Testing

### Penetration Testing

```bash
# Run kube-hunter
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-hunter/main/job.yaml

# View results
kubectl logs job/kube-hunter
```

### Security Audit

```bash
# Audit RBAC permissions
kubectl auth can-i --list --namespace=vertice-subordinates --as=system:serviceaccount:vertice-subordinates:penelope

# Audit network policies
kubectl get networkpolicies -n vertice-subordinates -o yaml

# Audit pod security
kubectl get psp
kubectl get pods -n vertice-subordinates -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'
```

## 🚨 Incident Response

### Security Breach Protocol

1. **Isolate**: Apply network policy to isolate compromised pod
2. **Investigate**: Collect logs, events, and forensics
3. **Remediate**: Patch vulnerability, rotate secrets
4. **Recover**: Redeploy from known-good image
5. **Review**: Post-mortem and policy updates

```bash
# Isolate pod
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-compromised-pod
  namespace: vertice-subordinates
spec:
  podSelector:
    matchLabels:
      pod-name: compromised-pod
  policyTypes:
    - Ingress
    - Egress
EOF

# Collect forensics
kubectl logs -n vertice-subordinates compromised-pod > forensics.log
kubectl describe pod -n vertice-subordinates compromised-pod > forensics-describe.txt

# Rotate secrets
kubectl delete secret subordinates-secrets -n vertice-subordinates
# Recreate with new values
```

## 📖 Compliance

### LGPD (Brazilian Data Protection)
- ✅ PII detection enabled (MVP)
- ✅ Data encryption at rest
- ✅ Data encryption in transit
- ✅ Audit logging

### SOC 2
- ✅ Access controls (RBAC)
- ✅ Encryption (TLS, etcd)
- ✅ Monitoring (Prometheus, Falco)
- ✅ Incident response

### OWASP Top 10
- ✅ Injection: Input validation, parameterized queries
- ✅ Broken Auth: RBAC, service accounts
- ✅ Sensitive Data: Secrets management, encryption
- ✅ XXE: XML parsing disabled
- ✅ Broken Access: Network policies, RBAC
- ✅ Security Misconfig: OPA Gatekeeper, PSP
- ✅ XSS: Input sanitization
- ✅ Deserialization: Pickle disabled
- ✅ Known Vulns: Trivy, Bandit scanning
- ✅ Logging: Centralized logging (Loki)

## 🙏 Biblical Principles

### Stewardship (Mordomia)
> "Each of you should use whatever gift you have received to serve others, as faithful stewards of God's grace in its various forms." - 1 Peter 4:10

Security is stewardship of user data and system resources.

### Wisdom (Sophia)
> "The fear of the LORD is the beginning of wisdom, and knowledge of the Holy One is understanding." - Proverbs 9:10

Security policies embody wisdom through defense-in-depth.

### Truth (Aletheia)
> "Then you will know the truth, and the truth will set you free." - John 8:32

Transparent security practices and honest vulnerability disclosure.

## 📚 References

- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [OWASP Kubernetes Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [NSA/CISA Kubernetes Hardening Guide](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF)

---

🙏 Soli Deo Gloria

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
