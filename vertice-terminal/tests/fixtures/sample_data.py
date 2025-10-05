"""
Test Fixtures and Sample Data
==============================

Dados de teste para validação completa.
"""

import json
from pathlib import Path

# Diretório de fixtures
FIXTURES_DIR = Path(__file__).parent

# Sample targets para testes
SAMPLE_TARGETS = {
    "domain_safe": "example.com",
    "domain_test": "test.example.com",
    "ip_safe": "127.0.0.1",
    "ip_test": "8.8.8.8",
    "hash_test": "d41d8cd98f00b204e9800998ecf8427e",  # MD5 empty string
    "username_test": "test_user_vertice",
    "email_test": "test@example.com",
    "cve_test": "CVE-2021-44228",  # Log4Shell
}

# Sample threat data for Immunis
SAMPLE_THREAT_DATA = {
    "source": "test_network_monitor",
    "data": {
        "packets": [
            {"src": "192.168.1.100", "dst": "192.168.1.1", "port": 443},
            {"src": "192.168.1.100", "dst": "malicious.example.com", "port": 4444}
        ]
    },
    "context": {
        "interface": "eth0",
        "timestamp": "2025-10-04T00:00:00Z"
    }
}

# Sample decision request for Cognitive
SAMPLE_DECISION_REQUEST = {
    "situation": "Suspicious network activity detected from internal host",
    "options": [
        {
            "action": "block_immediately",
            "risk": "low",
            "impact": "high",
            "cost": 100
        },
        {
            "action": "monitor_and_alert",
            "risk": "medium",
            "impact": "low",
            "cost": 10
        },
        {
            "action": "investigate_further",
            "risk": "high",
            "impact": "low",
            "cost": 50
        }
    ],
    "constraints": {
        "time_critical": True,
        "max_cost": 100,
        "compliance_required": ["PCI-DSS", "GDPR"]
    },
    "objectives": [
        "minimize_security_risk",
        "maintain_operations",
        "comply_with_regulations"
    ]
}

# Sample HCL workflow
SAMPLE_HCL_WORKFLOW = """
workflow "security_audit_test" {
    description = "Test security audit workflow"

    step "scan" {
        action = "scan_network"
        target = "127.0.0.1"
        scan_type = "quick"
    }

    step "analyze" {
        action = "analyze_vulnerabilities"
        depends_on = ["scan"]
    }

    step "report" {
        action = "generate_report"
        depends_on = ["analyze"]
        format = "json"
    }
}
"""

def create_test_files():
    """Cria arquivos de teste necessários."""
    # Threat data JSON
    threat_file = FIXTURES_DIR / "sample_threat.json"
    with open(threat_file, 'w') as f:
        json.dump(SAMPLE_THREAT_DATA, f, indent=2)

    # Decision request JSON
    decision_file = FIXTURES_DIR / "sample_decision.json"
    with open(decision_file, 'w') as f:
        json.dump(SAMPLE_DECISION_REQUEST, f, indent=2)

    # HCL workflow
    hcl_file = FIXTURES_DIR / "sample_workflow.hcl"
    with open(hcl_file, 'w') as f:
        f.write(SAMPLE_HCL_WORKFLOW)

    return {
        "threat_file": str(threat_file),
        "decision_file": str(decision_file),
        "hcl_file": str(hcl_file)
    }

# Test session IDs
TEST_SESSION_IDS = {
    "valid": "test_session_valid_123",
    "invalid": "test_session_invalid_999",
    "memory_test": "test_session_memory_456"
}

# Expected service ports
SERVICE_PORTS = {
    "maximus_core": 8001,
    "api_gateway": 8000,
    "threat_intel": 8013,
    "osint": 8007,
    "malware": 8011,
    "ssl_monitor": 8012,
    "ip_intel": 8000,
    "nmap": 8006,
    "domain": 8003,
}

if __name__ == "__main__":
    files = create_test_files()
    print("✅ Test fixtures created:")
    for name, path in files.items():
        print(f"  - {name}: {path}")
