# Network Reconnaissance Service

**Two-Stage Network Reconnaissance: Masscan (Breadth) → Nmap (Depth)**

Part of the **Maximus AI 3.0 Offensive Security Arsenal**

---

## 📋 Overview

O Network Reconnaissance Service implementa a estratégia de reconhecimento em dois estágios conforme o documento "The 2025 Offensive Security Arsenal":

- **Stage 1 (Breadth)**: Masscan high-speed sweeping para descoberta ampla
- **Stage 2 (Depth)**: Nmap deep enumeration com NSE scripting para análise detalhada

### Diferencial Estratégico

> *"Nmap offers depth (service versioning, OS detection, NSE scripts), while Masscan provides breadth (6M packets/sec, internet-scale scanning). The intelligent platform uses Masscan for initial sweep → Nmap for targeted analysis."*

---

## 🎯 Capabilities

### Two-Stage Reconnaissance
- ✅ **Masscan Sweep**: Asynchronous port scanning (10K-100K pps)
- ✅ **Intelligent Prioritization**: Target selection based on high-value ports
- ✅ **Nmap Deep Scan**: Service versioning, OS fingerprinting, NSE scripts
- ✅ **Adaptive Scanning**: Homeostatic Regulation throttling

### Autonomic Safety Architecture Integration
- 🧠 **Visual Cortex**: Malware vision on discovered services
- 🎧 **Auditory Cortex**: C2 beacon detection in network traffic
- 🤚 **Somatosensory**: Pain processing for critical threats
- 👃 **Chemical Sensing**: Payload taste analysis
- 🔄 **Digital Thalamus**: Sensory gating (noise reduction)
- ⚖️ **Homeostatic Regulation**: Scan rate control based on system stress

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Network Reconnaissance Service (8032)         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────────────────┐    │
│  │   Stage 1    │  →   │   Prioritization Logic   │    │
│  │   Masscan    │      │   (High-value ports)     │    │
│  │  (Breadth)   │      └──────────────────────────┘    │
│  └──────────────┘                   │                   │
│         │                           ↓                   │
│         │               ┌──────────────────────────┐    │
│         │               │      Stage 2: Nmap       │    │
│         │               │   (Deep enumeration)     │    │
│         │               └──────────────────────────┘    │
│         │                           │                   │
│         ↓                           ↓                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │        Autonomic Safety Integration             │   │
│  │  • Visual Cortex (Malware Vision)              │   │
│  │  • Digital Thalamus (Sensory Gating)           │   │
│  │  • Homeostatic Regulation (Scan Rate Control)  │   │
│  │  • Somatosensory (Pain Processing)             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Build & Run

```bash
# Navigate to service directory
cd backend/services/network_recon_service

# Build Docker image
docker build -t network-recon:latest .

# Run service
docker-compose up -d
```

### 2. Verify Installation

```bash
# Health check
curl http://localhost:8032/health

# Service status
curl http://localhost:8032/status
```

---

## 📡 API Endpoints

### Two-Stage Reconnaissance

#### Execute Two-Stage Scan (Async)
```bash
POST /api/v1/recon/two-stage
```

**Request Body:**
```json
{
  "target_range": "10.0.0.0/24",
  "masscan_ports": "80,443,22,3389",
  "masscan_rate": 10000,
  "deep_scan_threshold": 50,
  "prioritization": "high_value_ports",
  "nmap_version_detection": true,
  "nmap_os_detection": true,
  "nmap_nse_scripts": "default,vuln",
  "enable_asa_integration": true
}
```

**Response:**
```json
{
  "job_id": "job_20251003_230800_a1b2c3d4",
  "scan_type": "two_stage",
  "status": "pending",
  "created_at": "2025-10-03T23:08:00Z",
  "target_range": "10.0.0.0/24"
}
```

#### Get Scan Job Status
```bash
GET /api/v1/recon/job/{job_id}
```

**Response:**
```json
{
  "job_id": "job_20251003_230800_a1b2c3d4",
  "status": "completed",
  "progress": 100.0,
  "result": {
    "scan_id": "recon_20251003_230800_xyz",
    "stage1_hosts_discovered": 25,
    "stage2_hosts_scanned": 15,
    "total_duration": 45.2,
    "asa_integration_enabled": true,
    "homeostatic_scan_rate": 8000,
    "system_stress_detected": true
  }
}
```

### Masscan-Only

#### Execute Masscan Sweep
```bash
POST /api/v1/recon/masscan
```

**Request:**
```json
{
  "target_range": "192.168.1.0/24",
  "ports": "80,443,22",
  "rate": 10000,
  "exclude_ranges": ["192.168.1.1/32"]
}
```

#### Estimate Scan Duration
```bash
POST /api/v1/recon/masscan/estimate
```

### Nmap-Only

#### Execute Nmap Deep Scan
```bash
POST /api/v1/recon/nmap
```

**Request:**
```json
{
  "targets": ["10.0.0.1", "10.0.0.2"],
  "ports": "1-1000",
  "scan_type": "syn",
  "version_detection": true,
  "os_detection": true,
  "nse_scripts": "vuln,exploit",
  "timing_template": 3
}
```

#### Quick Scan (Top 100 Ports)
```bash
POST /api/v1/recon/nmap/quick
```

#### Vulnerability Scan (NSE Vuln Scripts)
```bash
POST /api/v1/recon/nmap/vulnerability
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=network_reconnaissance
SERVICE_PORT=8032
LOG_LEVEL=INFO

# Scanning Configuration
DEFAULT_MASSCAN_RATE=10000          # Packets/sec
MAX_SCAN_RATE=100000                # Max allowed rate
DEFAULT_DEEP_SCAN_THRESHOLD=100     # Max hosts for Stage 2

# ASA Integration
ENABLE_ASA_INTEGRATION=true
VISUAL_CORTEX_URL=http://visual_cortex_service:8006
DIGITAL_THALAMUS_URL=http://digital_thalamus_service:8012
HOMEOSTATIC_REGULATION_URL=http://homeostatic_regulation:8015
SOMATOSENSORY_URL=http://somatosensory_service:8008

# Timeouts
ASA_REQUEST_TIMEOUT=10.0
SCAN_TIMEOUT=3600
```

---

## 🔬 How It Works

### 1. Two-Stage Strategy

**Stage 1 - Masscan (Breadth)**
- Asynchronous scanning at 10K-100K packets/sec
- Custom TCP/IP stack (bypasses OS limitations)
- Discovers all hosts with open ports on common services

**Stage 2 - Nmap (Depth)**
- Targeted deep enumeration on prioritized hosts
- Service version detection (`-sV`)
- OS fingerprinting (`-O`)
- NSE vulnerability scripts

### 2. Intelligent Prioritization

Targets are scored based on:
- **High-Value Ports**: Web (80, 443), DB (3306, 5432), Remote (22, 3389)
- **Vulnerability-Prone**: FTP (21), Telnet (23), SMB (445)
- **Port Count**: More open ports = higher priority

### 3. ASA Integration Flow

```
Masscan Sweep → Digital Thalamus Gating → Prioritization
                                              ↓
                                         Nmap Scan
                                              ↓
                                    Visual Cortex Analysis
                                              ↓
                                  [If Critical Threat Detected]
                                              ↓
                                 Somatosensory Pain Processing
```

### 4. Adaptive Scan Rate

```python
# Query Homeostatic Regulation
if system_state == "stressed":
    scan_rate = 1000  # Throttle to 1K pps
elif system_state == "elevated":
    scan_rate = 5000  # Moderate throttling
else:
    scan_rate = 10000  # Full speed
```

---

## 📊 Metrics

### Prometheus Endpoints

```bash
# Get metrics
GET /metrics

# Metrics model
GET /api/v1/metrics
```

**Available Metrics:**
- `recon_scans_total{scan_type}` - Total scans by type
- `recon_scans_completed_total` - Completed scans
- `recon_scans_failed_total` - Failed scans
- `recon_hosts_discovered_total` - Total hosts discovered
- `recon_services_enumerated_total` - Total services enumerated
- `recon_asa_calls_total{service}` - ASA integration calls
- `recon_homeostatic_throttles_total` - Scan rate throttles
- `recon_scan_duration_seconds` - Scan duration histogram

---

## 🛡️ Security Considerations

### Privileged Operations

Masscan and Nmap require elevated privileges for certain scan types:

- **SYN Scan (`-sS`)**: Requires `NET_ADMIN` capability
- **OS Detection (`-O`)**: Requires `NET_RAW` capability

**Docker Configuration:**
```yaml
cap_add:
  - NET_ADMIN
  - NET_RAW
```

### Rate Limiting

- Default: 10,000 packets/sec
- Maximum: 100,000 packets/sec (configurable)
- Homeostatic Regulation enforces adaptive throttling

---

## 🧪 Testing

### Unit Tests
```bash
pytest tests/test_masscan_wrapper.py
pytest tests/test_nmap_wrapper.py
pytest tests/test_recon_engine.py
```

### Integration Tests
```bash
pytest tests/integration/test_two_stage_recon.py
pytest tests/integration/test_asa_integration.py
```

### Manual Testing

**Test Masscan:**
```bash
curl -X POST http://localhost:8032/api/v1/recon/masscan \
  -H "Content-Type: application/json" \
  -d '{
    "target_range": "192.168.1.0/24",
    "ports": "80,443",
    "rate": 5000
  }'
```

**Test Two-Stage:**
```bash
curl -X POST http://localhost:8032/api/v1/recon/two-stage \
  -H "Content-Type: application/json" \
  -d '{
    "target_range": "10.0.0.0/24",
    "masscan_ports": "80,443,22",
    "masscan_rate": 10000,
    "deep_scan_threshold": 50,
    "enable_asa_integration": true
  }'
```

---

## 📚 References

### Strategic Documentation
- **Source**: "The 2025 Offensive Security Arsenal: A Strategic Implementation Roadmap for the Maximus AI Platform"
- **Section**: 1.2 - Network Reconnaissance: High-Speed Sweeps vs. Deep Scans

### Key Insights
> *"An external assessment against a large organization may involve scanning tens of thousands of IPs. A deep Nmap scan is infeasible. However, a Masscan sweep to identify hosts with common web ports is trivial and completes in minutes. The output can then feed into Nmap for surgical, deep-dive analysis."*

### Tools
- [Masscan](https://github.com/robertdavidgraham/masscan) - High-speed port scanner
- [Nmap](https://nmap.org/) - Network exploration and security auditing
- [NSE Scripts](https://nmap.org/nsedoc/) - Nmap Scripting Engine

---

## 📝 TODO

- [ ] Database persistence for scan results (PostgreSQL)
- [ ] Redis job queue for distributed scanning
- [ ] WebSocket support for real-time scan updates
- [ ] Export results to MITRE ATT&CK Navigator format
- [ ] Integration with Nuclei for template-driven vuln scanning

---

## 🏆 Quality Standard

**Implementation Philosophy:**
- ✅ **NO MOCKS**: Real Masscan and Nmap integration
- ✅ **NO PLACEHOLDERS**: Fully functional ASA integration
- ✅ **PRODUCTION READY**: Docker, metrics, health checks, error handling
- ✅ **QUALITY-FIRST**: Following Maximus AI gold standard

---

**Version**: 1.0.0
**Port**: 8032 (API), 9032 (Metrics)
**Author**: Maximus AI Platform
**Status**: ✅ Production Ready
