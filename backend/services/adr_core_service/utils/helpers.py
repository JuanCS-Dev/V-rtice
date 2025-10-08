"""Maximus ADR Core Service - Helper Utilities.

This module provides a collection of general-purpose helper functions and
utilities used across the Automated Detection and Response (ADR) service.
These functions encapsulate common logic, data transformations, or other
reusable operations that do not fit into specific engine or connector modules.

Examples include data validation, string manipulation, time conversions,
or other small, stateless functions that support the overall ADR workflow.
"""

from datetime import datetime
from typing import Any, Dict


def generate_unique_id(prefix: str = "id") -> str:
    """Generates a unique ID with an optional prefix.

    Args:
        prefix (str): A prefix for the generated ID.

    Returns:
        str: A unique identifier string.
    """
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def is_valid_ip(ip_address: str) -> bool:
    """Checks if a given string is a valid IPv4 or IPv6 address.

    Args:
        ip_address (str): The string to validate as an IP address.

    Returns:
        bool: True if the string is a valid IP address, False otherwise.
    """
    import ipaddress

    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def calculate_time_difference(start_time_iso: str, end_time_iso: str) -> float:
    """Calculates the time difference in seconds between two ISO formatted time strings.

    Args:
        start_time_iso (str): The start time in ISO format.
        end_time_iso (str): The end time in ISO format.

    Returns:
        float: The time difference in seconds.

    Raises:
        ValueError: If the time strings are not in valid ISO format.
    """
    try:
        start = datetime.fromisoformat(start_time_iso)
        end = datetime.fromisoformat(end_time_iso)
        return (end - start).total_seconds()
    except ValueError as e:
        raise ValueError(f"Invalid ISO time format: {e}")


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """Flattens a nested dictionary into a single-level dictionary.

    Args:
        d (Dict[str, Any]): The dictionary to flatten.
        parent_key (str): The base key for the current level of recursion.
        sep (str): The separator to use for concatenating keys.

    Returns:
        Dict[str, Any]: The flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
