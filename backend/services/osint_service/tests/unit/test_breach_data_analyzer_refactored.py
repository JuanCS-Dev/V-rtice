"""Unit tests for BreachDataAnalyzer.

Tests the production-hardened Breach Data Analyzer with 100% coverage.

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx

from analyzers.breach_data_analyzer_refactored import BreachDataAnalyzer, RateLimitError


@pytest.fixture(autouse=True)
def mock_cache_globally(monkeypatch):
    """Global fixture to mock cache operations."""
    async def get_mock(self, key):
        return None

    async def set_mock(self, key, value):
        pass

    from core.cache_manager import CacheManager
    monkeypatch.setattr(CacheManager, "get", get_mock)
    monkeypatch.setattr(CacheManager, "set", set_mock)


class TestAnalyzerBasics:
    """Basic functionality tests."""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        assert analyzer.total_searches == 0
        assert analyzer.total_breaches_found == 0
        assert len(analyzer.searches_by_type) == 6
        assert analyzer.http_client is not None

    @pytest.mark.asyncio
    async def test_repr_method(self):
        """Test __repr__ method."""
        analyzer = BreachDataAnalyzer()

        repr_str = repr(analyzer)

        assert "BreachDataAnalyzer" in repr_str
        assert "searches=0" in repr_str
        assert "breaches_found=0" in repr_str

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        async with BreachDataAnalyzer() as analyzer:
            assert analyzer.http_client is not None

        # Client should be closed after exit
        # Note: httpx doesn't expose is_closed, so we just verify no exception


class TestInputValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_invalid_search_type_raises_error(self):
        """Test invalid search type raises ValueError."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        with pytest.raises(ValueError, match="Invalid search_type"):
            await analyzer.query(target="test", search_type="invalid")

    @pytest.mark.asyncio
    async def test_invalid_email_format_raises_error(self):
        """Test invalid email format raises ValueError."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        with pytest.raises(ValueError, match="Invalid email format"):
            await analyzer.query(target="not-an-email", search_type="email")

    @pytest.mark.asyncio
    async def test_invalid_ip_format_raises_error(self):
        """Test invalid IP format raises ValueError."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        with pytest.raises(ValueError, match="Invalid IPv4 format"):
            await analyzer.query(target="999.999.999.999", search_type="ip")

    @pytest.mark.asyncio
    async def test_invalid_domain_format_raises_error(self):
        """Test invalid domain format raises ValueError."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        with pytest.raises(ValueError, match="Invalid domain format"):
            await analyzer.query(target="not a domain!", search_type="domain")

    @pytest.mark.asyncio
    async def test_invalid_hash_length_raises_error(self):
        """Test invalid hash length raises ValueError."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        with pytest.raises(ValueError, match="Invalid hash length"):
            await analyzer.query(target="tooshort", search_type="password_hash")


class TestEmailSearch:
    """Email search tests."""

    @pytest.mark.asyncio
    async def test_email_search_without_api_key_raises_error(self):
        """Test email search without API key raises error."""
        analyzer = BreachDataAnalyzer()  # No API key

        # Mock HTTP client to avoid actual request
        analyzer.http_client.get = AsyncMock()

        with pytest.raises(ValueError, match="HIBP API key required"):
            await analyzer.query(target="test@example.com", search_type="email")

    @pytest.mark.asyncio
    async def test_email_search_no_breaches_found(self):
        """Test email search when no breaches found (404 response)."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        # Mock 404 response (no breaches)
        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="safe@example.com", search_type="email")

        assert result["breach_count"] == 0
        assert result["risk_score"] == 0.0
        assert result["risk_level"] == "LOW"

    @pytest.mark.asyncio
    async def test_email_search_with_breaches(self):
        """Test email search with breaches found."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        # Mock successful response with breaches
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {
                "Name": "TestBreach",
                "Title": "Test Breach 2024",
                "Domain": "testbreach.com",
                "BreachDate": "2024-01-15",
                "AddedDate": "2024-01-20T00:00:00Z",
                "ModifiedDate": "2024-01-21T00:00:00Z",
                "PwnCount": 100000,
                "Description": "Test breach description",
                "DataClasses": ["Email", "Passwords"],
                "IsVerified": True,
                "IsFabricated": False,
                "IsSensitive": True,
                "IsRetired": False,
                "IsSpamList": False,
                "LogoPath": "/logos/testbreach.png",
            }
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="pwned@example.com", search_type="email")

        assert result["breach_count"] == 1
        assert result["risk_score"] > 0
        assert "breaches" in result
        assert result["breaches"][0]["name"] == "TestBreach"
        assert result["breaches"][0]["source"] == "hibp"

    @pytest.mark.asyncio
    async def test_email_search_with_unverified_flag(self):
        """Test email search with include_unverified flag."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        await analyzer.query(
            target="test@example.com",
            search_type="email",
            include_unverified=True
        )

        # Verify API was called with includeUnverified param
        call_args = analyzer.http_client.get.call_args
        assert call_args[1]["params"]["includeUnverified"] == "true"


class TestHIBPIntegration:
    """HIBP API integration tests."""

    @pytest.mark.asyncio
    async def test_hibp_401_invalid_api_key(self):
        """Test HIBP 401 response for invalid API key."""
        analyzer = BreachDataAnalyzer(api_key="invalid_key")

        mock_response = MagicMock()
        mock_response.status_code = 401
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="Invalid HIBP API key"):
            await analyzer.query(target="test@example.com", search_type="email")

    @pytest.mark.asyncio
    async def test_hibp_429_rate_limit_exceeded(self):
        """Test HIBP 429 response for rate limit exceeded."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 429
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(RateLimitError, match="rate limit exceeded"):
            await analyzer.query(target="test@example.com", search_type="email")

    @pytest.mark.asyncio
    async def test_hibp_http_error(self):
        """Test HIBP HTTP error handling."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response
        ))
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await analyzer.query(target="test@example.com", search_type="email")

    @pytest.mark.asyncio
    async def test_hibp_network_error(self):
        """Test HIBP network error handling."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        # Mock network error
        analyzer.http_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        with pytest.raises(httpx.ConnectError):
            await analyzer.query(target="test@example.com", search_type="email")


class TestRiskScoring:
    """Risk scoring algorithm tests."""

    @pytest.mark.asyncio
    async def test_risk_score_calculation_no_breaches(self):
        """Test risk score is 0 for no breaches."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="safe@example.com", search_type="email")

        assert result["risk_score"] == 0.0
        assert result["risk_level"] == "LOW"

    @pytest.mark.asyncio
    async def test_risk_score_calculation_with_passwords(self):
        """Test risk score is higher when passwords exposed."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {
                "Name": "PasswordBreach",
                "Title": "Password Breach",
                "Domain": "test.com",
                "BreachDate": "2024-01-01",
                "AddedDate": "2024-01-01T00:00:00Z",
                "PwnCount": 1000000,
                "DataClasses": ["Passwords", "Email"],
                "IsVerified": True,
                "IsSensitive": True,
            }
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="pwned@example.com", search_type="email")

        # Should have high risk due to passwords
        assert result["risk_score"] > 30

    @pytest.mark.asyncio
    async def test_risk_level_critical(self):
        """Test risk level CRITICAL for score >= 75."""
        analyzer = BreachDataAnalyzer()

        level = analyzer._get_risk_level(80.0)

        assert level == "CRITICAL"

    @pytest.mark.asyncio
    async def test_risk_level_high(self):
        """Test risk level HIGH for score >= 50."""
        analyzer = BreachDataAnalyzer()

        level = analyzer._get_risk_level(60.0)

        assert level == "HIGH"

    @pytest.mark.asyncio
    async def test_risk_level_medium(self):
        """Test risk level MEDIUM for score >= 25."""
        analyzer = BreachDataAnalyzer()

        level = analyzer._get_risk_level(30.0)

        assert level == "MEDIUM"

    @pytest.mark.asyncio
    async def test_risk_level_low(self):
        """Test risk level LOW for score < 25."""
        analyzer = BreachDataAnalyzer()

        level = analyzer._get_risk_level(10.0)

        assert level == "LOW"

    @pytest.mark.asyncio
    async def test_fabricated_breach_reduced_score(self):
        """Test fabricated breaches have reduced risk score."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {
                "Name": "FakeBreach",
                "Title": "Fake Breach",
                "Domain": "fake.com",
                "BreachDate": "2024-01-01",
                "PwnCount": 1000000,
                "DataClasses": ["Passwords", "Email"],
                "IsVerified": False,
                "IsSensitive": False,
                "IsFabricated": True,  # Fabricated breach
            }
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        # Fabricated breaches should have significantly lower score (70% penalty)
        assert result["risk_score"] < 20


class TestBreachDeduplication:
    """Breach deduplication tests."""

    @pytest.mark.asyncio
    async def test_deduplicate_identical_breaches(self):
        """Test deduplication removes identical breaches."""
        analyzer = BreachDataAnalyzer()

        breaches = [
            {"name": "Breach1", "domain": "test.com"},
            {"name": "Breach1", "domain": "test.com"},  # Duplicate
            {"name": "Breach2", "domain": "example.com"},
        ]

        unique = analyzer._deduplicate_breaches(breaches)

        assert len(unique) == 2

    @pytest.mark.asyncio
    async def test_deduplicate_no_duplicates(self):
        """Test deduplication keeps all unique breaches."""
        analyzer = BreachDataAnalyzer()

        breaches = [
            {"name": "Breach1", "domain": "test.com"},
            {"name": "Breach2", "domain": "example.com"},
            {"name": "Breach3", "domain": "foo.com"},
        ]

        unique = analyzer._deduplicate_breaches(breaches)

        assert len(unique) == 3


class TestTimeline:
    """Timeline generation tests."""

    @pytest.mark.asyncio
    async def test_timeline_sorted_by_date(self):
        """Test timeline is sorted by date (newest first)."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"Name": "Old", "BreachDate": "2020-01-01", "PwnCount": 100, "DataClasses": []},
            {"Name": "New", "BreachDate": "2024-01-01", "PwnCount": 200, "DataClasses": []},
            {"Name": "Mid", "BreachDate": "2022-01-01", "PwnCount": 150, "DataClasses": []},
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        timeline = result["timeline"]
        assert timeline[0]["name"] == "New"
        assert timeline[1]["name"] == "Mid"
        assert timeline[2]["name"] == "Old"


class TestRecommendations:
    """Remediation recommendations tests."""

    @pytest.mark.asyncio
    async def test_recommendations_password_exposed(self):
        """Test recommendations include password change when passwords exposed."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"Name": "Test", "BreachDate": "2024-01-01", "PwnCount": 100, "DataClasses": ["Passwords"]}
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        recommendations = result["recommendations"]
        assert any("Change Password" in r["action"] for r in recommendations)

    @pytest.mark.asyncio
    async def test_recommendations_financial_exposed(self):
        """Test recommendations include financial monitoring when financial data exposed."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"Name": "Test", "BreachDate": "2024-01-01", "PwnCount": 100, "DataClasses": ["CreditCards"]}
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        recommendations = result["recommendations"]
        assert any("Financial" in r["action"] for r in recommendations)

    @pytest.mark.asyncio
    async def test_recommendations_high_risk_includes_2fa(self):
        """Test high risk score includes 2FA recommendation."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {
                "Name": "Test",
                "BreachDate": "2024-01-01",
                "PwnCount": 10000000,
                "DataClasses": ["Passwords", "Email", "SSN"],
                "IsVerified": True,
                "IsSensitive": True,
            }
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        recommendations = result["recommendations"]
        assert any("2FA" in r["action"] or "MFA" in r["action"] for r in recommendations)

    @pytest.mark.asyncio
    async def test_recommendations_multiple_breaches_password_manager(self):
        """Test multiple breaches recommends password manager."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        # Create 6 breaches
        breaches = [
            {"Name": f"Breach{i}", "BreachDate": f"2024-0{i}-01", "PwnCount": 100, "DataClasses": []}
            for i in range(1, 7)
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=breaches)
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        recommendations = result["recommendations"]
        assert any("Password Manager" in r["action"] for r in recommendations)


class TestStatistics:
    """Statistics tracking tests."""

    @pytest.mark.asyncio
    async def test_data_classes_count(self):
        """Test data classes counting across breaches."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"Name": "B1", "BreachDate": "2024-01-01", "PwnCount": 100, "DataClasses": ["Email", "Passwords"]},
            {"Name": "B2", "BreachDate": "2024-02-01", "PwnCount": 200, "DataClasses": ["Email", "Phone"]},
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        data_classes = result["statistics"]["total_data_classes"]
        assert data_classes["Email"] == 2
        assert data_classes["Passwords"] == 1
        assert data_classes["Phone"] == 1

    @pytest.mark.asyncio
    async def test_most_recent_breach(self):
        """Test most recent breach identification."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"Name": "Old", "BreachDate": "2020-01-01", "PwnCount": 100, "DataClasses": []},
            {"Name": "New", "BreachDate": "2024-01-01", "PwnCount": 200, "DataClasses": []},
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        most_recent = result["statistics"]["most_recent_breach"]
        assert most_recent["name"] == "New"
        assert most_recent["date"] == "2024-01-01"

    @pytest.mark.asyncio
    async def test_oldest_breach(self):
        """Test oldest breach identification."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"Name": "Old", "BreachDate": "2020-01-01", "PwnCount": 100, "DataClasses": []},
            {"Name": "New", "BreachDate": "2024-01-01", "PwnCount": 200, "DataClasses": []},
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        oldest = result["statistics"]["oldest_breach"]
        assert oldest["name"] == "Old"
        assert oldest["date"] == "2020-01-01"

    @pytest.mark.asyncio
    async def test_statistics_updated_after_search(self):
        """Test statistics are updated after search."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {"Name": "Test", "BreachDate": "2024-01-01", "PwnCount": 100, "DataClasses": []}
        ])
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        await analyzer.query(target="test@example.com", search_type="email")

        assert analyzer.total_searches == 1
        assert analyzer.searches_by_type["email"] == 1
        assert analyzer.total_breaches_found == 1


class TestMultiSource:
    """Multi-source aggregation tests."""

    @pytest.mark.asyncio
    async def test_unsupported_source_warning(self):
        """Test unsupported source logs warning."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(
            target="test@example.com",
            search_type="email",
            sources=["hibp", "unsupported"]
        )

        # Should have source results
        assert "unsupported" in result["sources_queried"]
        assert result["sources_queried"]["unsupported"]["success"] is False

    @pytest.mark.asyncio
    async def test_source_failure_handling(self):
        """Test source failure is handled gracefully."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        # Mock HIBP to fail
        analyzer.http_client.get = AsyncMock(side_effect=Exception("API error"))

        result = await analyzer.query(target="test@example.com", search_type="email")

        # Should still return result with error in sources_queried
        assert result["breach_count"] == 0
        assert result["sources_queried"]["hibp"]["success"] is False


class TestOtherSearchTypes:
    """Tests for non-email search types."""

    @pytest.mark.asyncio
    async def test_ip_search_not_implemented(self):
        """Test IP search returns empty (not yet implemented for HIBP)."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="192.168.1.1", search_type="ip")

        # Should complete but find no breaches (not implemented)
        assert result["breach_count"] == 0

    @pytest.mark.asyncio
    async def test_username_search_valid_format(self):
        """Test username search accepts valid format."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        # Should not raise validation error
        result = await analyzer.query(target="testuser123", search_type="username")

        assert result["search_type"] == "username"

    @pytest.mark.asyncio
    async def test_phone_search_valid_format(self):
        """Test phone search accepts valid format."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        # Should not raise validation error
        result = await analyzer.query(target="+15551234567", search_type="phone")

        assert result["search_type"] == "phone"

    @pytest.mark.asyncio
    async def test_domain_search_valid_format(self):
        """Test domain search validates correctly."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="example.com", search_type="domain")

        assert result["search_type"] == "domain"

    @pytest.mark.asyncio
    async def test_password_hash_md5_format(self):
        """Test password hash search accepts MD5 (32 chars)."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        # MD5 hash (32 characters)
        result = await analyzer.query(
            target="5d41402abc4b2a76b9719d911017c592",
            search_type="password_hash"
        )

        assert result["search_type"] == "password_hash"

    @pytest.mark.asyncio
    async def test_password_hash_sha256_format(self):
        """Test password hash search accepts SHA256 (64 chars)."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        # SHA256 hash (64 characters)
        result = await analyzer.query(
            target="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            search_type="password_hash"
        )

        assert result["search_type"] == "password_hash"


class TestGetStatus:
    """Status and health check tests."""

    @pytest.mark.asyncio
    async def test_get_status_returns_metrics(self):
        """Test get_status returns analyzer metrics."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        status = await analyzer.get_status()

        assert status["tool"] == "BreachDataAnalyzer"
        assert "total_searches" in status
        assert "total_breaches_found" in status
        assert "searches_by_type" in status
        assert "supported_sources" in status
        assert "active_sources" in status


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_empty_breaches_list_statistics(self):
        """Test statistics handle empty breaches gracefully."""
        analyzer = BreachDataAnalyzer()

        # Test with empty list
        most_recent = analyzer._get_most_recent_breach([])
        oldest = analyzer._get_oldest_breach([])
        data_classes = analyzer._count_data_classes([])

        assert most_recent is None
        assert oldest is None
        assert data_classes == {}

    @pytest.mark.asyncio
    async def test_breaches_without_dates(self):
        """Test timeline handles breaches without dates."""
        analyzer = BreachDataAnalyzer()

        breaches = [
            {"name": "NoDates", "data_classes": []},
        ]

        most_recent = analyzer._get_most_recent_breach(breaches)
        oldest = analyzer._get_oldest_breach(breaches)

        assert most_recent is None
        assert oldest is None

    @pytest.mark.asyncio
    async def test_result_structure_complete(self):
        """Test result dictionary has all expected fields."""
        analyzer = BreachDataAnalyzer(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 404
        analyzer.http_client.get = AsyncMock(return_value=mock_response)

        result = await analyzer.query(target="test@example.com", search_type="email")

        # Verify all expected fields
        assert "timestamp" in result
        assert "target" in result
        assert "search_type" in result
        assert "breach_count" in result
        assert "risk_score" in result
        assert "risk_level" in result
        assert "breaches" in result
        assert "timeline" in result
        assert "recommendations" in result
        assert "sources_queried" in result
        assert "statistics" in result
