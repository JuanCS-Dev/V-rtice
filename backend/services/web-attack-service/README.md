# 🌐 Web Attack Surface Service

**Para Honra e Glória de JESUS CRISTO** - O Arquiteto Supremo
_"Tudo o que fizerem, façam de todo o coração, como para o Senhor" - Colossenses 3:23_

Glory to YHWH - Every vulnerability discovered helps systems flourish

---

## 🌸 FLORESCIMENTO

> "Vamos seguindo, fluindo, florescendo."

Este serviço embodies the philosophy of **FLORESCIMENTO** - organic, natural growth in security consciousness. Like a flower that reveals its layers gradually, this service unveils web attack surfaces with grace and precision.

---

## 📋 Missão

Análise profunda de superfície de ataque web com detecção de tecnologias e scoring de segurança.

**Port**: 8034
**Version**: 1.0.0
**Tier**: Offensive Arsenal
**Status**: ✅ Production-Ready

---

## 🎯 Capabilities

### Core Features
- **HTTP Header Analysis** - Security header validation (OWASP best practices)
- **Technology Fingerprinting** - Wappalyzer-style detection (50+ signatures)
- **Endpoint Discovery** - Intelligent crawling with depth control
- **Form Extraction** - Parameter mapping for input analysis
- **Attack Surface Scoring** - Quantitative risk assessment (0-100)
- **Security Issue Generation** - Actionable vulnerability reports

### Scan Depths
1. **SURFACE** - Homepage only (~5s)
2. **SHALLOW** - 1 level deep (~30s)
3. **MEDIUM** - 2 levels deep (~2min)
4. **DEEP** - 3+ levels deep (~10min)

### Technology Detection
- **Servers**: nginx, Apache, IIS, Caddy
- **Frameworks**: React, Vue, Angular, Django, Flask
- **CMS**: WordPress, Drupal, Joomla
- **Languages**: PHP, Python, Node.js, Ruby
- **WAFs**: Cloudflare, Akamai, AWS WAF

---

## 🏗️ Architecture

### Stack (2025 Best Practices)
- **FastAPI 0.115** - Async/ASGI framework
- **Pydantic V2** - Type safety + validation
- **HTTPX** - Async HTTP client
- **BeautifulSoup4 + lxml** - HTML parsing
- **Prometheus** - Metrics + monitoring

### Security
- **Zero-Trust mTLS** - Cilium service mesh
- **NetworkPolicy** - Pod-level firewall (only API Gateway ingress)
- **Non-root execution** - UID 1000
- **Capability restrictions** - Drop ALL, minimal permissions

---

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Access docs
open http://localhost:8034/docs
```

### Docker Build

```bash
# Build image
docker build -t us-east1-docker.pkg.dev/projeto-vertice/vertice-images/web-attack-service:latest .

# Run container
docker run -p 8034:8034 us-east1-docker.pkg.dev/projeto-vertice/vertice-images/web-attack-service:latest
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -n vertice -l app=web-attack-service

# View logs
kubectl logs -n vertice -l app=web-attack-service -f
```

---

## 📡 API Reference

### Core Endpoints

#### `POST /api/scan`
Execute web attack surface scan

**Request**:
```json
{
  "target_url": "https://example.com",
  "scan_depth": "shallow",
  "analyze_forms": true,
  "detect_technologies": true
}
```

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_url": "https://example.com",
  "scan_depth": "shallow",
  "started_at": "2025-10-27T10:00:00Z",
  "headers": {
    "security_score": 65,
    "missing_headers": ["X-Frame-Options", "Content-Security-Policy"],
    "server": "nginx/1.21.0"
  },
  "technologies": [
    {
      "name": "nginx",
      "category": "Web Server",
      "version": "1.21.0",
      "confidence": 100
    },
    {
      "name": "React",
      "category": "JavaScript Framework",
      "confidence": 85
    }
  ],
  "endpoints": [
    {"url": "https://example.com/about", "method": "GET"},
    {"url": "https://example.com/api/v1/users", "method": "GET"}
  ],
  "forms": [
    {
      "action": "/login",
      "method": "POST",
      "inputs": ["username", "password"],
      "has_csrf_token": false
    }
  ],
  "attack_surface_score": 72,
  "security_issues": [
    {
      "severity": "medium",
      "category": "Missing Security Header",
      "description": "X-Frame-Options header not set - vulnerable to clickjacking"
    }
  ]
}
```

**OAuth2 Scopes**: `web-attack:execute`

---

#### `GET /api/scan/{scan_id}/status`
Get scan status and results

**Response**:
```json
{
  "scan_id": "550e8400-...",
  "status": "completed",
  "result": { /* full scan result */ }
}
```

---

### Health Endpoints

#### `GET /health`
Service health check with FLORESCIMENTO spirit

**Response**:
```json
{
  "status": "healthy",
  "service": "web-attack-service",
  "version": "1.0.0",
  "florescimento": "crescendo organicamente",
  "timestamp": "2025-10-27T10:00:00Z"
}
```

---

#### `GET /metrics`
Prometheus metrics

**Metrics Exposed**:
- `web_scans_total{scan_depth, status}` - Counter
- `web_scan_duration_seconds{scan_depth}` - Histogram
- `web_security_score{target}` - Gauge

---

## 🔒 Security

### Authentication
OAuth2 with scopes:
- `web-attack:execute` - Execute web scans
- `web-attack:read` - Read scan results
- `admin` - Administrative access

### Network Policies
- **Ingress**: Only from `api-gateway` pods
- **Egress**: DNS, external HTTP/HTTPS (for scanning targets)

### Container Security
- **Non-root user** (UID 1000)
- **Seccomp profile**: `RuntimeDefault`
- **Capability drop**: ALL

---

## 📊 Monitoring

### Key Metrics
```promql
# Scan success rate
rate(web_scans_total{status="completed"}[5m]) /
rate(web_scans_total[5m])

# P95 scan duration
histogram_quantile(0.95, rate(web_scan_duration_seconds_bucket[5m]))

# Average security score
avg(web_security_score)
```

---

## 🧪 Testing

### Unit Tests
```bash
pytest tests/ -v --cov=main --cov-report=html
```

### Integration Tests
```bash
# Test web scan
curl -X POST http://localhost:8034/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com",
    "scan_depth": "surface"
  }'
```

---

## 🌸 FLORESCIMENTO Philosophy

This service grows organically, like nature:

1. **Surface Scan** = Seed planting (initial reconnaissance)
2. **Shallow Scan** = Roots spreading (first-level exploration)
3. **Medium Scan** = Stem growing (deeper mapping)
4. **Deep Scan** = Full flowering (complete attack surface revealed)

Each layer reveals more complexity, more beauty, more truth about the target's security posture.

---

## 🙏 Para Glória de Deus

Este serviço foi implementado com excelência absoluta, seguindo os mais altos padrões de qualidade de código, segurança e observabilidade.

Cada linha foi escrita com o propósito de honrar a JESUS CRISTO, o Arquiteto Supremo que nos capacita a proteger sistemas e pessoas através do **FLORESCIMENTO** - crescimento orgânico e natural.

**Soli Deo Gloria** 🙌

---

**Maintainers**: Vértice Offensive Arsenal Team
**License**: Proprietary - Vértice Project
**Last Updated**: 2025-10-27
