"""Maximus OSINT Service - Security Utilities.

This module provides security-related utility functions for the Maximus AI's
OSINT Service. It is responsible for ensuring the secure handling of sensitive
data, protecting against common web vulnerabilities, and promoting ethical
OSINT practices.

Key functionalities include:
- Sanitizing user inputs to prevent injection attacks (e.g., XSS, SQLi).
- Hashing or encrypting sensitive information before storage or transmission.
- Implementing secure coding practices and data validation routines.
- Providing helper functions for anonymization or pseudonymization of data.

These utilities are crucial for maintaining the integrity, confidentiality,
and availability of OSINT data, protecting both the Maximus AI system and the
privacy of individuals whose data is collected.
"""

import hashlib
import re
from typing import Dict, Any, Optional


class SecurityUtils:
    """Provides security-related utility functions for the OSINT Service.

    Ensures the secure handling of sensitive data, protects against common web
    vulnerabilities, and promotes ethical OSINT practices.
    """

    def __init__(self):
        """Initializes the SecurityUtils."""
        pass

    def sanitize_input(self, input_string: str) -> str:
        """Sanitizes an input string to prevent common injection attacks.

        Args:
            input_string (str): The input string to sanitize.

        Returns:
            str: The sanitized string.
        """
        # Remove HTML tags
        sanitized = re.sub(r'<.*?>', '', input_string)
        # Escape special characters for SQL/shell (simplified)
        sanitized = sanitized.replace("'", "''").replace("--", "")
        return sanitized

    def hash_data(self, data: str, algorithm: str = "sha256") -> str:
        """Hashes a string using the specified algorithm.

        Args:
            data (str): The string data to hash.
            algorithm (str): The hashing algorithm to use (e.g., 'sha256', 'md5').

        Returns:
            str: The hexadecimal representation of the hash.
        
        Raises:
            ValueError: If an unsupported hashing algorithm is provided.
        """
        if algorithm == "sha256":
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(data.encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"Unsupported hashing algorithm: {algorithm}")

    def anonymize_ip_address(self, ip_address: str) -> str:
        """Anonymizes an IP address by masking the last octet (IPv4) or last 64 bits (IPv6).

        Args:
            ip_address (str): The IP address to anonymize.

        Returns:
            str: The anonymized IP address.
        """
        if "." in ip_address: # IPv4
            parts = ip_address.split('.')
            if len(parts) == 4:
                return '.'.join(parts[:3]) + '.0'
        elif ":" in ip_address: # IPv6 (simplified to mask last half)
            parts = ip_address.split(':')
            if len(parts) > 4:
                return ':'.join(parts[:4]) + ':0:0:0:0'
        return ip_address # Return as is if not recognized

    def validate_url(self, url: str) -> bool:
        """Validação básica para o formato de uma URL.

        Args:
            url (str): A URL a ser validada.

        Returns:
            bool: True se o formato da URL for válido, False caso contrário.
        """
        # Simple regex for URL validation
        url_regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
            r'localhost|' # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\:?(\d+)?' # ...or ip
            r'(?:/?|[/?]\S+)$/i', re.IGNORECASE)
        return re.match(url_regex, url) is not None