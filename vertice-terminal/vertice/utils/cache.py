"""Local cache utilities."""

from pathlib import Path
from typing import Any
import json
import time


class Cache:
    """Simple file-based cache."""

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or (Path.home() / ".vertice" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, ttl: int = 3600) -> Any:
        """
        Get cached value if exists and not expired.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            Cached value or None if not found or expired
        """
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            # Check if expired
            if time.time() - data.get("timestamp", 0) > ttl:
                cache_file.unlink()
                return None

            return data.get("value")
        except (json.JSONDecodeError, IOError):
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set cached value with timestamp.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
        """
        cache_file = self.cache_dir / f"{key}.json"
        data = {"value": value, "timestamp": time.time()}

        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except (IOError, TypeError):
            pass  # Fail silently

    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except IOError:
                pass
