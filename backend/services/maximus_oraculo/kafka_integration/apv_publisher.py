"""Kafka integration for APV publishing.

This module handles publishing APVs to Kafka topics with proper
serialization, error handling, and delivery guarantees.

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: Doutrina MAXIMUS | Type Hints 100% | Production-Ready
"""

from typing import List, Optional, Dict, Any
import asyncio
import logging
import json
from datetime import datetime

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)


class APVPublisher:
    """
    Publishes APVs to Kafka topics.
    
    Features:
    - Async Kafka producer (aiokafka)
    - JSON serialization
    - Delivery guarantees (at-least-once)
    - Error handling with DLQ
    - Metrics collection
    
    Theoretical Foundation:
    - Event Streaming: Kafka as event bus
    - At-Least-Once Delivery: acks=all
    - Dead Letter Queue: For failed messages
    
    Usage:
        >>> async with APVPublisher(bootstrap_servers="localhost:9096") as publisher:
        ...     await publisher.publish_apv(apv)
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9096",
        apv_topic: str = "maximus.adaptive-immunity.apv",
        dlq_topic: str = "maximus.adaptive-immunity.dlq"
    ):
        """
        Initialize APV publisher.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            apv_topic: Topic for APVs
            dlq_topic: Dead letter queue topic
        """
        self.bootstrap_servers = bootstrap_servers
        self.apv_topic = apv_topic
        self.dlq_topic = dlq_topic
        
        self._producer: Optional[AIOKafkaProducer] = None
        self._published_count = 0
        self._failed_count = 0
        
        logger.info(
            f"Initialized APVPublisher: "
            f"servers={bootstrap_servers}, topic={apv_topic}"
        )
    
    async def __aenter__(self) -> 'APVPublisher':
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()
    
    async def start(self) -> None:
        """Start Kafka producer."""
        if self._producer is not None:
            logger.warning("Producer already started")
            return
        
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                compression_type='gzip',
                max_request_size=1048576,  # 1MB
                request_timeout_ms=30000,
            )
            
            await self._producer.start()
            logger.info("Kafka producer started")
            
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop Kafka producer."""
        if self._producer is not None:
            try:
                await self._producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
            finally:
                self._producer = None
    
    async def publish_apv(
        self,
        apv: Any,  # APV model instance
        key: Optional[str] = None
    ) -> bool:
        """
        Publish a single APV to Kafka.
        
        Args:
            apv: APV model instance
            key: Optional message key (defaults to CVE ID)
            
        Returns:
            True if published successfully, False otherwise
        """
        if self._producer is None:
            raise RuntimeError("Producer not started. Use 'async with' or call start()")
        
        # Use CVE ID as key if not provided
        if key is None:
            key = apv.cve_id
        
        try:
            # Serialize APV to Kafka message format
            message = apv.to_kafka_message()
            
            # Add metadata
            message["_published_at"] = datetime.utcnow().isoformat()
            message["_publisher"] = "maximus_oraculo"
            
            # Send to Kafka
            await self._producer.send_and_wait(
                topic=self.apv_topic,
                value=message,
                key=key
            )
            
            self._published_count += 1
            logger.info(f"Published APV: {apv.cve_id} to {self.apv_topic}")
            
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing APV {apv.cve_id}: {e}")
            await self._send_to_dlq(apv, str(e))
            self._failed_count += 1
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error publishing APV {apv.cve_id}: {e}")
            await self._send_to_dlq(apv, str(e))
            self._failed_count += 1
            return False
    
    async def publish_batch(
        self,
        apvs: List[Any]
    ) -> Dict[str, int]:
        """
        Publish multiple APVs in batch.
        
        Args:
            apvs: List of APV model instances
            
        Returns:
            Dict with success and failure counts
        """
        results = {
            "success": 0,
            "failed": 0,
            "total": len(apvs)
        }
        
        logger.info(f"Publishing batch of {len(apvs)} APVs")
        
        for apv in apvs:
            success = await self.publish_apv(apv)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(
            f"Batch publish complete: "
            f"{results['success']} success, {results['failed']} failed"
        )
        
        return results
    
    async def _send_to_dlq(self, apv: Any, error_msg: str) -> None:
        """
        Send failed message to dead letter queue.
        
        Args:
            apv: APV that failed to publish
            error_msg: Error message
        """
        if self._producer is None:
            logger.error("Cannot send to DLQ: producer not started")
            return
        
        try:
            dlq_message = {
                "original_message": apv.to_kafka_message(),
                "error": error_msg,
                "failed_at": datetime.utcnow().isoformat(),
                "topic": self.apv_topic,
                "cve_id": apv.cve_id
            }
            
            await self._producer.send_and_wait(
                topic=self.dlq_topic,
                value=dlq_message,
                key=apv.cve_id
            )
            
            logger.info(f"Sent APV {apv.cve_id} to DLQ: {error_msg}")
            
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get publisher statistics.
        
        Returns:
            Dict with published and failed counts
        """
        return {
            "published": self._published_count,
            "failed": self._failed_count,
            "total": self._published_count + self._failed_count
        }
