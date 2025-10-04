# 🤖 MAXIMUS AI ASSISTANT V2: Intelligent Security Analyst
## From Tool to Teammate - AI-Powered Workflow Augmentation

> **Vision**: Transform Maximus from a powerful AI engine into a proactive, context-aware security analyst that understands workspace state, correlates findings, suggests next steps, and automates tedious tasks.

---

## 📊 CURRENT STATE (Maximus AI v1)

### What We Have
- ✅ **57 AI tools** orchestrated via Gemini
- ✅ **Reasoning engine** for tool selection
- ✅ **Memory system** (working, episodic, semantic)
- ✅ **AI-orchestrated investigations**: `vcli investigate <target>`

### Limitations
- ❌ Not workspace-aware (doesn't query project database)
- ❌ No proactive suggestions (reactive only)
- ❌ No vulnerability correlation with CVE databases
- ❌ No PoC generation
- ❌ No automated report drafting
- ❌ No natural language queries against findings

---

## 🎯 TARGET STATE (Maximus Assistant v2)

### Vision: The AI Analyst

**Maximus v2 is not just a tool orchestrator - it's a digital security analyst that:**
1. **Observes** - Listens to workspace events (new hosts, vulns discovered)
2. **Analyzes** - Correlates findings, identifies patterns, prioritizes risks
3. **Suggests** - Recommends next steps based on context
4. **Automates** - Generates PoCs, drafts reports, chains attack steps
5. **Explains** - Provides reasoning for all actions (transparency)

---

## 🏗️ ARCHITECTURE

```
┌──────────────────────────────────────────────────────────┐
│               MAXIMUS ASSISTANT V2                       │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Core AI Engine (Gemini)                    │ │
│  │  - Reasoning & planning                            │ │
│  │  - Natural language understanding                  │ │
│  │  - Code generation (PoC, scripts)                  │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │                                   │
│  ┌───────────────────▼────────────────────────────────┐ │
│  │         Context Manager                            │ │
│  │  - Workspace state reader                          │ │
│  │  - Memory system integration                       │ │
│  │  - Event listener (on_host_discovered, etc.)       │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │                                   │
│  ┌───────────────────▼────────────────────────────────┐ │
│  │         Capability Modules                         │ │
│  │                                                     │ │
│  │  ┌──────────────────┐  ┌──────────────────┐       │ │
│  │  │ NL Query Engine  │  │ Vuln Correlator  │       │ │
│  │  └──────────────────┘  └──────────────────┘       │ │
│  │  ┌──────────────────┐  ┌──────────────────┐       │ │
│  │  │ Suggester        │  │ PoC Generator    │       │ │
│  │  └──────────────────┘  └──────────────────┘       │ │
│  │  ┌──────────────────┐  ┌──────────────────┐       │ │
│  │  │ Report Drafter   │  │ Attack Planner   │       │ │
│  │  └──────────────────┘  └──────────────────┘       │ │
│  └─────────────────────────────────────────────────── │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Knowledge Bases                            │ │
│  │  - CVE/NVD database                                │ │
│  │  - ExploitDB integration                           │ │
│  │  - MITRE ATT&CK framework                          │ │
│  │  - Security best practices                         │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Workspace DB    │
              │ (SQLite)        │
              └─────────────────┘
```

---

## 🔧 CAPABILITY MODULES

### 1. Natural Language Query Engine

**Purpose**: Allow users to query workspace findings using plain English.

**Examples**:
```bash
$ vcli ask "show all SSH servers"
→ SELECT hosts.ip_address, ports.port, ports.version
  FROM hosts JOIN ports ON hosts.id = ports.host_id
  WHERE ports.port = 22

$ vcli ask "what hosts have critical vulnerabilities?"
→ SELECT DISTINCT hosts.ip_address, vulnerabilities.title
  FROM hosts JOIN vulnerabilities ON hosts.id = vulnerabilities.host_id
  WHERE vulnerabilities.severity = 'critical'

$ vcli ask "find web servers with outdated Apache"
→ [Complex query with version parsing]
```

**Implementation**:
```python
# vertice/ai/modules/nl_query.py

from vertice.ai.core import GeminiClient
from vertice.workspace import WorkspaceManager

class NLQueryEngine:
    def __init__(self):
        self.gemini = GeminiClient()
        self.workspace = WorkspaceManager()

    def query(self, question: str) -> dict:
        """
        Convert natural language question to SQL query.

        Uses Gemini with schema context to generate SQL.
        """
        # Get workspace schema
        schema = self._get_schema()

        # Build prompt for Gemini
        prompt = f"""
You are a SQL expert. Convert this natural language question to SQL.

Database Schema:
{schema}

Question: {question}

Generate a valid SQLite SELECT query. Return ONLY the SQL, no explanation.
"""

        sql = self.gemini.generate(prompt)

        # Execute query
        results = self.workspace._session.execute(sql).fetchall()

        return {
            "question": question,
            "sql": sql,
            "results": results
        }
```

---

### 2. Vulnerability Correlator

**Purpose**: Auto-correlate discovered services/versions with CVE databases and exploit availability.

**Flow**:
```
Port 22 discovered → Service: OpenSSH 7.4
    ↓
Maximus queries NVD: "CVEs for OpenSSH 7.4"
    ↓
Finds: CVE-2018-15473 (User Enumeration)
    ↓
Checks ExploitDB: exploit/linux/ssh/openssh_enum_users
    ↓
Stores in vulnerabilities table + suggests:
    "💡 OpenSSH 7.4 vulnerable to user enumeration (CVE-2018-15473).
     Exploit available in Metasploit. Run user enum?"
```

**Implementation**:
```python
# vertice/ai/modules/vuln_correlator.py

import requests
from typing import List, Dict

class VulnCorrelator:
    NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def correlate_service(self, service: str, version: str) -> List[Dict]:
        """
        Query NVD for CVEs matching service/version.

        Returns: List of CVEs with metadata
        """
        # Query NVD
        params = {
            "keywordSearch": f"{service} {version}",
            "resultsPerPage": 20
        }
        response = requests.get(self.NVD_API, params=params)
        data = response.json()

        vulns = []
        for item in data.get("vulnerabilities", []):
            cve = item["cve"]
            vulns.append({
                "cve_id": cve["id"],
                "description": cve["descriptions"][0]["value"],
                "cvss_score": cve.get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("baseScore"),
                "severity": self._get_severity(cve)
            })

        # Check ExploitDB for each CVE
        for vuln in vulns:
            vuln["exploit_available"] = self._check_exploitdb(vuln["cve_id"])

        return vulns

    def _check_exploitdb(self, cve_id: str) -> Optional[str]:
        """Check if exploit exists in ExploitDB"""
        # Query ExploitDB API or scrape
        pass

# Event listener integration
from vertice.workspace import WorkspaceManager

workspace = WorkspaceManager()

@workspace.on("port_discovered")
def auto_correlate_vuln(event):
    port_id = event["port_id"]
    port = workspace._session.query(Port).get(port_id)

    if port.service and port.version:
        correlator = VulnCorrelator()
        cves = correlator.correlate_service(port.service, port.version)

        for cve in cves:
            workspace.add_vulnerability(
                host_id=port.host_id,
                port_id=port.id,
                cve_id=cve["cve_id"],
                title=cve["description"][:100],
                description=cve["description"],
                severity=cve["severity"],
                cvss_score=cve["cvss_score"],
                exploitable=bool(cve["exploit_available"]),
                exploit_available=cve["exploit_available"]
            )
```

---

### 3. Next-Step Suggester

**Purpose**: Analyze workspace state and recommend logical next actions.

**Examples**:
- "Port 80 open → Suggest: Run Nikto web scan"
- "SMB port 445 open → Suggest: Check for EternalBlue (MS17-010)"
- "5 SSH servers found → Suggest: Attempt SSH key reuse attack"

**Implementation**:
```python
# vertice/ai/modules/suggester.py

class NextStepSuggester:
    RULES = [
        {
            "condition": lambda ws: ws.has_port(80) or ws.has_port(443),
            "suggestion": "Run web vulnerability scan (Nikto/Nuclei)",
            "command": "vcli scan web {host}"
        },
        {
            "condition": lambda ws: ws.has_port(445),
            "suggestion": "Check for SMB vulnerabilities (EternalBlue)",
            "command": "vcli exploit check MS17-010 {host}"
        },
        {
            "condition": lambda ws: len(ws.get_open_hosts()) > 10,
            "suggestion": "Scan all hosts in parallel",
            "command": "vcli scan batch --targets all"
        }
    ]

    def suggest(self, workspace: WorkspaceManager) -> List[str]:
        suggestions = []
        for rule in self.RULES:
            if rule["condition"](workspace):
                suggestions.append({
                    "text": rule["suggestion"],
                    "command": rule["command"],
                    "reasoning": "Based on discovered services"
                })

        # Store in DB
        for s in suggestions:
            workspace.add_suggestion(
                suggestion_text=s["text"],
                reasoning=s["reasoning"]
            )

        return suggestions
```

---

### 4. PoC Generator

**Purpose**: Generate safe, ethical proof-of-concept exploit code for common vulnerabilities.

**Supported Vuln Types**:
- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- Command Injection
- Path Traversal
- SSRF (Server-Side Request Forgery)

**Example**:
```bash
$ vcli ai generate-poc --vuln sqli --target "http://example.com/login.php?user=admin"

✅ PoC Generated:

# SQL Injection PoC for http://example.com/login.php
# CVE: None (Generic SQLi)
# Description: Tests for boolean-based blind SQL injection

import requests

url = "http://example.com/login.php"

# Test 1: Boolean-based injection
payloads = [
    "admin' OR '1'='1",
    "admin' OR '1'='1'--",
    "admin' OR '1'='1'#"
]

for payload in payloads:
    response = requests.get(url, params={"user": payload})
    if "Welcome" in response.text:
        print(f"✅ VULNERABLE: Payload '{payload}' successful")
        break
else:
    print("❌ Not vulnerable to tested payloads")

# Remediation:
# - Use parameterized queries (prepared statements)
# - Input validation and sanitization
```

**Implementation**:
```python
# vertice/ai/modules/poc_generator.py

class PoCGenerator:
    TEMPLATES = {
        "sqli": """
import requests

url = "{target}"

payloads = [
    "admin' OR '1'='1",
    "admin' OR '1'='1'--"
]

for payload in payloads:
    response = requests.get(url, params={{"{param}": payload}})
    if "{success_indicator}" in response.text:
        print(f"✅ VULNERABLE: {{payload}}")
        break
""",
        "xss": """
import requests

url = "{target}"
payload = '<script>alert("XSS")</script>'

response = requests.post(url, data={{"{param}": payload}})

if payload in response.text:
    print("✅ VULNERABLE: Reflected XSS")
else:
    print("❌ Not vulnerable")
"""
    }

    def generate(self, vuln_type: str, target: str, **kwargs) -> str:
        template = self.TEMPLATES.get(vuln_type)
        if not template:
            raise ValueError(f"Unsupported vuln type: {vuln_type}")

        return template.format(target=target, **kwargs)
```

---

### 5. Report Drafter

**Purpose**: Auto-generate professional penetration test reports from workspace data.

**Output Formats**:
- PDF (executive summary + technical details)
- HTML (interactive, searchable)
- Markdown (for documentation)
- JSON (for integration with other tools)

**Sections**:
1. Executive Summary
2. Methodology
3. Findings (by severity)
4. Detailed Technical Analysis
5. Remediation Recommendations
6. Appendices (evidence, raw data)

**Implementation**:
```python
# vertice/ai/modules/report_drafter.py

from jinja2 import Template
import pdfkit

class ReportDrafter:
    TEMPLATE_EXECUTIVE = """
# Penetration Test Report: {{ project.name }}

## Executive Summary

During the assessment of {{ project.scope }}, a total of **{{ stats.hosts }} hosts** were discovered with **{{ stats.vulnerabilities }} vulnerabilities** identified.

### Risk Summary:
- 🔴 Critical: {{ stats.critical }}
- 🟠 High: {{ stats.high }}
- 🟡 Medium: {{ stats.medium }}
- 🟢 Low: {{ stats.low }}

### Key Findings:
{% for vuln in top_vulns %}
- **{{ vuln.title }}** ({{ vuln.severity }})
  - Affected: {{ vuln.host.ip_address }}
  - Impact: {{ vuln.description[:100] }}
{% endfor %}
"""

    def draft_report(self, workspace: WorkspaceManager, format: str = "markdown") -> str:
        project = workspace.get_current_project()
        stats = self._get_stats(workspace)
        top_vulns = workspace.query("SELECT * FROM vulnerabilities ORDER BY cvss_score DESC LIMIT 5")

        template = Template(self.TEMPLATE_EXECUTIVE)
        report = template.render(
            project=project,
            stats=stats,
            top_vulns=top_vulns
        )

        if format == "pdf":
            pdfkit.from_string(report, "report.pdf")
            return "report.pdf"

        return report
```

---

## 🎮 USER EXPERIENCE

### Proactive Assistance

**Scenario 1: During Scan**
```bash
$ vcli scan nmap 10.10.1.0/24

[Nmap running...]
✅ Host 10.10.1.5 discovered (22, 80, 443 open)

💡 Maximus: "SSH and HTTPS detected on 10.10.1.5.
    Next steps:
    1. Check for weak SSH credentials
    2. Run SSL/TLS scan (testssl.sh)
    3. Run web vulnerability scan

    Which would you like to do? [1/2/3/skip]"
```

**Scenario 2: After Findings**
```bash
$ vcli project status

📊 Project: pentest-acme
   Hosts: 12
   Vulns: 3 critical, 5 high

💡 Maximus Insights:
   • 3 hosts running outdated Apache (CVE-2021-44228 - Log4Shell)
   • Exploit available in Metasploit
   • Recommendation: Test exploitation in controlled manner

   Generate report? [Y/n]
```

---

## 📋 ROADMAP

### Phase 1 (Q1 2025): Foundation
- ✅ NL Query Engine (basic SQL generation)
- ✅ Event listener integration
- ✅ Vuln correlation (NVD API)

### Phase 2 (Q2 2025): Intelligence
- ✅ Next-step suggester (rule-based)
- ✅ PoC generator (5 vuln types)
- ✅ Report drafter (Markdown/HTML)

### Phase 3 (Q3-Q4 2025): Advanced
- ✅ Attack chain planner (MITRE ATT&CK mapping)
- ✅ Autonomous exploitation (with approval)
- ✅ Threat actor TTPs correlation
- ✅ Collaborative AI (multi-agent system)

---

**Document Version**: 1.0
**Last Updated**: January 2025
**Status**: 📋 Design Complete, Implementation Pending
