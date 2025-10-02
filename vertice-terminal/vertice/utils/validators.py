"""Input validation utilities."""
import re
from ipaddress import ip_address, AddressValueError

def validate_ip(ip):
    """Validate IP address."""
    try:
        ip_address(ip)
        return True
    except AddressValueError:
        return False

def validate_domain(domain):
    """Validate domain name."""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return re.match(pattern, domain) is not None

def validate_hash(hash_value, hash_type='md5'):
    """Validate hash value."""
    patterns = {
        'md5': r'^[a-fA-F0-9]{32}$',
        'sha1': r'^[a-fA-F0-9]{40}$',
        'sha256': r'^[a-fA-F0-9]{64}$',
    }
    pattern = patterns.get(hash_type.lower())
    if not pattern:
        return False
    return re.match(pattern, hash_value) is not None
