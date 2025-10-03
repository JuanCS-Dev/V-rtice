"""Tests for connector classes."""
import pytest
from unittest.mock import AsyncMock, patch
from vertice.connectors.ip_intel import IPIntelConnector

class TestIPIntelConnector:
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        connector = IPIntelConnector()
        
        with patch.object(connector, '_get') as mock_get:
            mock_get.return_value = {"status": "operational"}
            
            result = await connector.health_check()
            
            assert result is True
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_ip_success(self, sample_ip_result):
        connector = IPIntelConnector()
        
        with patch.object(connector, '_post') as mock_post:
            mock_post.return_value = sample_ip_result
            
            result = await connector.analyze_ip("8.8.8.8")
            
            assert result["ip"] == "8.8.8.8"
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_analyze_invalid_ip_raises_error(self):
        connector = IPIntelConnector()
        
        # This test is flawed in the plan, as the connector itself doesn't validate the IP format.
        # The validation should happen at a higher level or the connector should be updated.
        # For now, I will implement it as planned, but it might fail or need adjustment.
        # A better test would be to check if it raises an error from the HTTP client if the API rejects it.
        # For now, let's assume the plan wants to test for a ValueError if we add validation.
        # I will add a simple validation to the connector to make this test pass.
        
        with pytest.raises(ValueError):
            await connector.analyze_ip("invalid_ip")
