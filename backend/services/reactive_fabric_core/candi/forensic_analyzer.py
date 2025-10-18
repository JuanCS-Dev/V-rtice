"""
Forensic Analyzer
Advanced multi-layer behavioral and payload analysis for attack events
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class ForensicReport:
    """Complete forensic analysis report"""
    event_id: str
    timestamp: datetime

    # Behavioral Analysis
    behaviors: List[str] = field(default_factory=list)
    attack_stages: List[str] = field(default_factory=list)
    sophistication_score: float = 0.0  # 0-10 scale

    # Network Analysis
    source_ip: str = ""
    source_port: int = 0
    destination_port: int = 0
    protocol: str = ""
    user_agent: Optional[str] = None
    connection_duration: float = 0.0
    bytes_transferred: int = 0

    # Payload Analysis
    malware_detected: bool = False
    malware_family: Optional[str] = None
    file_hashes: List[str] = field(default_factory=list)
    exploit_cves: List[str] = field(default_factory=list)
    suspicious_commands: List[str] = field(default_factory=list)

    # Indicators of Compromise
    network_iocs: List[str] = field(default_factory=list)
    file_iocs: List[str] = field(default_factory=list)

    # Credential Analysis
    credentials_compromised: bool = False
    usernames_attempted: List[str] = field(default_factory=list)
    passwords_attempted: List[str] = field(default_factory=list)

    # Temporal Analysis
    attack_duration: float = 0.0
    request_rate: float = 0.0  # requests per second
    is_automated: bool = False

    # Context
    honeypot_type: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    analysis_confidence: float = 0.0  # 0-100%


class ForensicAnalyzer:
    """
    Multi-layer forensic analysis engine

    Analysis Layers:
    1. Behavioral - Attack patterns and TTPs
    2. Network - Connection metadata and traffic patterns
    3. Payload - Commands, exploits, malware
    4. Temporal - Timing, automation detection
    5. Sophistication - Skill level assessment
    """

    def __init__(self):
        """Initialize forensic analyzer"""
        self._initialized = False

        # Pattern databases
        self.ssh_patterns = self._load_ssh_patterns()
        self.web_patterns = self._load_web_patterns()
        self.sql_patterns = self._load_sql_patterns()
        self.command_patterns = self._load_command_patterns()

        # Known malware signatures (simplified - would integrate with real AV)
        self.malware_signatures = self._load_malware_signatures()

        # CVE database (simplified - would integrate with CVE API)
        self.cve_database = self._load_cve_database()

        # Statistics
        self.stats = {
            "total_analyzed": 0,
            "malware_detected": 0,
            "credentials_compromised": 0,
            "exploits_detected": 0
        }

    async def initialize(self):
        """Initialize analyzer with external resources"""
        if self._initialized:
            return

        logger.info("Initializing Forensic Analyzer...")

        # In production, would load:
        # - Updated malware signatures
        # - CVE database
        # - Threat actor profiles
        # - ML models for behavior analysis

        self._initialized = True
        logger.info("Forensic Analyzer initialized")

    async def analyze(self, event: Dict[str, Any]) -> ForensicReport:
        """
        Perform complete forensic analysis on event

        Args:
            event: Event data from honeypot

        Returns:
            Complete forensic report
        """
        start_time = datetime.now()

        event_id = event.get('attack_id', event.get('event_id', 'unknown'))
        honeypot_type = event.get('honeypot_type', 'unknown')

        logger.info(f"Starting forensic analysis: {event_id} (type: {honeypot_type})")

        # Initialize report
        report = ForensicReport(
            event_id=event_id,
            timestamp=datetime.now(),
            honeypot_type=honeypot_type,
            source_ip=event.get('source_ip', 'unknown'),
            source_port=event.get('source_port', 0),
            destination_port=event.get('destination_port', 0),
            protocol=event.get('protocol', 'unknown'),
            raw_data=event
        )

        # Layer 1: Network Analysis
        await self._analyze_network(event, report)

        # Layer 2: Behavioral Analysis (honeypot-specific)
        if honeypot_type in ['ssh', 'cowrie']:
            await self._analyze_ssh_behavior(event, report)
        elif honeypot_type == 'web':
            await self._analyze_web_behavior(event, report)
        elif honeypot_type == 'database':
            await self._analyze_database_behavior(event, report)

        # Layer 3: Payload Analysis
        await self._analyze_payload(event, report)

        # Layer 4: Credential Analysis
        await self._analyze_credentials(event, report)

        # Layer 5: Temporal Analysis
        await self._analyze_temporal_patterns(event, report)

        # Layer 6: Sophistication Scoring
        report.sophistication_score = self._calculate_sophistication_score(report)

        # Layer 7: IOC Extraction
        self._extract_iocs(report)

        # Calculate confidence
        report.analysis_confidence = self._calculate_confidence(report)

        # Update statistics
        self.stats["total_analyzed"] += 1
        if report.malware_detected:
            self.stats["malware_detected"] += 1
        if report.credentials_compromised:
            self.stats["credentials_compromised"] += 1
        if report.exploit_cves:
            self.stats["exploits_detected"] += 1

        analysis_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Forensic analysis complete: {event_id} "
            f"(sophistication: {report.sophistication_score:.1f}/10, "
            f"confidence: {report.analysis_confidence:.1f}%, time: {analysis_time:.2f}s)"
        )

        return report

    async def _analyze_network(self, event: Dict, report: ForensicReport):
        """Analyze network-level indicators"""
        # Extract network metadata
        report.user_agent = event.get('user_agent')
        report.connection_duration = event.get('session_duration', 0.0)
        report.bytes_transferred = event.get('bytes_transferred', 0)

        # Check for suspicious user agents
        if report.user_agent:
            suspicious_agents = [
                'sqlmap', 'nikto', 'masscan', 'nmap', 'metasploit',
                'burp', 'zap', 'acunetix', 'nessus'
            ]
            if any(agent in report.user_agent.lower() for agent in suspicious_agents):
                report.behaviors.append('scanner_user_agent')
                report.attack_stages.append('reconnaissance')

        # Analyze connection patterns
        if report.connection_duration < 1.0 and report.bytes_transferred > 1000:
            report.behaviors.append('high_speed_data_exfiltration')
            report.attack_stages.append('exfiltration')

    async def _analyze_ssh_behavior(self, event: Dict, report: ForensicReport):
        """Analyze SSH/Telnet attack behavior"""
        commands = event.get('commands', [])

        for cmd in commands:
            cmd_lower = cmd.lower()

            # Pattern matching
            for pattern_name, pattern in self.ssh_patterns.items():
                if pattern.search(cmd):
                    report.behaviors.append(pattern_name)

            # Specific behavior detection
            if any(word in cmd_lower for word in ['wget', 'curl', 'tftp']):
                report.behaviors.append('download_malware')
                report.attack_stages.append('execution')
                report.suspicious_commands.append(cmd)

            if any(word in cmd_lower for word in ['nc', 'netcat', 'bash -i', '/dev/tcp']):
                report.behaviors.append('reverse_shell')
                report.attack_stages.append('persistence')
                report.suspicious_commands.append(cmd)

            if 'crontab' in cmd_lower or 'systemctl' in cmd_lower:
                report.behaviors.append('persistence_mechanism')
                report.attack_stages.append('persistence')
                report.suspicious_commands.append(cmd)

            if any(word in cmd_lower for word in ['rm -rf', 'dd if=/dev/zero']):
                report.behaviors.append('destructive_commands')
                report.attack_stages.append('impact')
                report.suspicious_commands.append(cmd)

        # Check for credential attempts
        auth_attempts = event.get('auth_attempts', [])
        if auth_attempts:
            report.usernames_attempted = [a.get('username') for a in auth_attempts]
            report.passwords_attempted = [a.get('password') for a in auth_attempts]

            if len(auth_attempts) > 10:
                report.behaviors.append('ssh_brute_force')
                report.attack_stages.append('initial_access')

    async def _analyze_web_behavior(self, event: Dict, report: ForensicReport):
        """Analyze web attack behavior"""
        requests = event.get('requests', [])

        for req in requests:
            url = req.get('url', '')
            method = req.get('method', '')
            body = req.get('body', '')

            full_request = f"{url} {body}".lower()

            # SQL Injection detection
            for pattern in self.sql_patterns:
                if pattern.search(full_request):
                    report.behaviors.append('sql_injection')
                    report.attack_stages.append('initial_access')
                    break

            # XSS detection
            xss_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'onerror\s*=',
                r'onclick\s*=',
                r'<iframe'
            ]
            for pattern in xss_patterns:
                if re.search(pattern, full_request, re.IGNORECASE):
                    report.behaviors.append('xss_attack')
                    report.attack_stages.append('initial_access')
                    break

            # Command Injection
            cmd_injection_patterns = [
                r';\s*(cat|ls|id|whoami|pwd)',
                r'\|\s*(cat|ls|id|whoami)',
                r'`.*`',
                r'\$\(.*\)'
            ]
            for pattern in cmd_injection_patterns:
                if re.search(pattern, full_request):
                    report.behaviors.append('command_injection')
                    report.attack_stages.append('execution')
                    break

            # Path Traversal
            if '../' in url or '..\\' in url:
                report.behaviors.append('path_traversal')
                report.attack_stages.append('discovery')

            # File Upload
            if method == 'POST' and 'upload' in url:
                report.behaviors.append('file_upload')
                report.attack_stages.append('execution')

            # Authentication Bypass
            auth_bypass_patterns = [
                r"'\s*or\s*'1'\s*=\s*'1",
                r"'\s*or\s*1\s*=\s*1",
                r"admin'\s*--",
                r"' union select"
            ]
            for pattern in auth_bypass_patterns:
                if re.search(pattern, full_request, re.IGNORECASE):
                    report.behaviors.append('auth_bypass')
                    report.attack_stages.append('privilege_escalation')
                    break

    async def _analyze_database_behavior(self, event: Dict, report: ForensicReport):
        """Analyze database attack behavior"""
        queries = event.get('queries', [])

        for query in queries:
            query_lower = query.lower()

            # Data exfiltration
            if 'select' in query_lower:
                if any(table in query_lower for table in ['customers', 'users', 'credit_card', 'api_credentials']):
                    report.behaviors.append('data_exfiltration')
                    report.attack_stages.append('exfiltration')

                # Check for honeytoken access
                if 'api_credentials' in query_lower or 'ssh_keys' in query_lower:
                    report.behaviors.append('honeytoken_access')
                    report.attack_stages.append('collection')

            # Privilege escalation
            if any(word in query_lower for word in ['grant', 'alter user', 'create user']):
                report.behaviors.append('privilege_escalation')
                report.attack_stages.append('privilege_escalation')

            # Data destruction
            if any(word in query_lower for word in ['drop table', 'truncate', 'delete from']):
                report.behaviors.append('data_destruction')
                report.attack_stages.append('impact')

            # SQL injection in query
            if '--' in query or '/*' in query or 'union select' in query_lower:
                report.behaviors.append('sql_injection')
                report.attack_stages.append('initial_access')

    async def _analyze_payload(self, event: Dict, report: ForensicReport):
        """Analyze payloads for malware and exploits"""
        # Check for uploaded files
        files = event.get('uploaded_files', [])
        for file_info in files:
            file_hash = file_info.get('sha256')
            if file_hash:
                report.file_hashes.append(file_hash)

                # Check against malware signatures
                if file_hash in self.malware_signatures:
                    report.malware_detected = True
                    report.malware_family = self.malware_signatures[file_hash]
                    report.behaviors.append('malware_upload')
                    report.attack_stages.append('execution')

        # Check for exploit signatures
        payload = event.get('payload', '')
        if payload:
            for cve, signature in self.cve_database.items():
                if signature in payload:
                    report.exploit_cves.append(cve)
                    report.behaviors.append('exploit_attempt')
                    report.attack_stages.append('exploitation')

    async def _analyze_credentials(self, event: Dict, report: ForensicReport):
        """Analyze credential usage and compromise"""
        # Check for successful authentication
        if event.get('auth_success', False):
            report.credentials_compromised = True
            report.behaviors.append('successful_authentication')
            report.attack_stages.append('initial_access')

        # Check for credential dumping
        commands = event.get('commands', [])
        cred_dump_patterns = [
            'mimikatz', '/etc/shadow', '/etc/passwd',
            'sam', 'lsass', 'hashdump'
        ]
        for cmd in commands:
            if any(pattern in cmd.lower() for pattern in cred_dump_patterns):
                report.behaviors.append('credential_dumping')
                report.attack_stages.append('credential_access')
                report.suspicious_commands.append(cmd)

    async def _analyze_temporal_patterns(self, event: Dict, report: ForensicReport):
        """Analyze timing patterns to detect automation"""
        # Get request timing
        requests = event.get('requests', [])
        if len(requests) > 5:
            # Calculate request intervals
            timestamps = [r.get('timestamp') for r in requests if r.get('timestamp')]
            if len(timestamps) > 1:
                intervals = []
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    intervals.append(interval)

                # Check for consistent timing (indicates automation)
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)

                    if variance < 0.1:  # Very consistent timing
                        report.is_automated = True
                        report.behaviors.append('automated_attack')

                    report.request_rate = 1.0 / avg_interval if avg_interval > 0 else 0.0

        # Attack duration
        report.attack_duration = event.get('session_duration', 0.0)

    def _calculate_sophistication_score(self, report: ForensicReport) -> float:
        """
        Calculate attack sophistication score (0-10)

        Factors:
        - Exploit usage (3 points)
        - Custom malware (2 points)
        - Multi-stage attack (2 points)
        - Anti-detection techniques (2 points)
        - Manual operation vs automation (1 point)
        """
        score = 0.0

        # Exploit usage
        if report.exploit_cves:
            score += 3.0

        # Malware sophistication
        if report.malware_detected:
            if report.malware_family and 'custom' in report.malware_family.lower():
                score += 2.0
            else:
                score += 1.0

        # Multi-stage attack
        unique_stages = set(report.attack_stages)
        if len(unique_stages) >= 3:
            score += 2.0
        elif len(unique_stages) >= 2:
            score += 1.0

        # Anti-detection
        anti_detection_behaviors = [
            'obfuscation', 'anti_vm', 'sandbox_evasion',
            'defense_evasion', 'log_deletion'
        ]
        if any(b in report.behaviors for b in anti_detection_behaviors):
            score += 2.0

        # Manual vs automated
        if not report.is_automated:
            score += 1.0

        return min(score, 10.0)

    def _extract_iocs(self, report: ForensicReport):
        """Extract all Indicators of Compromise"""
        # Network IOCs
        if report.source_ip and report.source_ip != 'unknown':
            report.network_iocs.append(f"ip:{report.source_ip}")

        # File IOCs
        for file_hash in report.file_hashes:
            report.file_iocs.append(f"sha256:{file_hash}")

        # Extract IPs and domains from commands
        for cmd in report.suspicious_commands:
            # IP addresses
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ips = re.findall(ip_pattern, cmd)
            for ip in ips:
                if ip not in report.network_iocs:
                    report.network_iocs.append(f"ip:{ip}")

            # Domains
            domain_pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b'
            domains = re.findall(domain_pattern, cmd, re.IGNORECASE)
            for domain in domains:
                if domain not in report.network_iocs:
                    report.network_iocs.append(f"domain:{domain}")

    def _calculate_confidence(self, report: ForensicReport) -> float:
        """Calculate analysis confidence (0-100%)"""
        confidence = 50.0  # Base confidence

        # More behaviors identified = higher confidence
        confidence += min(len(report.behaviors) * 5, 30)

        # File hashes available = higher confidence
        if report.file_hashes:
            confidence += 10

        # Known exploits = higher confidence
        if report.exploit_cves:
            confidence += 10

        return min(confidence, 100.0)

    def _load_ssh_patterns(self) -> Dict[str, re.Pattern]:
        """Load SSH attack patterns"""
        return {
            'reconnaissance': re.compile(r'(uname|whoami|id|ps|netstat|ifconfig)', re.IGNORECASE),
            'privilege_escalation': re.compile(r'(sudo|su -|chmod \+s)', re.IGNORECASE),
            'lateral_movement': re.compile(r'(ssh|scp|rsync).*@', re.IGNORECASE),
            'persistence': re.compile(r'(crontab|\.bashrc|\.profile|authorized_keys)', re.IGNORECASE),
            'credential_access': re.compile(r'(/etc/shadow|/etc/passwd|\.ssh/id_rsa)', re.IGNORECASE),
            'discovery': re.compile(r'(find|locate|ls -la|cat /etc)', re.IGNORECASE),
        }

    def _load_web_patterns(self) -> Dict[str, re.Pattern]:
        """Load web attack patterns"""
        return {
            'sql_injection': re.compile(
                r"(\bSELECT\b|\bUNION\b|\bINSERT\b|'.*or.*=|--|\*\/)",
                re.IGNORECASE
            ),
            'xss': re.compile(r'<script|javascript:|onerror=|onclick=', re.IGNORECASE),
            'command_injection': re.compile(r';\s*(cat|ls|id|whoami)', re.IGNORECASE),
        }

    def _load_sql_patterns(self) -> List[re.Pattern]:
        """Load SQL injection patterns"""
        return [
            re.compile(r"'\s*or\s*'1'\s*=\s*'1", re.IGNORECASE),
            re.compile(r"'\s*or\s*1\s*=\s*1", re.IGNORECASE),
            re.compile(r"\bunion\b.*\bselect\b", re.IGNORECASE),
            re.compile(r";\s*drop\s+table", re.IGNORECASE),
            re.compile(r"--", re.IGNORECASE),
        ]

    def _load_command_patterns(self) -> Dict[str, re.Pattern]:
        """Load command injection patterns"""
        return {
            'shell_execution': re.compile(r'`.*`|\$\(.*\)', re.IGNORECASE),
            'pipe_command': re.compile(r'\|\s*(cat|nc|bash)', re.IGNORECASE),
        }

    def _load_malware_signatures(self) -> Dict[str, str]:
        """Load malware signatures (simplified)"""
        # In production, this would be a real malware database
        return {
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855': 'Mirai',
            '5f4dcc3b5aa765d61d8327deb882cf99': 'Generic_Backdoor',
            'd41d8cd98f00b204e9800998ecf8427e': 'Empty_File',
        }

    def _load_cve_database(self) -> Dict[str, str]:
        """Load CVE signatures (simplified)"""
        # In production, this would integrate with CVE API
        return {
            'CVE-2021-44228': 'jndi:ldap://',  # Log4Shell
            'CVE-2017-5638': 'Content-Type:.*ognl',  # Struts2
            'CVE-2019-0708': 'RDP_BlueKeep_Signature',  # BlueKeep
        }

    def get_stats(self) -> Dict:
        """Get analyzer statistics"""
        return self.stats.copy()
