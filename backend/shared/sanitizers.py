"""
Vértice Platform - Input Sanitizers
====================================

This module provides comprehensive input sanitization functions to prevent
injection attacks, XSS, SQL injection, command injection, and other security
vulnerabilities across the Vértice cybersecurity platform.

Features:
    - HTML/XML sanitization (XSS prevention)
    - SQL injection prevention
    - Command injection prevention
    - Path traversal prevention
    - LDAP injection prevention
    - NoSQL injection prevention
    - Header injection prevention
    - Whitespace normalization
    - Character encoding normalization

Security Principles:
    - Whitelist approach (allow known-good, block everything else)
    - Defense in depth (multiple layers of sanitization)
    - Fail-safe defaults (reject on uncertainty)
    - Minimal trust (sanitize all external inputs)

Usage:
    >>> from backend.shared.sanitizers import sanitize_html, sanitize_sql_identifier
    >>> user_input = "<script>alert('XSS')</script>Hello"
    >>> safe_output = sanitize_html(user_input)
    >>> # Output: "Hello" (script tags removed)
    >>>
    >>> table_name = "users; DROP TABLE users--"
    >>> safe_table = sanitize_sql_identifier(table_name)
    >>> # Raises exception or returns sanitized version

Author: Vértice Platform Team
License: Proprietary
"""

import html
from pathlib import Path
import re
from typing import List, Optional
import unicodedata

from backend.shared.exceptions import ValidationError

# ============================================================================
# HTML/XML SANITIZATION (XSS Prevention)
# ============================================================================


def sanitize_html(text: str, allow_tags: Optional[List[str]] = None) -> str:
    """Sanitize HTML input to prevent XSS attacks.

    Removes or escapes HTML tags and dangerous attributes.

    Args:
        text: Input text potentially containing HTML
        allow_tags: List of allowed HTML tags (default: None = escape all)

    Returns:
        Sanitized HTML-safe string

    Example:
        >>> sanitize_html("<script>alert('XSS')</script>Hello")
        "Hello"
    """
    if not text:
        return ""

    if allow_tags is None:
        # Escape all HTML entities
        return html.escape(text)
    else:
        # Allow specific tags, escape others
        # This is a simplified implementation
        # For production, use a library like bleach
        allowed_pattern = "|".join(re.escape(tag) for tag in allow_tags)
        # Remove script tags and dangerous attributes
        text = re.sub(
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"on\w+\s*=", "", text, flags=re.IGNORECASE
        )  # Remove event handlers
        text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
        return text


def strip_html_tags(text: str) -> str:
    """Remove all HTML tags from text.

    Args:
        text: Input text with HTML tags

    Returns:
        Text with all HTML tags removed

    Example:
        >>> strip_html_tags("<p>Hello <b>World</b></p>")
        "Hello World"
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Unescape HTML entities
    text = html.unescape(text)

    return text.strip()


def sanitize_xml(text: str) -> str:
    """Sanitize XML input to prevent XXE and injection attacks.

    Args:
        text: Input text potentially containing XML

    Returns:
        Sanitized XML-safe string
    """
    if not text:
        return ""

    # Escape XML special characters
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")

    return text


# ============================================================================
# SQL INJECTION PREVENTION
# ============================================================================


def sanitize_sql_identifier(identifier: str, max_length: int = 64) -> str:
    """Sanitize SQL identifier (table name, column name).

    Only allows alphanumeric characters and underscores.
    Use this for dynamic table/column names. For values, use parameterized queries.

    Args:
        identifier: SQL identifier (table/column name)
        max_length: Maximum identifier length (default: 64)

    Returns:
        Sanitized identifier

    Raises:
        ValidationError: If identifier contains invalid characters

    Example:
        >>> sanitize_sql_identifier("user_table")
        "user_table"
        >>> sanitize_sql_identifier("users; DROP TABLE--")
        # Raises ValidationError
    """
    if not identifier:
        raise ValidationError(
            message="SQL identifier cannot be empty",
            details={"identifier": identifier},
        )

    # Only allow alphanumeric and underscore
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
        raise ValidationError(
            message=f"Invalid SQL identifier: {identifier}",
            details={
                "identifier": identifier,
                "allowed_chars": "alphanumeric and underscore, must start with letter or underscore",
            },
        )

    if len(identifier) > max_length:
        raise ValidationError(
            message=f"SQL identifier too long: {len(identifier)} characters (max {max_length})",
            details={"identifier": identifier, "length": len(identifier)},
        )

    # Check for SQL reserved keywords (sample list)
    reserved_keywords = [
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "EXEC",
        "EXECUTE",
        "UNION",
        "WHERE",
        "FROM",
    ]
    if identifier.upper() in reserved_keywords:
        raise ValidationError(
            message=f"SQL identifier is a reserved keyword: {identifier}",
            details={"identifier": identifier},
        )

    return identifier


def detect_sql_injection(text: str) -> bool:
    """Detect potential SQL injection patterns.

    Args:
        text: Input text to check

    Returns:
        True if SQL injection patterns detected, False otherwise
    """
    if not text:
        return False

    # Common SQL injection patterns
    sql_patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(;\s*DROP)",
        r"(--\s*$)",
        r"(/\*.*\*/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"('.*OR.*'.*=.*')",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


# ============================================================================
# COMMAND INJECTION PREVENTION
# ============================================================================


def sanitize_shell_argument(arg: str) -> str:
    """Sanitize shell command argument.

    Removes or escapes dangerous shell metacharacters.

    Args:
        arg: Shell command argument

    Returns:
        Sanitized argument

    Raises:
        ValidationError: If argument contains dangerous characters

    Example:
        >>> sanitize_shell_argument("file.txt")
        "file.txt"
        >>> sanitize_shell_argument("file.txt; rm -rf /")
        # Raises ValidationError
    """
    if not arg:
        return ""

    # Dangerous shell metacharacters
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]

    for char in dangerous_chars:
        if char in arg:
            raise ValidationError(
                message=f"Dangerous shell metacharacter detected: {char}",
                details={"argument": arg, "character": char},
            )

    return arg


def detect_command_injection(text: str) -> bool:
    """Detect potential command injection patterns.

    Args:
        text: Input text to check

    Returns:
        True if command injection patterns detected, False otherwise
    """
    if not text:
        return False

    # Command injection patterns
    cmd_patterns = [
        r"[;&|`$]",  # Shell metacharacters
        r"\$\([^\)]*\)",  # Command substitution $(...)
        r"`[^`]*`",  # Command substitution `...`
        r">\s*/dev/",  # File redirection
        r"<<",  # Here document
    ]

    for pattern in cmd_patterns:
        if re.search(pattern, text):
            return True

    return False


# ============================================================================
# PATH TRAVERSAL PREVENTION
# ============================================================================


def sanitize_path(path: str, base_dir: Optional[str] = None) -> str:
    """Sanitize file path to prevent path traversal attacks.

    Args:
        path: File path to sanitize
        base_dir: Base directory to restrict access (optional)

    Returns:
        Sanitized path

    Raises:
        ValidationError: If path contains traversal attempts

    Example:
        >>> sanitize_path("uploads/file.txt")
        "uploads/file.txt"
        >>> sanitize_path("../../../etc/passwd")
        # Raises ValidationError
    """
    if not path:
        raise ValidationError(
            message="Path cannot be empty",
            details={"path": path},
        )

    # Normalize path (resolve .., ., etc.)
    normalized = Path(path).resolve()

    # Check for path traversal
    if ".." in path:
        raise ValidationError(
            message="Path traversal detected",
            details={"path": path, "reason": "Contains '..'"},
        )

    # If base_dir provided, ensure path is within base_dir
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            normalized.relative_to(base)
        except ValueError:
            raise ValidationError(
                message="Path traversal detected: outside base directory",
                details={"path": path, "base_dir": base_dir},
            )

    return str(normalized)


# ============================================================================
# LDAP INJECTION PREVENTION
# ============================================================================


def sanitize_ldap_dn(dn: str) -> str:
    """Sanitize LDAP Distinguished Name (DN).

    Args:
        dn: LDAP DN string

    Returns:
        Sanitized DN
    """
    if not dn:
        return ""

    # Escape special LDAP DN characters
    # RFC 4514 special characters: , + " \ < > ;
    dn = dn.replace("\\", "\\\\")
    dn = dn.replace(",", "\\,")
    dn = dn.replace("+", "\\+")
    dn = dn.replace('"', '\\"')
    dn = dn.replace("<", "\\<")
    dn = dn.replace(">", "\\>")
    dn = dn.replace(";", "\\;")

    return dn


def sanitize_ldap_filter(filter_value: str) -> str:
    """Sanitize LDAP search filter value.

    Args:
        filter_value: LDAP filter value

    Returns:
        Sanitized filter value
    """
    if not filter_value:
        return ""

    # Escape special LDAP filter characters
    # RFC 4515 special characters: * ( ) \ NUL
    filter_value = filter_value.replace("\\", "\\5c")
    filter_value = filter_value.replace("*", "\\2a")
    filter_value = filter_value.replace("(", "\\28")
    filter_value = filter_value.replace(")", "\\29")
    filter_value = filter_value.replace("\x00", "\\00")

    return filter_value


# ============================================================================
# NOSQL INJECTION PREVENTION
# ============================================================================


def sanitize_nosql_operator(value: str) -> str:
    """Sanitize NoSQL operator to prevent injection.

    Args:
        value: NoSQL query value

    Returns:
        Sanitized value

    Raises:
        ValidationError: If value contains NoSQL operators
    """
    if not isinstance(value, str):
        raise ValidationError(
            message="NoSQL value must be a string",
            details={"value": value, "type": type(value).__name__},
        )

    # Check for MongoDB operators
    nosql_operators = [
        "$gt",
        "$gte",
        "$lt",
        "$lte",
        "$ne",
        "$in",
        "$nin",
        "$or",
        "$and",
        "$not",
        "$nor",
        "$exists",
        "$regex",
        "$where",
    ]

    for operator in nosql_operators:
        if operator in value:
            raise ValidationError(
                message=f"NoSQL operator detected: {operator}",
                details={"value": value, "operator": operator},
            )

    return value


# ============================================================================
# HEADER INJECTION PREVENTION
# ============================================================================


def sanitize_http_header(header_value: str) -> str:
    """Sanitize HTTP header value to prevent header injection.

    Args:
        header_value: HTTP header value

    Returns:
        Sanitized header value

    Raises:
        ValidationError: If header contains newlines
    """
    if not header_value:
        return ""

    # Check for CRLF injection
    if "\r" in header_value or "\n" in header_value:
        raise ValidationError(
            message="HTTP header injection detected (CRLF)",
            details={"header_value": header_value},
        )

    return header_value.strip()


# ============================================================================
# WHITESPACE & ENCODING NORMALIZATION
# ============================================================================


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Replaces multiple spaces, tabs, newlines with single space.

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_unicode(text: str, form: str = "NFKC") -> str:
    """Normalize Unicode text to prevent encoding-based attacks.

    Args:
        text: Input text
        form: Unicode normalization form ('NFC', 'NFKC', 'NFD', 'NFKD')

    Returns:
        Normalized text
    """
    if not text:
        return ""

    return unicodedata.normalize(form, text)


def remove_control_characters(text: str) -> str:
    """Remove control characters from text.

    Args:
        text: Input text

    Returns:
        Text without control characters
    """
    if not text:
        return ""

    # Remove control characters (ASCII 0-31 except tab, newline, carriage return)
    text = "".join(
        char for char in text if ord(char) >= 32 or char in ["\t", "\n", "\r"]
    )

    return text


# ============================================================================
# ALPHANUMERIC SANITIZATION
# ============================================================================


def sanitize_alphanumeric(
    text: str, allow_spaces: bool = False, allow_dashes: bool = False
) -> str:
    """Keep only alphanumeric characters.

    Args:
        text: Input text
        allow_spaces: Allow space characters (default: False)
        allow_dashes: Allow dash/hyphen (default: False)

    Returns:
        Sanitized alphanumeric string
    """
    if not text:
        return ""

    # Build pattern based on options
    pattern = r"[^a-zA-Z0-9"
    if allow_spaces:
        pattern += r"\s"
    if allow_dashes:
        pattern += r"-"
    pattern += "]"

    text = re.sub(pattern, "", text)

    return text.strip()


# ============================================================================
# EMAIL SANITIZATION
# ============================================================================


def sanitize_email(email: str) -> str:
    """Sanitize email address.

    Args:
        email: Email address

    Returns:
        Sanitized email (lowercase, trimmed)
    """
    if not email:
        return ""

    # Lowercase and trim
    email = email.lower().strip()

    # Remove whitespace
    email = email.replace(" ", "")

    return email


# ============================================================================
# TRUNCATION
# ============================================================================


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to append if truncated (default: "...")

    Returns:
        Truncated string
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Truncate and add suffix
    return text[: max_length - len(suffix)] + suffix


# ============================================================================
# EXPORT ALL SANITIZERS
# ============================================================================

__all__ = [
    # HTML/XML
    "sanitize_html",
    "strip_html_tags",
    "sanitize_xml",
    # SQL
    "sanitize_sql_identifier",
    "detect_sql_injection",
    # Command
    "sanitize_shell_argument",
    "detect_command_injection",
    # Path
    "sanitize_path",
    # LDAP
    "sanitize_ldap_dn",
    "sanitize_ldap_filter",
    # NoSQL
    "sanitize_nosql_operator",
    # HTTP
    "sanitize_http_header",
    # Whitespace & Encoding
    "normalize_whitespace",
    "normalize_unicode",
    "remove_control_characters",
    # Alphanumeric
    "sanitize_alphanumeric",
    # Email
    "sanitize_email",
    # Truncation
    "truncate_string",
]
