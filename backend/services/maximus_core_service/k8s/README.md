# Kubernetes Deployment - MAXIMUS AI 3.0

## Quick Deploy

```bash
# Create namespace and deploy all
kubectl apply -f all-in-one.yaml

# Or deploy individually
kubectl apply -f deployment.yaml
```

## Prerequisites

- Kubernetes 1.24+
- Ingress controller (nginx)
- Cert-manager (for TLS)
- PersistentVolume provisioner

## Configuration

Edit `all-in-one.yaml` secrets section:
- `postgres_url`
- `gemini_api_key`
- `anthropic_api_key`
- `openai_api_key`

## Scaling

```bash
kubectl scale deployment maximus-core --replicas=5 -n maximus-ai
```

## Status

```bash
kubectl get all -n maximus-ai
```
