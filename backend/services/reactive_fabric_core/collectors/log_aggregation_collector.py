"""
Log Aggregation Collector for centralized log analysis.

This collector integrates with log aggregation systems like Elasticsearch,
Splunk, and ELK Stack to collect and analyze security-relevant logs.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field, validator

from .base_collector import BaseCollector, CollectedEvent, CollectorConfig

logger = logging.getLogger(__name__)


class LogAggregationConfig(CollectorConfig):
    """Configuration for Log Aggregation Collector."""

    backend_type: str = Field(
        default="elasticsearch",
        description="Type of log backend (elasticsearch, splunk, graylog)"
    )
    host: str = Field(default="localhost", description="Log backend host")
    port: int = Field(default=9200, description="Log backend port")
    username: Optional[str] = Field(default=None, description="Authentication username")
    password: Optional[str] = Field(default=None, description="Authentication password")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    indices: List[str] = Field(
        default_factory=lambda: ["logs-*", "security-*"],
        description="Indices/indexes to query"
    )
    query_window_minutes: int = Field(
        default=5,
        description="Time window for each query in minutes"
    )
    max_results_per_query: int = Field(
        default=1000,
        description="Maximum results per query"
    )
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates")

    @validator("backend_type")
    def validate_backend_type(cls, v: str) -> str:
        """Validate backend type."""
        allowed = ["elasticsearch", "splunk", "graylog"]
        if v not in allowed:
            raise ValueError(f"backend_type must be one of {allowed}")
        return v


class SecurityEventPattern(BaseModel):
    """Pattern for identifying security events in logs."""

    name: str
    severity: str
    patterns: List[str]
    fields_to_extract: List[str]
    mitre_techniques: List[str] = Field(default_factory=list)


class LogAggregationCollector(BaseCollector):
    """
    Collector for aggregating and analyzing logs from centralized systems.

    Supports Elasticsearch, Splunk, and Graylog backends.
    Focuses on security-relevant events and patterns.
    """

    def __init__(self, config: LogAggregationConfig):
        """Initialize the log aggregation collector."""
        super().__init__(config)
        self.config: LogAggregationConfig = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_query_time = datetime.utcnow() - timedelta(
            minutes=config.query_window_minutes
        )

        # Define security event patterns
        self.security_patterns = self._init_security_patterns()

    def _init_security_patterns(self) -> List[SecurityEventPattern]:
        """Initialize security event detection patterns."""
        return [
            SecurityEventPattern(
                name="failed_authentication",
                severity="medium",
                patterns=[
                    "authentication failed",
                    "invalid credentials",
                    "login failed",
                    "unauthorized access"
                ],
                fields_to_extract=["user", "source_ip", "destination"],
                mitre_techniques=["T1078", "T1110"]
            ),
            SecurityEventPattern(
                name="privilege_escalation",
                severity="high",
                patterns=[
                    "privilege escalation",
                    "sudo",
                    "elevation",
                    "administrator access"
                ],
                fields_to_extract=["user", "process", "command"],
                mitre_techniques=["T1548", "T1134"]
            ),
            SecurityEventPattern(
                name="suspicious_command",
                severity="high",
                patterns=[
                    "wget", "curl", "nc", "netcat",
                    "/etc/passwd", "/etc/shadow",
                    "base64", "eval", "exec"
                ],
                fields_to_extract=["command", "user", "process_id"],
                mitre_techniques=["T1059", "T1105"]
            ),
            SecurityEventPattern(
                name="network_scanning",
                severity="medium",
                patterns=[
                    "port scan",
                    "network discovery",
                    "nmap",
                    "masscan",
                    "zmap"
                ],
                fields_to_extract=["source_ip", "destination_ports", "tool"],
                mitre_techniques=["T1046", "T1595"]
            ),
            SecurityEventPattern(
                name="data_exfiltration",
                severity="critical",
                patterns=[
                    "data transfer",
                    "large upload",
                    "suspicious outbound",
                    "exfiltration"
                ],
                fields_to_extract=["source", "destination", "bytes_transferred"],
                mitre_techniques=["T1041", "T1048"]
            ),
            SecurityEventPattern(
                name="malware_indicators",
                severity="critical",
                patterns=[
                    "malware",
                    "virus",
                    "trojan",
                    "ransomware",
                    "backdoor",
                    "c2 communication"
                ],
                fields_to_extract=["file_hash", "process_name", "source"],
                mitre_techniques=["T1055", "T1571"]
            )
        ]

    async def initialize(self) -> None:
        """Initialize connection to log aggregation backend."""
        # Create HTTP session with appropriate auth
        auth = None
        headers = {}

        if self.config.username and self.config.password:
            auth = aiohttp.BasicAuth(self.config.username, self.config.password)
        elif self.config.api_key:
            if self.config.backend_type == "elasticsearch":
                headers["Authorization"] = f"ApiKey {self.config.api_key}"
            elif self.config.backend_type == "splunk":
                headers["Authorization"] = f"Bearer {self.config.api_key}"

        connector = aiohttp.TCPConnector(ssl=self.config.ssl_verify)
        self.session = aiohttp.ClientSession(
            auth=auth,
            headers=headers,
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )

        logger.info(f"Initialized {self.config.backend_type} collector")

    async def validate_source(self) -> bool:
        """Validate connection to log backend."""
        if not self.session:
            return False

        try:
            if self.config.backend_type == "elasticsearch":
                url = f"http://{self.config.host}:{self.config.port}/_cluster/health"
                async with self.session.get(url) as response:
                    return response.status == 200

            elif self.config.backend_type == "splunk":
                url = f"https://{self.config.host}:{self.config.port}/services/server/info"
                async with self.session.get(url) as response:
                    return response.status == 200

            elif self.config.backend_type == "graylog":
                url = f"http://{self.config.host}:{self.config.port}/api/system/cluster"
                async with self.session.get(url) as response:
                    return response.status == 200

            return False

        except Exception as e:
            logger.error(f"Source validation failed: {e}")
            return False

    async def collect(self) -> AsyncIterator[CollectedEvent]:
        """Collect and analyze logs from the backend."""
        current_time = datetime.utcnow()

        # Query logs for the time window
        query_from = self.last_query_time
        query_to = current_time

        try:
            if self.config.backend_type == "elasticsearch":
                async for event in self._collect_elasticsearch(query_from, query_to):
                    yield event

            elif self.config.backend_type == "splunk":
                async for event in self._collect_splunk(query_from, query_to):
                    yield event

            elif self.config.backend_type == "graylog":
                async for event in self._collect_graylog(query_from, query_to):
                    yield event

            # Update last query time after successful collection
            self.last_query_time = query_to

        except Exception as e:
            logger.error(f"Error collecting logs: {e}")
            self.metrics.errors_count += 1

    async def _collect_elasticsearch(
        self,
        from_time: datetime,
        to_time: datetime
    ) -> AsyncIterator[CollectedEvent]:
        """Collect logs from Elasticsearch."""
        if not self.session:
            return

        # Build query for security events
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": from_time.isoformat(),
                                    "lte": to_time.isoformat()
                                }
                            }
                        }
                    ],
                    "should": [
                        {"match": {"message": pattern}}
                        for security_pattern in self.security_patterns
                        for pattern in security_pattern.patterns
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": self.config.max_results_per_query,
            "sort": [{"@timestamp": "asc"}]
        }

        # Query each index
        for index in self.config.indices:
            url = f"http://{self.config.host}:{self.config.port}/{index}/_search"

            try:
                async with self.session.post(url, json=query) as response:
                    if response.status != 200:
                        self.metrics.errors_count += 1
                        continue

                    data = await response.json()
                    hits = data.get("hits", {}).get("hits", [])

                    for hit in hits:
                        event = await self._parse_elasticsearch_hit(hit)
                        if event:
                            self.metrics.events_collected += 1
                            yield event

            except Exception as e:
                logger.error(f"Error querying index {index}: {e}")
                self.metrics.errors_count += 1

    async def _parse_elasticsearch_hit(
        self,
        hit: Dict[str, Any]
    ) -> Optional[CollectedEvent]:
        """Parse Elasticsearch hit into CollectedEvent."""
        try:
            source = hit.get("_source", {})
            message = source.get("message", "")

            # Identify matching security pattern
            matched_pattern = None
            for pattern in self.security_patterns:
                if any(p.lower() in message.lower() for p in pattern.patterns):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                return None

            # Extract relevant fields
            extracted_data = {}
            for field in matched_pattern.fields_to_extract:
                if field in source:
                    extracted_data[field] = source[field]

            return CollectedEvent(
                collector_type="LogAggregation",
                source=f"elasticsearch:{hit.get('_index')}",
                severity=matched_pattern.severity,
                raw_data=source,
                parsed_data={
                    "pattern_name": matched_pattern.name,
                    "extracted_fields": extracted_data,
                    "mitre_techniques": matched_pattern.mitre_techniques,
                    "index": hit.get("_index"),
                    "doc_id": hit.get("_id")
                },
                tags=[
                    f"pattern:{matched_pattern.name}",
                    f"backend:elasticsearch",
                    *[f"mitre:{t}" for t in matched_pattern.mitre_techniques]
                ]
            )

        except Exception as e:
            logger.error(f"Error parsing Elasticsearch hit: {e}")
            return None

    async def _collect_splunk(
        self,
        from_time: datetime,
        to_time: datetime
    ) -> AsyncIterator[CollectedEvent]:
        """Collect logs from Splunk."""
        if not self.session:
            return

        # Build Splunk search query
        search_patterns = " OR ".join([
            f'"{pattern}"'
            for security_pattern in self.security_patterns
            for pattern in security_pattern.patterns
        ])

        search_query = (
            f"search earliest={from_time.timestamp()} "
            f"latest={to_time.timestamp()} "
            f"({search_patterns})"
        )

        # Submit search job
        job_url = f"https://{self.config.host}:{self.config.port}/services/search/jobs"
        job_data = {
            "search": search_query,
            "output_mode": "json",
            "max_count": self.config.max_results_per_query
        }

        try:
            async with self.session.post(job_url, data=job_data) as response:
                if response.status != 201:
                    logger.error(f"Failed to create Splunk search job: {response.status}")
                    return

                job_info = await response.json()
                job_sid = job_info.get("sid")

                if not job_sid:
                    return

                # Wait for job completion and get results
                results_url = (
                    f"https://{self.config.host}:{self.config.port}"
                    f"/services/search/jobs/{job_sid}/results"
                )

                # Poll for job completion
                await asyncio.sleep(2)  # Give job time to process

                async with self.session.get(f"{results_url}?output_mode=json") as response:
                    if response.status != 200:
                        return

                    data = await response.json()
                    for result in data.get("results", []):
                        event = await self._parse_splunk_result(result)
                        if event:
                            yield event

        except Exception as e:
            logger.error(f"Error collecting from Splunk: {e}")

    async def _parse_splunk_result(
        self,
        result: Dict[str, Any]
    ) -> Optional[CollectedEvent]:
        """Parse Splunk result into CollectedEvent."""
        try:
            raw_text = result.get("_raw", "")

            # Identify matching security pattern
            matched_pattern = None
            for pattern in self.security_patterns:
                if any(p.lower() in raw_text.lower() for p in pattern.patterns):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                return None

            return CollectedEvent(
                collector_type="LogAggregation",
                source=f"splunk:{result.get('index', 'unknown')}",
                severity=matched_pattern.severity,
                raw_data=result,
                parsed_data={
                    "pattern_name": matched_pattern.name,
                    "host": result.get("host"),
                    "source": result.get("source"),
                    "sourcetype": result.get("sourcetype"),
                    "mitre_techniques": matched_pattern.mitre_techniques
                },
                tags=[
                    f"pattern:{matched_pattern.name}",
                    f"backend:splunk",
                    *[f"mitre:{t}" for t in matched_pattern.mitre_techniques]
                ]
            )

        except Exception as e:
            logger.error(f"Error parsing Splunk result: {e}")
            return None

    async def _collect_graylog(
        self,
        from_time: datetime,
        to_time: datetime
    ) -> AsyncIterator[CollectedEvent]:
        """Collect logs from Graylog."""
        if not self.session:
            return

        # Build Graylog query
        query_patterns = " OR ".join([
            pattern
            for security_pattern in self.security_patterns
            for pattern in security_pattern.patterns
        ])

        query_params = {
            "query": query_patterns,
            "from": from_time.isoformat(),
            "to": to_time.isoformat(),
            "limit": self.config.max_results_per_query
        }

        url = f"http://{self.config.host}:{self.config.port}/api/search/universal/relative"

        try:
            async with self.session.get(url, params=query_params) as response:
                if response.status != 200:
                    return

                data = await response.json()
                for message in data.get("messages", []):
                    event = await self._parse_graylog_message(message)
                    if event:
                        yield event

        except Exception as e:
            logger.error(f"Error collecting from Graylog: {e}")

    async def _parse_graylog_message(
        self,
        message: Dict[str, Any]
    ) -> Optional[CollectedEvent]:
        """Parse Graylog message into CollectedEvent."""
        try:
            msg_text = message.get("message", {}).get("message", "")

            # Identify matching security pattern
            matched_pattern = None
            for pattern in self.security_patterns:
                if any(p.lower() in msg_text.lower() for p in pattern.patterns):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                return None

            return CollectedEvent(
                collector_type="LogAggregation",
                source=f"graylog:{message.get('index', 'unknown')}",
                severity=matched_pattern.severity,
                raw_data=message.get("message", {}),
                parsed_data={
                    "pattern_name": matched_pattern.name,
                    "stream_ids": message.get("stream_ids", []),
                    "mitre_techniques": matched_pattern.mitre_techniques
                },
                tags=[
                    f"pattern:{matched_pattern.name}",
                    f"backend:graylog",
                    *[f"mitre:{t}" for t in matched_pattern.mitre_techniques]
                ]
            )

        except Exception as e:
            logger.error(f"Error parsing Graylog message: {e}")
            return None

    async def cleanup(self) -> None:
        """Clean up collector resources."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info(f"Cleaned up {self.config.backend_type} collector")

    def __repr__(self) -> str:
        """String representation of the log aggregation collector."""
        return (
            f"LogAggregationCollector("
            f"backend={self.config.backend_type}, "
            f"host={self.config.host}, "
            f"health={self.metrics.health.value}, "
            f"events={self.metrics.events_collected}, "
            f"errors={self.metrics.errors_count})"
        )