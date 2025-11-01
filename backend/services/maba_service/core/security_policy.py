"""Security Policy - Domain Whitelist and Access Control for MABA.

Implements domain whitelisting and blacklisting to prevent unauthorized
navigation and access to internal networks.

Security Principle: Defense in depth - multiple layers of protection
Biblical Foundation: Proverbs 4:23 - "Guard your heart above all else"

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)


class SecurityPolicy:
    """Domain whitelist and security controls for MABA.

    Prevents navigation to unauthorized domains and internal networks.

    Architecture:
    - Whitelist: YAML config with allowed domains (supports wildcards)
    - Blacklist: Hardcoded private networks and localhost
    - Pattern matching: Supports wildcards like *.github.com
    - Default: Permissive (*) if no config, with warning

    Security Layers:
    1. Blacklist check (private networks, localhost)
    2. Whitelist check (configured allowed domains)
    3. Logging and metrics for blocked attempts

    Biblical Principle: Wisdom guards (Proverbs 2:11)
    """

    def __init__(
        self, whitelist_path: Path | str = Path("config/domain_whitelist.yaml")
    ):
        """Initialize Security Policy.

        Args:
            whitelist_path: Path to YAML whitelist config
        """
        if isinstance(whitelist_path, str):
            whitelist_path = Path(whitelist_path)

        self.whitelist_path = whitelist_path
        self.whitelist = self._load_whitelist(whitelist_path)
        self.blacklist = self._load_blacklist()

        logger.info(
            f"Security Policy initialized: {len(self.whitelist)} whitelist patterns, "
            f"{len(self.blacklist)} blacklist patterns"
        )

    def _load_whitelist(self, path: Path) -> set[str]:
        """Load whitelisted domains from YAML config.

        Args:
            path: Path to whitelist YAML file

        Returns:
            Set of allowed domain patterns
        """
        if not path.exists():
            logger.warning(
                f"⚠️  No domain whitelist found at {path}, using permissive default. "
                "This is NOT recommended for production!"
            )
            return {"*"}  # Allow all (not recommended for production)

        try:
            config = yaml.safe_load(path.read_text())

            if not config or "allowed_domains" not in config:
                logger.warning(
                    "Whitelist config missing 'allowed_domains', using permissive default"
                )
                return {"*"}

            domains = set(config.get("allowed_domains", []))

            if not domains:
                logger.warning("Whitelist is empty, using permissive default")
                return {"*"}

            logger.info(f"✅ Loaded {len(domains)} whitelisted domain patterns")
            return domains

        except Exception as e:
            logger.error(f"Failed to load whitelist from {path}: {e}")
            logger.warning("Using permissive default due to error")
            return {"*"}

    def _load_blacklist(self) -> set[str]:
        """Load blacklisted domains (internal networks, localhost).

        Returns:
            Set of blocked domain patterns
        """
        # RFC 1918 private networks, localhost, link-local
        return {
            "localhost",
            "127.0.0.1",
            "127.*",
            "0.0.0.0",
            "10.*",  # Private network 10.0.0.0/8
            "172.16.*",  # Private network 172.16.0.0/12
            "172.17.*",
            "172.18.*",
            "172.19.*",
            "172.20.*",
            "172.21.*",
            "172.22.*",
            "172.23.*",
            "172.24.*",
            "172.25.*",
            "172.26.*",
            "172.27.*",
            "172.28.*",
            "172.29.*",
            "172.30.*",
            "172.31.*",
            "192.168.*",  # Private network 192.168.0.0/16
            "169.254.*",  # Link-local 169.254.0.0/16
            "*.internal",
            "*.local",
            "*.localhost",
        }

    def is_allowed(self, url: str) -> tuple[bool, str]:
        """Check if URL is allowed by security policy.

        Performs two-stage validation:
        1. Check against blacklist (private networks, localhost)
        2. Check against whitelist (configured allowed domains)

        Args:
            url: Full URL to validate

        Returns:
            (allowed, reason): Tuple of bool and explanation string
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            if not domain:
                return False, "Invalid URL: no domain/netloc found"

            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Check blacklist first (security critical)
            for pattern in self.blacklist:
                if self._match_pattern(domain, pattern):
                    logger.warning(
                        f"🚫 Blocked access to blacklisted domain: {domain} "
                        f"(matches pattern: {pattern})"
                    )
                    return (
                        False,
                        f"Domain {domain} is blacklisted (internal/private network)",
                    )

            # Check whitelist
            if "*" in self.whitelist:
                return True, "All domains allowed (permissive mode)"

            for pattern in self.whitelist:
                if self._match_pattern(domain, pattern):
                    return True, f"Domain {domain} matches whitelist pattern {pattern}"

            # Not in whitelist
            logger.warning(
                f"🚫 Blocked access to non-whitelisted domain: {domain}. "
                f"Add to whitelist if this is intended."
            )
            return False, f"Domain {domain} not in whitelist"

        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False, f"URL validation error: {e}"

    def _match_pattern(self, domain: str, pattern: str) -> bool:
        """Match domain against pattern (supports wildcards).

        Patterns:
        - "*" matches all domains
        - "*.example.com" matches any subdomain of example.com
        - "example.com" matches exactly example.com

        Args:
            domain: Domain to match
            pattern: Pattern with optional wildcards

        Returns:
            True if domain matches pattern
        """
        if pattern == "*":
            return True

        # Wildcard pattern
        if "*" in pattern:
            # Convert wildcard to regex
            # Escape dots, convert * to .*
            regex = pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.match(f"^{regex}$", domain, re.IGNORECASE))

        # Exact match (case-insensitive)
        return domain.lower() == pattern.lower()

    def get_stats(self) -> dict[str, Any]:
        """Get security policy statistics.

        Returns:
            Statistics dict with whitelist/blacklist sizes
        """
        return {
            "whitelist_size": len(self.whitelist),
            "blacklist_size": len(self.blacklist),
            "permissive_mode": "*" in self.whitelist,
            "whitelist_path": str(self.whitelist_path),
            "whitelist_exists": self.whitelist_path.exists(),
        }

    def reload_whitelist(self) -> bool:
        """Reload whitelist from config file.

        Useful for updating whitelist without restarting service.

        Returns:
            True if reload succeeded
        """
        try:
            new_whitelist = self._load_whitelist(self.whitelist_path)
            self.whitelist = new_whitelist
            logger.info(f"✅ Reloaded whitelist: {len(self.whitelist)} patterns")
            return True
        except Exception as e:
            logger.error(f"Failed to reload whitelist: {e}")
            return False
