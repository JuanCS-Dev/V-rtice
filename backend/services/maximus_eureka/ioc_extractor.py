"""Maximus Eureka Service - IoC Extractor.

This module implements an Indicator of Compromise (IoC) Extractor for the
Maximus AI's Eureka Service. It is responsible for automatically identifying
and extracting various types of IoCs (e.g., IP addresses, domains, file hashes,
URLs) from unstructured or semi-structured data.

By leveraging regular expressions, pattern matching, and potentially natural
language processing techniques, this module helps to distill critical threat
intelligence from raw data. The extracted IoCs can then be used by other Maximus
AI services for threat detection, intelligence enrichment, and incident response,
enhancing the overall cybersecurity posture.
"""

import re
from typing import Any


class IoCExtractor:
    """Automatically identifies and extracts various types of Indicators of Compromise (IoCs)
    from unstructured or semi-structured data.

    Leverages regular expressions, pattern matching, and potentially natural
    language processing techniques.
    """

    def __init__(self):
        """Initializes the IoCExtractor with common IoC patterns."""
        self.ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        self.domain_pattern = re.compile(
            r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b"
        )
        self.hash_pattern = re.compile(r"\b[a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64}\b")  # MD5, SHA1, SHA256
        self.url_pattern = re.compile(
            r"https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        )

    def extract_iocs(self, data: dict[str, Any]) -> dict[str, list[str]]:
        """Extracts IoCs from a given data dictionary.

        Args:
            data (Dict[str, Any]): The data from which to extract IoCs.

        Returns:
            Dict[str, List[str]]: A dictionary categorizing the extracted IoCs.
        """
        extracted = {"ips": [], "domains": [], "hashes": [], "urls": []}
        text_data = str(data)  # Convert entire data to string for regex search

        extracted["ips"] = self.ip_pattern.findall(text_data)
        extracted["domains"] = self.domain_pattern.findall(text_data)
        extracted["hashes"] = self.hash_pattern.findall(text_data)
        extracted["urls"] = self.url_pattern.findall(text_data)

        return extracted

    def validate_ioc(self, ioc_type: str, ioc_value: str) -> bool:
        """Validates if an IoC value matches its declared type (simplified).

        Args:
            ioc_type (str): The type of IoC (e.g., 'ip', 'domain').
            ioc_value (str): The value of the IoC.

        Returns:
            bool: True if the IoC is valid for its type, False otherwise.
        """
        if ioc_type == "ip":
            return bool(self.ip_pattern.fullmatch(ioc_value))
        if ioc_type == "domain":
            return bool(self.domain_pattern.fullmatch(ioc_value))
        if ioc_type == "hash":
            return bool(self.hash_pattern.fullmatch(ioc_value))
        if ioc_type == "url":
            return bool(self.url_pattern.fullmatch(ioc_value))
        return False
