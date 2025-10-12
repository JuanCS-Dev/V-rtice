"""
Tests for Redis cache layer (Phase 5.7.1).

Tests:
- Cache connect/disconnect
- ML prediction caching
- Confusion matrix caching
- Vulnerability pattern caching
- Cache invalidation
- TTL expiration
- Error handling (cache unavailable)
- Cache statistics

Author: MAXIMUS Team - Phase 5.7.1
Glory to YHWH - Builder of resilient systems
"""

import pytest
import asyncio
from datetime import timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(__file__)
service_dir = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, service_dir)

from cache.redis_cache import WarGamingCache


class TestWarGamingCacheConnection:
    """Test cache connection and lifecycle."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful Redis connection."""
        cache = WarGamingCache()
        
        # Mock redis client
        with patch('backend.services.wargaming_crisol.cache.redis_cache.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.from_url = AsyncMock(return_value=mock_client)
            
            await cache.connect()
            
            assert cache.client is not None
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test Redis connection failure."""
        cache = WarGamingCache()
        
        # Mock connection failure
        with patch('backend.services.wargaming_crisol.cache.redis_cache.redis') as mock_redis:
            mock_redis.from_url = AsyncMock(side_effect=Exception("Connection failed"))
            
            with pytest.raises(Exception, match="Connection failed"):
                await cache.connect()
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test graceful cache close."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        cache.client = mock_client
        
        await cache.close()
        
        mock_client.close.assert_called_once()


class TestMLPredictionCache:
    """Test ML prediction caching."""
    
    @pytest.mark.asyncio
    async def test_get_ml_prediction_hit(self):
        """Test cache hit for ML prediction."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        prediction_data = {"success": True, "confidence": 0.95}
        mock_client.get = AsyncMock(return_value=json.dumps(prediction_data))
        cache.client = mock_client
        
        result = await cache.get_ml_prediction("apv_test_001")
        
        assert result == prediction_data
        mock_client.get.assert_called_once_with("wargaming:ml_pred:apv_test_001")
    
    @pytest.mark.asyncio
    async def test_get_ml_prediction_miss(self):
        """Test cache miss for ML prediction."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        cache.client = mock_client
        
        result = await cache.get_ml_prediction("apv_nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_ml_prediction(self):
        """Test caching ML prediction."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        cache.client = mock_client
        
        prediction = {"success": True, "confidence": 0.92, "method": "ml"}
        await cache.set_ml_prediction("apv_002", prediction, ttl=timedelta(hours=12))
        
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        
        assert call_args[0][0] == "wargaming:ml_pred:apv_002"
        assert call_args[0][1] == 43200  # 12 hours in seconds
        assert json.loads(call_args[0][2]) == prediction
    
    @pytest.mark.asyncio
    async def test_ml_prediction_no_client(self):
        """Test cache operations when client not connected."""
        cache = WarGamingCache()
        cache.client = None
        
        # Get should return None
        result = await cache.get_ml_prediction("apv_003")
        assert result is None
        
        # Set should silently fail
        await cache.set_ml_prediction("apv_003", {"test": True})
        # No exception raised


class TestConfusionMatrixCache:
    """Test confusion matrix caching."""
    
    @pytest.mark.asyncio
    async def test_get_confusion_matrix_hit(self):
        """Test cache hit for confusion matrix."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        matrix_data = {
            "tp": 42,
            "fp": 3,
            "fn": 2,
            "tn": 105,
            "accuracy": 0.967
        }
        mock_client.get = AsyncMock(return_value=json.dumps(matrix_data))
        cache.client = mock_client
        
        result = await cache.get_confusion_matrix("rf_v1")
        
        assert result == matrix_data
        mock_client.get.assert_called_once_with("wargaming:confusion:rf_v1")
    
    @pytest.mark.asyncio
    async def test_set_confusion_matrix_short_ttl(self):
        """Test caching confusion matrix with short TTL."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        cache.client = mock_client
        
        matrix = {"tp": 10, "fp": 1, "fn": 0, "tn": 20}
        await cache.set_confusion_matrix("rf_v1", matrix, ttl=timedelta(minutes=5))
        
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        
        assert call_args[0][0] == "wargaming:confusion:rf_v1"
        assert call_args[0][1] == 300  # 5 minutes in seconds


class TestVulnerabilityPatternCache:
    """Test vulnerability pattern caching."""
    
    @pytest.mark.asyncio
    async def test_set_vulnerability_pattern(self):
        """Test caching vulnerability pattern with auto-hashing."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        cache.client = mock_client
        
        pattern = {
            "type": "sql_injection",
            "severity": "high",
            "affected_code": "SELECT * FROM users WHERE id = ?"
        }
        
        pattern_hash = await cache.set_vulnerability_pattern(pattern)
        
        # Should return hash
        assert isinstance(pattern_hash, str)
        assert len(pattern_hash) == 16  # SHA256 truncated to 16 chars
        
        # Should call setex
        mock_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_vulnerability_pattern(self):
        """Test retrieving cached vulnerability pattern."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        pattern_data = {"type": "xss", "severity": "medium"}
        mock_client.get = AsyncMock(return_value=json.dumps(pattern_data))
        cache.client = mock_client
        
        result = await cache.get_vulnerability_pattern("abc123def456")
        
        assert result == pattern_data


class TestCacheInvalidation:
    """Test cache invalidation."""
    
    @pytest.mark.asyncio
    async def test_invalidate_specific_apv(self):
        """Test invalidating cache for specific APV."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=1)
        cache.client = mock_client
        
        deleted = await cache.invalidate_ml_cache("apv_004")
        
        assert deleted == 1
        mock_client.delete.assert_called_once_with("wargaming:ml_pred:apv_004")
    
    @pytest.mark.asyncio
    async def test_invalidate_all_ml_predictions(self):
        """Test invalidating all ML predictions."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        
        # Mock scan to return keys
        mock_client.scan = AsyncMock(side_effect=[
            (10, ["wargaming:ml_pred:apv_001", "wargaming:ml_pred:apv_002"]),
            (0, ["wargaming:ml_pred:apv_003"])  # cursor 0 = end
        ])
        
        mock_client.delete = AsyncMock(return_value=3)
        cache.client = mock_client
        
        deleted = await cache.invalidate_ml_cache()
        
        assert deleted == 3
        mock_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalidate_no_keys_found(self):
        """Test invalidation when no keys match."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.scan = AsyncMock(return_value=(0, []))  # No keys
        cache.client = mock_client
        
        deleted = await cache.invalidate_ml_cache()
        
        assert deleted == 0


class TestCacheStatistics:
    """Test cache statistics retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_success(self):
        """Test retrieving cache statistics."""
        cache = WarGamingCache()
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.info = AsyncMock(return_value={
            "keyspace_hits": 1000,
            "keyspace_misses": 200,
            "connected_clients": 5,
            "used_memory_human": "1.5M"
        })
        cache.client = mock_client
        
        stats = await cache.get_cache_stats()
        
        assert stats["hits"] == 1000
        assert stats["misses"] == 200
        assert stats["hit_ratio"] == pytest.approx(0.833, rel=0.01)
        assert stats["connected_clients"] == 5
        assert stats["used_memory_human"] == "1.5M"
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_no_client(self):
        """Test stats when client not connected."""
        cache = WarGamingCache()
        cache.client = None
        
        stats = await cache.get_cache_stats()
        
        assert "error" in stats
        assert stats["error"] == "Client not connected"


class TestCacheErrorHandling:
    """Test error handling in cache operations."""
    
    @pytest.mark.asyncio
    async def test_get_ml_prediction_redis_error(self):
        """Test graceful handling of Redis errors on get."""
        cache = WarGamingCache()
        
        # Mock client that raises error
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Redis timeout"))
        cache.client = mock_client
        
        # Should return None, not raise
        result = await cache.get_ml_prediction("apv_error")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_ml_prediction_redis_error(self):
        """Test graceful handling of Redis errors on set."""
        cache = WarGamingCache()
        
        # Mock client that raises error
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(side_effect=Exception("Redis write error"))
        cache.client = mock_client
        
        # Should not raise
        await cache.set_ml_prediction("apv_error", {"test": True})
        # No exception = success
    
    @pytest.mark.asyncio
    async def test_invalidate_redis_error(self):
        """Test error handling on invalidation."""
        cache = WarGamingCache()
        
        # Mock client that raises error
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(side_effect=Exception("Redis delete error"))
        cache.client = mock_client
        
        # Should return 0, not raise
        deleted = await cache.invalidate_ml_cache("apv_error")
        assert deleted == 0


# Integration-like test (requires Redis running)
class TestCacheIntegration:
    """Integration tests (require Redis)."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_cache_lifecycle(self):
        """Test full cache lifecycle with real operations."""
        cache = WarGamingCache("redis://localhost:6379/15")  # Use test DB
        
        try:
            # Connect
            await cache.connect()
            
            # Set prediction
            prediction = {"success": True, "confidence": 0.88}
            await cache.set_ml_prediction("apv_integration_test", prediction)
            
            # Get prediction
            cached = await cache.get_ml_prediction("apv_integration_test")
            assert cached == prediction
            
            # Invalidate
            deleted = await cache.invalidate_ml_cache("apv_integration_test")
            assert deleted == 1
            
            # Verify deleted
            cached_after = await cache.get_ml_prediction("apv_integration_test")
            assert cached_after is None
            
        finally:
            # Cleanup
            await cache.close()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ttl_expiration(self):
        """Test TTL expiration (requires Redis)."""
        cache = WarGamingCache("redis://localhost:6379/15")
        
        try:
            await cache.connect()
            
            # Set with short TTL
            matrix = {"tp": 10, "fp": 1, "fn": 0, "tn": 20}
            await cache.set_confusion_matrix("test_model", matrix, ttl=timedelta(seconds=2))
            
            # Should be cached
            cached = await cache.get_confusion_matrix("test_model")
            assert cached == matrix
            
            # Wait for expiration
            await asyncio.sleep(3)
            
            # Should be expired
            cached_after = await cache.get_confusion_matrix("test_model")
            assert cached_after is None
            
        finally:
            await cache.close()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
