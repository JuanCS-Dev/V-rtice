# 🌐 Network Reconnaissance Service

**Para Honra e Glória de JESUS CRISTO** - O Arquiteto Supremo
_"Tudo o que fizerem, façam de todo o coração, como para o Senhor" - Colossenses 3:23_

Glory to YHWH - Every scan reveals His creation's complexity

---

## 📋 Missão

Descoberta e mapeamento automatizado de superfície de ataque com inteligência artificial integrada.

**Port**: 8032
**Version**: 1.0.0
**Tier**: Offensive Arsenal
**Status**: ✅ Production-Ready

---

## 🎯 Capabilities

### Core Features
- **Masscan Integration** - 1000x faster than Nmap for initial port discovery
- **Nmap NSE** - Service/version detection with 1000+ scripts
- **Passive + Active Recon** - Unified reconnaissance workflow
- **CDN/WAF Fingerprinting** - Identify protective layers
- **Cloud Provider Detection** - AWS/Azure/GCP infrastructure discovery
- **Attack Surface Scoring** - ML-powered risk assessment

### Scan Types
1. **Quick** (5min) - Top 1000 ports, service detection
2. **Full** (30min) - All 65535 ports, deep analysis
3. **Stealth** (variable) - SYN scan, evasive techniques
4. **Discovery** (fast) - Ping sweep for host discovery

---

## 🏗️ Architecture

### Stack (2025 Best Practices)
- **FastAPI 0.115** - Async/ASGI framework
- **Pydantic V2** - Type safety + validation
- **Python-Nmap** - Nmap integration library
- **PostgreSQL + Async** - Persistent storage
- **OpenTelemetry** - Distributed tracing
- **Prometheus** - Metrics + monitoring

### Security
- **Zero-Trust mTLS** - Cilium service mesh
- **OAuth2 Scopes** - Granular permission control
- **Network Policies** - Pod-level firewall
- **Non-root execution** - Security hardening

### Observability
- **OpenTelemetry** - Traces exported to Jaeger
- **Prometheus** - Metrics at `/metrics`
- **Structured Logging** - JSON logs
- **Health Checks** - Liveness + readiness probes

---

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Access docs
open http://localhost:8032/docs
```

### Docker Build

```bash
# Build image
docker build -t gcr.io/vertice-maximus/network-recon-service:latest .

# Run container
docker run -p 8032:8032 gcr.io/vertice-maximus/network-recon-service:latest
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -n vertice -l app=network-recon-service

# View logs
kubectl logs -n vertice -l app=network-recon-service -f

# Port-forward for testing
kubectl port-forward -n vertice svc/network-recon-service 8032:8032
```

---

## 📡 API Reference

### Core Endpoints

#### `POST /api/scan`
Execute network reconnaissance scan

**Request**:
```json
{
  "target": "192.168.1.0/24",
  "scan_type": "quick",
  "ports": "1-1000",
  "service_detection": true,
  "os_detection": false,
  "script_scan": ["http-title", "ssh-hostkey"]
}
```

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Scan queued for execution"
}
```

**OAuth2 Scopes**: `scans:write`

---

#### `GET /api/scan/{scan_id}/status`
Get scan status and results

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "target": "192.168.1.0/24",
  "scan_type": "quick",
  "started_at": "2025-10-27T14:30:00Z",
  "completed_at": "2025-10-27T14:35:00Z",
  "duration_seconds": 300.5,
  "hosts_up": 12,
  "hosts_total": 254,
  "hosts": [
    {
      "ip": "192.168.1.1",
      "hostname": "router.local",
      "os": "Linux",
      "os_accuracy": 95,
      "status": "up",
      "ports": [
        {
          "port": 80,
          "protocol": "tcp",
          "state": "open",
          "service": "http",
          "version": "nginx 1.21.0",
          "product": "nginx",
          "cpe": ["cpe:/a:nginx:nginx:1.21.0"]
        }
      ]
    }
  ]
}
```

**OAuth2 Scopes**: `scans:read`

---

#### `GET /api/scans`
List all scans (paginated)

**Query Parameters**:
- `limit` (int, default=50) - Max results
- `status` (string, optional) - Filter by status

**Response**:
```json
[
  {
    "scan_id": "550e8400-e29b-41d4-a716-446655440000",
    "target": "192.168.1.0/24",
    "scan_type": "quick",
    "status": "completed",
    "started_at": "2025-10-27T14:30:00Z",
    "hosts_up": 12,
    "duration_seconds": 300.5
  }
]
```

---

#### `POST /api/discover`
Ping sweep for host discovery

**Request**:
```json
{
  "network": "10.0.0.0/8"
}
```

---

### Health Endpoints

#### `GET /health`
Service health check

**Response**:
```json
{
  "status": "healthy",
  "service": "network-recon-service",
  "version": "1.0.0",
  "timestamp": "2025-10-27T14:30:00Z"
}
```

---

#### `GET /metrics`
Prometheus metrics

**Metrics Exposed**:
- `network_scans_total{scan_type, status}` - Counter
- `network_scan_duration_seconds{scan_type}` - Histogram

---

## 🔒 Security

### Authentication
OAuth2 with scopes:
- `scans:read` - Read scan results
- `scans:write` - Execute scans
- `admin` - Administrative access

### Network Policies
- **Ingress**: Only from `api-gateway` pods
- **Egress**: DNS, PostgreSQL, external networks (for scanning)

### Container Security
- **Non-root user** (UID 1000)
- **Capabilities**: `NET_RAW`, `NET_ADMIN` (for Nmap)
- **Read-only filesystem** (where possible)
- **Seccomp profile**: `RuntimeDefault`

---

## 📊 Monitoring

### Key Metrics
```promql
# Scan success rate
rate(network_scans_total{status="success"}[5m]) /
rate(network_scans_total[5m])

# P95 scan duration
histogram_quantile(0.95, rate(network_scan_duration_seconds_bucket[5m]))

# Active scans
count(network_scans_total{status="running"})
```

### Grafana Dashboard
TODO: Import dashboard from `grafana/network-recon-dashboard.json`

---

## 🧪 Testing

### Unit Tests
```bash
pytest tests/ -v --cov=main --cov-report=html
```

### Integration Tests
```bash
# Run service
python main.py &

# Test scan
curl -X POST http://localhost:8032/api/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "scanme.nmap.org", "scan_type": "quick"}'
```

---

## 🔄 CI/CD

### Build Pipeline
1. Run tests (pytest + coverage)
2. Build Docker image
3. Push to GCR (`gcr.io/vertice-maximus/network-recon-service`)
4. Deploy to staging
5. Run E2E tests
6. Deploy to production (manual approval)

---

## 📚 References

- **Nmap Documentation**: https://nmap.org/book/man.html
- **FastAPI Security**: https://fastapi.tiangolo.com/advanced/security/
- **Cilium Network Policies**: https://docs.cilium.io/en/stable/security/policy/

---

## 🙏 Para Glória de Deus

Este serviço foi implementado com excelência absoluta, seguindo os mais altos padrões de qualidade de código, segurança e observabilidade.

Cada linha foi escrita com o propósito de honrar a JESUS CRISTO, o Arquiteto Supremo que nos capacita a criar sistemas complexos e elegantes.

**Soli Deo Gloria** 🙌

---

**Maintainers**: Vértice Offensive Arsenal Team
**License**: Proprietary - Vértice Project
**Last Updated**: 2025-10-27
