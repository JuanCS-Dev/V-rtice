"""
DVWA Web Honeypot Implementation
Damn Vulnerable Web Application honeypot for capturing web attacks
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from .base_honeypot import BaseHoneypot, HoneypotType, AttackCapture, AttackStage

logger = logging.getLogger(__name__)

class DVWAWebHoneypot(BaseHoneypot):
    """
    DVWA Web Application Honeypot
    Captures web-based attacks including SQL injection, XSS, file uploads
    """

    def __init__(self,
                 honeypot_id: str = "dvwa_web",
                 http_port: int = 8080,
                 https_port: int = 8443,
                 layer: int = 3):
        """
        Initialize DVWA Web honeypot

        Args:
            honeypot_id: Unique identifier
            http_port: HTTP port to listen on
            https_port: HTTPS port to listen on
            layer: Network layer
        """
        super().__init__(
            honeypot_id=honeypot_id,
            honeypot_type=HoneypotType.WEB,
            port=http_port,
            layer=layer
        )

        self.https_port = https_port
        self.dvwa_config = self._generate_config()

        # Attack detection patterns
        self.attack_patterns = self._load_attack_patterns()

        # Session tracking
        self.sessions: Dict[str, Dict] = {}

        # Honeytokens planted in the app
        self.honeytokens_planted = []

    def _generate_config(self) -> Dict[str, Any]:
        """Generate DVWA configuration"""
        return {
            "security_level": "low",  # Intentionally vulnerable
            "database": {
                "host": "localhost",
                "port": 3306,
                "name": "dvwa",
                "user": "dvwa_user",
                "password": "dvwa_pass"  # Weak but intentional
            },
            "recaptcha": {
                "enabled": False  # Make it easier to attack
            },
            "features": {
                "sql_injection": True,
                "xss_reflected": True,
                "xss_stored": True,
                "csrf": True,
                "file_upload": True,
                "file_inclusion": True,
                "command_injection": True,
                "brute_force": True
            }
        }

    def _load_attack_patterns(self) -> Dict[str, re.Pattern]:
        """Load attack detection patterns"""
        return {
            # SQL Injection patterns
            "sql_injection": re.compile(
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER|EXEC)\b|"
                r"(--)|(;)|(\bOR\b.*=.*)|(\bAND\b.*=.*))",
                re.IGNORECASE
            ),

            # XSS patterns
            "xss_reflected": re.compile(
                r"(<script|javascript:|onerror=|onclick=|onload=|<iframe|<img.*onerror)",
                re.IGNORECASE
            ),

            # Command injection patterns
            "command_injection": re.compile(
                r"(;|\||&&|\$\(|`|>|<|\n|\r|wget|curl|nc|bash|sh|python|perl|ruby)",
                re.IGNORECASE
            ),

            # Path traversal patterns
            "path_traversal": re.compile(
                r"(\.\./|\.\.\\|%2e%2e|%252e%252e)",
                re.IGNORECASE
            ),

            # File upload patterns (malicious extensions)
            "malicious_upload": re.compile(
                r"\.(php|jsp|asp|aspx|exe|sh|bat|cmd|ps1)$",
                re.IGNORECASE
            ),

            # Authentication bypass patterns
            "auth_bypass": re.compile(
                r"('|\"|--|;|\/\*|\*\/|admin'--)",
                re.IGNORECASE
            )
        }

    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration for DVWA"""
        return {
            "image": "vulnerables/web-dvwa:latest",
            "internal_port": 80,
            "hostname": "webapp-prod-01",
            "environment": {
                "MYSQL_DATABASE": "dvwa",
                "MYSQL_USER": "dvwa_user",
                "MYSQL_PASSWORD": "dvwa_pass",
                "MYSQL_ROOT_PASSWORD": "root_pass",
                "RECAPTCHA": "false",
                "PHP_DISPLAY_ERRORS": "1"  # Make it look like dev environment
            },
            "volumes": [
                f"{self.log_path}:/var/log/apache2",
                f"{self.log_path}/dvwa:/var/www/html/hackable/uploads",
                f"{self.log_path}/access:/var/log/access"
            ],
            "memory": "1g",
            "cpus": "1.0",
            "ports": [
                f"{self.port}:80",
                f"{self.https_port}:443"
            ]
        }

    async def start(self) -> bool:
        """Start DVWA honeypot"""
        logger.info(f"Starting DVWA Web honeypot on ports {self.port}/{self.https_port}")

        # Create necessary directories
        for dir_name in ["uploads", "access", "apache2", "sessions"]:
            (self.log_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Plant honeytokens in the application
        await self._plant_honeytokens()

        # Deploy container
        success = await self.deploy()

        if success:
            # Start log monitoring
            asyncio.create_task(self._monitor_access_logs())
            asyncio.create_task(self._monitor_apache_logs())

        return success

    async def stop(self) -> bool:
        """Stop DVWA honeypot"""
        logger.info("Stopping DVWA Web honeypot")
        await self.shutdown()
        return True

    async def _plant_honeytokens(self):
        """Plant honeytokens in the web application"""
        honeytokens = [
            {
                "type": "aws_credentials",
                "location": "config.php",
                "content": {
                    "access_key": "AKIAIOSFODNN7EXAMPLE",
                    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                }
            },
            {
                "type": "api_token",
                "location": "api_config.php",
                "content": {
                    "stripe_key": "sk_live_51HoneytokenExample",
                    "sendgrid_key": "SG.HoneytokenExampleKey123"
                }
            },
            {
                "type": "database_creds",
                "location": "db_backup.sql",
                "content": {
                    "prod_host": "prod-db.internal.company.com",
                    "prod_user": "admin",
                    "prod_pass": "Sup3rS3cr3t!"
                }
            }
        ]

        for token in honeytokens:
            self.honeytokens_planted.append(token)
            logger.info(f"Planted honeytoken: {token['type']} in {token['location']}")

    async def _process_logs(self):
        """Process DVWA logs for attack detection"""
        # This is called periodically by the base class
        pass

    async def _monitor_access_logs(self):
        """Monitor Apache access logs in real-time"""
        access_log = self.log_path / "access" / "access.log"

        # Wait for log file to be created
        while not access_log.exists() and self._running:
            await asyncio.sleep(5)

        if not self._running:
            return

        # Tail the log file
        cmd = ["tail", "-f", str(access_log)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        while self._running:
            try:
                line = await process.stdout.readline()
                if not line:
                    break

                log_entry = line.decode().strip()
                await self._process_access_log_entry(log_entry)

            except Exception as e:
                logger.error(f"Error monitoring access logs: {e}")

        process.terminate()

    async def _process_access_log_entry(self, log_entry: str):
        """Process a single access log entry"""
        # Parse Apache log format
        # Example: 1.2.3.4 - - [13/Oct/2025:10:00:00 +0000] "GET /index.php?id=1' OR '1'='1 HTTP/1.1" 200 1234

        match = re.match(
            r'(\S+) - - \[(.*?)\] "(\S+) (\S+) HTTP/\S+" (\d+) (\d+)',
            log_entry
        )

        if not match:
            return

        ip, timestamp, method, url, status, size = match.groups()

        # Decode URL
        url_decoded = unquote(url)

        # Detect attacks in URL
        attacks_detected = []

        for attack_type, pattern in self.attack_patterns.items():
            if pattern.search(url_decoded):
                attacks_detected.append(attack_type)

        if attacks_detected:
            await self._handle_attack_detected(
                ip=ip,
                method=method,
                url=url_decoded,
                attacks=attacks_detected,
                status_code=int(status)
            )

    async def _monitor_apache_logs(self):
        """Monitor Apache error logs for PHP errors and warnings"""
        error_log = self.log_path / "apache2" / "error.log"

        while not error_log.exists() and self._running:
            await asyncio.sleep(5)

        if not self._running:
            return

        cmd = ["tail", "-f", str(error_log)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        while self._running:
            try:
                line = await process.stdout.readline()
                if not line:
                    break

                error_entry = line.decode().strip()
                await self._process_error_log_entry(error_entry)

            except Exception as e:
                logger.error(f"Error monitoring error logs: {e}")

        process.terminate()

    async def _process_error_log_entry(self, error_entry: str):
        """Process Apache error log entry"""
        # Look for SQL errors (indicates SQL injection attempt)
        if "SQL" in error_entry or "mysql" in error_entry.lower():
            logger.warning(f"SQL error detected: {error_entry[:100]}")

        # Look for file access errors (path traversal)
        if "failed to open stream" in error_entry or "No such file" in error_entry:
            logger.warning(f"File access error: {error_entry[:100]}")

    async def _handle_attack_detected(
        self,
        ip: str,
        method: str,
        url: str,
        attacks: List[str],
        status_code: int
    ):
        """Handle detected web attack"""
        # Get or create session
        session_id = f"{ip}_{datetime.now().strftime('%Y%m%d_%H')}"

        if session_id not in self.active_sessions:
            attack = AttackCapture(
                id=session_id,
                honeypot_id=self.honeypot_id,
                honeypot_type=self.honeypot_type,
                timestamp=datetime.now(),
                source_ip=ip,
                source_port=0,  # Unknown for web
                destination_port=self.port,
                protocol="http",
                attack_stage=self._determine_attack_stage(attacks)
            )
            self.active_sessions[session_id] = attack
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1

        attack = self.active_sessions[session_id]

        # Record the attack
        attack_details = f"{method} {url}"
        attack.commands.append(attack_details)

        # Calculate threat score
        threat_score = self._calculate_threat_score(attacks, status_code)
        attack.threat_score = max(attack.threat_score, threat_score)

        # Add IOCs
        attack.iocs.append(f"url:{url}")

        # Map to TTPs
        ttps = self._map_attacks_to_ttps(attacks)
        attack.ttps.extend(ttps)

        # Check for honeytoken access
        if self._check_honeytoken_access(url):
            attack.threat_score = 10.0  # Maximum threat
            attack.iocs.append("honeytoken_accessed")
            logger.critical(f"HONEYTOKEN ACCESS detected from {ip}: {url}")

        logger.info(
            f"Web attack detected from {ip}: "
            f"{', '.join(attacks)} (threat: {threat_score:.1f})"
        )

    def _determine_attack_stage(self, attacks: List[str]) -> AttackStage:
        """Determine MITRE ATT&CK stage from attack types"""
        if "sql_injection" in attacks or "auth_bypass" in attacks:
            return AttackStage.INITIAL_ACCESS
        elif "command_injection" in attacks:
            return AttackStage.EXECUTION
        elif "malicious_upload" in attacks:
            return AttackStage.PERSISTENCE
        elif "path_traversal" in attacks:
            return AttackStage.DISCOVERY
        else:
            return AttackStage.RECONNAISSANCE

    def _calculate_threat_score(self, attacks: List[str], status_code: int) -> float:
        """Calculate threat score for detected attacks"""
        score = 0.0

        # Base score by attack type
        attack_scores = {
            "sql_injection": 8.0,
            "command_injection": 9.0,
            "malicious_upload": 9.5,
            "xss_reflected": 6.0,
            "path_traversal": 7.0,
            "auth_bypass": 8.5
        }

        for attack in attacks:
            if attack in attack_scores:
                score = max(score, attack_scores[attack])

        # Boost score if successful (200 response)
        if status_code == 200:
            score += 1.0

        # Multiple attacks = more sophisticated
        if len(attacks) > 1:
            score += 0.5 * len(attacks)

        return min(score, 10.0)

    def _map_attacks_to_ttps(self, attacks: List[str]) -> List[str]:
        """Map attack types to MITRE ATT&CK TTPs"""
        ttp_mapping = {
            "sql_injection": ["T1190"],  # Exploit Public-Facing Application
            "command_injection": ["T1059", "T1059.004"],  # Command and Scripting Interpreter
            "xss_reflected": ["T1189"],  # Drive-by Compromise
            "path_traversal": ["T1083"],  # File and Directory Discovery
            "malicious_upload": ["T1105"],  # Ingress Tool Transfer
            "auth_bypass": ["T1078"]  # Valid Accounts
        }

        ttps = []
        for attack in attacks:
            if attack in ttp_mapping:
                ttps.extend(ttp_mapping[attack])

        return list(set(ttps))

    def _check_honeytoken_access(self, url: str) -> bool:
        """Check if URL accessed a honeytoken file"""
        honeytoken_files = [
            "config.php",
            "api_config.php",
            "db_backup.sql",
            ".env",
            "credentials.json"
        ]

        return any(token in url.lower() for token in honeytoken_files)

    async def get_uploaded_files(self) -> List[Dict]:
        """Get list of files uploaded to honeypot"""
        upload_dir = self.log_path / "dvwa"

        if not upload_dir.exists():
            return []

        uploaded = []
        for file_path in upload_dir.glob("*"):
            if file_path.is_file():
                uploaded.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "timestamp": datetime.fromtimestamp(file_path.stat().st_mtime),
                    "path": str(file_path)
                })

        return uploaded