# ENDPOINTS DETALHADOS - VÉRTICE API GATEWAY v3.3.1

## Lista Completa de Todos os Endpoints

### 1. HEALTH & MONITORING (5)

```
GET  /                       Root endpoint
GET  /health                 Aggregated health check
GET  /api/v1/                V1 root endpoint
GET  /api/v1/health          V1 health check
GET  /metrics                Prometheus metrics (text/plain)
```

### 2. AUTHENTICATION & AUTHORIZATION (5)

```
POST /auth/token                  Login (OAuth2PasswordRequestForm)
POST /auth/google                 Google OAuth authentication
POST /auth/logout                 Logout session
GET  /auth/me                     Get current user profile
GET  /auth/verify-token           Verify JWT token validity
```

### 3. CYBER SECURITY (8)

```
POST /cyber/network-scan           Start network scan (Rate: 5/min, Timeout: 60s)
GET  /cyber/port-analysis          Analyze open ports
GET  /cyber/file-integrity         Check file integrity
GET  /cyber/process-analysis       Analyze running processes
GET  /cyber/certificate-check      Check SSL/TLS certificates
GET  /cyber/security-config        Get security configuration
GET  /cyber/security-logs          Retrieve security logs
GET  /cyber/health                 Health check for cyber service
```

### 4. NETWORK SCANNING - NMAP (3)

```
POST /api/nmap/scan              Start nmap scan
GET  /api/nmap/profiles          List available scan profiles
GET  /nmap/health                Health check
```

### 5. OSINT - DOMAIN INTELLIGENCE (2)

```
POST /api/domain/analyze         Analyze domain (WHOIS, DNS, MX, etc)
GET  /domain/health              Health check
```

### 6. OSINT - IP INTELLIGENCE (4)

```
POST /api/ip/analyze             Analyze IP address (GeoIP, ASN, reputation)
GET  /api/ip/my-ip               Get client's public IP
POST /api/ip/analyze-my-ip       Analyze client's IP
GET  /ip/health                  Health check
```

### 7. NETWORK MONITORING (2)

```
GET  /api/network/monitor        Monitor network traffic/anomalies
GET  /network/health             Health check
```

### 8. OSINT - GOOGLE (8)

```
POST /api/google/search/basic          Basic Google search
POST /api/google/search/advanced       Advanced Google search with operators
POST /api/google/search/documents      Search for documents (PDF, DOC, XLS)
POST /api/google/search/images         Reverse image search
POST /api/google/search/social         Search social media profiles
GET  /api/google/dorks/patterns        List Google dork patterns
GET  /api/google/stats                 Statistics about search results
GET  /api/google/health                Health check
```

### 9. OSINT - GENERAL (7)

```
POST /api/email/analyze          Analyze email address
POST /api/phone/analyze          Analyze phone number
POST /api/image/analyze          Analyze image
POST /api/social/profile         Analyze social media profile
POST /api/username/search        Search username across platforms
POST /api/search/comprehensive   Comprehensive OSINT search
POST /api/investigate/auto       Automated investigation workflow
GET  /api/osint/stats            OSINT statistics
GET  /api/osint/health           Health check
```

### 10. MALWARE ANALYSIS (4)

```
POST /api/malware/analyze-file   Analyze file for malware
POST /api/malware/analyze-hash   Lookup file hash (MD5, SHA1, SHA256)
POST /api/malware/analyze-url    Analyze URL for malware
GET  /malware/health             Health check
```

### 11. THREAT INTELLIGENCE (2)

```
POST /api/threat-intel/check     Check if indicator is known threat
GET  /threat-intel/health        Health check
```

### 12. SSL/TLS MONITORING (2)

```
POST /api/ssl/check              Check SSL/TLS certificate validity
GET  /ssl/health                 Health check
```

### 13. DEFENSIVE SYSTEMS - BEHAVIORAL (7)

```
POST /api/defensive/behavioral/analyze              Analyze single behavior
POST /api/defensive/behavioral/analyze-batch        Batch analyze behaviors
POST /api/defensive/behavioral/train-baseline       Train baseline model
GET  /api/defensive/behavioral/baseline-status      Get baseline status
GET  /api/defensive/behavioral/metrics              Get behavioral metrics
POST /api/defensive/traffic/analyze                 Analyze traffic patterns
POST /api/defensive/traffic/analyze-batch           Batch analyze traffic
GET  /api/defensive/traffic/metrics                 Get traffic metrics
GET  /api/defensive/health                          Health check
```

### 14. OFFENSIVE SECURITY - SOCIAL ENGINEERING (6)

```
POST /api/social-eng/campaign              Create social engineering campaign
GET  /api/social-eng/campaign/{campaign_id}     Get campaign details
GET  /api/social-eng/templates               List campaign templates
POST /api/social-eng/awareness               Launch awareness training
GET  /api/social-eng/analytics/{campaign_id}   Get campaign analytics
GET  /social-eng/health                      Health check
```

### 15. OFFENSIVE SECURITY - VULNERABILITY SCANNER (5)

```
POST /api/vuln-scanner/scan           Start vulnerability scan
GET  /api/vuln-scanner/scan/{scan_id}      Get scan status/results
GET  /api/vuln-scanner/exploits           List available exploits
POST /api/vuln-scanner/exploit            Execute specific exploit
GET  /vuln-scanner/health                 Health check
```

### 16. AI AGENT (4)

```
POST /api/ai/chat                      Chat with AI agent
GET  /api/ai/                          Get AI agent info
GET  /api/ai/tools                     List available tools
GET  /ai/health                        Health check
```

### 17. AURORA ORCHESTRATOR (4)

```
POST /api/aurora/investigate           Start investigation
GET  /api/aurora/investigation/{id}    Get investigation status
GET  /api/aurora/services              List available services
GET  /aurora/health                    Health check
```

### 18. ACTIVE IMMUNE CORE (14)

```
POST /api/immune/threats/detect        Detect new threats
GET  /api/immune/threats               List all threats
GET  /api/immune/threats/{threat_id}   Get threat details
GET  /api/immune/agents                List immune agents
GET  /api/immune/agents/{agent_id}     Get agent details
POST /api/immune/homeostasis/adjust    Adjust system homeostasis
GET  /api/immune/homeostasis           Get homeostasis status
GET  /api/immune/lymphnodes            List lymph nodes
GET  /api/immune/lymphnodes/{node_id}  Get lymph node details
GET  /api/immune/memory/antibodies     Get antibodies in memory
GET  /api/immune/memory/search         Search immunological memory
GET  /api/immune/metrics               Get immune system metrics
GET  /api/immune/stats                 Get immune system stats
GET  /api/immune/health                Health check
```

### 19. PROTECTED ENDPOINTS (3)

```
GET  /protected/admin           Admin-only resources (requires 'admin' role)
GET  /protected/analyst         Analyst-only resources (requires 'analyst' role)
GET  /protected/offensive       Offensive tools (requires 'offensive' role)
```

### 20. SINESP INTEGRATION - BRAZILIAN PUBLIC SECURITY (3)

```
GET  /veiculos/{placa}          Vehicle info lookup (Rate: 30/min, Cached 1h)
GET  /ocorrencias/tipos         List crime occurrence types (Rate: 10/min)
GET  /ocorrencias/heatmap       Get crime heatmap (Rate: 10/min)
```

### 21. ATLAS GIS (1 - Wildcard Proxy)

```
GET/POST/PUT/DELETE /atlas/{full_path}    Proxy to Atlas GIS service (Rate: 60/min)
```

### 22. DYNAMIC SERVICE PROXIES (50+)

Each service has a dynamic proxy path pattern:

```
GET/POST/PUT/DELETE /auth-service/{path}
GET/POST/PUT/DELETE /behavioral-analyzer-service/{path}
GET/POST/PUT/DELETE /c2-orchestration-service/{path}
GET/POST/PUT/DELETE /google-osint-service/{path}
GET/POST/PUT/DELETE /homeostatic-regulation/{path}
GET/POST/PUT/DELETE /ip-intelligence-service/{path}
GET/POST/PUT/DELETE /malware-analysis-service/{path}
GET/POST/PUT/DELETE /mav-detection-service/{path}
GET/POST/PUT/DELETE /memory-consolidation-service/{path}
GET/POST/PUT/DELETE /narrative-manipulation-filter/{path}
GET/POST/PUT/DELETE /network-monitor-service/{path}
GET/POST/PUT/DELETE /network-recon-service/{path}
GET/POST/PUT/DELETE /neuromodulation-service/{path}
GET/POST/PUT/DELETE /nis-service/{path}
GET/POST/PUT/DELETE /offensive-gateway/{path}
GET/POST/PUT/DELETE /offensive-orchestrator-service/{path}
GET/POST/PUT/DELETE /offensive-tools-service/{path}
GET/POST/PUT/DELETE /osint-service/{path}
GET/POST/PUT/DELETE /predictive-threat-hunting-service/{path}
GET/POST/PUT/DELETE /prefrontal-cortex-service/{path}
GET/POST/PUT/DELETE /purple-team/{path}
GET/POST/PUT/DELETE /sinesp-service/{path}
GET/POST/PUT/DELETE /somatosensory-service/{path}
GET/POST/PUT/DELETE /ssl-monitor-service/{path}
GET/POST/PUT/DELETE /tataca-ingestion/{path}
GET/POST/PUT/DELETE /threat-intel-bridge/{path}
GET/POST/PUT/DELETE /threat-intel-service/{path}
GET/POST/PUT/DELETE /traffic-analyzer-service/{path}
GET/POST/PUT/DELETE /vestibular-service/{path}
GET/POST/PUT/DELETE /visual-cortex-service/{path}
GET/POST/PUT/DELETE /vuln-intel-service/{path}
GET/POST/PUT/DELETE /vuln-scanner-service/{path}

[... and 20+ more service proxies]
```

## Rate Limiting by Endpoint

```
/                              Unlimited
/health, /metrics              Unlimited
/auth/*                        100/min
/protected/*                   1000/min (authenticated only)

/cyber/network-scan            5/min
/cyber/*                       10/min

/api/nmap/scan                 5/min
/api/nmap/*                    10/min

/api/domain/analyze            10/min
/api/ip/analyze*               10/min

/api/google/search/*           10/min
/api/google/*                  10/min

/api/osint/*                   10/min
/api/malware/*                 5/min
/api/threat-intel/*            10/min
/api/ssl/*                     10/min

/api/defensive/behavioral/*    10/min
/api/defensive/traffic/*       10/min

/api/social-eng/*              5/min
/api/vuln-scanner/scan         5/min
/api/vuln-scanner/*            10/min

/api/ai/*                      100/min
/api/aurora/*                  10/min
/api/immune/*                  100/min

/veiculos/*                    30/min
/ocorrencias/*                 10/min

/atlas/*                       60/min

/{service}/*                   Default 100/min or as configured
```

## Request/Response Format

### Standard Request Headers
```
Authorization: Bearer <jwt_token>          (for protected endpoints)
Content-Type: application/json             (for POST/PUT/PATCH)
X-Request-ID: <uuid>                       (optional, auto-generated)
```

### Standard Response (Success 2xx)
```json
{
  "status": "success",
  "data": {...},
  "timestamp": "2025-11-15T12:34:56.789Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Standard Error Response
```json
{
  "detail": "Human-readable error message",
  "error_code": "AUTH_001",                    // Standardized code
  "timestamp": "2025-11-15T12:34:56.789Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "path": "/api/v1/scan/start"
}
```

### Validation Error Response (422)
```json
{
  "detail": "Request validation failed",
  "error_code": "VAL_422",
  "timestamp": "2025-11-15T12:34:56.789Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "path": "/api/v1/users",
  "validation_errors": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

## Authentication Flow

### 1. Login
```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=user&password=password

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Using Token
```
GET /protected/admin
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Verify Token
```
GET /auth/verify-token
Authorization: Bearer <token>

Response:
{
  "valid": true,
  "user": "username",
  "roles": ["admin", "analyst"],
  "expires_at": "2025-11-15T12:34:56.789Z"
}
```

## Example cURL Commands

### Simple Health Check
```bash
curl -X GET http://localhost:8000/health
```

### Login
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

### Protected Endpoint
```bash
TOKEN="<from-login-response>"
curl -X GET http://localhost:8000/protected/admin \
  -H "Authorization: Bearer $TOKEN"
```

### Domain Analysis
```bash
curl -X POST http://localhost:8000/api/domain/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain": "example.com"}'
```

### Network Scan
```bash
curl -X POST http://localhost:8000/cyber/network-scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "target": "192.168.0.0/24",
    "scan_type": "comprehensive",
    "timeout": 60
  }'
```

### Threat Detection
```bash
curl -X POST http://localhost:8000/api/immune/threats/detect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "signature": "suspicious_pattern",
    "behavior": "port_scanning",
    "severity": "high"
  }'
```

### List Google OSINT Patterns
```bash
curl -X GET http://localhost:8000/api/google/dorks/patterns \
  -H "Authorization: Bearer $TOKEN"
```

## Service Proxy Example

For any service, use the dynamic proxy:

```bash
curl -X POST http://localhost:8000/network-recon-service/api/v1/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"target": "example.com"}'

# Gets forwarded to: http://network-recon-service:8032/api/v1/scan
```

---

**Total Endpoints**: 250+
**Generated**: 2025-11-15
**Version**: 3.3.1
