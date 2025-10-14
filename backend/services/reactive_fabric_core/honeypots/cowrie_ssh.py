"""
Cowrie SSH Honeypot Implementation
High-interaction SSH/Telnet honeypot
"""

import asyncio
import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_honeypot import BaseHoneypot, HoneypotType, AttackCapture, AttackStage

logger = logging.getLogger(__name__)

class CowrieSSHHoneypot(BaseHoneypot):
    """
    Cowrie SSH/Telnet Honeypot
    Captures brute force attacks, commands, and uploaded malware
    """

    def __init__(self,
                 honeypot_id: str = "cowrie_ssh",
                 ssh_port: int = 2222,
                 telnet_port: int = 2223,
                 layer: int = 3):
        """
        Initialize Cowrie SSH honeypot

        Args:
            honeypot_id: Unique identifier
            ssh_port: SSH port to listen on
            telnet_port: Telnet port to listen on
            layer: Network layer
        """
        super().__init__(
            honeypot_id=honeypot_id,
            honeypot_type=HoneypotType.SSH,
            port=ssh_port,
            layer=layer
        )

        self.telnet_port = telnet_port
        self.cowrie_config = self._generate_config()

        # Attack patterns
        self.brute_force_attempts: Dict[str, List] = {}
        self.known_malware_hashes: Set[str] = set()

    def _generate_config(self) -> Dict[str, Any]:
        """Generate Cowrie configuration"""
        return {
            "ssh": {
                "enabled": True,
                "port": self.port,
                "version": "SSH-2.0-OpenSSH_7.4",
                "auth_methods": ["password", "publickey"],
                "max_auth_tries": 6
            },
            "telnet": {
                "enabled": True,
                "port": self.telnet_port
            },
            "honeypot": {
                "hostname": "production-server-01",
                "kernel_version": "4.15.0-142-generic",
                "kernel_build": "#146-Ubuntu SMP Tue Jun 29 14:33:35 UTC 2021",
                "operating_system": "Ubuntu 18.04.5 LTS",
                "architecture": "x86_64"
            },
            "output": {
                "json": {
                    "enabled": True,
                    "logfile": str(self.log_path / "cowrie.json")
                },
                "tty": {
                    "enabled": True,
                    "path": str(self.log_path / "tty")
                },
                "downloads": {
                    "enabled": True,
                    "path": str(self.log_path / "downloads")
                }
            },
            "shell": {
                "filesystem": "/opt/cowrie/share/cowrie/fs.pickle",
                "processes": "/opt/cowrie/share/cowrie/cmdoutput.json",
                "exec_enabled": True,
                "download_limit": 10485760  # 10MB
            }
        }

    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration for Cowrie"""
        return {
            "image": "cowrie/cowrie:latest",
            "internal_port": 2222,
            "hostname": "production-server-01",
            "environment": {
                "COWRIE_SSH_ENABLED": "yes",
                "COWRIE_TELNET_ENABLED": "yes",
                "COWRIE_OUTPUT_JSON_ENABLED": "yes",
                "COWRIE_HOSTNAME": self.cowrie_config["honeypot"]["hostname"],
                "COWRIE_KERNEL_VERSION": self.cowrie_config["honeypot"]["kernel_version"]
            },
            "volumes": [
                f"{self.log_path}:/cowrie/cowrie-logs",
                f"{self.log_path}/downloads:/cowrie/downloads",
                f"{self.log_path}/tty:/cowrie/tty",
                f"{self.log_path}/keys:/cowrie/etc/keys"
            ],
            "memory": "1g",
            "cpus": "1.0"
        }

    async def start(self) -> bool:
        """Start Cowrie honeypot"""
        logger.info(f"Starting Cowrie SSH honeypot on port {self.port}")

        # Create necessary directories
        for dir_name in ["downloads", "tty", "keys", "json"]:
            (self.log_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Deploy container
        success = await self.deploy()

        if success:
            # Start log monitoring
            asyncio.create_task(self._monitor_cowrie_logs())

        return success

    async def stop(self) -> bool:
        """Stop Cowrie honeypot"""
        logger.info("Stopping Cowrie SSH honeypot")
        await self.shutdown()
        return True

    async def _process_logs(self):
        """Process Cowrie JSON logs for attacks"""
        json_log = self.log_path / "cowrie.json"

        if not json_log.exists():
            return

        try:
            # Read new lines since last check
            with open(json_log, "r") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        await self._process_cowrie_event(event)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Error processing Cowrie logs: {e}")

    async def _monitor_cowrie_logs(self):
        """Monitor Cowrie logs in real-time"""
        json_log = self.log_path / "cowrie.json"

        # Wait for log file to be created
        while not json_log.exists() and self._running:
            await asyncio.sleep(5)

        # Tail the log file
        cmd = ["tail", "-f", str(json_log)]
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

                event = json.loads(line.decode().strip())
                await self._process_cowrie_event(event)

            except Exception as e:
                logger.error(f"Error monitoring Cowrie logs: {e}")

        process.terminate()

    async def _process_cowrie_event(self, event: Dict):
        """Process a single Cowrie event"""
        event_id = event.get("eventid", "")
        src_ip = event.get("src_ip", "")
        session = event.get("session", "")

        # Track sessions
        if event_id == "cowrie.session.connect":
            await self._handle_new_session(event)

        elif event_id == "cowrie.login.success":
            await self._handle_successful_login(event)

        elif event_id == "cowrie.login.failed":
            await self._handle_failed_login(event)

        elif event_id == "cowrie.command.input":
            await self._handle_command(event)

        elif event_id == "cowrie.session.file_download":
            await self._handle_file_download(event)

        elif event_id == "cowrie.session.file_upload":
            await self._handle_file_upload(event)

        elif event_id == "cowrie.session.closed":
            await self._handle_session_closed(event)

    async def _handle_new_session(self, event: Dict):
        """Handle new SSH/Telnet session"""
        session_id = event.get("session", "")
        src_ip = event.get("src_ip", "")
        src_port = event.get("src_port", 0)
        protocol = event.get("protocol", "ssh")

        logger.info(f"New {protocol} session from {src_ip}:{src_port}")

        # Create attack capture
        attack = AttackCapture(
            id=session_id,
            honeypot_id=self.honeypot_id,
            honeypot_type=self.honeypot_type,
            timestamp=datetime.fromisoformat(event.get("timestamp", "")),
            source_ip=src_ip,
            source_port=src_port,
            destination_port=self.port if protocol == "ssh" else self.telnet_port,
            protocol=protocol,
            attack_stage=AttackStage.INITIAL_ACCESS,
            metadata={"session_id": session_id}
        )

        self.active_sessions[session_id] = attack
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1

    async def _handle_successful_login(self, event: Dict):
        """Handle successful login attempt"""
        session_id = event.get("session", "")
        username = event.get("username", "")
        password = event.get("password", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.credentials_used = {"username": username, "password": password}
            attack.attack_stage = AttackStage.CREDENTIAL_ACCESS

            # High threat score for successful login
            attack.threat_score = 7.0

            logger.warning(f"Successful login: {username}:{password} from {attack.source_ip}")

            # Add IOC
            attack.iocs.append(f"credential:{username}:{password}")

    async def _handle_failed_login(self, event: Dict):
        """Handle failed login attempt"""
        src_ip = event.get("src_ip", "")
        username = event.get("username", "")
        password = event.get("password", "")

        # Track brute force attempts
        if src_ip not in self.brute_force_attempts:
            self.brute_force_attempts[src_ip] = []

        self.brute_force_attempts[src_ip].append({
            "timestamp": event.get("timestamp", ""),
            "username": username,
            "password": password
        })

        # Detect brute force attack
        if len(self.brute_force_attempts[src_ip]) > 10:
            logger.warning(f"Brute force attack detected from {src_ip}")

            # Create attack capture for brute force
            attack = self.capture_attack(
                source_ip=src_ip,
                source_port=0,
                attack_stage=AttackStage.CREDENTIAL_ACCESS,
                threat_score=5.0,
                ttps=["T1110 - Brute Force"]
            )

    async def _handle_command(self, event: Dict):
        """Handle executed command"""
        session_id = event.get("session", "")
        command = event.get("input", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.commands.append(command)

            # Analyze command for malicious behavior
            threat_level = self._analyze_command(command)

            if threat_level > 0:
                attack.threat_score = max(attack.threat_score, threat_level)
                attack.attack_stage = self._determine_attack_stage(command)

            logger.info(f"Command executed in {session_id}: {command}")

            # Check for specific TTPs
            ttps = self._extract_ttps_from_command(command)
            attack.ttps.extend(ttps)

    def _analyze_command(self, command: str) -> float:
        """
        Analyze command for threat level

        Returns:
            Threat score (0-10)
        """
        threat_score = 0

        # High threat commands
        high_threat = [
            r"wget\s+http",
            r"curl\s+.*\|\s*sh",
            r"chmod\s+\+x",
            r"/etc/passwd",
            r"/etc/shadow",
            r"nc\s+-e",
            r"python\s+-c",
            r"perl\s+-e"
        ]

        # Medium threat commands
        medium_threat = [
            r"uname",
            r"whoami",
            r"id\s",
            r"ps\s+aux",
            r"netstat",
            r"ifconfig",
            r"cat\s+/proc"
        ]

        for pattern in high_threat:
            if re.search(pattern, command, re.IGNORECASE):
                threat_score = max(threat_score, 8.0)
                break

        for pattern in medium_threat:
            if re.search(pattern, command, re.IGNORECASE):
                threat_score = max(threat_score, 5.0)

        return threat_score

    def _determine_attack_stage(self, command: str) -> AttackStage:
        """Determine attack stage from command"""
        if re.search(r"(wget|curl|scp|ftp)", command):
            return AttackStage.EXECUTION
        elif re.search(r"(crontab|systemctl|service)", command):
            return AttackStage.PERSISTENCE
        elif re.search(r"(sudo|su\s|passwd)", command):
            return AttackStage.PRIVILEGE_ESCALATION
        elif re.search(r"(uname|whoami|id\s|hostname)", command):
            return AttackStage.DISCOVERY
        elif re.search(r"(tar|zip|7z|gzip)", command):
            return AttackStage.COLLECTION
        elif re.search(r"(nc|telnet|ssh\s)", command):
            return AttackStage.LATERAL_MOVEMENT
        else:
            return AttackStage.EXECUTION

    def _extract_ttps_from_command(self, command: str) -> List[str]:
        """Extract MITRE ATT&CK TTPs from command"""
        ttps = []

        ttp_patterns = {
            "T1059": r"(bash|sh|cmd|powershell)",  # Command and Scripting Interpreter
            "T1105": r"(wget|curl|scp|ftp)",  # Ingress Tool Transfer
            "T1053": r"(cron|at\s|schtasks)",  # Scheduled Task/Job
            "T1548": r"(sudo|su\s)",  # Abuse Elevation Control Mechanism
            "T1083": r"(find|locate|ls\s)",  # File and Directory Discovery
            "T1057": r"(ps\s|tasklist)",  # Process Discovery
            "T1016": r"(ifconfig|ipconfig|netstat)",  # System Network Configuration Discovery
            "T1560": r"(tar|zip|rar|7z)",  # Archive Collected Data
            "T1021": r"(ssh\s|telnet|rdp)"  # Remote Services
        }

        for ttp_id, pattern in ttp_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                ttps.append(ttp_id)

        return ttps

    async def _handle_file_download(self, event: Dict):
        """Handle file download attempt"""
        session_id = event.get("session", "")
        url = event.get("url", "")
        filename = event.get("outfile", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.files_downloaded.append(filename)
            attack.threat_score = max(attack.threat_score, 8.0)

            # Add IOC
            attack.iocs.append(f"url:{url}")
            attack.iocs.append(f"file:{filename}")

            logger.warning(f"File download in {session_id}: {url} -> {filename}")

    async def _handle_file_upload(self, event: Dict):
        """Handle file upload (potential malware)"""
        session_id = event.get("session", "")
        filename = event.get("filename", "")
        filepath = event.get("filepath", "")
        shasum = event.get("shasum", "")

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.files_uploaded.append(filename)
            attack.threat_score = 9.0  # High threat for uploads

            # Add IOCs
            attack.iocs.append(f"file:{filename}")
            attack.iocs.append(f"sha256:{shasum}")

            # Mark as known malware if seen before
            if shasum in self.known_malware_hashes:
                attack.iocs.append(f"known_malware:{shasum}")
                attack.threat_score = 10.0

            self.known_malware_hashes.add(shasum)

            logger.critical(f"FILE UPLOAD in {session_id}: {filename} (SHA: {shasum})")

            # Queue for malware analysis
            await self._queue_for_analysis(filepath, shasum)

    async def _queue_for_analysis(self, filepath: str, file_hash: str):
        """Queue uploaded file for malware analysis"""
        # This would send to Cuckoo Sandbox or other analysis engine
        logger.info(f"Queuing {filepath} for malware analysis")

    async def _handle_session_closed(self, event: Dict):
        """Handle session closure"""
        session_id = event.get("session", "")
        duration = event.get("duration", 0)

        if session_id in self.active_sessions:
            attack = self.active_sessions[session_id]
            attack.session_duration = duration

            # Move to captured attacks
            self.captured_attacks.append(attack)
            del self.active_sessions[session_id]

            self.stats["active_connections"] -= 1

            # Generate final report
            self._generate_attack_report(attack)

    def _generate_attack_report(self, attack: AttackCapture):
        """Generate detailed attack report"""
        report = {
            "attack_id": attack.id,
            "timestamp": attack.timestamp.isoformat(),
            "source": f"{attack.source_ip}:{attack.source_port}",
            "duration": attack.session_duration,
            "threat_score": attack.threat_score,
            "attack_stage": attack.attack_stage.value,
            "credentials": attack.credentials_used,
            "commands_executed": len(attack.commands),
            "files_uploaded": len(attack.files_uploaded),
            "files_downloaded": len(attack.files_downloaded),
            "iocs": attack.iocs,
            "ttps": attack.ttps,
            "summary": self._generate_attack_summary(attack)
        }

        # Save report
        report_file = self.log_path / f"reports/attack_{attack.id}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Attack report generated: {report_file}")

    def _generate_attack_summary(self, attack: AttackCapture) -> str:
        """Generate human-readable attack summary"""
        summary_parts = []

        if attack.threat_score >= 8:
            summary_parts.append("HIGH THREAT ATTACK")
        elif attack.threat_score >= 5:
            summary_parts.append("Medium threat activity")
        else:
            summary_parts.append("Low threat reconnaissance")

        if attack.credentials_used:
            summary_parts.append(f"Successful login as {attack.credentials_used.get('username', 'unknown')}")

        if attack.files_uploaded:
            summary_parts.append(f"Uploaded {len(attack.files_uploaded)} files (potential malware)")

        if attack.commands:
            summary_parts.append(f"Executed {len(attack.commands)} commands")

        if attack.ttps:
            summary_parts.append(f"Detected {len(attack.ttps)} MITRE ATT&CK techniques")

        return ". ".join(summary_parts)