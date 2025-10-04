"""General helper utilities for the ADR Core Service.

This module contains miscellaneous helper functions that are used across
different parts of the service. These include functions for ID generation,
hashing, and data parsing.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any


def generate_id(prefix: str = "") -> str:
    """Generates a unique ID with an optional prefix.

    Creates a short, unique identifier using a portion of a UUID4. This is
    suitable for generating non-critical, human-readable identifiers.

    Args:
        prefix (str, optional): A prefix to prepend to the generated ID.
            Defaults to "".

    Returns:
        str: The generated unique identifier string.
    """
    uid = str(uuid.uuid4())[:8]
    return f"{prefix}{uid}" if prefix else uid


def calculate_hash(data: str, algorithm: str = "sha256") -> str:
    """Calculates the hash of a given string.

    Supports MD5, SHA1, and SHA256 algorithms. The input data is encoded
    as UTF-8 before hashing.

    Args:
        data (str): The input string to hash.
        algorithm (str, optional): The hashing algorithm to use ('md5', 'sha1',
            or 'sha256'). Defaults to "sha256".

    Returns:
        str: The hexadecimal digest of the hash.
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
    """Parses a value into a standardized severity string.

    Converts an integer score or a string into one of the standard severity
    levels: "critical", "high", "medium", "low", or "info".

    Args:
        severity (Any): The input severity, can be an integer score or a string.

    Returns:
        str: The standardized severity string.
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
    """Formats a datetime object into a string representation.

    If no datetime object is provided, the current UTC time is used.

    Args:
        dt (datetime, optional): The datetime object to format. Defaults to None.
        fmt (str, optional): The output format ('iso', 'unix', 'readable').
            Defaults to "iso".

    Returns:
        str: The formatted timestamp string.
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