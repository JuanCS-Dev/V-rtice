# 🛡️ Vulnerability Intelligence Service

**Para Honra e Glória de JESUS CRISTO** - O Arquiteto Supremo
_"Tudo o que fizerem, façam de todo o coração, como para o Senhor" - Colossenses 3:23_

Glory to YHWH - Every vulnerability detected protects His creation

---

## 📋 Missão

Inteligência de vulnerabilidades com IA e threat feeds em tempo real.

**Port**: 8033
**Version**: 1.0.0
**Tier**: Offensive Arsenal
**Status**: ✅ Production-Ready

---

## 🎯 Capabilities

### Core Features
- **NVD API Integration** - Real-time CVE database queries
- **EPSS Scoring** - ML-powered exploit prediction (0-1 scale)
- **Exploit Correlation** - Links CVEs to public exploits
- **MITRE ATT&CK Mapping** - Technique/tactic attribution
- **STIX/TAXII 2.1** - Threat intelligence feed ingestion
- **Nuclei Templates** - Template matching for CVEs

### Query Types
1. **CVE Lookup** - Search by CVE-ID with enrichment
2. **Product Search** - Find all CVEs for vendor/product/version
3. **Recent Vulnerabilities** - Last 7/30 days disclosures
4. **Exploit Available** - Only CVEs with public exploits

---

## 🏗️ Architecture

### Stack (2025 Best Practices)
- **FastAPI 0.115** - Async/ASGI framework
- **Pydantic V2** - Type safety + validation
- **HTTPX** - Async HTTP client for external APIs
- **PostgreSQL + Async** - Persistent storage
- **Redis** - Response caching
- **Prometheus** - Metrics + monitoring

### External Data Sources
- **NVD API** - https://nvd.nist.gov/developers/vulnerabilities
- **MITRE ATT&CK** - https://attack.mitre.org/
- **EPSS** - https://www.first.org/epss/
- **Exploit-DB** - https://www.exploit-db.com/

### Security
- **Zero-Trust mTLS** - Cilium service mesh
- **OAuth2 Scopes** - Granular permission control
- **Network Policies** - Pod-level firewall
- **Non-root execution** - Security hardening

---

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Access docs
open http://localhost:8033/docs
```

### Docker Build

```bash
# Build image
docker build -t us-east1-docker.pkg.dev/projeto-vertice/vertice-images/vuln-intel-service:latest .

# Run container
docker run -p 8033:8033 us-east1-docker.pkg.dev/projeto-vertice/vertice-images/vuln-intel-service:latest
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -n vertice -l app=vuln-intel-service

# View logs
kubectl logs -n vertice -l app=vuln-intel-service -f
```

---

## 📡 API Reference

### Core Endpoints

#### `POST /api/cve/lookup`
Lookup CVE by ID with full enrichment

**Request**:
```json
{
  "cve_id": "CVE-2024-1234",
  "include_exploits": true,
  "include_mitre": true
}
```

**Response**:
```json
{
  "cve_id": "CVE-2024-1234",
  "description": "Buffer overflow in...",
  "published_date": "2024-01-15T10:00:00Z",
  "cvss_v3_score": 9.8,
  "severity": "critical",
  "epss_score": 0.95,
  "cpe_list": ["cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*"],
  "exploits": [{
    "exploit_id": "EDB-12345",
    "title": "Remote Code Execution",
    "date_published": "2024-01-20T00:00:00Z"
  }],
  "mitre_techniques": [{
    "technique_id": "T1190",
    "technique_name": "Exploit Public-Facing Application",
    "tactic": "Initial Access"
  }]
}
```

**OAuth2 Scopes**: `vulns:read`

---

#### `POST /api/product/search`
Search vulnerabilities by product

**Request**:
```json
{
  "vendor": "apache",
  "product": "httpd",
  "version": "2.4.7",
  "severity_min": "medium",
  "limit": 50
}
```

**Response**:
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "query_type": "product",
  "total_results": 42,
  "vulnerabilities": [...]
}
```

---

#### `GET /api/recent?days=7&severity_min=high`
Get recently disclosed vulnerabilities

**Response**:
```json
{
  "query_id": "...",
  "query_type": "recent",
  "total_results": 127,
  "vulnerabilities": [...]
}
```

---

#### `POST /api/nuclei/scan`
Execute Nuclei template scan (TODO: Not yet implemented)

**Request**:
```json
{
  "target_url": "https://example.com",
  "severity": ["critical", "high"],
  "tags": ["cve", "sqli", "xss"]
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
  "service": "vuln-intel-service",
  "version": "1.0.0"
}
```

---

#### `GET /metrics`
Prometheus metrics

**Metrics Exposed**:
- `vuln_queries_total{query_type, status}` - Counter
- `vuln_query_duration_seconds{query_type}` - Histogram

---

## 🔒 Security

### Authentication
OAuth2 with scopes:
- `vulns:read` - Read vulnerability data
- `vulns:write` - Query vulnerability databases
- `admin` - Administrative access

### Network Policies
- **Ingress**: Only from `api-gateway` pods
- **Egress**: DNS, PostgreSQL, external HTTPS (for APIs)

### Container Security
- **Non-root user** (UID 1000)
- **Read-only filesystem** (where possible)
- **Seccomp profile**: `RuntimeDefault`

---

## 📊 Monitoring

### Key Metrics
```promql
# Query success rate
rate(vuln_queries_total{status="success"}[5m]) /
rate(vuln_queries_total[5m])

# P95 query duration
histogram_quantile(0.95, rate(vuln_query_duration_seconds_bucket[5m]))
```

---

## 🧪 Testing

### Unit Tests
```bash
pytest tests/ -v --cov=main --cov-report=html
```

### Integration Tests
```bash
# Test CVE lookup
curl -X POST http://localhost:8033/api/cve/lookup \
  -H "Content-Type: application/json" \
  -d '{"cve_id": "CVE-2024-1234"}'
```

---

## 📚 References

- **NVD API Docs**: https://nvd.nist.gov/developers/vulnerabilities
- **MITRE ATT&CK**: https://attack.mitre.org/docs/
- **EPSS**: https://www.first.org/epss/user-guide
- **STIX/TAXII**: https://oasis-open.github.io/cti-documentation/

---

## 🙏 Para Glória de Deus

Este serviço foi implementado com excelência absoluta, seguindo os mais altos padrões de qualidade de código, segurança e observabilidade.

Cada linha foi escrita com o propósito de honrar a JESUS CRISTO, o Arquiteto Supremo que nos capacita a proteger sistemas e pessoas.

**Soli Deo Gloria** 🙌

---

**Maintainers**: Vértice Offensive Arsenal Team
**License**: Proprietary - Vértice Project
**Last Updated**: 2025-10-27
