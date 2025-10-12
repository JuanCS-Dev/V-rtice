"""
TTP Mapper - MITRE ATT&CK Technique Mapping
Maps observed behaviors to MITRE ATT&CK techniques.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation - NO MOCK, NO PLACEHOLDER

Compliance com Paper:
- "Métricas de Validação para a Fase 1"
- "Quantos TTPs de APTs precisamos identificar para validar o modelo"
- Target: ≥10 técnicas MITRE ATT&CK únicas
"""

import re
import structlog
from typing import List, Dict, Any, Optional, Set

logger = structlog.get_logger()


class TTPMapper:
    """
    Maps observed attack behaviors to MITRE ATT&CK techniques.
    
    Uses pattern matching on commands, credentials, and attack types
    to identify tactics, techniques, and procedures (TTPs) used by attackers.
    
    References:
    - MITRE ATT&CK Framework: https://attack.mitre.org/
    - Focus on techniques observed in honeypots (Initial Access, Execution, Discovery, C2)
    """
    
    # Comprehensive TTP pattern database
    TTP_PATTERNS = {
        # ====================================================================
        # INITIAL ACCESS (TA0001)
        # ====================================================================
        "T1190": {  # Exploit Public-Facing Application
            "patterns": [
                r"(?i)(sql injection|sqli|union select|' or '1'='1)",
                r"(?i)(xss|cross-site scripting|<script>)",
                r"(?i)(rce|remote code execution|eval\(|exec\()",
                r"(?i)(command injection|;.*cat|;.*ls|&&.*whoami)"
            ],
            "name": "Exploit Public-Facing Application",
            "tactic": "Initial Access"
        },
        "T1133": {  # External Remote Services
            "patterns": [
                r"(?i)(ssh|rdp|vnc|telnet).*login",
                r"(?i)remote.*access"
            ],
            "name": "External Remote Services",
            "tactic": "Initial Access"
        },
        "T1566": {  # Phishing
            "patterns": [
                r"(?i)(phish|malicious.*link|credential.*harvest)"
            ],
            "name": "Phishing",
            "tactic": "Initial Access"
        },
        
        # ====================================================================
        # EXECUTION (TA0002)
        # ====================================================================
        "T1059.004": {  # Command and Scripting Interpreter: Unix Shell
            "patterns": [
                r"/bin/(bash|sh|zsh|csh|ksh)",
                r"(?i)bash -c",
                r"(?i)sh -c",
                r"#!/bin/(bash|sh)"
            ],
            "name": "Command and Scripting Interpreter: Unix Shell",
            "tactic": "Execution"
        },
        "T1059.006": {  # Command and Scripting Interpreter: Python
            "patterns": [
                r"(?i)python\s+",
                r"(?i)python3\s+",
                r"#!/usr/bin/(env )?python"
            ],
            "name": "Command and Scripting Interpreter: Python",
            "tactic": "Execution"
        },
        "T1053.003": {  # Scheduled Task/Job: Cron
            "patterns": [
                r"(?i)crontab",
                r"(?i)/etc/crontab",
                r"(?i)/var/spool/cron"
            ],
            "name": "Scheduled Task/Job: Cron",
            "tactic": "Execution"
        },
        
        # ====================================================================
        # PERSISTENCE (TA0003)
        # ====================================================================
        "T1053": {  # Scheduled Task/Job
            "patterns": [
                r"(?i)(crontab|at |systemd timer)",
                r"(?i)echo.*>>/etc/crontab"
            ],
            "name": "Scheduled Task/Job",
            "tactic": "Persistence"
        },
        "T1098": {  # Account Manipulation
            "patterns": [
                r"(?i)useradd",
                r"(?i)adduser",
                r"(?i)usermod",
                r"(?i)passwd\s+"
            ],
            "name": "Account Manipulation",
            "tactic": "Persistence"
        },
        "T1136": {  # Create Account
            "patterns": [
                r"(?i)(useradd|adduser) ",
                r"(?i)net user.*add"
            ],
            "name": "Create Account",
            "tactic": "Persistence"
        },
        
        # ====================================================================
        # PRIVILEGE ESCALATION (TA0004)
        # ====================================================================
        "T1068": {  # Exploitation for Privilege Escalation
            "patterns": [
                r"(?i)(dirty.*cow|dirtycow|ptrace)",
                r"(?i)exploit.*priv.*esc"
            ],
            "name": "Exploitation for Privilege Escalation",
            "tactic": "Privilege Escalation"
        },
        "T1548.003": {  # Abuse Elevation Control Mechanism: Sudo
            "patterns": [
                r"(?i)sudo ",
                r"(?i)/etc/sudoers"
            ],
            "name": "Abuse Elevation Control Mechanism: Sudo",
            "tactic": "Privilege Escalation"
        },
        
        # ====================================================================
        # DEFENSE EVASION (TA0005)
        # ====================================================================
        "T1070.004": {  # Indicator Removal: File Deletion
            "patterns": [
                r"(?i)rm -rf",
                r"(?i)rm .*\.log",
                r"(?i)echo.*> /var/log",
                r"(?i)>.*history"
            ],
            "name": "Indicator Removal: File Deletion",
            "tactic": "Defense Evasion"
        },
        "T1070.003": {  # Indicator Removal: Clear Command History
            "patterns": [
                r"(?i)history -c",
                r"(?i)unset HISTFILE",
                r"(?i)export HISTFILE=/dev/null",
                r"(?i)rm .*bash_history"
            ],
            "name": "Indicator Removal: Clear Command History",
            "tactic": "Defense Evasion"
        },
        
        # ====================================================================
        # CREDENTIAL ACCESS (TA0006)
        # ====================================================================
        "T1110": {  # Brute Force
            "patterns": [
                r"(?i)(brute.*force|password.*spray)",
                r"(?i)(hydra|medusa|ncrack|patator)"
            ],
            "name": "Brute Force",
            "tactic": "Credential Access"
        },
        "T1110.001": {  # Brute Force: Password Guessing
            "patterns": [
                r"(?i)(admin|root|user|test):.*",
                r"(?i)password.*guess"
            ],
            "name": "Brute Force: Password Guessing",
            "tactic": "Credential Access"
        },
        "T1003": {  # OS Credential Dumping
            "patterns": [
                r"(?i)cat /etc/shadow",
                r"(?i)cat /etc/passwd",
                r"(?i)mimikatz",
                r"(?i)hashdump"
            ],
            "name": "OS Credential Dumping",
            "tactic": "Credential Access"
        },
        
        # ====================================================================
        # DISCOVERY (TA0007)
        # ====================================================================
        "T1082": {  # System Information Discovery
            "patterns": [
                r"(?i)uname",
                r"(?i)hostname",
                r"(?i)cat /etc/issue",
                r"(?i)cat /proc/version",
                r"(?i)systeminfo",
                r"(?i)whoami"
            ],
            "name": "System Information Discovery",
            "tactic": "Discovery"
        },
        "T1083": {  # File and Directory Discovery
            "patterns": [
                r"(?i)(ls|dir) ",
                r"(?i)find /",
                r"(?i)tree ",
                r"(?i)cat .*\.(txt|log|conf|cfg)"
            ],
            "name": "File and Directory Discovery",
            "tactic": "Discovery"
        },
        "T1033": {  # System Owner/User Discovery
            "patterns": [
                r"(?i)whoami",
                r"(?i)id$",
                r"(?i)w$",
                r"(?i)who$",
                r"(?i)last$"
            ],
            "name": "System Owner/User Discovery",
            "tactic": "Discovery"
        },
        "T1057": {  # Process Discovery
            "patterns": [
                r"(?i)ps ",
                r"(?i)top$",
                r"(?i)htop$",
                r"(?i)tasklist"
            ],
            "name": "Process Discovery",
            "tactic": "Discovery"
        },
        "T1046": {  # Network Service Discovery
            "patterns": [
                r"(?i)netstat",
                r"(?i)ss -",
                r"(?i)lsof -i"
            ],
            "name": "Network Service Discovery",
            "tactic": "Discovery"
        },
        
        # ====================================================================
        # COLLECTION (TA0009)
        # ====================================================================
        "T1005": {  # Data from Local System
            "patterns": [
                r"(?i)cat .*(passwd|shadow|secret|private|key)",
                r"(?i)find .*\.(txt|doc|pdf|xls)"
            ],
            "name": "Data from Local System",
            "tactic": "Collection"
        },
        
        # ====================================================================
        # COMMAND AND CONTROL (TA0011)
        # ====================================================================
        "T1071.001": {  # Application Layer Protocol: Web Protocols
            "patterns": [
                r"(?i)(wget|curl) http",
                r"(?i)python.*http\.server",
                r"(?i)nc.*-l.*-p"
            ],
            "name": "Application Layer Protocol: Web Protocols",
            "tactic": "Command and Control"
        },
        "T1105": {  # Ingress Tool Transfer
            "patterns": [
                r"(?i)(wget|curl).*\.(sh|py|exe|elf)",
                r"(?i)scp ",
                r"(?i)ftp.*get"
            ],
            "name": "Ingress Tool Transfer",
            "tactic": "Command and Control"
        },
        "T1572": {  # Protocol Tunneling
            "patterns": [
                r"(?i)(ssh -[DLR]|reverse.*tunnel)",
                r"(?i)proxychains"
            ],
            "name": "Protocol Tunneling",
            "tactic": "Command and Control"
        },
        
        # ====================================================================
        # IMPACT (TA0040)
        # ====================================================================
        "T1486": {  # Data Encrypted for Impact
            "patterns": [
                r"(?i)(ransomware|encrypt|crypt|aes)",
                r"(?i)openssl.*enc"
            ],
            "name": "Data Encrypted for Impact",
            "tactic": "Impact"
        },
        "T1490": {  # Inhibit System Recovery
            "patterns": [
                r"(?i)vssadmin.*delete.*shadows",
                r"(?i)wbadmin.*delete.*backup",
                r"(?i)rm -rf /.*backup"
            ],
            "name": "Inhibit System Recovery",
            "tactic": "Impact"
        }
    }
    
    def map_ttps(
        self,
        commands: List[str],
        attack_type: str,
        credentials: Optional[List[tuple[str, str]]] = None
    ) -> List[str]:
        """
        Map observed commands and attack type to MITRE ATT&CK TTPs.
        
        Args:
            commands: List of commands executed by attacker
            attack_type: Type of attack (e.g., "ssh_brute_force")
            credentials: Optional list of (username, password) tuples
        
        Returns:
            List of MITRE technique IDs (e.g., ["T1110", "T1059.004"])
        """
        detected_ttps: Set[str] = set()
        
        # Combine all commands for pattern matching
        all_commands = " ".join(commands).lower()
        
        # Pattern-based matching
        for ttp_id, ttp_info in self.TTP_PATTERNS.items():
            for pattern in ttp_info["patterns"]:
                if re.search(pattern, all_commands, re.IGNORECASE):
                    detected_ttps.add(ttp_id)
                    logger.debug(
                        "ttp_pattern_matched",
                        ttp_id=ttp_id,
                        technique=ttp_info["name"],
                        pattern=pattern
                    )
        
        # Attack-type based mapping
        detected_ttps.update(self._map_by_attack_type(attack_type))
        
        # Credential-based mapping
        if credentials:
            detected_ttps.update(self._map_by_credentials(credentials))
        
        # Command-based heuristics
        detected_ttps.update(self._map_by_command_heuristics(commands))
        
        result = sorted(list(detected_ttps))
        
        logger.info(
            "ttp_mapping_completed",
            ttps_identified=len(result),
            ttps=result,
            commands_analyzed=len(commands)
        )
        
        return result
    
    def _map_by_attack_type(self, attack_type: str) -> Set[str]:
        """Map based on attack type classification."""
        mapping = {
            "ssh_brute_force": {"T1110", "T1110.001", "T1133"},
            "ssh_successful_login": {"T1133"},
            "ssh_post_exploitation": {"T1059.004", "T1082", "T1083"},
            "ssh_compromise_malware_download": {"T1105", "T1071.001"},
            "sql_injection": {"T1190"},
            "web_exploit": {"T1190"},
            "command_injection": {"T1190", "T1059.004"}
        }
        
        return mapping.get(attack_type, set())
    
    def _map_by_credentials(self, credentials: List[tuple[str, str]]) -> Set[str]:
        """Map based on credential usage patterns."""
        ttps: Set[str] = set()
        
        # Check for common/default credentials
        common_users = {"root", "admin", "administrator", "user", "test"}
        common_passwords = {"password", "123456", "admin", "root", "toor"}
        
        for username, password in credentials:
            if username.lower() in common_users or password.lower() in common_passwords:
                ttps.add("T1110.001")  # Password Guessing
        
        # Multiple credential attempts → Brute Force
        if len(credentials) > 3:
            ttps.add("T1110")
        
        return ttps
    
    def _map_by_command_heuristics(self, commands: List[str]) -> Set[str]:
        """Advanced heuristics for TTP identification."""
        ttps = set()
        
        if not commands:
            return ttps
        
        # Check for reconnaissance patterns
        recon_commands = {"uname", "whoami", "hostname", "id", "w", "who"}
        if any(cmd in recon_commands for cmd in [c.split()[0] if c.split() else "" for c in commands]):
            ttps.add("T1082")  # System Information Discovery
        
        # Check for persistence attempts
        persistence_keywords = {"crontab", "systemctl", "service", "rc.local"}
        if any(kw in " ".join(commands).lower() for kw in persistence_keywords):
            ttps.add("T1053")  # Scheduled Task/Job
        
        # Check for data exfiltration
        if any(cmd.startswith(("curl", "wget")) for cmd in commands):
            ttps.add("T1105")  # Ingress Tool Transfer
        
        # Check for covering tracks
        if any("history" in cmd.lower() or "rm" in cmd.lower() for cmd in commands):
            ttps.add("T1070")  # Indicator Removal
        
        return ttps
    
    def get_ttp_info(self, technique_id: str) -> Dict[str, Any]:
        """
        Get TTP information (name, tactic) for a given technique ID.
        
        Args:
            technique_id: MITRE technique ID (e.g., "T1110")
        
        Returns:
            Dict with technique_id, name and tactic keys
        """
        ttp_info = self.TTP_PATTERNS.get(technique_id, {})
        
        # Extract name and tactic (both are strings in TTP_PATTERNS)
        name = ttp_info.get("name") if ttp_info else f"Unknown Technique {technique_id}"
        tactic = ttp_info.get("tactic") if ttp_info else "Unknown"
        
        return {
            "technique_id": technique_id,
            "name": name if isinstance(name, str) else str(name),
            "tactic": tactic if isinstance(tactic, str) else str(tactic)
        }
    
    def get_all_techniques(self) -> List[Dict[str, Any]]:
        """
        Get list of all techniques this mapper can identify.
        
        Returns:
            List of dicts with technique_id, name, tactic
        """
        return [
            {
                "technique_id": tid,
                "name": str(info.get("name", "Unknown")),
                "tactic": str(info.get("tactic", "Unknown"))
            }
            for tid, info in self.TTP_PATTERNS.items()
        ]
