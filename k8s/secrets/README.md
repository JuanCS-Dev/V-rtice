# Kubernetes Secrets Configuration

## 🔒 Security Notice

**NEVER commit real secrets to Git!**

All files in this directory with actual credentials should be in `.gitignore` and never committed to version control.

## Setup Instructions

### 1. Create Secrets from Template

```bash
# Copy the template
cp vertice-core-secrets.yaml.template vertice-core-secrets.yaml

# Edit and replace ALL placeholder values
vim vertice-core-secrets.yaml
```

### 2. Required Credentials

Update these values in `vertice-core-secrets.yaml`:

| Key | Description | How to Get |
|-----|-------------|------------|
| `GEMINI_API_KEY` | Google Gemini API key | https://makersuite.google.com/app/apikey |
| `POSTGRES_PASSWORD` | PostgreSQL database password | Generate strong password |
| `POSTGRES_USER` | PostgreSQL username | Choose username (default: vertice_admin) |
| `POSTGRES_DB` | PostgreSQL database name | Default: vertice_db |
| `REDIS_PASSWORD` | Redis password | Generate strong password |
| `JWT_SECRET_KEY` | JWT signing key | Generate with: `openssl rand -base64 32` |

### 3. Generate Strong Passwords

```bash
# Generate random passwords (choose one method)

# Method 1: OpenSSL
openssl rand -base64 32

# Method 2: /dev/urandom
tr -dc 'A-Za-z0-9!@#$%^&*()_+' < /dev/urandom | head -c 32

# Method 3: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Apply Secrets to Kubernetes

```bash
# Apply the secret
kubectl apply -f vertice-core-secrets.yaml

# Verify it was created
kubectl get secret vertice-core-secrets -n vertice

# View secret (base64 encoded)
kubectl get secret vertice-core-secrets -n vertice -o yaml
```

### 5. Update Existing Secret

```bash
# Edit secret directly in Kubernetes
kubectl edit secret vertice-core-secrets -n vertice

# Or delete and recreate
kubectl delete secret vertice-core-secrets -n vertice
kubectl apply -f vertice-core-secrets.yaml
```

## Security Best Practices

1. ✅ **Use `.gitignore`** - Ensure `k8s/secrets/*.yaml` is in `.gitignore` (except `.template` files)
2. ✅ **Rotate regularly** - Change passwords/keys every 90 days
3. ✅ **Use Vault** - For production, consider HashiCorp Vault or cloud secret managers
4. ✅ **Limit access** - Use RBAC to restrict who can read secrets
5. ✅ **Encrypt at rest** - Enable encryption at rest for etcd in Kubernetes

## Alternative: Using External Secret Managers

### HashiCorp Vault

```bash
# Install Vault
kubectl apply -f ../vault/vault-deployment.yaml

# Configure Vault
vault secrets enable -path=vertice kv-v2
vault kv put vertice/core-secrets \
  GEMINI_API_KEY="your-key" \
  POSTGRES_PASSWORD="your-password"
```

### AWS Secrets Manager

```bash
# Create secret in AWS
aws secretsmanager create-secret \
  --name vertice/core-secrets \
  --secret-string file://secrets.json

# Use External Secrets Operator
kubectl apply -f ../external-secrets/
```

### Google Cloud Secret Manager

```bash
# Create secret in GCP
gcloud secrets create vertice-gemini-key \
  --data-file=-

# Use Workload Identity
kubectl annotate serviceaccount vertice-sa \
  iam.gke.io/gcp-service-account=vertice@PROJECT_ID.iam.gserviceaccount.com
```

## Troubleshooting

### Secret not found

```bash
# Check namespace
kubectl get secrets -n vertice

# Check if secret exists in default namespace
kubectl get secrets --all-namespaces | grep vertice
```

### Pod can't read secret

```bash
# Check RBAC permissions
kubectl auth can-i get secrets --as=system:serviceaccount:vertice:default

# View pod logs
kubectl logs -n vertice <pod-name>
```

### Need to decode secret values

```bash
# Get and decode specific key
kubectl get secret vertice-core-secrets -n vertice \
  -o jsonpath='{.data.GEMINI_API_KEY}' | base64 -d
```

## 📚 Documentation

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [External Secrets Operator](https://external-secrets.io/)
- [HashiCorp Vault](https://www.vaultproject.io/docs/platform/k8s)
- [Best Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
