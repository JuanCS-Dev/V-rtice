"""Integration tests for Kafka APV Publisher.

Tests cover:
- Publisher initialization
- Single APV publishing
- Batch publishing
- DLQ handling
- Metrics collection

Note: These tests use mocks for Kafka to avoid needing real Kafka instance.
For true integration tests with real Kafka, see tests/integration/

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: TDD | Coverage ≥90%
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json

# Add parent to path
service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(service_root))

from kafka_integration.apv_publisher import APVPublisher
from services.maximus_oraculo.models.apv import APV, AffectedPackage


class TestAPVPublisher:
    """Test APV Publisher."""
    
    def test_publisher_initialization(self):
        """Test publisher initialization."""
        publisher = APVPublisher(
            bootstrap_servers="localhost:9096",
            apv_topic="test.apv",
            dlq_topic="test.dlq"
        )
        
        assert publisher.bootstrap_servers == "localhost:9096"
        assert publisher.apv_topic == "test.apv"
        assert publisher.dlq_topic == "test.dlq"
        assert publisher._published_count == 0
        assert publisher._failed_count == 0
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping producer."""
        publisher = APVPublisher()
        
        with patch('kafka_integration.apv_publisher.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            # Start
            await publisher.start()
            assert mock_producer.start.called
            
            # Stop
            await publisher.stop()
            assert mock_producer.stop.called
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        with patch('kafka_integration.apv_publisher.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            async with APVPublisher() as publisher:
                assert mock_producer.start.called
                assert publisher._producer is not None
            
            # Should stop after exiting context
            assert mock_producer.stop.called
    
    @pytest.mark.asyncio
    async def test_publish_apv_success(self):
        """Test successful APV publishing."""
        # Create a test APV
        apv = APV(
            cve_id="CVE-2024-12345",
            published=datetime.utcnow(),
            modified=datetime.utcnow(),
            summary="Test vulnerability",
            details="Test details with sufficient length for validation",
            affected_packages=[
                AffectedPackage(
                    ecosystem="PyPI",
                    name="test-package",
                    affected_versions=["*"],
                    fixed_versions=["1.0.0"]
                )
            ],
            source_feed="test"
        )
        
        publisher = APVPublisher()
        
        with patch('kafka_integration.apv_publisher.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer.send_and_wait = AsyncMock(return_value=None)
            mock_producer_class.return_value = mock_producer
            
            await publisher.start()
            
            # Publish
            success = await publisher.publish_apv(apv)
            
            assert success is True
            assert publisher._published_count == 1
            assert publisher._failed_count == 0
            
            # Check that send_and_wait was called
            assert mock_producer.send_and_wait.called
            call_args = mock_producer.send_and_wait.call_args
            
            # Verify topic
            assert call_args.kwargs['topic'] == publisher.apv_topic
            
            # Verify key is CVE ID
            assert call_args.kwargs['key'] == "CVE-2024-12345"
            
            # Verify message has metadata
            message = call_args.kwargs['value']
            assert '_published_at' in message
            assert '_publisher' in message
            
            await publisher.stop()
    
    @pytest.mark.asyncio
    async def test_publish_apv_failure_to_dlq(self):
        """Test APV publishing failure with DLQ."""
        apv = APV(
            cve_id="CVE-2024-FAIL",
            published=datetime.utcnow(),
            modified=datetime.utcnow(),
            summary="Test vulnerability",
            details="Test details with sufficient length for validation",
            affected_packages=[
                AffectedPackage(
                    ecosystem="PyPI",
                    name="test-package",
                    affected_versions=["*"]
                )
            ],
            source_feed="test"
        )
        
        publisher = APVPublisher()
        
        with patch('kafka_integration.apv_publisher.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            
            # First call fails (main topic)
            # Second call succeeds (DLQ)
            mock_producer.send_and_wait = AsyncMock(
                side_effect=[
                    Exception("Kafka error"),  # Main topic fails
                    None  # DLQ succeeds
                ]
            )
            mock_producer_class.return_value = mock_producer
            
            await publisher.start()
            
            # Publish (should fail and go to DLQ)
            success = await publisher.publish_apv(apv)
            
            assert success is False
            assert publisher._published_count == 0
            assert publisher._failed_count == 1
            
            # Should have called send_and_wait twice (main + DLQ)
            assert mock_producer.send_and_wait.call_count == 2
            
            # Check DLQ call
            dlq_call = mock_producer.send_and_wait.call_args_list[1]
            assert dlq_call.kwargs['topic'] == publisher.dlq_topic
            
            dlq_message = dlq_call.kwargs['value']
            assert 'error' in dlq_message
            assert 'failed_at' in dlq_message
            assert 'original_message' in dlq_message
            
            await publisher.stop()
    
    @pytest.mark.asyncio
    async def test_publish_batch(self):
        """Test batch publishing."""
        apvs = [
            APV(
                cve_id=f"CVE-2024-0000{i}",
                published=datetime.utcnow(),
                modified=datetime.utcnow(),
                summary=f"Test vulnerability {i}",
                details="Test details with sufficient length for validation",
                affected_packages=[
                    AffectedPackage(
                        ecosystem="PyPI",
                        name="test-package",
                        affected_versions=["*"]
                    )
                ],
                source_feed="test"
            )
            for i in range(5)
        ]
        
        publisher = APVPublisher()
        
        with patch('kafka_integration.apv_publisher.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer.send_and_wait = AsyncMock(return_value=None)
            mock_producer_class.return_value = mock_producer
            
            await publisher.start()
            
            # Publish batch
            results = await publisher.publish_batch(apvs)
            
            assert results['total'] == 5
            assert results['success'] == 5
            assert results['failed'] == 0
            
            # Should have called send_and_wait 5 times
            assert mock_producer.send_and_wait.call_count == 5
            
            await publisher.stop()
    
    @pytest.mark.asyncio
    async def test_publish_batch_partial_failure(self):
        """Test batch publishing with some failures."""
        apvs = [
            APV(
                cve_id=f"CVE-2024-0000{i}",
                published=datetime.utcnow(),
                modified=datetime.utcnow(),
                summary=f"Test vulnerability {i}",
                details="Test details with sufficient length for validation",
                affected_packages=[
                    AffectedPackage(
                        ecosystem="PyPI",
                        name="test-package",
                        affected_versions=["*"]
                    )
                ],
                source_feed="test"
            )
            for i in range(3)
        ]
        
        publisher = APVPublisher()
        
        with patch('kafka_integration.apv_publisher.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            
            # First succeeds, second fails (+ DLQ), third succeeds
            mock_producer.send_and_wait = AsyncMock(
                side_effect=[
                    None,  # APV 1 success
                    Exception("Kafka error"),  # APV 2 fails
                    None,  # APV 2 DLQ
                    None   # APV 3 success
                ]
            )
            mock_producer_class.return_value = mock_producer
            
            await publisher.start()
            
            results = await publisher.publish_batch(apvs)
            
            assert results['total'] == 3
            assert results['success'] == 2
            assert results['failed'] == 1
            
            await publisher.stop()
    
    def test_get_stats(self):
        """Test getting publisher statistics."""
        publisher = APVPublisher()
        
        # Simulate some publishes
        publisher._published_count = 42
        publisher._failed_count = 3
        
        stats = publisher.get_stats()
        
        assert stats['published'] == 42
        assert stats['failed'] == 3
        assert stats['total'] == 45
    
    @pytest.mark.asyncio
    async def test_publish_without_start_raises_error(self):
        """Test that publishing without starting raises error."""
        publisher = APVPublisher()
        
        apv = APV(
            cve_id="CVE-2024-12345",
            published=datetime.utcnow(),
            modified=datetime.utcnow(),
            summary="Test vulnerability",
            details="Test details with sufficient length for validation",
            affected_packages=[
                AffectedPackage(
                    ecosystem="PyPI",
                    name="test-package",
                    affected_versions=["*"]
                )
            ],
            source_feed="test"
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            await publisher.publish_apv(apv)
        
        assert "not started" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_custom_key(self):
        """Test publishing with custom message key."""
        apv = APV(
            cve_id="CVE-2024-12345",
            published=datetime.utcnow(),
            modified=datetime.utcnow(),
            summary="Test vulnerability",
            details="Test details with sufficient length for validation",
            affected_packages=[
                AffectedPackage(
                    ecosystem="PyPI",
                    name="test-package",
                    affected_versions=["*"]
                )
            ],
            source_feed="test"
        )
        
        publisher = APVPublisher()
        
        with patch('kafka_integration.apv_publisher.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer.send_and_wait = AsyncMock(return_value=None)
            mock_producer_class.return_value = mock_producer
            
            await publisher.start()
            
            # Publish with custom key
            await publisher.publish_apv(apv, key="custom-key-123")
            
            call_args = mock_producer.send_and_wait.call_args
            assert call_args.kwargs['key'] == "custom-key-123"
            
            await publisher.stop()


# Run tests with:
# pytest tests/unit/test_kafka_publisher.py -v
# pytest tests/unit/test_kafka_publisher.py -v --cov=kafka_integration

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
