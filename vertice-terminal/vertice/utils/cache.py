"""Local cache utilities."""
from pathlib import Path
import json
import time

class Cache:
    """Simple file-based cache."""

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or (Path.home() / ".vertice" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key, ttl=3600):
        """Get cached value."""
        # TODO: Implement
        pass

    def set(self, key, value):
        """Set cached value."""
        # TODO: Implement
        pass

    def clear(self):
        """Clear all cache."""
        # TODO: Implement
        pass
