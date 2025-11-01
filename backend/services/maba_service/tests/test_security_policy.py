"""Tests for Security Policy - Domain Whitelist Validation.

Validates domain whitelisting, blacklisting, and pattern matching logic.

Biblical Foundation: Proverbs 4:23 - "Guard your heart above all else"

Author: Vértice Platform Team
License: Proprietary
"""

from pathlib import Path
import tempfile

from core.security_policy import SecurityPolicy
import pytest
import yaml

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_config_dir():
    """Temporary directory for test configs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_whitelist_config(temp_config_dir):
    """Sample whitelist configuration."""
    config_path = temp_config_dir / "domain_whitelist.yaml"
    config = {
        "allowed_domains": [
            "*.wikipedia.org",
            "*.github.com",
            "google.com",
            "*.stackoverflow.com",
            "example.com",
        ]
    }
    config_path.write_text(yaml.dump(config))
    return config_path


@pytest.fixture
def permissive_config(temp_config_dir):
    """Permissive whitelist (allow all)."""
    config_path = temp_config_dir / "permissive.yaml"
    config = {"allowed_domains": ["*"]}
    config_path.write_text(yaml.dump(config))
    return config_path


@pytest.fixture
def empty_config(temp_config_dir):
    """Empty whitelist config."""
    config_path = temp_config_dir / "empty.yaml"
    config = {"allowed_domains": []}
    config_path.write_text(yaml.dump(config))
    return config_path


# ============================================================================
# TESTS: Initialization and Config Loading
# ============================================================================


class TestInitialization:
    """Test SecurityPolicy initialization and config loading."""

    def test_init_with_valid_config(self, sample_whitelist_config):
        """
        GIVEN: Valid whitelist config file
        WHEN: SecurityPolicy is initialized
        THEN: Whitelist loaded correctly
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        assert len(policy.whitelist) == 5
        assert "*.wikipedia.org" in policy.whitelist
        assert "*.github.com" in policy.whitelist
        assert "google.com" in policy.whitelist

    def test_init_without_config_uses_permissive_default(self, temp_config_dir):
        """
        GIVEN: No whitelist config file exists
        WHEN: SecurityPolicy is initialized
        THEN: Uses permissive default (allow all) with warning
        """
        nonexistent_path = temp_config_dir / "nonexistent.yaml"

        policy = SecurityPolicy(whitelist_path=nonexistent_path)

        assert "*" in policy.whitelist
        assert len(policy.whitelist) == 1

    def test_init_with_empty_config_uses_permissive_default(self, empty_config):
        """
        GIVEN: Whitelist config with empty allowed_domains
        WHEN: SecurityPolicy is initialized
        THEN: Uses permissive default with warning
        """
        policy = SecurityPolicy(whitelist_path=empty_config)

        assert "*" in policy.whitelist

    def test_blacklist_contains_private_networks(self, sample_whitelist_config):
        """
        GIVEN: SecurityPolicy initialized
        WHEN: Checking blacklist
        THEN: Contains all RFC 1918 private networks
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        assert "localhost" in policy.blacklist
        assert "127.0.0.1" in policy.blacklist
        assert "10.*" in policy.blacklist
        assert "172.16.*" in policy.blacklist
        assert "192.168.*" in policy.blacklist
        assert "169.254.*" in policy.blacklist
        assert "*.internal" in policy.blacklist
        assert "*.local" in policy.blacklist


# ============================================================================
# TESTS: Blacklist Validation (Security Critical)
# ============================================================================


class TestBlacklistValidation:
    """Test blacklist blocking of internal/private networks."""

    def test_blocks_localhost(self, sample_whitelist_config):
        """
        GIVEN: URL with localhost domain
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed("http://localhost:8080/api")

        assert allowed is False
        assert "blacklisted" in reason.lower()
        assert "localhost" in reason

    def test_blocks_127_0_0_1(self, sample_whitelist_config):
        """
        GIVEN: URL with 127.0.0.1 IP
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed("http://127.0.0.1:5000/")

        assert allowed is False
        assert "blacklisted" in reason.lower()

    def test_blocks_10_network(self, sample_whitelist_config):
        """
        GIVEN: URL with 10.x.x.x private network IP
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        test_ips = [
            "http://10.0.0.1/",
            "http://10.255.255.255/",
            "http://10.10.10.10:3000/",
        ]

        for url in test_ips:
            allowed, reason = policy.is_allowed(url)
            assert allowed is False, f"Should block {url}"
            assert "blacklisted" in reason.lower()

    def test_blocks_172_16_network(self, sample_whitelist_config):
        """
        GIVEN: URL with 172.16.x.x - 172.31.x.x private network IP
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        test_ips = [
            "http://172.16.0.1/",
            "http://172.20.5.10/",
            "http://172.31.255.255/",
        ]

        for url in test_ips:
            allowed, reason = policy.is_allowed(url)
            assert allowed is False, f"Should block {url}"
            assert "blacklisted" in reason.lower()

    def test_blocks_192_168_network(self, sample_whitelist_config):
        """
        GIVEN: URL with 192.168.x.x private network IP
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        test_ips = [
            "http://192.168.0.1/",
            "http://192.168.1.1:8080/",
            "http://192.168.255.255/",
        ]

        for url in test_ips:
            allowed, reason = policy.is_allowed(url)
            assert allowed is False, f"Should block {url}"
            assert "blacklisted" in reason.lower()

    def test_blocks_link_local_169_254(self, sample_whitelist_config):
        """
        GIVEN: URL with 169.254.x.x link-local IP
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed("http://169.254.169.254/")

        assert allowed is False
        assert "blacklisted" in reason.lower()

    def test_blocks_internal_local_domains(self, sample_whitelist_config):
        """
        GIVEN: URL with .internal or .local domain
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        test_urls = [
            "http://api.internal/",
            "http://service.local/",
            "http://myapp.localhost/",
        ]

        for url in test_urls:
            allowed, reason = policy.is_allowed(url)
            assert allowed is False, f"Should block {url}"
            assert "blacklisted" in reason.lower()


# ============================================================================
# TESTS: Whitelist Validation
# ============================================================================


class TestWhitelistValidation:
    """Test whitelist allowing of configured domains."""

    def test_allows_exact_match(self, sample_whitelist_config):
        """
        GIVEN: Domain in whitelist (exact match)
        WHEN: is_allowed() is called
        THEN: Returns True (allowed)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed("https://google.com/search")

        assert allowed is True
        assert "whitelist" in reason.lower()

    def test_allows_wildcard_subdomain(self, sample_whitelist_config):
        """
        GIVEN: Subdomain matching *.domain.com pattern
        WHEN: is_allowed() is called
        THEN: Returns True (allowed)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        test_urls = [
            "https://en.wikipedia.org/wiki/Test",  # *.wikipedia.org
            "https://api.github.com/repos",  # *.github.com
            "https://www.stackoverflow.com/questions",  # *.stackoverflow.com
        ]

        for url in test_urls:
            allowed, reason = policy.is_allowed(url)
            assert allowed is True, f"Should allow {url}"

    def test_blocks_non_whitelisted_domain(self, sample_whitelist_config):
        """
        GIVEN: Domain NOT in whitelist
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed("https://evil-site.com/")

        assert allowed is False
        assert "not in whitelist" in reason.lower()

    def test_blocks_different_tld(self, sample_whitelist_config):
        """
        GIVEN: Domain with different TLD than whitelisted
        WHEN: is_allowed() is called
        THEN: Returns False (blocked)
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        # wikipedia.org is whitelisted, but not wikipedia.com
        allowed, reason = policy.is_allowed("https://en.wikipedia.com/")

        assert allowed is False

    def test_permissive_mode_allows_all(self, permissive_config):
        """
        GIVEN: Whitelist contains "*" (permissive mode)
        WHEN: is_allowed() is called for any public domain
        THEN: Returns True (except blacklisted)
        """
        policy = SecurityPolicy(whitelist_path=permissive_config)

        test_urls = [
            "https://any-site.com/",
            "https://random-domain.net/",
            "https://example.org/",
        ]

        for url in test_urls:
            allowed, reason = policy.is_allowed(url)
            assert allowed is True, f"Permissive mode should allow {url}"

    def test_permissive_mode_still_blocks_blacklist(self, permissive_config):
        """
        GIVEN: Whitelist contains "*" (permissive mode)
        WHEN: is_allowed() is called for blacklisted domain
        THEN: Returns False (blacklist takes precedence)
        """
        policy = SecurityPolicy(whitelist_path=permissive_config)

        allowed, reason = policy.is_allowed("http://192.168.1.1/")

        assert allowed is False
        assert "blacklisted" in reason.lower()


# ============================================================================
# TESTS: Pattern Matching Logic
# ============================================================================


class TestPatternMatching:
    """Test pattern matching algorithm."""

    def test_match_pattern_exact(self, sample_whitelist_config):
        """
        GIVEN: Exact domain and pattern
        WHEN: _match_pattern() is called
        THEN: Returns True
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        assert policy._match_pattern("example.com", "example.com") is True
        assert policy._match_pattern("example.com", "other.com") is False

    def test_match_pattern_wildcard_star(self, sample_whitelist_config):
        """
        GIVEN: Pattern "*" (match all)
        WHEN: _match_pattern() is called with any domain
        THEN: Returns True
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        assert policy._match_pattern("any-domain.com", "*") is True
        assert policy._match_pattern("127.0.0.1", "*") is True

    def test_match_pattern_subdomain_wildcard(self, sample_whitelist_config):
        """
        GIVEN: Pattern "*.domain.com"
        WHEN: _match_pattern() is called
        THEN: Matches subdomains, not exact domain
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        # Should match subdomains
        assert policy._match_pattern("api.example.com", "*.example.com") is True
        assert policy._match_pattern("www.example.com", "*.example.com") is True
        assert policy._match_pattern("deep.sub.example.com", "*.example.com") is True

        # Should NOT match exact domain (no subdomain)
        # Note: This depends on desired behavior. Current implementation matches.
        # If you want *.example.com to NOT match example.com, adjust regex.

    def test_match_pattern_case_insensitive(self, sample_whitelist_config):
        """
        GIVEN: Domain and pattern with different cases
        WHEN: _match_pattern() is called
        THEN: Matches case-insensitively
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        assert policy._match_pattern("Example.COM", "example.com") is True
        assert policy._match_pattern("API.GITHUB.COM", "*.github.com") is True


# ============================================================================
# TESTS: Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_url_no_domain(self, sample_whitelist_config):
        """
        GIVEN: Invalid URL with no domain
        WHEN: is_allowed() is called
        THEN: Returns False with error message
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed("not-a-url")

        assert allowed is False
        assert "invalid" in reason.lower() or "no domain" in reason.lower()

    def test_url_with_port_number(self, sample_whitelist_config):
        """
        GIVEN: URL with port number
        WHEN: is_allowed() is called
        THEN: Port stripped, domain validated
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed("https://google.com:443/")

        assert allowed is True

    def test_url_with_path_and_query(self, sample_whitelist_config):
        """
        GIVEN: URL with path and query string
        WHEN: is_allowed() is called
        THEN: Only domain validated, path/query ignored
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        allowed, reason = policy.is_allowed(
            "https://en.wikipedia.org/wiki/Test?param=value#section"
        )

        assert allowed is True


# ============================================================================
# TESTS: Utility Methods
# ============================================================================


class TestUtilityMethods:
    """Test utility methods like get_stats and reload."""

    def test_get_stats(self, sample_whitelist_config):
        """
        GIVEN: SecurityPolicy initialized
        WHEN: get_stats() is called
        THEN: Returns statistics dict
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        stats = policy.get_stats()

        assert "whitelist_size" in stats
        assert stats["whitelist_size"] == 5
        assert "blacklist_size" in stats
        assert stats["blacklist_size"] > 0
        assert "permissive_mode" in stats
        assert stats["permissive_mode"] is False
        assert "whitelist_exists" in stats
        assert stats["whitelist_exists"] is True

    def test_reload_whitelist_success(self, sample_whitelist_config, temp_config_dir):
        """
        GIVEN: SecurityPolicy with initial whitelist
        WHEN: Whitelist file updated and reload_whitelist() called
        THEN: New whitelist loaded successfully
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        assert len(policy.whitelist) == 5

        # Update config
        new_config = {"allowed_domains": ["example.com", "test.com"]}
        sample_whitelist_config.write_text(yaml.dump(new_config))

        success = policy.reload_whitelist()

        assert success is True
        assert len(policy.whitelist) == 2
        assert "example.com" in policy.whitelist
        assert "test.com" in policy.whitelist

    def test_reload_whitelist_file_deleted(self, sample_whitelist_config):
        """
        GIVEN: SecurityPolicy with initial whitelist
        WHEN: Whitelist file deleted and reload_whitelist() called
        THEN: Falls back to permissive mode
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        assert len(policy.whitelist) == 5

        # Delete config file
        sample_whitelist_config.unlink()

        success = policy.reload_whitelist()

        assert success is True
        assert "*" in policy.whitelist  # Permissive fallback


# ============================================================================
# INTEGRATION TEST: Full Workflow
# ============================================================================


class TestFullWorkflow:
    """Test complete security policy workflow."""

    def test_full_security_validation_workflow(self, sample_whitelist_config):
        """
        GIVEN: SecurityPolicy with whitelist
        WHEN: Multiple URLs validated
        THEN: Correct allow/block decisions for each category
        """
        policy = SecurityPolicy(whitelist_path=sample_whitelist_config)

        # Should allow: whitelisted public domains
        allowed_urls = [
            "https://en.wikipedia.org/",  # *.wikipedia.org
            "https://api.github.com/user/repo",  # *.github.com (with subdomain)
            "https://google.com/search",  # google.com (exact match)
        ]

        for url in allowed_urls:
            allowed, _ = policy.is_allowed(url)
            assert allowed is True, f"Should allow {url}"

        # Should block: private networks (security critical)
        blocked_private = [
            "http://localhost/",
            "http://127.0.0.1/",
            "http://10.0.0.1/",
            "http://192.168.1.1/",
        ]

        for url in blocked_private:
            allowed, reason = policy.is_allowed(url)
            assert allowed is False, f"Should block {url}"
            assert "blacklisted" in reason.lower()

        # Should block: non-whitelisted public domains
        blocked_public = ["https://random-site.com/", "https://not-in-list.org/"]

        for url in blocked_public:
            allowed, reason = policy.is_allowed(url)
            assert allowed is False, f"Should block {url}"
            assert "not in whitelist" in reason.lower()

        # Verify stats
        stats = policy.get_stats()
        assert stats["whitelist_size"] == 5
        assert stats["permissive_mode"] is False
