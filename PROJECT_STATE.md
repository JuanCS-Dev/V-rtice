# VERTICE Project - Current State
**Last Updated:** 2025-10-03

## Project Overview
VERTICE is a comprehensive cybersecurity platform combining OSINT, threat intelligence, network scanning, and AI-powered analysis capabilities.

---

## Current Architecture

### Active Services (Running)
1. **ADR Core Service** (Port 8001)
   - Automated Detection & Response
   - Integrates with malware analysis
   - Playbook-based response system
   - Connectors: Malware Analysis, IP Intelligence, Threat Intelligence

2. **IP Intelligence Service** (Port 8003)
   - IP reputation lookup
   - Geolocation data
   - Threat categorization
   - SQLite database: `ip_intel.db`

3. **Malware Analysis Service** (Port 8004)
   - File hash analysis
   - Sandbox integration
   - YARA rules support
   - SQLite database: `malware.db`

4. **Network Monitor Service** (Port 8005)
   - Real-time network monitoring
   - Traffic analysis
   - Anomaly detection

5. **Nmap Scanner Service** (Port 8006)
   - Port scanning
   - Service detection
   - OS fingerprinting

6. **SSL Monitor Service** (Port 8007)
   - Certificate validation
   - Expiry monitoring
   - Security checks

7. **Threat Intelligence Service** (Port 8008)
   - IOC lookups
   - Threat feeds integration
   - Intelligence correlation

8. **Vulnerability Scanner Service** (Port 8009)
   - CVE database
   - Security assessment
   - Compliance checks

### Frontend (Port 5173)
- React-based UI
- Landing page with monitoring widgets
- OSINT Dashboard
- Cyber tools interface
- Authentication system

---

## Maximus AI - Next Generation (In Development)

### Status: 🚀 **REVOLUTIONARY REDESIGN**
**Baseado em:** Neuro-Inspired Architecture + Immunis Machina
**Documentos:** `MAXIMUS_AI_ROADMAP_2025.md`

### Visão Arquitetural
Maximus AI será reconstruído do zero como um **sistema verdadeiramente autônomo**, inspirado no cérebro humano e sistema imunológico, implementando não apenas cognição consciente, mas a vasta infraestrutura **inconsciente** que sustenta inteligência eficiente.

**Componentes Principais:**
1. **Homeostatic Control Loop (HCL)** - Sistema Autonômico MAPE-K
2. **Hierarchical Predictive Coding (hPC)** - Free Energy Principle
3. **Dynamic Attention & Saliency (DASM)** - Dual Streams + Multi-Stage Attention
4. **Hybrid Skill Acquisition (HSAS)** - RL híbrido com primitives composicionais
5. **Neuromodulation System (NMS)** - Meta-learning via neurotransmitters
6. **Immunis Machina** - Defesa biomimética em camadas

**Timeline:** 18-24 meses para capacidade NSA-level
**Fases:** 5 fases (Q1 2025 - Q1 2026)

### Serviços Legados (Descontinuados)
- **maximus_core_service** - Será substituído por HCL + hPC
- **maximus_eureka** - Será substituído por DASM
- **maximus_oraculo** - Será substituído por HSAS
- **maximus_orchestrator_service** - Será substituído por NMS
- **maximus_predict** - Integrado em hPC Network
- **maximus_integration_service** - Substituído por SOS (Event-Driven)

**Reason for Redesign:** Arquitetura legada não implementava princípios neuro-biológicos de autonomia real. Nova arquitetura baseada em pesquisa cutting-edge (Friston, Doya, Rao & Ballard).

---

## Project Structure

```
vertice-dev/
├── backend/
│   └── services/
│       ├── adr_core_service/          # Active - Main AI/ADR logic
│       ├── ip_intelligence_service/   # Active
│       ├── malware_analysis_service/  # Active
│       ├── network_monitor_service/   # Active
│       ├── nmap_scanner_service/      # Active
│       ├── ssl_monitor_service/       # Active
│       ├── threat_intel_service/      # Active
│       └── vuln_scanner_service/      # Active
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── LandingPage/          # Recent redesign
│       │   ├── osint/                # OSINT modules
│       │   └── cyber/                # Cyber tools
│       └── contexts/
│           └── AuthContext.jsx       # Authentication
├── vertice-terminal/                  # CLI interface
│   ├── vertice/
│   │   ├── commands/                 # CLI commands
│   │   ├── connectors/               # Service connectors
│   │   └── utils/                    # Utilities
│   └── docs/                         # Documentation
└── docker-compose.yml                # Service orchestration
```

---

## Recent Changes (Last 5 Commits)

1. **90bf1e4** - Landing page with monitoring widgets
2. **f981d4f** - Polish threat locations and layout
3. **dcaec02** - Functional landing page with fixes
4. **4cb5f9b** - Aurora AI templates, frontend refactoring
5. **091c40a** - Implementation of core services

---

## Current Git Status

### Modified Files
**Backend:**
- `backend/services/adr_core_service/connectors/__init__.py`
- `backend/services/adr_core_service/main.py`
- `backend/services/adr_core_service/requirements.txt`
- `backend/services/ip_intelligence_service/ip_intel.db`
- `backend/services/malware_analysis_service/malware.db`
- `docker-compose.yml`

**Frontend:**
- `frontend/src/App.jsx`
- `frontend/src/components/LandingPage/` (multiple files)
- `frontend/src/components/OSINTDashboard.jsx`
- `frontend/src/components/cyber/` (multiple files)
- `frontend/src/components/osint/` (multiple files)
- `frontend/src/contexts/AuthContext.jsx`

**Vertice Terminal:**
- Multiple CLI command files updated
- Configuration files updated
- Connector implementations updated

### Deleted Files (Cleanup)
- All Maximus AI services
- All Aurora AI services
- Legacy AI agent service

### New Untracked Files
- Documentation files (.md)
- ADR Core Service components
- Maximus legacy service files (for reference)
- Analysis reports
- Test scripts

---

## Active Development Areas

### 1. ADR Core Service
**Status:** In active development
- Recent integration with malware analysis
- Playbook system implemented
- Engine architecture in place
- Models and utils structured

**Key Files:**
- `backend/services/adr_core_service/main.py`
- `backend/services/adr_core_service/connectors/`
- `backend/services/adr_core_service/engines/`
- `backend/services/adr_core_service/playbooks/`

### 2. Frontend Landing Page
**Status:** Production-ready (2025-10-03)
- Widget-based monitoring dashboard
- Threat location visualization
- Module grid layout
- Responsive design
- **Authentication system fully integrated**
- **Visual cohesion complete**
- Animated login/logout flow
- Real-time threat data feed

**Key Files:**
- `frontend/src/components/LandingPage/index.jsx` - Main component
- `frontend/src/components/LandingPage/LandingPage.css` - Styles & animations
- `frontend/src/components/LandingPage/ModuleGrid.jsx` - Module cards
- `frontend/src/components/LandingPage/StatsPanel.jsx` - Live statistics
- `frontend/src/components/LandingPage/LiveFeed.jsx` - Activity feed
- `frontend/src/components/LandingPage/ThreatGlobe.jsx` - Global threat map
- `frontend/src/contexts/AuthContext.jsx` - Authentication context

### 3. OSINT Dashboard
**Status:** Stable, ongoing improvements
- Email investigation
- Phone lookup
- Username search
- Social media analysis
- Breach data widget

### 4. Vertice Terminal
**Status:** Stable CLI interface
- Command system refactored
- Service connectors updated
- Authentication system
- Interactive shell mode

---

## Configuration

### Docker Compose Services
```yaml
- adr_core_service: 8001
- ip_intelligence_service: 8003
- malware_analysis_service: 8004
- network_monitor_service: 8005
- nmap_scanner_service: 8006
- ssl_monitor_service: 8007
- threat_intel_service: 8008
- vuln_scanner_service: 8009
- frontend: 5173
```

### Environment
- **Platform:** Linux 6.14.0-32-generic
- **Working Directory:** /home/juan/vertice-dev
- **Git Branch:** main
- **Git Repository:** Yes

---

## Known Issues & TODO

### Pending Tasks
1. Complete ADR Core Service integration testing
2. Document ADR playbook creation
3. Frontend API integration with ADR
4. CLI commands for ADR workflows
5. Database migration strategy
6. Service health monitoring

### Technical Debt
1. Remove obsolete .md documentation files
2. Clean up untracked analysis directories
3. Consolidate service configurations
4. Update main README.md
5. Add integration tests

---

## Dependencies

### Backend Core
- FastAPI
- Uvicorn
- SQLite
- Python 3.9+

### Frontend
- React
- Vite
- Modern CSS modules

### CLI
- Click
- Rich (terminal UI)
- YAML configuration

---

## Next Steps (Recommended)

1. **Immediate:**
   - Test ADR Core Service endpoints
   - Verify service connectivity
   - Update frontend to consume ADR APIs

2. **Short-term:**
   - Documentation cleanup
   - Integration test suite
   - Performance benchmarking

3. **Long-term:**
   - Scalability improvements
   - Advanced AI/ML models
   - Enterprise features

---

## Reference Documentation

- `EXECUTIVE_SUMMARY.md` - High-level overview
- `ADR_CORE_COMPLETE.md` - ADR service details
- `LANDING_PAGE_REDESIGN.md` - Frontend updates
- `PRODUCTION_READY.md` - Terminal CLI status
- `VERTICE_UPGRADE_PLAN.md` - Migration guide

---

## Notes
- This is a living document that should be updated after significant changes
- Always check git status before major operations
- Maximus AI services removed but reference files kept for documentation
- Aurora AI deprecated in favor of integrated ADR approach
