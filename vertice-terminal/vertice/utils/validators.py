"""
Security validators - PRODUCTION READY
"""
import re
import ipaddress
from pathlib import Path
from typing import Optional

class ValidationError(Exception):
    pass

def sanitize_file_path(file_path: str, allowed_base_dir: Optional[str] = None) -> Path:
    """Prevent path traversal attacks."""
    path = Path(file_path).resolve()
    
    if '..' in file_path:
        raise ValidationError("Path traversal detected")
    
    if file_path.startswith('/') or file_path.startswith('\\'):
        if not allowed_base_dir:
            raise ValidationError("Absolute paths not allowed")
    
    if allowed_base_dir:
        base = Path(allowed_base_dir).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise ValidationError(f"Path outside allowed directory")
    
    if not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
    
    if not path.is_file():
        raise ValidationError(f"Not a regular file: {file_path}")
    
    # 100MB limit
    if path.stat().st_size > 100 * 1024 * 1024:
        raise ValidationError(f"File too large (max 100MB)")
    
    return path

def validate_ip_address(ip: str) -> bool:
    """Validate IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError as e:
        raise ValidationError(f"Invalid IP: {ip}") from e

def sanitize_command_arg(arg: str) -> str:
    """Prevent command injection."""
    dangerous = [';', '|', '&', '$', '`', '\n', '$(', '${']
    for char in dangerous:
        if char in arg:
            raise ValidationError(f"Dangerous character: {char}")
    if len(arg) > 1000:
        raise ValidationError("Argument too long")
    return arg
