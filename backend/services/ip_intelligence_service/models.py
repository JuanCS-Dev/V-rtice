"""Maximus IP Intelligence Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the IP Intelligence Service. These schemas ensure data
consistency and provide a clear structure for representing IP addresses, their
associated intelligence, and query requests.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the IP intelligence ecosystem.
"""

from typing import List, Optional

from pydantic import BaseModel


class IPInfo(BaseModel):
    """Represents detailed intelligence information about an IP address.

    Attributes:
        ip_address (str): The IP address.
        country (str): Geographic country of the IP address.
        city (str): Geographic city of the IP address.
        isp (str): Internet Service Provider associated with the IP address.
        reputation (str): Reputation of the IP (e.g., 'Clean', 'Malicious', 'Suspicious').
        threat_score (float): A numerical threat score for the IP (0.0 to 1.0).
        last_checked (str): ISO formatted timestamp of when the IP was last checked.
        tags (List[str]): Optional tags associated with the IP (e.g., 'VPN', 'TOR', 'Botnet').
        asn (Optional[str]): Autonomous System Number.
    """

    ip_address: str
    country: str
    city: str
    isp: str
    reputation: str
    threat_score: float
    last_checked: str
    tags: List[str] = []
    asn: Optional[str] = None


class IPQuery(BaseModel):
    """Request model for querying IP intelligence.

    Attributes:
        ip_address (str): The IP address to query.
    """

    ip_address: str
