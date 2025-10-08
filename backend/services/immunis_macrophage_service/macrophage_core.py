"""Maximus Immunis Macrophage Service - Production-Ready Macrophage Core

Bio-inspired phagocytosis service that:
1. Engulfs malicious samples (files, memory dumps, network captures)
2. Analyzes via Cuckoo Sandbox (dynamic analysis)
3. Extracts IOCs and auto-generates YARA signatures
4. Presents antigens to Dendritic Cells via Kafka

NO MOCKS - Production-ready implementation.
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Kafka for antigen presentation
try:
    from kafka import KafkaProducer

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not available - antigen presentation disabled")


class CuckooSandboxClient:
    """Client for Cuckoo Sandbox API integration."""

    def __init__(self, cuckoo_url: str = "http://localhost:8090"):
        """Initialize Cuckoo client.

        Args:
            cuckoo_url: Cuckoo REST API URL
        """
        self.cuckoo_url = cuckoo_url
        self.enabled = True

    async def submit_sample(self, file_path: str, timeout: int = 120) -> Dict:
        """Submit sample to Cuckoo for dynamic analysis.

        Args:
            file_path: Path to malware sample
            timeout: Analysis timeout in seconds

        Returns:
            Analysis results dictionary
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # Submit file
                with open(file_path, "rb") as f:
                    files = {"file": (Path(file_path).name, f)}
                    response = await client.post(
                        f"{self.cuckoo_url}/tasks/create/file",
                        files=files,
                        data={"timeout": timeout},
                    )

                if response.status_code != 200:
                    logger.error(f"Cuckoo submission failed: {response.text}")
                    return self._fallback_static_analysis(file_path)

                task_id = response.json()["task_id"]
                logger.info(f"Cuckoo task created: {task_id}")

                # Poll for results
                for _ in range(60):  # Max 5 min wait
                    await asyncio.sleep(5)

                    status_resp = await client.get(f"{self.cuckoo_url}/tasks/view/{task_id}")
                    status = status_resp.json()["task"]["status"]

                    if status == "reported":
                        # Get report
                        report_resp = await client.get(f"{self.cuckoo_url}/tasks/report/{task_id}")
                        return report_resp.json()

                logger.warning(f"Cuckoo analysis timeout for task {task_id}")
                return self._fallback_static_analysis(file_path)

        except Exception as e:
            logger.error(f"Cuckoo analysis error: {e}")
            return self._fallback_static_analysis(file_path)

    def _fallback_static_analysis(self, file_path: str) -> Dict:
        """Fallback static analysis when Cuckoo unavailable."""
        with open(file_path, "rb") as f:
            data = f.read()

        return {
            "info": {"id": "static_analysis"},
            "target": {"file": {"name": Path(file_path).name, "size": len(data)}},
            "behavior": {"processes": [], "network": []},
            "signatures": [],
            "static": {
                "md5": hashlib.md5(data).hexdigest(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "file_type": "unknown",
            },
            "fallback": True,
        }


class YARAGenerator:
    """Auto-generates YARA signatures from malware samples."""

    def __init__(self):
        """Initialize YARA generator."""
        pass

    def extract_iocs(self, sample_data: bytes, analysis_report: Dict) -> Dict[str, List[str]]:
        """Extract Indicators of Compromise from sample and analysis.

        Args:
            sample_data: Raw malware bytes
            analysis_report: Cuckoo analysis report

        Returns:
            Dictionary of IOC types and values
        """
        iocs = {
            "file_hashes": [],
            "strings": [],
            "ips": [],
            "domains": [],
            "urls": [],
            "registry_keys": [],
            "mutexes": [],
            "file_paths": [],
        }

        # File hashes
        iocs["file_hashes"].extend(
            [
                analysis_report.get("static", {}).get("md5", ""),
                analysis_report.get("static", {}).get("sha256", ""),
            ]
        )

        # Extract strings (printable ASCII/Unicode)
        strings = self._extract_strings(sample_data)
        iocs["strings"] = strings[:100]  # Limit to 100

        # Network IOCs from behavior
        for network_item in analysis_report.get("network", {}).get("http", []):
            if "uri" in network_item:
                iocs["urls"].append(network_item["uri"])
            if "host" in network_item:
                iocs["domains"].append(network_item["host"])

        for dns_item in analysis_report.get("network", {}).get("dns", []):
            if "request" in dns_item:
                iocs["domains"].append(dns_item["request"])

        # Registry keys
        for proc in analysis_report.get("behavior", {}).get("processes", []):
            for call in proc.get("calls", []):
                if call.get("category") == "registry":
                    if "arguments" in call and "regkey" in call["arguments"]:
                        iocs["registry_keys"].append(call["arguments"]["regkey"])

        # Mutexes
        for proc in analysis_report.get("behavior", {}).get("processes", []):
            for call in proc.get("calls", []):
                if call.get("api") == "CreateMutexA" or call.get("api") == "CreateMutexW":
                    if "arguments" in call and "mutex_name" in call["arguments"]:
                        iocs["mutexes"].append(call["arguments"]["mutex_name"])

        # Remove duplicates and empty values
        for key in iocs:
            iocs[key] = list(set(filter(None, iocs[key])))

        return iocs

    def _extract_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Extract printable strings from binary data."""
        ascii_strings = re.findall(rb"[\x20-\x7E]{" + str(min_length).encode() + rb",}", data)
        unicode_strings = re.findall(rb"(?:[\x20-\x7E]\x00){" + str(min_length).encode() + rb",}", data)

        strings = [s.decode("ascii", errors="ignore") for s in ascii_strings]
        strings += [s.decode("utf-16le", errors="ignore") for s in unicode_strings]

        return list(set(strings))[:100]  # Limit and deduplicate

    def generate_yara_rule(self, iocs: Dict[str, List[str]], malware_family: str = "unknown") -> str:
        """Generate YARA rule from IOCs.

        Args:
            iocs: Dictionary of IOCs
            malware_family: Malware family name

        Returns:
            YARA rule string
        """
        rule_name = f"{malware_family}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        strings_section = []
        for i, string in enumerate(iocs.get("strings", [])[:20]):  # Max 20 strings
            if len(string) >= 6:  # Minimum length
                # Escape special characters
                escaped = string.replace("\\", "\\\\").replace('"', '\\"')
                strings_section.append(f'        $str{i} = "{escaped}" ascii wide')

        for i, hash_val in enumerate(iocs.get("file_hashes", [])):
            if hash_val:
                strings_section.append(f'        $hash{i} = "{hash_val}"')

        condition = "any of them" if strings_section else "false"

        yara_rule = f"""rule {rule_name} {{
    meta:
        description = "Auto-generated YARA rule for {malware_family}"
        author = "Maximus AI Macrophage Service"
        date = "{datetime.now().isoformat()}"
        family = "{malware_family}"
        md5 = "{iocs.get("file_hashes", [""])[0]}"

    strings:
{chr(10).join(strings_section) if strings_section else "        // No strings extracted"}

    condition:
        {condition}
}}
"""
        return yara_rule


class MacrophageCore:
    """Production-ready Macrophage service for malware phagocytosis.

    Engulfs malicious samples, analyzes via Cuckoo Sandbox,
    extracts IOCs, generates YARA signatures, and presents
    antigens to Dendritic Cells via Kafka.
    """

    def __init__(
        self,
        cuckoo_url: str = "http://localhost:8090",
        kafka_bootstrap_servers: str = "localhost:9092",
    ):
        """Initialize Macrophage Core.

        Args:
            cuckoo_url: Cuckoo Sandbox API URL
            kafka_bootstrap_servers: Kafka broker addresses
        """
        self.cuckoo = CuckooSandboxClient(cuckoo_url)
        self.yara_gen = YARAGenerator()

        # Kafka producer for antigen presentation
        self.kafka_producer = None
        if KAFKA_AVAILABLE:
            try:
                self.kafka_producer = KafkaProducer(
                    bootstrap_servers=kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                logger.info("Kafka producer initialized for antigen presentation")
            except Exception as e:
                logger.warning(f"Kafka initialization failed: {e}")

        self.processed_artifacts: List[Dict[str, Any]] = []
        self.generated_signatures: List[str] = []
        self.last_cleanup_time: Optional[datetime] = None

        logger.info("MacrophageCore initialized (production-ready)")

    async def phagocytose(self, sample_path: str, malware_family: str = "unknown") -> Dict[str, Any]:
        """Phagocytose (engulf and analyze) malicious sample.

        Args:
            sample_path: Path to malware sample
            malware_family: Malware family name (if known)

        Returns:
            Processed artifact with analysis results and generated signatures
        """
        logger.info(f"Phagocytosing sample: {sample_path}")

        # 1. Dynamic analysis via Cuckoo Sandbox
        logger.info("Submitting to Cuckoo Sandbox for dynamic analysis...")
        analysis_report = await self.cuckoo.submit_sample(sample_path, timeout=120)

        # 2. Extract IOCs
        logger.info("Extracting IOCs from analysis...")
        with open(sample_path, "rb") as f:
            sample_data = f.read()

        iocs = self.yara_gen.extract_iocs(sample_data, analysis_report)

        # 3. Generate YARA signature
        logger.info("Generating YARA signature...")
        yara_rule = self.yara_gen.generate_yara_rule(iocs, malware_family)
        self.generated_signatures.append(yara_rule)

        # 4. Create processed artifact
        artifact = {
            "timestamp": datetime.now().isoformat(),
            "sample_hash": hashlib.sha256(sample_data).hexdigest(),
            "malware_family": malware_family,
            "file_size": len(sample_data),
            "analysis": {
                "cuckoo_task_id": analysis_report.get("info", {}).get("id"),
                "signatures_matched": [sig["name"] for sig in analysis_report.get("signatures", [])],
                "severity": analysis_report.get("info", {}).get("score", 0) / 10.0,  # 0-1 scale
                "fallback": analysis_report.get("fallback", False),
            },
            "iocs": iocs,
            "yara_signature": yara_rule,
            "antigen_status": "pending_presentation",
        }

        self.processed_artifacts.append(artifact)
        self.last_cleanup_time = datetime.now()

        logger.info(f"Phagocytosis complete: {artifact['sample_hash'][:16]}...")

        return artifact

    async def present_antigen(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Present processed threat information (antigen) to Dendritic Cells via Kafka.

        Args:
            artifact: Processed malware artifact

        Returns:
            Presentation confirmation
        """
        logger.info(f"Presenting antigen: {artifact['sample_hash'][:16]}...")

        antigen = {
            "antigen_id": artifact["sample_hash"],
            "timestamp": datetime.now().isoformat(),
            "malware_family": artifact["malware_family"],
            "severity": artifact["analysis"]["severity"],
            "iocs": artifact["iocs"],
            "yara_signature": artifact["yara_signature"],
            "source": "macrophage_service",
        }

        if self.kafka_producer:
            try:
                # Send to Kafka topic 'antigen.presentation'
                future = self.kafka_producer.send("antigen.presentation", value=antigen)
                result = future.get(timeout=10)

                artifact["antigen_status"] = "presented"

                logger.info(f"Antigen presented to Kafka: partition={result.partition}, offset={result.offset}")

                return {
                    "status": "antigen_presented",
                    "antigen_id": antigen["antigen_id"],
                    "kafka_partition": result.partition,
                    "kafka_offset": result.offset,
                }

            except Exception as e:
                logger.error(f"Kafka presentation failed: {e}")
                artifact["antigen_status"] = "presentation_failed"
                return {"status": "presentation_failed", "error": str(e)}
        else:
            logger.warning("Kafka unavailable - antigen presentation skipped")
            return {"status": "kafka_unavailable"}

    async def cleanup_debris(self) -> Dict[str, Any]:
        """Cleanup old artifacts and temporary files.

        Returns:
            Cleanup statistics
        """
        logger.info("Performing cleanup...")

        # Keep only last 1000 artifacts
        if len(self.processed_artifacts) > 1000:
            removed = len(self.processed_artifacts) - 1000
            self.processed_artifacts = self.processed_artifacts[-1000:]
        else:
            removed = 0

        # Keep only last 500 signatures
        if len(self.generated_signatures) > 500:
            sig_removed = len(self.generated_signatures) - 500
            self.generated_signatures = self.generated_signatures[-500:]
        else:
            sig_removed = 0

        self.last_cleanup_time = datetime.now()

        return {
            "artifacts_removed": removed,
            "signatures_removed": sig_removed,
            "timestamp": self.last_cleanup_time.isoformat(),
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Macrophage service status.

        Returns:
            Service status dictionary
        """
        return {
            "status": "operational",
            "processed_artifacts_count": len(self.processed_artifacts),
            "generated_signatures_count": len(self.generated_signatures),
            "last_cleanup": (self.last_cleanup_time.isoformat() if self.last_cleanup_time else "N/A"),
            "cuckoo_enabled": self.cuckoo.enabled,
            "kafka_enabled": self.kafka_producer is not None,
        }
