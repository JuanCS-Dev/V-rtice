"""
Complete coverage tests for Threat Intelligence Collector.
Target: 100% code coverage (19 missing lines)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ..threat_intelligence_collector import (
    ThreatIntelligenceCollector,
    ThreatIntelligenceConfig,
    ThreatIndicator
)


class TestThreatIntelComplete100Coverage:
    """Tests to achieve 100% coverage for Threat Intelligence Collector."""

    @pytest.mark.asyncio
    async def test_check_ip_when_check_ips_disabled(self):
        """Test check_ip returns None when check_ips is False."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            check_ips=False  # Disable IP checks - covers line 248
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Should return None immediately without checking
        result = await collector.check_ip("8.8.8.8")
        assert result is None  # Line 249 covered

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_ip_rate_limit_exceeded(self):
        """Test check_ip returns None when rate limit exceeded."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            requests_per_minute=1  # Very low limit
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Fill up rate limit
        for _ in range(10):
            collector.request_times.append(datetime.utcnow())

        # Should return None due to rate limit - covers line 263
        result = await collector.check_ip("8.8.8.8")
        assert result is None  # No API call made

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_domain_when_check_domains_disabled(self):
        """Test check_domain returns None when check_domains is False."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            check_domains=False  # Disable domain checks - covers line 306
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Should return None immediately
        result = await collector.check_domain("example.com")
        assert result is None  # Line 307 covered

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_domain_cache_hit(self):
        """Test check_domain returns cached result."""
        config = ThreatIntelligenceConfig(virustotal_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)

        # Pre-populate cache - covers lines 311-312
        cached_indicator = ThreatIndicator(
            indicator_type="domain",
            value="evil.com",
            source="cache",
            severity="high",
            confidence=0.9
        )
        collector.cache["domain:evil.com"] = cached_indicator

        # Should return cached value - line 312 covered
        result = await collector.check_domain("evil.com")
        assert result == cached_indicator

    @pytest.mark.asyncio
    async def test_check_domain_rate_limit_exceeded(self):
        """Test check_domain returns None when rate limited."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            requests_per_minute=1
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Fill rate limit
        for _ in range(10):
            collector.request_times.append(datetime.utcnow())

        # Should return None - covers line 315
        result = await collector.check_domain("example.com")
        assert result is None

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_domain_no_scores_available(self):
        """Test check_domain returns None when no scores from APIs."""
        config = ThreatIntelligenceConfig(virustotal_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Mock API to return None score
        with patch.object(collector, '_check_domain_virustotal', return_value=None):
            result = await collector.check_domain("example.com")
            assert result is None  # Line 328 covered (no scores)

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_hash_when_check_hashes_disabled(self):
        """Test check_hash returns None when check_hashes is False."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            check_hashes=False  # Disable hash checks - covers line 352
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Should return None immediately
        result = await collector.check_hash("abc123")
        assert result is None  # Line 353 covered

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_hash_cache_hit(self):
        """Test check_hash returns cached result."""
        config = ThreatIntelligenceConfig(virustotal_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)

        # Pre-populate cache - covers lines 357-358
        cached_indicator = ThreatIndicator(
            indicator_type="hash",
            value="abc123",
            source="cache",
            severity="critical",
            confidence=0.95
        )
        collector.cache["hash:abc123"] = cached_indicator

        # Should return cached value - line 358 covered
        result = await collector.check_hash("abc123")
        assert result == cached_indicator

    @pytest.mark.asyncio
    async def test_check_hash_rate_limit_exceeded(self):
        """Test check_hash returns None when rate limited."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            requests_per_minute=1
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Fill rate limit
        for _ in range(10):
            collector.request_times.append(datetime.utcnow())

        # Should return None - covers line 361
        result = await collector.check_hash("abc123")
        assert result is None

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_hash_no_scores_available(self):
        """Test check_hash returns None when no API scores."""
        config = ThreatIntelligenceConfig(virustotal_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Mock API to return None
        with patch.object(collector, '_check_hash_virustotal', return_value=None):
            result = await collector.check_hash("abc123")
            assert result is None  # Line 374 covered

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_hash_below_threshold(self):
        """Test check_hash returns None when score below threshold."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            min_reputation_score=0.8  # High threshold
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Mock API to return low score (0.2)
        with patch.object(collector, '_check_hash_virustotal', return_value=0.2):
            result = await collector.check_hash("abc123")
            assert result is None  # Line 393 covered (below threshold)

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_hash_virustotal_non_200_response(self):
        """Test _check_hash_virustotal returns None on non-200 status."""
        config = ThreatIntelligenceConfig(virustotal_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Create mock response object
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get to return the mock response
        collector.session.get = MagicMock(return_value=mock_response)

        # Should return None - covers line 491
        result = await collector._check_hash_virustotal("abc123")
        assert result is None

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_collect_alienvault_non_200_response(self):
        """Test _collect_alienvault returns empty list on non-200."""
        config = ThreatIntelligenceConfig(alienvault_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Create mock response object
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get to return the mock response
        collector.session.get = MagicMock(return_value=mock_response)

        # Should return empty list - covers line 529
        indicators = await collector._collect_alienvault()
        assert indicators == []

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_collect_misp_non_200_response(self):
        """Test _collect_misp returns empty list on non-200."""
        config = ThreatIntelligenceConfig(
            misp_url="http://misp.local",
            misp_api_key="test_key"
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Create mock response object
        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get to return the mock response
        collector.session.get = MagicMock(return_value=mock_response)

        # Should return empty list - covers line 570
        indicators = await collector._collect_misp()
        assert indicators == []

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_collect_misp_event_no_id(self):
        """Test _collect_misp skips events without ID."""
        config = ThreatIntelligenceConfig(
            misp_url="http://misp.local",
            misp_api_key="test_key"
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Create mock response object with events without IDs
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {"Event": {}},  # No ID - covers lines 576-577
            {"Event": {"other_field": "value"}}
        ])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get to return the mock response
        collector.session.get = MagicMock(return_value=mock_response)

        # Should skip events without ID
        indicators = await collector._collect_misp()
        assert indicators == []

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_collect_misp_detail_non_200(self):
        """Test _collect_misp skips events when detail fetch fails."""
        config = ThreatIntelligenceConfig(
            misp_url="http://misp.local",
            misp_api_key="test_key"
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Mock multiple calls - first succeeds (list), second fails (detail)
        call_count = [0]  # Use list to make it mutable in nested function

        def mock_get(*args, **kwargs):
            call_count[0] += 1

            if call_count[0] == 1:
                # First call (list events) succeeds
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value=[
                    {"Event": {"id": "123"}}
                ])
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)
                return mock_response
            else:
                # Second call (detail) fails - covers line 583-584
                mock_response = MagicMock()
                mock_response.status = 500
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)
                return mock_response

        collector.session.get = mock_get

        # Should skip event due to failed detail fetch
        indicators = await collector._collect_misp()
        assert indicators == []

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_clean_cache_dict_entry_with_timestamp(self):
        """Test _clean_cache handles dict entries with timestamp field."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            cache_ttl_minutes=60
        )
        collector = ThreatIntelligenceCollector(config)

        # Add dict entry with old timestamp (should be expired)
        old_time = datetime.utcnow() - timedelta(minutes=120)
        collector.cache["old_entry"] = {
            "data": "test",
            "timestamp": old_time  # Covers line 670-672
        }

        # Add dict entry with recent timestamp (should NOT expire)
        collector.cache["new_entry"] = {
            "data": "test",
            "timestamp": datetime.utcnow()
        }

        # Clean cache
        collector._clean_cache()

        # Old entry should be deleted, new entry should remain
        assert "old_entry" not in collector.cache  # Line 675 covered
        assert "new_entry" in collector.cache

    def test_repr_string(self):
        """Test __repr__ returns expected string."""
        config = ThreatIntelligenceConfig(virustotal_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)

        repr_str = repr(collector)
        assert "ThreatIntelligenceCollector" in repr_str
        assert "healthy" in repr_str

    @pytest.mark.asyncio
    async def test_check_domain_below_threshold(self):
        """Test check_domain returns None when score below threshold."""
        config = ThreatIntelligenceConfig(
            virustotal_api_key="test_key",
            min_reputation_score=0.8  # High threshold
        )
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Mock API to return low score (0.2)
        with patch.object(collector, '_check_domain_virustotal', return_value=0.2):
            result = await collector.check_domain("example.com")
            assert result is None  # Line 347 covered (below threshold)

        await collector.cleanup()

    @pytest.mark.asyncio
    async def test_check_domain_virustotal_non_200_response(self):
        """Test _check_domain_virustotal returns None on non-200 status."""
        config = ThreatIntelligenceConfig(virustotal_api_key="test_key")
        collector = ThreatIntelligenceCollector(config)
        await collector.initialize()

        # Create mock response object
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get to return the mock response
        collector.session.get = MagicMock(return_value=mock_response)

        # Should return None - covers line 466
        result = await collector._check_domain_virustotal("example.com")
        assert result is None

        await collector.cleanup()
