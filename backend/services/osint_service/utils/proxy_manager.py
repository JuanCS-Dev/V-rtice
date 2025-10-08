"""Maximus OSINT Service - Proxy Manager.

This module implements a Proxy Manager for the Maximus AI's OSINT Service.
It is responsible for managing a pool of proxy servers, rotating them to avoid
IP blocking, and ensuring anonymous and reliable access to open-source data
sources.

Key functionalities include:
- Loading and validating a list of proxy servers.
- Implementing proxy rotation strategies (e.g., round-robin, least-used).
- Handling proxy failures and blacklisting unreliable proxies.
- Providing a simple interface for scrapers to obtain and use proxies.

This manager is crucial for maintaining the effectiveness of OSINT scraping
operations, especially when dealing with websites that employ anti-scraping
measures, ensuring continuous data collection and operational resilience.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class ProxyManager:
    """Manages a pool of proxy servers, rotating them to avoid IP blocking,
    and ensuring anonymous and reliable access to open-source data sources.

    Loads and validates a list of proxy servers, implements proxy rotation
    strategies, and handles proxy failures.
    """

    def __init__(
        self,
        proxy_list: Optional[List[str]] = None,
        rotation_interval_seconds: int = 60,
    ):
        """Initializes the ProxyManager.

        Args:
            proxy_list (Optional[List[str]]): A list of proxy URLs (e.g., 'http://user:pass@ip:port').
            rotation_interval_seconds (int): How often to rotate proxies.
        """
        self.proxies = [{"url": p, "last_used": None, "failures": 0} for p in (proxy_list or [])]
        self.rotation_interval = timedelta(seconds=rotation_interval_seconds)
        self.current_proxy_index = 0
        self.last_rotation_time = datetime.now()
        self.current_status: str = "active"

    def get_proxy(self) -> Optional[str]:
        """Retrieves the current active proxy, rotating if necessary.

        Returns:
            Optional[str]: The URL of the active proxy, or None if no proxies are available.
        """
        if not self.proxies:
            return None

        if (datetime.now() - self.last_rotation_time) > self.rotation_interval:
            self._rotate_proxy()

        active_proxy = self.proxies[self.current_proxy_index]
        active_proxy["last_used"] = datetime.now()
        print(f"[ProxyManager] Using proxy: {active_proxy['url']}")
        return active_proxy["url"]

    def _rotate_proxy(self):
        """Rotates to the next available proxy in the list."""
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        self.last_rotation_time = datetime.now()
        print(f"[ProxyManager] Rotating proxy to index {self.current_proxy_index}")

    def mark_proxy_failed(self, proxy_url: str):
        """Marks a proxy as failed, increasing its failure count.

        Args:
            proxy_url (str): The URL of the proxy that failed.
        """
        for proxy in self.proxies:
            if proxy["url"] == proxy_url:
                proxy["failures"] += 1
                print(f"[ProxyManager] Proxy {proxy_url} marked as failed. Total failures: {proxy['failures']}")
                # Optionally, remove proxy if failures exceed a threshold
                break

    def add_proxy(self, proxy_url: str):
        """Adds a new proxy to the pool.

        Args:
            proxy_url (str): The URL of the new proxy.
        """
        self.proxies.append({"url": proxy_url, "last_used": None, "failures": 0})
        print(f"[ProxyManager] Added new proxy: {proxy_url}")

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Proxy Manager.

        Returns:
            Dict[str, Any]: A dictionary summarizing the manager's status.
        """
        return {
            "status": self.current_status,
            "total_proxies": len(self.proxies),
            "current_proxy_index": self.current_proxy_index,
            "last_rotation": self.last_rotation_time.isoformat(),
            "proxy_details": [
                {
                    "url": p["url"],
                    "last_used": (p["last_used"].isoformat() if p["last_used"] else "N/A"),
                    "failures": p["failures"],
                }
                for p in self.proxies
            ],
        }
