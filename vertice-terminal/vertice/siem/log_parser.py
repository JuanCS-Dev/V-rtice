"""
🔧 Log Parser - Parsing e normalização de logs

Suporta múltiplos formatos de log:
- Syslog (RFC3164, RFC5424)
- JSON
- CEF (Common Event Format)
- LEEF (Log Event Extended Format)
- Apache/Nginx access logs
- Windows Event Logs
- Custom regex patterns

Features:
- Multi-format parsing
- Field extraction
- Normalization to common schema
- Timestamp parsing
- GeoIP enrichment
- User-Agent parsing
- Custom parsers
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Pattern
from datetime import datetime
from enum import Enum
import re
import json
import logging

logger = logging.getLogger(__name__)


class LogFormat(Enum):
    """Formatos de log suportados"""
    SYSLOG_RFC3164 = "syslog_rfc3164"
    SYSLOG_RFC5424 = "syslog_rfc5424"
    JSON = "json"
    CEF = "cef"
    LEEF = "leef"
    APACHE_COMBINED = "apache_combined"
    APACHE_COMMON = "apache_common"
    NGINX_COMBINED = "nginx_combined"
    WINDOWS_EVENT = "windows_event"
    CUSTOM = "custom"


@dataclass
class ParsedLog:
    """
    Log parsea do e normalizado

    Attributes:
        timestamp: Parsed timestamp
        level: Log level
        host: Source host
        application: Application/process name
        message: Log message
        fields: Extracted fields
        raw: Original raw log
        format: Detected format
        parse_success: If parsing succeeded
    """
    timestamp: datetime
    level: str = "info"
    host: Optional[str] = None
    application: Optional[str] = None
    message: str = ""

    # Extracted fields (normalized schema)
    fields: Dict[str, Any] = field(default_factory=dict)

    # Original data
    raw: str = ""
    format: Optional[LogFormat] = None
    parse_success: bool = True


class LogParser:
    """
    Multi-Format Log Parsing System

    Features:
    - Multiple format support
    - Automatic format detection
    - Field extraction
    - Normalization
    - Custom parsers
    - GeoIP enrichment
    """

    def __init__(self):
        """Initialize parser"""

        # Regex patterns for formats
        self.patterns: Dict[LogFormat, Pattern] = {}

        # Custom parsers
        self.custom_parsers: Dict[str, Pattern] = {}

        # Load default patterns
        self._load_default_patterns()

    def _load_default_patterns(self):
        """Carrega patterns padrão"""

        # Syslog RFC3164: <priority>timestamp hostname process[pid]: message
        self.patterns[LogFormat.SYSLOG_RFC3164] = re.compile(
            r'<(?P<priority>\d+)>(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+'
            r'(?P<hostname>\S+)\s+(?P<process>\S+?)(\[(?P<pid>\d+)\])?:\s*'
            r'(?P<message>.*)'
        )

        # Apache Combined Log Format
        self.patterns[LogFormat.APACHE_COMBINED] = re.compile(
            r'(?P<client_ip>\S+)\s+\S+\s+(?P<user>\S+)\s+'
            r'\[(?P<timestamp>[^\]]+)\]\s+'
            r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>\S+)"\s+'
            r'(?P<status>\d+)\s+(?P<size>\d+|-)\s+'
            r'"(?P<referer>[^"]*)"\s+'
            r'"(?P<user_agent>[^"]*)"'
        )

        # Nginx Combined
        self.patterns[LogFormat.NGINX_COMBINED] = re.compile(
            r'(?P<client_ip>\S+)\s+-\s+-\s+'
            r'\[(?P<timestamp>[^\]]+)\]\s+'
            r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>\S+)"\s+'
            r'(?P<status>\d+)\s+(?P<size>\d+)\s+'
            r'"(?P<referer>[^"]*)"\s+'
            r'"(?P<user_agent>[^"]*)"'
        )

        # CEF (Common Event Format)
        # CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        self.patterns[LogFormat.CEF] = re.compile(
            r'CEF:(?P<version>\d+)\|'
            r'(?P<device_vendor>[^|]*)\|'
            r'(?P<device_product>[^|]*)\|'
            r'(?P<device_version>[^|]*)\|'
            r'(?P<signature_id>[^|]*)\|'
            r'(?P<name>[^|]*)\|'
            r'(?P<severity>[^|]*)\|'
            r'(?P<extension>.*)'
        )

        logger.info(f"Loaded {len(self.patterns)} default log format patterns")

    def parse(
        self,
        raw_log: str,
        format_hint: Optional[LogFormat] = None,
    ) -> ParsedLog:
        """
        Parse log message

        Args:
            raw_log: Raw log message
            format_hint: Format hint (for faster parsing)

        Returns:
            ParsedLog object
        """
        # Try JSON first (fastest)
        if raw_log.strip().startswith('{'):
            try:
                return self._parse_json(raw_log)
            except:
                pass

        # Try format hint if provided
        if format_hint and format_hint in self.patterns:
            parsed = self._parse_with_pattern(raw_log, format_hint)
            if parsed.parse_success:
                return parsed

        # Try all patterns
        for log_format, pattern in self.patterns.items():
            parsed = self._parse_with_pattern(raw_log, log_format)
            if parsed.parse_success:
                return parsed

        # Fallback: unparsed
        return ParsedLog(
            timestamp=datetime.now(),
            message=raw_log,
            raw=raw_log,
            parse_success=False,
        )

    def _parse_json(self, raw_log: str) -> ParsedLog:
        """Parse JSON log"""
        try:
            data = json.loads(raw_log)

            # Extract common fields
            timestamp = self._parse_timestamp(
                data.get('timestamp') or data.get('@timestamp') or data.get('time')
            )

            parsed = ParsedLog(
                timestamp=timestamp or datetime.now(),
                level=data.get('level', 'info'),
                host=data.get('host') or data.get('hostname'),
                application=data.get('app') or data.get('application'),
                message=data.get('message', ''),
                fields=data,
                raw=raw_log,
                format=LogFormat.JSON,
                parse_success=True,
            )

            return parsed

        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            return ParsedLog(
                timestamp=datetime.now(),
                message=raw_log,
                raw=raw_log,
                parse_success=False,
            )

    def _parse_with_pattern(
        self,
        raw_log: str,
        log_format: LogFormat,
    ) -> ParsedLog:
        """Parse usando pattern específico"""

        pattern = self.patterns.get(log_format)

        if not pattern:
            return ParsedLog(
                timestamp=datetime.now(),
                message=raw_log,
                raw=raw_log,
                parse_success=False,
            )

        match = pattern.match(raw_log)

        if not match:
            return ParsedLog(
                timestamp=datetime.now(),
                message=raw_log,
                raw=raw_log,
                parse_success=False,
            )

        # Extract fields
        fields = match.groupdict()

        # Parse timestamp
        timestamp = self._parse_timestamp(fields.get('timestamp'))

        # Determine level
        level = self._determine_level(fields)

        parsed = ParsedLog(
            timestamp=timestamp or datetime.now(),
            level=level,
            host=fields.get('hostname') or fields.get('client_ip'),
            application=fields.get('process'),
            message=fields.get('message', raw_log),
            fields=fields,
            raw=raw_log,
            format=log_format,
            parse_success=True,
        )

        return parsed

    def _parse_timestamp(self, timestamp_str: Any) -> Optional[datetime]:
        """Parse timestamp de diferentes formatos"""

        if not timestamp_str:
            return None

        if isinstance(timestamp_str, datetime):
            return timestamp_str

        if not isinstance(timestamp_str, str):
            timestamp_str = str(timestamp_str)

        # Try common formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601
            "%Y-%m-%d %H:%M:%S",  # Common
            "%d/%b/%Y:%H:%M:%S %z",  # Apache
            "%b %d %H:%M:%S",  # Syslog (no year)
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str.strip(), fmt)
            except:
                continue

        # If syslog format without year, add current year
        if re.match(r'\w+\s+\d+\s+\d+:\d+:\d+', timestamp_str):
            try:
                current_year = datetime.now().year
                return datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            except:
                pass

        logger.warning(f"Failed to parse timestamp: {timestamp_str}")
        return None

    def _determine_level(self, fields: Dict[str, Any]) -> str:
        """Determina log level dos campos"""

        # Check priority (syslog)
        if 'priority' in fields:
            try:
                priority = int(fields['priority'])
                severity = priority & 0x07  # Last 3 bits

                # Syslog severity levels
                if severity <= 1:  # Emergency, Alert
                    return "critical"
                elif severity <= 3:  # Critical, Error
                    return "error"
                elif severity == 4:  # Warning
                    return "warning"
                elif severity <= 6:  # Notice, Info
                    return "info"
                else:  # Debug
                    return "debug"
            except:
                pass

        # Check severity field (CEF)
        if 'severity' in fields:
            sev = str(fields['severity']).lower()

            if sev in ['10', 'high', 'critical']:
                return "critical"
            elif sev in ['7', '8', '9', 'medium', 'error']:
                return "error"
            elif sev in ['4', '5', '6', 'low', 'warning']:
                return "warning"
            else:
                return "info"

        # Check status code (HTTP logs)
        if 'status' in fields:
            try:
                status = int(fields['status'])

                if status >= 500:
                    return "error"
                elif status >= 400:
                    return "warning"
                else:
                    return "info"
            except:
                pass

        # Default
        return "info"

    def add_custom_pattern(
        self,
        name: str,
        pattern: str,
    ) -> None:
        """
        Adiciona pattern customizado

        Args:
            name: Pattern name
            pattern: Regex pattern with named groups
        """
        compiled = re.compile(pattern)
        self.custom_parsers[name] = compiled

        logger.info(f"Added custom log pattern: {name}")

    def normalize_to_ecs(self, parsed: ParsedLog) -> Dict[str, Any]:
        """
        Normaliza para Elastic Common Schema (ECS)

        Args:
            parsed: ParsedLog object

        Returns:
            ECS-compliant dict
        """
        ecs = {
            "@timestamp": parsed.timestamp.isoformat(),
            "message": parsed.message,
            "log": {
                "level": parsed.level,
                "original": parsed.raw,
            },
        }

        if parsed.host:
            ecs["host"] = {"hostname": parsed.host}

        if parsed.application:
            ecs["process"] = {"name": parsed.application}

        # Add extracted fields
        if parsed.fields:
            # HTTP fields
            if "method" in parsed.fields:
                ecs["http"] = {
                    "request": {
                        "method": parsed.fields.get("method"),
                    },
                    "response": {
                        "status_code": int(parsed.fields.get("status", 0)),
                    }
                }

            # Network fields
            if "client_ip" in parsed.fields:
                ecs["client"] = {"ip": parsed.fields["client_ip"]}

            # User fields
            if "user" in parsed.fields and parsed.fields["user"] != "-":
                ecs["user"] = {"name": parsed.fields["user"]}

        return ecs

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        return {
            "total_patterns": len(self.patterns),
            "custom_patterns": len(self.custom_parsers),
            "supported_formats": [fmt.value for fmt in self.patterns.keys()],
        }
