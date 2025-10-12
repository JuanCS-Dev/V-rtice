"""
Cowrie Honeypot JSON Log Parser
Extracts attacks, credentials, commands from Cowrie logs.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation - NO MOCK, NO PLACEHOLDER
"""

import json
import structlog
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from backend.services.reactive_fabric_analysis.parsers.base import (
    ForensicParser,
    ParserError,
)

logger = structlog.get_logger()


class CowrieJSONParser(ForensicParser):
    """
    Parser for Cowrie honeypot JSON logs.

    Cowrie is an SSH/Telnet honeypot that logs all interactions in JSON format.
    Each line in the log is a JSON object representing an event.

    Event types:
    - cowrie.login.success: Successful login (credentials)
    - cowrie.login.failed: Failed login attempt
    - cowrie.command.input: Command executed
    - cowrie.session.file_download: File downloaded
    - cowrie.session.connect: New session
    - cowrie.session.closed: Session ended

    Example log line:
    {
        "eventid": "cowrie.login.success",
        "username": "root",
        "password": "toor",
        "src_ip": "45.142.120.15",
        "timestamp": "2025-10-12T20:15:33.123456Z",
        "session": "abc123"
    }
    """

    def supports(self, file_path: Path) -> bool:
        """
        Check if file is a Cowrie JSON log.

        Args:
            file_path: Path to check

        Returns:
            True if filename contains 'cowrie' and extension is .json
        """
        return (
            file_path.suffix.lower() == ".json" and "cowrie" in file_path.name.lower()
        )

    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse Cowrie JSON log and extract structured attack data.

        Args:
            file_path: Path to Cowrie JSON log

        Returns:
            Structured attack data dict

        Raises:
            FileNotFoundError: If file doesn't exist
            ParserError: If parsing fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info("cowrie_parser_started", file=str(file_path))

        # Initialize data structure
        data = {
            "attacker_ip": None,
            "attack_type": "ssh_brute_force",  # Default for Cowrie
            "commands": [],
            "credentials": [],
            "file_hashes": [],
            "timestamps": [],
            "sessions": {},
            "metadata": self._extract_metadata(file_path),
        }

        successful_logins = 0
        failed_logins = 0
        command_count = 0
        download_count = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    try:
                        entry = json.loads(line.strip())

                        # Extract timestamp
                        if "timestamp" in entry:
                            try:
                                ts = datetime.fromisoformat(
                                    entry["timestamp"].replace("Z", "+00:00")
                                )
                                data["timestamps"].append(ts)
                            except (ValueError, AttributeError) as e:
                                logger.debug(
                                    "cowrie_timestamp_parse_error",
                                    timestamp=entry.get("timestamp"),
                                    error=str(e),
                                )
                                continue  # Skip malformed timestamp, continue parsing

                        # Extract attacker IP (first occurrence)
                        if not data["attacker_ip"] and "src_ip" in entry:
                            data["attacker_ip"] = entry["src_ip"]

                        # Extract session info
                        session_id = entry.get("session")
                        if session_id and session_id not in data["sessions"]:
                            data["sessions"][session_id] = {
                                "start_time": (
                                    data["timestamps"][-1]
                                    if data["timestamps"]
                                    else None
                                ),
                                "commands": [],
                                "credentials": [],
                                "downloads": [],
                            }

                        event_id = entry.get("eventid", "")

                        # Process successful logins
                        if event_id == "cowrie.login.success":
                            username = entry.get("username", "unknown")
                            password = entry.get("password", "unknown")
                            credential = (username, password)

                            if credential not in data["credentials"]:
                                data["credentials"].append(credential)

                            if session_id:
                                data["sessions"][session_id]["credentials"].append(
                                    credential
                                )

                            successful_logins += 1

                        # Process failed logins
                        elif event_id == "cowrie.login.failed":
                            failed_logins += 1

                        # Process commands
                        elif event_id == "cowrie.command.input":
                            command = entry.get("input", "")
                            if command:
                                data["commands"].append(command)
                                command_count += 1

                                if session_id:
                                    data["sessions"][session_id]["commands"].append(
                                        command
                                    )

                        # Process file downloads
                        elif event_id == "cowrie.session.file_download":
                            file_hash = entry.get("shasum") or entry.get("sha256")
                            if file_hash and file_hash not in data["file_hashes"]:
                                data["file_hashes"].append(file_hash)

                            download_url = entry.get("url", "")
                            download_count += 1

                            if session_id:
                                data["sessions"][session_id]["downloads"].append(
                                    {"url": download_url, "hash": file_hash}
                                )

                    except json.JSONDecodeError as e:
                        logger.warning(
                            "cowrie_json_decode_error",
                            file=str(file_path),
                            line=line_number,
                            error=str(e),
                        )
                        continue
                    except Exception as e:
                        logger.error(
                            "cowrie_line_parse_error",
                            file=str(file_path),
                            line=line_number,
                            error=str(e),
                        )
                        continue

        except Exception as e:
            logger.error("cowrie_file_parse_error", file=str(file_path), error=str(e))
            raise ParserError(f"Failed to parse Cowrie log: {e}") from e

        # Determine attack type based on behavior
        data["attack_type"] = self._determine_attack_type_cowrie(
            successful_logins, failed_logins, command_count, download_count
        )

        # Add statistics to metadata
        data["metadata"].update(
            {
                "successful_logins": successful_logins,
                "failed_logins": failed_logins,
                "total_commands": command_count,
                "file_downloads": download_count,
                "unique_sessions": len(data["sessions"]),
            }
        )

        logger.info(
            "cowrie_parser_completed",
            file=str(file_path),
            attacker_ip=data["attacker_ip"],
            credentials_found=len(data["credentials"]),
            commands_found=command_count,
            downloads=download_count,
            sessions=len(data["sessions"]),
        )

        return data

    def _determine_attack_type_cowrie(
        self,
        successful_logins: int,
        failed_logins: int,
        command_count: int,
        download_count: int,
    ) -> str:
        """
        Determine specific attack type based on Cowrie events.

        Args:
            successful_logins: Number of successful logins
            failed_logins: Number of failed login attempts
            command_count: Number of commands executed
            download_count: Number of files downloaded

        Returns:
            Attack type string
        """
        # Many failed logins → brute force
        if failed_logins > 10:
            return "ssh_brute_force"

        # Successful login + malware download → compromise
        if successful_logins > 0 and download_count > 0:
            return "ssh_compromise_malware_download"

        # Successful login + commands → post-exploitation
        if successful_logins > 0 and command_count > 0:
            return "ssh_post_exploitation"

        # Successful login only → credential compromise
        if successful_logins > 0:
            return "ssh_successful_login"

        # Default
        return "ssh_reconnaissance"

    def _extract_iocs(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract IoCs from parsed Cowrie data.

        Args:
            data: Parsed data dictionary

        Returns:
            Dict of IoC lists: {ips: [], usernames: [], file_hashes: []}
        """
        iocs = {
            "ips": [],
            "usernames": [],
            "passwords": [],  # Storing for intelligence, never reuse!
            "file_hashes": [],
            "domains": [],
            "urls": [],
        }

        # Extract attacker IP
        if data.get("attacker_ip"):
            iocs["ips"].append(data["attacker_ip"])

        # Extract credentials
        for username, password in data.get("credentials", []):
            if username not in iocs["usernames"]:
                iocs["usernames"].append(username)
            if password not in iocs["passwords"]:
                iocs["passwords"].append(password)

        # Extract file hashes
        iocs["file_hashes"] = data.get("file_hashes", [])

        # Extract URLs/domains from commands
        import re

        for command in data.get("commands", []):
            # Extract URLs (wget, curl)
            url_pattern = r"https?://[^\s]+"
            urls = re.findall(url_pattern, command)
            for url in urls:
                if url not in iocs["urls"]:
                    iocs["urls"].append(url)

                # Extract domain from URL
                domain_match = re.search(r"https?://([^/]+)", url)
                if domain_match:
                    domain = domain_match.group(1)
                    if domain not in iocs["domains"]:
                        iocs["domains"].append(domain)

        return iocs
