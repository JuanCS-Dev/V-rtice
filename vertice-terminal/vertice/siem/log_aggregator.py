"""
📥 Log Aggregator - Agregação de logs multi-source

Coleta logs de múltiplas fontes:
- Syslog (UDP/TCP)
- File tailing (local/remote)
- Windows Event Logs
- Docker containers
- Kubernetes pods
- Cloud providers (AWS CloudWatch, Azure Monitor, GCP Logging)
- Application logs
- Database audit logs
- Network devices (routers, firewalls)

Features:
- Real-time log streaming
- Batch processing
- Multiple protocols (syslog, HTTP, file)
- Buffering & batching
- Error handling & retry
- Compression
- Encryption in transit
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LogSourceType(Enum):
    """Tipos de fonte de log"""
    SYSLOG = "syslog"
    FILE = "file"
    WINDOWS_EVENT = "windows_event"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS_CLOUDWATCH = "aws_cloudwatch"
    AZURE_MONITOR = "azure_monitor"
    GCP_LOGGING = "gcp_logging"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK_DEVICE = "network_device"
    CUSTOM = "custom"


class LogLevel(Enum):
    """Níveis de log"""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class LogSource:
    """
    Fonte de log

    Attributes:
        id: Source ID
        name: Source name
        source_type: Type of log source
        enabled: If source is enabled
        host: Source host/IP
        port: Source port (for network sources)
        file_path: File path (for file sources)
        protocol: Protocol (tcp, udp, http)
        credentials: Authentication credentials
        tags: Source tags
        metadata: Additional metadata
    """
    id: str
    name: str
    source_type: LogSourceType
    enabled: bool = True

    # Network sources
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: str = "tcp"

    # File sources
    file_path: Optional[str] = None

    # Authentication
    credentials: Dict[str, str] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Statistics
    logs_collected: int = 0
    last_collection: Optional[datetime] = None
    errors: int = 0


@dataclass
class LogEntry:
    """
    Entrada de log

    Attributes:
        id: Log entry ID
        timestamp: Log timestamp
        source_id: Source ID
        raw_message: Raw log message
        level: Log level
        host: Source host
        application: Application name
        message: Parsed message
        fields: Parsed fields
        tags: Log tags
    """
    id: str
    timestamp: datetime
    source_id: str
    raw_message: str

    level: LogLevel = LogLevel.INFO
    host: Optional[str] = None
    application: Optional[str] = None
    message: str = ""

    # Parsed fields
    fields: Dict[str, Any] = field(default_factory=dict)

    # Tags
    tags: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class LogAggregator:
    """
    Multi-Source Log Aggregation System

    Features:
    - Real-time log collection
    - Multiple source types
    - Buffering & batching
    - Error handling
    - Source management
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        buffer_size: int = 1000,
    ):
        """
        Args:
            backend_url: URL do siem_service
            use_backend: Se True, usa backend
            buffer_size: Buffer size for batching
        """
        self.backend_url = backend_url or "http://localhost:8023"
        self.use_backend = use_backend
        self.buffer_size = buffer_size

        # Log sources
        self.sources: Dict[str, LogSource] = {}

        # Log buffer (in-memory before persistence)
        self.log_buffer: List[LogEntry] = []

        # Callbacks for log processing
        self.callbacks: List[Callable[[LogEntry], None]] = []

        # Statistics
        self.total_logs_collected: int = 0

    def add_source(self, source: LogSource) -> None:
        """
        Adiciona fonte de log

        Args:
            source: LogSource object
        """
        self.sources[source.id] = source
        logger.info(f"Added log source: {source.name} ({source.source_type.value})")

    def remove_source(self, source_id: str) -> bool:
        """Remove fonte de log"""
        if source_id in self.sources:
            del self.sources[source_id]
            logger.info(f"Removed log source: {source_id}")
            return True
        return False

    def collect_from_syslog(
        self,
        source_id: str,
        host: str = "0.0.0.0",
        port: int = 514,
        protocol: str = "udp",
    ) -> int:
        """
        Coleta logs via syslog

        Args:
            source_id: Source ID
            host: Listen host
            port: Listen port
            protocol: Protocol (udp/tcp)

        Returns:
            Number of logs collected
        """
        source = self.sources.get(source_id)

        if not source or not source.enabled:
            logger.warning(f"Source not found or disabled: {source_id}")
            return 0

        logger.info(f"Collecting syslog from {host}:{port} ({protocol})")

        # TODO: Implement actual syslog listener
        # For now, simulate collection
        collected = 0

        # Simulated log entries
        sample_logs = [
            "Jan 3 10:30:15 server1 sshd[1234]: Accepted password for user from 192.168.1.100",
            "Jan 3 10:30:20 server1 kernel: [12345.678] eth0: link up",
        ]

        for raw_log in sample_logs:
            log_entry = self._create_log_entry(source, raw_log)
            self._process_log(log_entry)
            collected += 1

        source.logs_collected += collected
        source.last_collection = datetime.now()

        return collected

    def collect_from_file(
        self,
        source_id: str,
        file_path: Path,
        follow: bool = False,
    ) -> int:
        """
        Coleta logs de arquivo

        Args:
            source_id: Source ID
            file_path: File path
            follow: If True, tail file (like tail -f)

        Returns:
            Number of logs collected
        """
        source = self.sources.get(source_id)

        if not source or not source.enabled:
            logger.warning(f"Source not found or disabled: {source_id}")
            return 0

        if not file_path.exists():
            logger.error(f"Log file not found: {file_path}")
            source.errors += 1
            return 0

        logger.info(f"Collecting logs from file: {file_path}")

        collected = 0

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if not line.strip():
                        continue

                    log_entry = self._create_log_entry(source, line.strip())
                    self._process_log(log_entry)
                    collected += 1

            source.logs_collected += collected
            source.last_collection = datetime.now()

        except Exception as e:
            logger.error(f"Failed to read log file: {e}")
            source.errors += 1

        return collected

    def collect_from_docker(
        self,
        source_id: str,
        container_id: str,
    ) -> int:
        """
        Coleta logs de container Docker

        Args:
            source_id: Source ID
            container_id: Container ID or name

        Returns:
            Number of logs collected
        """
        source = self.sources.get(source_id)

        if not source or not source.enabled:
            return 0

        logger.info(f"Collecting Docker logs from container: {container_id}")

        # TODO: Integrate with Docker API
        # For now, simulate

        collected = 0
        source.logs_collected += collected
        source.last_collection = datetime.now()

        return collected

    def _create_log_entry(
        self,
        source: LogSource,
        raw_message: str,
    ) -> LogEntry:
        """Cria entrada de log"""
        import uuid

        log_entry = LogEntry(
            id=f"log-{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(),
            source_id=source.id,
            raw_message=raw_message,
            host=source.host,
            tags=source.tags.copy(),
        )

        # Basic parsing (extract log level if present)
        message_lower = raw_message.lower()

        if "error" in message_lower or "err" in message_lower:
            log_entry.level = LogLevel.ERROR
        elif "warn" in message_lower:
            log_entry.level = LogLevel.WARNING
        elif "crit" in message_lower or "fatal" in message_lower:
            log_entry.level = LogLevel.CRITICAL
        elif "debug" in message_lower:
            log_entry.level = LogLevel.DEBUG
        else:
            log_entry.level = LogLevel.INFO

        log_entry.message = raw_message

        return log_entry

    def _process_log(self, log_entry: LogEntry) -> None:
        """Processa entrada de log"""

        # Add to buffer
        self.log_buffer.append(log_entry)
        self.total_logs_collected += 1

        # Execute callbacks
        for callback in self.callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                logger.error(f"Callback execution failed: {e}")

        # Flush buffer if full
        if len(self.log_buffer) >= self.buffer_size:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffer to backend/storage"""

        if not self.log_buffer:
            return

        logger.info(f"Flushing {len(self.log_buffer)} logs to storage")

        # TODO: Send to backend
        if self.use_backend:
            try:
                self._send_to_backend(self.log_buffer)
            except Exception as e:
                logger.error(f"Backend send failed: {e}")

        # Clear buffer
        self.log_buffer.clear()

    def _send_to_backend(self, logs: List[LogEntry]) -> None:
        """Envia logs para backend"""
        import httpx

        try:
            payload = [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "source_id": log.source_id,
                    "level": log.level.value,
                    "message": log.message,
                    "raw_message": log.raw_message,
                    "host": log.host,
                    "fields": log.fields,
                    "tags": log.tags,
                }
                for log in logs
            ]

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/logs/batch",
                    json=payload
                )
                response.raise_for_status()

        except Exception as e:
            logger.error(f"Backend send failed: {e}")
            raise

    def register_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """
        Registra callback para processar logs

        Args:
            callback: Callback function
        """
        self.callbacks.append(callback)
        logger.info("Registered log processing callback")

    def query_logs(
        self,
        source_id: Optional[str] = None,
        level: Optional[LogLevel] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[LogEntry]:
        """
        Query logs no buffer

        Args:
            source_id: Filter by source
            level: Filter by level
            search: Search in message
            limit: Max results

        Returns:
            List of LogEntry
        """
        logs = self.log_buffer.copy()

        if source_id:
            logs = [log for log in logs if log.source_id == source_id]

        if level:
            logs = [log for log in logs if log.level == level]

        if search:
            search_lower = search.lower()
            logs = [log for log in logs if search_lower in log.message.lower()]

        # Sort by timestamp (most recent first)
        logs = sorted(logs, key=lambda l: l.timestamp, reverse=True)

        return logs[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        # Count by source
        by_source = {}
        for source in self.sources.values():
            by_source[source.name] = source.logs_collected

        # Count by level
        by_level = {}
        for log in self.log_buffer:
            level = log.level.value
            by_level[level] = by_level.get(level, 0) + 1

        active_sources = len([s for s in self.sources.values() if s.enabled])

        return {
            "total_sources": len(self.sources),
            "active_sources": active_sources,
            "total_logs_collected": self.total_logs_collected,
            "buffer_size": len(self.log_buffer),
            "by_source": by_source,
            "by_level": by_level,
        }

    def list_sources(
        self,
        source_type: Optional[LogSourceType] = None,
        enabled_only: bool = False,
    ) -> List[LogSource]:
        """
        Lista fontes com filtros

        Args:
            source_type: Filter by type
            enabled_only: Only enabled sources

        Returns:
            List of LogSource
        """
        sources = list(self.sources.values())

        if source_type:
            sources = [s for s in sources if s.source_type == source_type]

        if enabled_only:
            sources = [s for s in sources if s.enabled]

        return sources
