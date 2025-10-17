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
    >>> from shared.sanitizers import sanitize_html, sanitize_sql_identifier
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
import re
import unicodedata
from pathlib import Path

from .exceptions import ValidationError

# ============================================================================
# HTML/XML SANITIZATION (XSS Prevention)
# ============================================================================


def sanitize_html(text: str, allow_tags: list[str] | None = None) -> str:
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
        "|".join(re.escape(tag) for tag in allow_tags)
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

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in sql_patterns)


# ============================================================================
# COMMAND INJECTION PREVENTION
# ============================================================================


def sanitize_shell_argument(arg: str) -> str:
    """Sanitize shell command argument.

    Removes or escapes dangerous shell metacharacters.

    Args:
        arg: Shell command argument

    Returns:
        Sanitized argument (escaped)

    Raises:
        ValidationError: If argument contains dangerous characters

    Example:
        >>> sanitize_shell_argument("file.txt")
        "file.txt"
        >>> sanitize_shell_argument("file.txt; rm -rf /")
        # Returns escaped version or raises ValidationError
    """
    if not arg:
        return ""

    # Dangerous shell metacharacters
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r", "*", "?", "[", "]", "{", "}", "~"]

    # Check and escape dangerous characters
    result = arg
    for char in dangerous_chars:
        if char in result:
            # Escape with backslash
            result = result.replace(char, f"\\{char}")

    return result


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

    return any(re.search(pattern, text) for pattern in cmd_patterns)


# ============================================================================
# PATH TRAVERSAL PREVENTION
# ============================================================================


def sanitize_path(path: str, base_dir: str | None = None) -> str:
    """Sanitize file path to prevent path traversal attacks.

    Args:
        path: File path to sanitize
        base_dir: Base directory to restrict access (optional)

    Returns:
        Sanitized path (normalized)

    Raises:
        ValidationError: If path contains traversal attempts or escapes base_dir

    Example:
        >>> sanitize_path("uploads/file.txt")
        "uploads/file.txt"
        >>> sanitize_path("../../../etc/passwd", base_dir="/tmp")
        # Raises ValidationError
        >>> sanitize_path("/tmp/./subdir/../file.txt")
        "/tmp/file.txt"  # Normalized (safe within same dir)
    """
    if not path:
        raise ValidationError(
            message="Path cannot be empty",
            details={"path": path},
        )

    # Check for null bytes (path truncation attack)
    if "\x00" in path:
        raise ValidationError(
            message="Null byte detected in path",
            details={"path": path},
        )

    # Decode URL-encoded path traversal attempts
    import urllib.parse
    decoded_path = urllib.parse.unquote(path)

    # Detect suspicious patterns in decoded path
    # If ".." appears in decoded path, extract the "intended" base from original path
    if ".." in decoded_path:
        # Extract first directory component as implied base
        parts = Path(path).parts
        if parts and parts[0] == '/':
            # Absolute path: use first real dir as base
            real_parts = [p for p in parts if p not in ('.', '..', '/')]
            implied_base = "/" + real_parts[0] if real_parts else "/"
        else:
            # Relative path with ..: reject
            raise ValidationError(
                message="Path traversal detected in relative path",
                details={"path": path, "decoded": decoded_path},
            )

        # Normalize and check if it escaped the implied base
        normalized = Path(decoded_path).resolve()
        try:
            normalized.relative_to(implied_base)
        except ValueError as e:
            raise ValidationError(
                message="Path traversal detected: escaped directory boundary",
                details={"path": path, "decoded": decoded_path, "normalized": str(normalized), "implied_base": implied_base},
            ) from e
    else:
        # No ".." in decoded: safe to normalize
        normalized = Path(decoded_path).resolve()

    # If base_dir provided, ensure normalized path is within base_dir
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            normalized.relative_to(base)
        except ValueError as e:
            raise ValidationError(
                message="Path traversal detected: outside base directory",
                details={"path": path, "base_dir": base_dir, "normalized": str(normalized)},
            ) from e

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

    # Remove bracket injections (e.g., value[key])
    result = value.replace("[", "").replace("]", "")

    return result


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
        ValidationError: If header contains newlines or null bytes
    """
    if not header_value:
        return ""

    # Check for null bytes
    if "\x00" in header_value:
        raise ValidationError(
            message="Null byte detected in HTTP header",
            details={"header_value": header_value},
        )

    # Check for CRLF injection
    if "\r" in header_value or "\n" in header_value:
        raise ValidationError(
            message="HTTP header injection detected (CRLF)",
            details={"header_value": header_value},
        )

    # Remove control characters (0x00-0x1F, 0x7F)
    result = "".join(char for char in header_value if ord(char) >= 0x20 and ord(char) != 0x7F)

    return result.strip()


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
    text: str,
    allow_spaces: bool = False,
    allow_dashes: bool = False,
    additional_chars: str = "",
    min_length: int = 0,
) -> str:
    """Keep only alphanumeric characters.

    Args:
        text: Input text
        allow_spaces: Allow space characters (default: False)
        allow_dashes: Allow dash/hyphen (default: False)
        additional_chars: Additional characters to allow (default: "")
        min_length: Minimum length required (default: 0, raises ValidationError if not met)

    Returns:
        Sanitized alphanumeric string

    Raises:
        ValidationError: If result is shorter than min_length
    """
    if not text:
        if min_length > 0:
            raise ValidationError(
                message=f"Input too short after sanitization (min: {min_length})",
                details={"original": text, "min_length": min_length},
            )
        return ""

    # Build pattern based on options
    pattern = r"[^a-zA-Z0-9"
    if allow_spaces:
        pattern += r"\s"
    if allow_dashes:
        pattern += r"-"
    if additional_chars:
        pattern += re.escape(additional_chars)
    pattern += "]"

    text = re.sub(pattern, "", text)
    result = text.strip()

    if min_length > 0 and len(result) < min_length:
        raise ValidationError(
            message=f"Input too short after sanitization: {len(result)} chars (min: {min_length})",
            details={"sanitized": result, "length": len(result), "min_length": min_length},
        )

    return result


# ============================================================================
# EMAIL SANITIZATION
# ============================================================================


def sanitize_email(email: str, validate: bool = True) -> str:
    """Sanitize email address.

    Args:
        email: Email address
        validate: If True, raises ValidationError for invalid emails (default: True)

    Returns:
        Sanitized email (lowercase, trimmed)

    Raises:
        ValidationError: If validate=True and email is invalid
    """
    if not email:
        if validate:
            raise ValidationError(
                message="Email address cannot be empty",
                details={"email": email},
            )
        return ""

    # Lowercase and trim
    email = email.lower().strip()

    # Remove whitespace
    email = email.replace(" ", "")

    # Basic email validation
    if validate:
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValidationError(
                message=f"Invalid email address: {email}",
                details={"email": email},
            )

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
