"""
Helper utilities for ADR Core Service
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any


def generate_id(prefix: str = "") -> str:
    """
    Generate unique ID

    Args:
        prefix: Optional prefix for ID

    Returns:
        Unique identifier string
    """
    uid = str(uuid.uuid4())[:8]
    return f"{prefix}{uid}" if prefix else uid


def calculate_hash(data: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of data

    Args:
        data: Data to hash
        algorithm: Hash algorithm (md5, sha1, sha256)

    Returns:
        Hex digest of hash
    """
    if algorithm == "md5":
        h = hashlib.md5()
    elif algorithm == "sha1":
        h = hashlib.sha1()
    else:
        h = hashlib.sha256()

    h.update(data.encode('utf-8'))
    return h.hexdigest()


def parse_severity(severity: Any) -> str:
    """
    Parse severity value to standard string

    Args:
        severity: Severity value (int, string, etc.)

    Returns:
        Standardized severity string
    """
    if isinstance(severity, int):
        if severity >= 80:
            return "critical"
        elif severity >= 60:
            return "high"
        elif severity >= 40:
            return "medium"
        elif severity >= 20:
            return "low"
        else:
            return "info"

    severity_str = str(severity).lower()
    valid = ["critical", "high", "medium", "low", "info"]

    return severity_str if severity_str in valid else "medium"


def format_timestamp(dt: datetime = None, fmt: str = "iso") -> str:
    """
    Format datetime to string

    Args:
        dt: Datetime object (defaults to now)
        fmt: Format type (iso, unix, readable)

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.utcnow()

    if fmt == "iso":
        return dt.isoformat()
    elif fmt == "unix":
        return str(int(dt.timestamp()))
    elif fmt == "readable":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.isoformat()
