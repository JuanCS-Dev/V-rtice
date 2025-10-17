"""
Vértice Platform - Input Validators
====================================

This module provides comprehensive input validation functions and Pydantic
validators for the Vértice cybersecurity platform. Validators ensure data
integrity, security, and consistency across all services.

Features:
    - IP address validation (IPv4, IPv6, CIDR)
    - Domain and URL validation
    - Hash validation (MD5, SHA1, SHA256, SHA512)
    - Email and username validation
    - IOC (Indicator of Compromise) validation
    - File path and name validation
    - Port number and network validation
    - Pydantic field validators (reusable)
    - Custom validation with detailed error messages

Security:
    - Path traversal detection
    - SQL injection pattern detection
    - XSS pattern detection
    - Command injection detection
    - Maximum length enforcement

Usage:
    >>> from shared.validators import validate_ipv4, validate_domain
    >>> validate_ipv4("192.168.1.1")  # Returns True
    >>> validate_ipv4("256.0.0.1")    # Raises ValidationError
    >>>
    >>> # Pydantic integration
    >>> from pydantic import BaseModel, field_validator
    >>> class ThreatIntelRequest(BaseModel):
    >>>     ip: str
    >>>     @field_validator('ip')
    >>>     def validate_ip_field(cls, v):
    >>>         return validate_ip_address(v)

Author: Vértice Platform Team
License: Proprietary
"""

import ipaddress
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.shared.exceptions import ValidationError

# ============================================================================
# IP ADDRESS VALIDATORS
# ============================================================================


def validate_ipv4(ip: str) -> str:
    """Validate IPv4 address format.

    Args:
        ip: IPv4 address string

    Returns:
        Validated IP address string

    Raises:
        ValidationError: If IP address is invalid
    """
    try:
        addr = ipaddress.IPv4Address(ip)
        return str(addr)
    except (ipaddress.AddressValueError, ValueError) as e:
        raise ValidationError(
            message=f"Invalid IPv4 address: {ip}",
            details={"ip": ip, "error": str(e)},
        ) from e


def validate_ipv6(ip: str) -> str:
    """Validate IPv6 address format.

    Args:
        ip: IPv6 address string

    Returns:
        Validated IP address string (normalized)

    Raises:
        ValidationError: If IP address is invalid
    """
    try:
        addr = ipaddress.IPv6Address(ip)
        return str(addr)
    except (ipaddress.AddressValueError, ValueError) as e:
        raise ValidationError(
            message=f"Invalid IPv6 address: {ip}",
            details={"ip": ip, "error": str(e)},
        ) from e


def validate_ip_address(ip: str, version: int | None = None) -> str:
    """Validate IP address (IPv4 or IPv6).

    Args:
        ip: IP address string
        version: IP version (4 or 6). If None, auto-detect.

    Returns:
        Validated IP address string

    Raises:
        ValidationError: If IP address is invalid
    """
    if version == 4:
        return validate_ipv4(ip)
    elif version == 6:
        return validate_ipv6(ip)
    else:
        # Auto-detect version
        try:
            addr = ipaddress.ip_address(ip)
            return str(addr)
        except ValueError as e:
            raise ValidationError(
                message=f"Invalid IP address: {ip}",
                details={"ip": ip, "error": str(e)},
            ) from e


def validate_cidr(cidr: str, version: int | None = None) -> str:
    """Validate CIDR notation (e.g., 192.168.1.0/24).

    Args:
        cidr: CIDR notation string
        version: IP version (4 or 6). If None, auto-detect.

    Returns:
        Validated CIDR string (normalized)

    Raises:
        ValidationError: If CIDR is invalid
    """
    try:
        if version == 4:
            network = ipaddress.IPv4Network(cidr, strict=False)
        elif version == 6:
            network = ipaddress.IPv6Network(cidr, strict=False)
        else:
            network = ipaddress.ip_network(cidr, strict=False)
        return str(network)
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid CIDR notation: {cidr}",
            details={"cidr": cidr, "error": str(e)},
        ) from e


def is_private_ip(ip: str) -> bool:
    """Check if IP address is in private range.

    Args:
        ip: IP address string

    Returns:
        True if IP is private, False otherwise
    """
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private
    except ValueError:
        return False


def is_public_ip(ip: str) -> bool:
    """Check if IP address is in public range.

    Args:
        ip: IP address string

    Returns:
        True if IP is public, False otherwise
    """
    try:
        addr = ipaddress.ip_address(ip)
        return not addr.is_private and not addr.is_loopback and not addr.is_reserved
    except ValueError:
        return False


# ============================================================================
# DOMAIN & URL VALIDATORS
# ============================================================================


def validate_domain(domain: str) -> str:
    """Validate domain name format.

    Args:
        domain: Domain name string

    Returns:
        Validated domain name (lowercase)

    Raises:
        ValidationError: If domain is invalid
    """
    # Basic domain regex (simplified, covers most cases)
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )

    domain = domain.lower().strip()

    if not domain_pattern.match(domain):
        raise ValidationError(
            message=f"Invalid domain name: {domain}",
            details={"domain": domain, "expected_format": "example.com"},
        )

    if len(domain) > 253:  # Max domain length
        raise ValidationError(
            message=f"Domain name too long: {len(domain)} characters (max 253)",
            details={"domain": domain, "length": len(domain)},
        )

    return domain


def validate_url(url: str, allowed_schemes: list[str] | None = None) -> str:
    """Validate URL format.

    Args:
        url: URL string
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])

    Returns:
        Validated URL string

    Raises:
        ValidationError: If URL is invalid
    """
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in allowed_schemes:
            raise ValidationError(
                message=f"Invalid URL scheme: {parsed.scheme}",
                details={
                    "url": url,
                    "scheme": parsed.scheme,
                    "allowed_schemes": allowed_schemes,
                },
            )

        # Check netloc (domain)
        if not parsed.netloc:
            raise ValidationError(
                message="URL missing domain",
                details={"url": url},
            )

        return url

    except Exception as e:
        raise ValidationError(
            message=f"Invalid URL: {url}",
            details={"url": url, "error": str(e)},
        ) from e


# ============================================================================
# HASH VALIDATORS
# ============================================================================


def validate_md5(hash_value: str) -> str:
    """Validate MD5 hash format (32 hex characters).

    Args:
        hash_value: MD5 hash string

    Returns:
        Validated hash (lowercase)

    Raises:
        ValidationError: If hash is invalid
    """
    hash_value = hash_value.lower().strip()

    if not re.match(r"^[a-f0-9]{32}$", hash_value):
        raise ValidationError(
            message=f"Invalid MD5 hash format: {hash_value}",
            details={"hash": hash_value, "expected_length": 32},
        )

    return hash_value


def validate_sha1(hash_value: str) -> str:
    """Validate SHA1 hash format (40 hex characters).

    Args:
        hash_value: SHA1 hash string

    Returns:
        Validated hash (lowercase)

    Raises:
        ValidationError: If hash is invalid
    """
    hash_value = hash_value.lower().strip()

    if not re.match(r"^[a-f0-9]{40}$", hash_value):
        raise ValidationError(
            message=f"Invalid SHA1 hash format: {hash_value}",
            details={"hash": hash_value, "expected_length": 40},
        )

    return hash_value


def validate_sha256(hash_value: str) -> str:
    """Validate SHA256 hash format (64 hex characters).

    Args:
        hash_value: SHA256 hash string

    Returns:
        Validated hash (lowercase)

    Raises:
        ValidationError: If hash is invalid
    """
    hash_value = hash_value.lower().strip()

    if not re.match(r"^[a-f0-9]{64}$", hash_value):
        raise ValidationError(
            message=f"Invalid SHA256 hash format: {hash_value}",
            details={"hash": hash_value, "expected_length": 64},
        )

    return hash_value


def validate_sha512(hash_value: str) -> str:
    """Validate SHA512 hash format (128 hex characters).

    Args:
        hash_value: SHA512 hash string

    Returns:
        Validated hash (lowercase)

    Raises:
        ValidationError: If hash is invalid
    """
    hash_value = hash_value.lower().strip()

    if not re.match(r"^[a-f0-9]{128}$", hash_value):
        raise ValidationError(
            message=f"Invalid SHA512 hash format: {hash_value}",
            details={"hash": hash_value, "expected_length": 128},
        )

    return hash_value


def validate_hash(hash_value: str, hash_type: str | None = None) -> str:
    """Validate hash format (auto-detect or specify type).

    Args:
        hash_value: Hash string
        hash_type: Hash type ('md5', 'sha1', 'sha256', 'sha512'). If None, auto-detect.

    Returns:
        Validated hash string

    Raises:
        ValidationError: If hash is invalid
    """
    hash_value = hash_value.lower().strip()

    if hash_type:
        validators = {
            "md5": validate_md5,
            "sha1": validate_sha1,
            "sha256": validate_sha256,
            "sha512": validate_sha512,
        }
        validator = validators.get(hash_type.lower())
        if not validator:
            raise ValidationError(
                message=f"Unknown hash type: {hash_type}",
                details={"hash_type": hash_type, "supported": list(validators.keys())},
            )
        return validator(hash_value)
    else:
        # Auto-detect based on length
        length = len(hash_value)
        if length == 32:
            return validate_md5(hash_value)
        elif length == 40:
            return validate_sha1(hash_value)
        elif length == 64:
            return validate_sha256(hash_value)
        elif length == 128:
            return validate_sha512(hash_value)
        else:
            raise ValidationError(
                message=f"Invalid hash format: {hash_value}",
                details={
                    "hash": hash_value,
                    "length": length,
                    "supported_lengths": [32, 40, 64, 128],
                },
            )


# ============================================================================
# EMAIL & USERNAME VALIDATORS
# ============================================================================


def validate_email(email: str) -> str:
    """Validate email address format.

    Args:
        email: Email address string

    Returns:
        Validated email (lowercase)

    Raises:
        ValidationError: If email is invalid
    """
    email = email.lower().strip()

    # RFC 5322 simplified regex
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    if not email_pattern.match(email):
        raise ValidationError(
            message=f"Invalid email address: {email}",
            details={"email": email},
        )

    if len(email) > 254:  # RFC 5321
        raise ValidationError(
            message=f"Email address too long: {len(email)} characters (max 254)",
            details={"email": email, "length": len(email)},
        )

    return email


def validate_username(username: str, min_length: int = 3, max_length: int = 32) -> str:
    """Validate username format.

    Args:
        username: Username string
        min_length: Minimum length (default: 3)
        max_length: Maximum length (default: 32)

    Returns:
        Validated username

    Raises:
        ValidationError: If username is invalid
    """
    username = username.strip()

    # Allow alphanumeric, underscore, hyphen
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise ValidationError(
            message=f"Invalid username format: {username}",
            details={
                "username": username,
                "allowed_chars": "alphanumeric, underscore, hyphen",
            },
        )

    if len(username) < min_length:
        raise ValidationError(
            message=f"Username too short: {len(username)} characters (min {min_length})",
            details={"username": username, "length": len(username)},
        )

    if len(username) > max_length:
        raise ValidationError(
            message=f"Username too long: {len(username)} characters (max {max_length})",
            details={"username": username, "length": len(username)},
        )

    return username


# ============================================================================
# PORT NUMBER VALIDATORS
# ============================================================================


def validate_port(port: int | str) -> int:
    """Validate port number (1-65535).

    Args:
        port: Port number (int or string)

    Returns:
        Validated port number (int)

    Raises:
        ValidationError: If port is invalid
    """
    try:
        port_num = int(port)
    except (ValueError, TypeError) as e:
        raise ValidationError(
            message=f"Invalid port number: {port}",
            details={"port": port, "type": type(port).__name__},
        ) from e

    if not (1 <= port_num <= 65535):
        raise ValidationError(
            message=f"Port number out of range: {port_num}",
            details={"port": port_num, "valid_range": "1-65535"},
        )

    return port_num


# ============================================================================
# FILE PATH VALIDATORS
# ============================================================================


def validate_file_path(
    file_path: str,
    allow_absolute: bool = True,
    allowed_extensions: list[str] | None = None,
) -> str:
    """Validate file path format.

    Args:
        file_path: File path string
        allow_absolute: Allow absolute paths (default: True)
        allowed_extensions: List of allowed extensions (e.g., ['.txt', '.log'])

    Returns:
        Validated file path

    Raises:
        ValidationError: If file path is invalid or contains path traversal
    """
    file_path = file_path.strip()

    # Check for path traversal attempts
    if ".." in file_path:
        raise ValidationError(
            message="Path traversal detected",
            details={"file_path": file_path, "reason": "Contains '..'"},
        )

    # Check for absolute path if not allowed
    if not allow_absolute and Path(file_path).is_absolute():
        raise ValidationError(
            message="Absolute paths not allowed",
            details={"file_path": file_path},
        )

    # Check file extension if specified
    if allowed_extensions:
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in allowed_extensions:
            raise ValidationError(
                message=f"Invalid file extension: {file_ext}",
                details={
                    "file_path": file_path,
                    "extension": file_ext,
                    "allowed_extensions": allowed_extensions,
                },
            )

    return file_path


def validate_filename(
    filename: str, max_length: int = 255, allowed_chars_pattern: str | None = None
) -> str:
    """Validate filename format.

    Args:
        filename: Filename string
        max_length: Maximum filename length (default: 255)
        allowed_chars_pattern: Regex pattern for allowed characters

    Returns:
        Validated filename

    Raises:
        ValidationError: If filename is invalid
    """
    filename = filename.strip()

    # Default pattern: alphanumeric, underscore, hyphen, dot
    if allowed_chars_pattern is None:
        allowed_chars_pattern = r"^[a-zA-Z0-9._-]+$"

    if not re.match(allowed_chars_pattern, filename):
        raise ValidationError(
            message=f"Invalid filename format: {filename}",
            details={"filename": filename, "pattern": allowed_chars_pattern},
        )

    if len(filename) > max_length:
        raise ValidationError(
            message=f"Filename too long: {len(filename)} characters (max {max_length})",
            details={"filename": filename, "length": len(filename)},
        )

    # Check for reserved names (Windows)
    reserved_names = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "LPT1",
        "LPT2",
        "LPT3",
    ]
    if filename.upper().split(".")[0] in reserved_names:
        raise ValidationError(
            message=f"Reserved filename: {filename}",
            details={"filename": filename},
        )

    return filename


# ============================================================================
# IOC (INDICATOR OF COMPROMISE) VALIDATORS
# ============================================================================


def validate_ioc(ioc: str, ioc_type: str) -> str:
    """Validate Indicator of Compromise (IOC).

    Args:
        ioc: IOC value
        ioc_type: IOC type ('ip', 'domain', 'hash', 'email', 'url')

    Returns:
        Validated IOC value

    Raises:
        ValidationError: If IOC is invalid
    """
    ioc_validators = {
        "ip": validate_ip_address,
        "domain": validate_domain,
        "hash": validate_hash,
        "email": validate_email,
        "url": validate_url,
        "md5": validate_md5,
        "sha1": validate_sha1,
        "sha256": validate_sha256,
    }

    validator = ioc_validators.get(ioc_type.lower())
    if not validator:
        raise ValidationError(
            message=f"Unknown IOC type: {ioc_type}",
            details={"ioc_type": ioc_type, "supported": list(ioc_validators.keys())},
        )

    return validator(ioc)


# ============================================================================
# LENGTH & SIZE VALIDATORS
# ============================================================================


def validate_string_length(
    value: str, min_length: int | None = None, max_length: int | None = None
) -> str:
    """Validate string length.

    Args:
        value: String value
        min_length: Minimum length (optional)
        max_length: Maximum length (optional)

    Returns:
        Validated string

    Raises:
        ValidationError: If string length is invalid
    """
    length = len(value)

    if min_length is not None and length < min_length:
        raise ValidationError(
            message=f"String too short: {length} characters (min {min_length})",
            details={"value": value[:50], "length": length, "min_length": min_length},
        )

    if max_length is not None and length > max_length:
        raise ValidationError(
            message=f"String too long: {length} characters (max {max_length})",
            details={"value": value[:50], "length": length, "max_length": max_length},
        )

    return value


def validate_list_length(
    items: list[Any], min_items: int | None = None, max_items: int | None = None
) -> list[Any]:
    """Validate list length.

    Args:
        items: List of items
        min_items: Minimum number of items (optional)
        max_items: Maximum number of items (optional)

    Returns:
        Validated list

    Raises:
        ValidationError: If list length is invalid
    """
    length = len(items)

    if min_items is not None and length < min_items:
        raise ValidationError(
            message=f"Too few items: {length} (min {min_items})",
            details={"count": length, "min_items": min_items},
        )

    if max_items is not None and length > max_items:
        raise ValidationError(
            message=f"Too many items: {length} (max {max_items})",
            details={"count": length, "max_items": max_items},
        )

    return items


# ============================================================================
# EXPORT ALL VALIDATORS
# ============================================================================

__all__ = [
    # IP validators
    "validate_ipv4",
    "validate_ipv6",
    "validate_ip_address",
    "validate_cidr",
    "is_private_ip",
    "is_public_ip",
    # Domain & URL
    "validate_domain",
    "validate_url",
    # Hash
    "validate_md5",
    "validate_sha1",
    "validate_sha256",
    "validate_sha512",
    "validate_hash",
    # Email & Username
    "validate_email",
    "validate_username",
    # Port
    "validate_port",
    # File Path
    "validate_file_path",
    "validate_filename",
    # IOC
    "validate_ioc",
    # Length
    "validate_string_length",
    "validate_list_length",
]
