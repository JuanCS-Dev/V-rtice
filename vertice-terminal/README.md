<div align="center">

# 🎯 VÉRTICE CLI

### Cyber Security Command Center Powered by AI

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/juancs-dev/vertice-terminal)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-30%2F30%20passing-success.svg)](./tests/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](./LICENSE)
[![AI](https://img.shields.io/badge/AI-Maximus%20Powered-orange.svg)](./docs/MAXIMUS_AI.md)

---

**28 Commands** • **100+ Subcommands** • **57 AI Tools** • **18+ Integrations**

[Quick Start](#-quick-start) • [Commands](#-command-reference) • [Features](#-features) • [Documentation](#-documentation)

</div>

---

## 📖 What is Vértice CLI?

**Vértice CLI** (`vcli`) is a comprehensive **Cyber Security Command Center** that brings the power of AI-driven security operations to your terminal. Built on top of **Maximus AI**, it provides a unified interface for:

- 🤖 **AI-Orchestrated Investigations** - Let Maximus decide the best tools
- 🔎 **OSINT & Reconnaissance** - From social media to breach databases
- ⚔️ **Offensive Security** - Authorized pentesting arsenal
- 🛡️ **Defense & Response** - AI Immune System with 8 specialized cells
- 📊 **Analytics & ML** - Behavioral analysis and risk scoring
- 🧠 **Memory System** - Context-aware operations with semantic search
- 📝 **Human-Centric Language** - Write security workflows in natural language

---

## ✨ Key Features

### 🤖 AI-First Architecture

```
                 vcli investigate example.com
                          ↓
           ╔══════════════════════════════╗
           ║    Maximus AI Core (8001)    ║
           ║    Reasoning Engine ✓        ║
           ║    57 Tools Available        ║
           ╚══════════════════════════════╝
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
  Autonomous Tool              Parallel Execution
  Selection                    (up to 5 tools)
        ↓                                   ↓
        └─────────────────┬─────────────────┘
                          ↓
           ╔══════════════════════════════╗
           ║     Intelligent Response     ║
           ║     + Reasoning Trace        ║
           ║     + Confidence Score       ║
           ╚══════════════════════════════╝
```

### 🧠 Memory System

- **Working Memory**: Immediate context
- **Episodic Memory**: Conversation history (25 conversations stored)
- **Semantic Memory**: Knowledge base with vector search
- **Recall Similar Investigations**: Find past cases like current one

### 🎨 Beautiful Terminal UI

```bash
vcli tui  # Launch full-screen dashboard
vcli shell  # Interactive shell with autocomplete
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/juancs-dev/vertice-terminal.git
cd vertice-terminal

# Install dependencies
pip install -e .

# Verify installation
vcli --version
```

### First Command

```bash
# Get help
vcli --help

# Login (required for most commands)
vcli auth login --email your.email@gmail.com

# Investigate a domain (AI-orchestrated)
vcli investigate target example.com --type defensive

# Check OSINT for a username
vcli osint username johndoe --platforms "twitter,linkedin"

# View memory status
vcli memory status
```

### Quick Tour

```bash
# Interactive shell with autocomplete
vcli shell

# Beautiful TUI dashboard
vcli tui

# Menu with categorized tools
vcli menu
```

---

## 📋 Command Reference

> **📚 Full documentation**: See [ANALISE_COMPLETA_VERTICE_CLI.md](/home/juan/vertice-dev/ANALISE_COMPLETA_VERTICE_CLI.md) for detailed command reference

### 🤖 AI & Intelligence (7 commands)

| Command | Description | Subcommands |
|---------|-------------|-------------|
| `investigate` | 🔍 AI-orchestrated investigation | `target`, `multi`, `history`, `similar` |
| `ask` | 🤖 AI-powered threat hunting | Interactive |
| `maximus` | 🌌 Maximus AI direct interface | `chat`, `tools`, `status` |
| `memory` | 🧠 Memory system management | `status`, `recall`, `similar`, `stats`, `clear` |
| `analytics` | 📊 Advanced analytics | `behavior`, `ml`, `risk`, `threat-intel` |
| `hunt` | 🔎 Threat hunting | Multiple |
| `detect` | 🔍 Threat detection (YARA/Sigma) | `yara`, `sigma`, `custom` |

**Example - AI Investigation**:
```bash
# Deep investigation with autonomous tool selection
vcli investigate target malware.exe --type defensive --depth comprehensive

# Find similar past investigations (semantic search)
vcli investigate similar "ransomware attack"
```

**Output Preview**:
```
🔍 Investigation Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Target: example.com
Type: defensive

Findings:
  • Threat intel: CLEAN (confidence: 95%)
  • SSL certificate: Valid (expires in 180 days)
  • DNS records: Properly configured

Tools Executed: ✓ threat_intel ✓ ssl_monitor ✓ domain_analysis

⚡ Maximus Reasoning:
  Confidence: 92.5%
  Next Actions: Monitor subdomain activity
```

---

### 🔎 OSINT & Reconnaissance (4 commands)

| Command | Description | Subcommands |
|---------|-------------|-------------|
| `osint` | 🔎 Open Source Intelligence | `username`, `breach`, `vehicle`, `multi`, `comprehensive` |
| `ip` | 🔍 IP Intelligence | `analyze`, `geo`, `whois`, `reputation` |
| `threat` | 🛡️ Threat intelligence | `analyze`, `feed`, `ttp` |
| `threat_intel` | 🌐 Threat intel platform | Multiple |

**Example - OSINT**:
```bash
# Social media profiling
vcli osint username johndoe --platforms "twitter,linkedin,github"

# Breach data lookup
vcli osint breach user@example.com

# SINESP vehicle query (Brazil)
vcli osint vehicle ABC1234
```

---

### ⚔️ Offensive Security (4 commands)

| Command | Description | Subcommands |
|---------|-------------|-------------|
| `offensive` | ⚔️ Offensive arsenal | `recon`, `vuln`, `exploit`, `web`, `bas` |
| `scan` | 🌐 Network scanning | `nmap`, `masscan`, `service` |
| `monitor` | 📊 Network monitoring | Multiple |
| `pentest` | 🔓 Penetration testing | Multiple |

⚠️ **WARNING**: Authorized use only!

**Example**:
```bash
# Network reconnaissance (authorized pentest)
vcli offensive recon 192.168.1.0/24 --type stealth

# Vulnerability intelligence
vcli offensive vuln CVE-2021-44228

# Web attack simulation
vcli offensive web https://test.example.com --attacks "sqli,xss"
```

---

### 🛡️ Defense & Response (6 commands)

| Command | Description | Subcommands |
|---------|-------------|-------------|
| `immunis` | 🛡️ AI Immune System (8 cells) | `status`, `detect`, `respond`, `patrol`, `memory` |
| `adr` | ⚔️ ADR (Anomaly Detection) | `detect`, `respond`, `plan` |
| `incident` | 🚨 Incident response | `create`, `investigate`, `timeline`, `evidence` |
| `policy` | 📜 Policy-as-Code | `create`, `apply`, `validate` |
| `malware` | 🦠 Malware analysis | `analyze`, `scan`, `sandbox` |
| `dlp` | 🔒 Data Loss Prevention | `scan`, `classify`, `alert` |

**Example - AI Immune System**:
```bash
# Check immune system status
vcli immunis status

# Activate NK patrol (proactive defense)
vcli immunis patrol network --targets "192.168.1.0/24"
```

**8 Immune Cell Types**:
- 🔬 Macrophage, ⚡ Neutrophil, 📊 Dendritic, 🧬 B-Cell
- 🤝 Helper T, ⚔️ Cytotoxic T, 👁️ NK Cell, 🛡️ Immunis API

---

### 📊 Management & Compliance (5 commands)

| Command | Description | Frameworks |
|---------|-------------|------------|
| `compliance` | 📋 Multi-framework compliance | PCI-DSS, GDPR, SOC2, HIPAA, ISO 27001 |
| `siem` | 🔍 SIEM integration | Splunk, Sentinel, QRadar, Elastic |
| `context` | 🎯 Context management | - |
| `auth` | 🔐 Authentication | - |
| `menu` | 📋 Interactive menu | - |

---

### 🧠 Advanced Features (2 commands)

| Command | Description | Subcommands |
|---------|-------------|-------------|
| `hcl` | 📝 Human-Centric Language | `execute`, `plan`, `analyze`, `query` |
| `cognitive` | 🧠 Cognitive services | `image`, `audio`, `decide` |

**Example - HCL Workflows**:
```bash
# Generate plan from objective
vcli hcl plan "Perform comprehensive security assessment"

# Execute HCL workflow
vcli hcl execute security_audit.hcl
```

---

### 🎨 UI & Shell (2 commands)

| Command | Description | Features |
|---------|-------------|----------|
| `tui` | 🎨 Text UI Dashboard (BETA) | Gradient UI, Quick actions, Command Palette |
| `shell` | 🚀 Interactive shell | Autocomplete, History, Suggestions |

**Bindings**:
- `Ctrl+P` - Command Palette
- `Ctrl+Q` - Quit
- `1-4` - Quick Actions

---

## 🔗 Integrations

### 🤖 AI & Orchestration

- **Maximus AI Core** (port 8001)
  - 57 tools available
  - Reasoning engine
  - Memory system

### 🛡️ Security Services (44+)

**Intelligence**: OSINT (5 sources), Threat intel, IP intel, Domain analysis

**Detection**: YARA, Sigma, ML models, Behavioral analytics

**Offensive**: Nmap, Masscan, Exploit DBs, BAS

**Defense**: 8 AI immune cells, ADR, Incident response, DLP

### 🔌 SIEM & SOAR

**SIEM**: Splunk, Microsoft Sentinel, IBM QRadar, Elastic

**SOAR**: Splunk SOAR, Sentinel, Custom playbooks

---

## 💡 Practical Examples

### 🔍 Defensive Security

```bash
# Complete domain investigation
vcli investigate target suspicious-domain.com --type defensive --depth deep

# Check for breached credentials
vcli osint breach leaked-emails.txt

# Malware analysis
vcli malware analyze suspicious.exe --sandbox
```

### ⚔️ Offensive Security (Authorized)

```bash
# Reconnaissance
vcli offensive recon target.com --type comprehensive

# Vulnerability assessment
vcli scan nmap 192.168.1.0/24 --script vuln

# BAS
vcli offensive bas phishing --target sales-team@company.com
```

### 🚨 Incident Response

```bash
# Create incident case
vcli incident create --title "Ransomware Attack" --severity critical

# Collect evidence
vcli incident evidence collect --case INC-2025-001

# Timeline reconstruction
vcli incident timeline --case INC-2025-001
```

### 📊 Compliance

```bash
# Run PCI-DSS audit
vcli compliance audit --framework pci-dss-4.0

# Generate report
vcli compliance report --frameworks "pci-dss,gdpr" --format pdf
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VÉRTICE CLI (vcli)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Commands │  │  Shell   │  │   TUI    │  │  Menu    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       └──────────────┴─────────────┴──────────────┘        │
│                    ┌─────▼─────┐                           │
│                    │ Connectors │                           │
│                    └─────┬─────┘                           │
└──────────────────────────┼─────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐     ┌─────▼──────┐    ┌────▼────┐
    │ Maximus │     │  Services  │    │  SIEM   │
    │AI (8001)│     │  (44+)     │    │Connectors│
    └────┬────┘     └────────────┘    └─────────┘
         │
    ┌────▼────────────────────┐
    │ - Reasoning Engine      │
    │ - 57 Tools              │
    │ - Memory System         │
    └─────────────────────────┘
```

---

## 🛠️ Development

### Setup

```bash
git clone https://github.com/juancs-dev/vertice-terminal.git
cd vertice-terminal

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install
pip install -e ".[dev]"

# Tests
pytest tests/ -v --cov=vertice
```

### Testing

```bash
# All tests
pytest tests/ -v

# Integration
pytest tests/integration/ -v

# E2E
pytest tests/e2e/ -v -m e2e

# Coverage
pytest tests/ --cov=vertice --cov-report=html
```

---

## 🔐 Security

⚠️ **IMPORTANT**: Authorized use only!

- ✅ Authorized: Company assets, authorized pentests
- ❌ Unauthorized: Third-party systems, malicious use

### Features

- 🔐 Authentication & permissions
- 🔑 Secure token storage
- 📝 Audit logging
- 🛡️ Sandboxing

### Reporting

Security issues: security@vertice.dev (NOT public issues)

---

## 📊 Statistics

- **Commands**: 28
- **Subcommands**: 100+
- **AI Tools**: 57
- **Connectors**: 18+
- **Services**: 44+
- **Tests**: 30/30 passing (100%)
- **Lines of Code**: 15,000+

---

## 🗺️ Roadmap

### v1.1 (Q1 2025)

- [ ] Web UI dashboard
- [ ] ChatOps (Slack, Teams)
- [ ] Plugin marketplace
- [ ] Auto-update

### v1.2 (Q2 2025)

- [ ] Cloud integrations (AWS, Azure, GCP)
- [ ] Kubernetes security
- [ ] Container security
- [ ] Mobile app

### v2.0 (Q3 2025)

- [ ] Distributed architecture
- [ ] Multi-tenant
- [ ] Advanced ML
- [ ] Real-time collaboration

---

## 📚 Documentation

Full documentation available:

- **[ANALISE_COMPLETA_VERTICE_CLI.md](/home/juan/vertice-dev/ANALISE_COMPLETA_VERTICE_CLI.md)** - Complete analysis
- **[INTEGRACAO_MAXIMUS_CLI_COMPLETA.md](/home/juan/vertice-dev/INTEGRACAO_MAXIMUS_CLI_COMPLETA.md)** - Integration guide
- **[CERTIFICACAO_FINAL_INTEGRACAO_MAXIMUS.md](/home/juan/vertice-dev/CERTIFICACAO_FINAL_INTEGRACAO_MAXIMUS.md)** - Certification

---

## 📜 License

MIT License - see [LICENSE](./LICENSE)

---

## 🙏 Acknowledgments

- **Maximus AI Team** - AI engine
- **JuanCS-Dev** - Creator
- **Open Source Community**

---

## 📞 Support

- 📧 Email: support@vertice.dev
- 🐛 Issues: [GitHub Issues](https://github.com/juancs-dev/vertice-terminal/issues)
- 📖 Docs: [docs.vertice.dev](https://docs.vertice.dev)

---

<div align="center">

**Made with ❤️ by the Vértice Team**

**Powered by 🤖 Maximus AI**

[⬆ Back to Top](#-vértice-cli)

</div>
