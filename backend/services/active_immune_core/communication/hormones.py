"""Hormone Communication via Redis Pub/Sub - PRODUCTION-READY

Global broadcast communication using Redis Pub/Sub.

Hormones are systemic chemical messengers in the endocrine system. In our digital
implementation, they're Redis Pub/Sub messages with:
- Global scope (broadcast to all agents)
- Higher latency (100-500ms) than cytokines
- Lower throughput (100s messages/sec)
- Fire-and-forget (no delivery guarantees)
- Used for: stress signals, global state changes, system-wide alerts

NO MOCKS, NO PLACEHOLDERS, NO TODOs.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

import redis.asyncio as aioredis
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ==================== MODELS ====================


class HormoneType:
    """Hormone types (systemic signaling)"""

    # Stress hormones
    CORTISOL = "cortisol"  # Stress response (suppress immunity)
    ADRENALINE = "adrenalina"  # Fight-or-flight (increase activity)

    # Regulatory hormones
    MELATONIN = "melatonina"  # Circadian rhythm (sleep cycle)
    INSULIN = "insulina"  # Resource availability
    GROWTH_HORMONE = "gh"  # Cloning trigger

    @classmethod
    def all(cls) -> List[str]:
        """Get all hormone types"""
        return [
            cls.CORTISOL,
            cls.ADRENALINE,
            cls.MELATONIN,
            cls.INSULIN,
            cls.GROWTH_HORMONE,
        ]


class HormoneMessage(BaseModel):
    """Hormone message model"""

    tipo: str = Field(description="Hormone type (cortisol, adrenalina, etc.)")
    emissor: str = Field(description="Source (lymphnode_id or 'global')")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp",
    )
    nivel: float = Field(ge=0.0, le=10.0, description="Hormone level (0-10)")
    payload: Dict[str, Any] = Field(description="Message payload")
    duracao_estimada_segundos: int = Field(
        default=300, ge=10, description="Estimated effect duration"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "cortisol",
                "emissor": "lymphnode_global",
                "timestamp": "2025-01-06T10:30:00",
                "nivel": 8.5,
                "payload": {
                    "evento": "sistema_sob_estresse",
                    "razao": "inflamacao_prolongada",
                    "temperatura_global": 39.5,
                },
                "duracao_estimada_segundos": 600,
            }
        }


# ==================== HORMONE MESSENGER ====================


class HormoneMessenger:
    """
    Redis Pub/Sub-based hormone messaging for global coordination.

    Features:
    - Async publisher/subscriber
    - Global broadcast (all agents receive)
    - Fire-and-forget (no delivery guarantees)
    - Multiple subscribers per hormone type
    - Graceful shutdown
    - Error handling
    - Connection pooling
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "hormonio",
        max_connections: int = 50,
    ):
        """
        Initialize Hormone Messenger.

        Args:
            redis_url: Redis connection URL
            channel_prefix: Channel prefix for hormones
            max_connections: Max connections in pool
        """
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.max_connections = max_connections

        self._redis_client: Optional[aioredis.Redis] = None
        self._pubsub_clients: Dict[str, aioredis.client.PubSub] = {}
        self._subscription_tasks: Set[asyncio.Task] = set()
        self._running = False
        self._degraded_mode = False  # Track if running without Redis

        logger.info(
            f"HormoneMessenger initialized (redis={redis_url}, "
            f"prefix={channel_prefix})"
        )

    # ==================== LIFECYCLE ====================

    async def start(self) -> None:
        """Start Redis connection - GRACEFUL DEGRADATION"""
        if self._redis_client:
            logger.warning("Redis client already started")
            return

        try:
            self._redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.max_connections,
            )

            # Test connection
            await self._redis_client.ping()

            self._running = True
            self._degraded_mode = False

            logger.info("HormoneMessenger Redis client started successfully")

        except Exception as e:
            logger.warning(
                f"Failed to start Redis client: {e}. Running in DEGRADED MODE "
                "(hormones will be logged but not transmitted)"
            )
            self._degraded_mode = True
            self._running = True  # Still mark as running (degraded mode)

    async def stop(self) -> None:
        """Stop all Redis connections gracefully"""
        logger.info("Stopping HormoneMessenger...")
        self._running = False

        # Stop all subscription tasks
        for task in self._subscription_tasks:
            task.cancel()

        if self._subscription_tasks:
            await asyncio.gather(*self._subscription_tasks, return_exceptions=True)
            self._subscription_tasks.clear()

        # Unsubscribe all pubsub clients
        for subscriber_id, pubsub in self._pubsub_clients.items():
            logger.info(f"Unsubscribing: {subscriber_id}")
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub {subscriber_id}: {e}")

        self._pubsub_clients.clear()

        # Close main client
        if self._redis_client:
            try:
                await self._redis_client.close()
                logger.info("Redis client closed successfully")
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")
            finally:
                self._redis_client = None

        logger.info("HormoneMessenger stopped")

    # ==================== PUBLISHER ====================

    async def publish_hormone(
        self,
        tipo: str,
        nivel: float,
        payload: Dict[str, Any],
        emissor: str = "global",
        duracao_estimada_segundos: int = 300,
    ) -> int:
        """
        Publish hormone message - GRACEFUL DEGRADATION.

        Args:
            tipo: Hormone type (cortisol, adrenalina, etc.)
            nivel: Hormone level (0-10)
            payload: Message payload
            emissor: Source (lymphnode_id or 'global')
            duracao_estimada_segundos: Effect duration

        Returns:
            Number of subscribers that received the message
        """
        # Degraded mode: log but don't publish
        if self._degraded_mode:
            logger.debug(
                f"[DEGRADED MODE] Hormone {tipo} from {emissor} (nivel={nivel})"
            )
            return 0

        if not self._redis_client:
            logger.error("Redis client not started")
            return 0

        # Create message
        message = HormoneMessage(
            tipo=tipo,
            emissor=emissor,
            timestamp=datetime.now().isoformat(),
            nivel=nivel,
            payload=payload,
            duracao_estimada_segundos=duracao_estimada_segundos,
        )

        channel = f"{self.channel_prefix}:{tipo}"

        try:
            # Publish to Redis Pub/Sub
            num_subscribers = await self._redis_client.publish(
                channel, json.dumps(message.model_dump())
            )

            logger.debug(
                f"Hormone {tipo} published by {emissor} "
                f"(nivel={nivel}, subscribers={num_subscribers})"
            )

            # Update metrics (if available)
            try:
                from main import cytokines_sent_total  # Reuse metric

                cytokines_sent_total.labels(type=f"hormone_{tipo}", priority=0).inc()
            except ImportError:
                pass

            return num_subscribers

        except Exception as e:
            logger.error(f"Failed to publish hormone {tipo}: {e}", exc_info=True)
            return 0

    # ==================== SUBSCRIBER ====================

    async def subscribe(
        self,
        hormone_types: List[str],
        callback: Callable[[HormoneMessage], None],
        subscriber_id: str,
    ) -> None:
        """
        Subscribe to hormone types - GRACEFUL DEGRADATION.

        Args:
            hormone_types: List of hormone types to subscribe to
            callback: Async callback function for each message
            subscriber_id: Unique subscriber ID
        """
        if subscriber_id in self._pubsub_clients:
            logger.warning(f"Subscriber {subscriber_id} already exists")
            return

        # Degraded mode: skip subscription
        if self._degraded_mode:
            logger.debug(
                f"[DEGRADED MODE] Would subscribe {subscriber_id} to {hormone_types}"
            )
            return

        if not self._redis_client:
            raise RuntimeError("Redis client not started")

        channels = [f"{self.channel_prefix}:{t}" for t in hormone_types]

        try:
            # Create PubSub client
            pubsub = self._redis_client.pubsub()

            # Subscribe to channels
            await pubsub.subscribe(*channels)

            self._pubsub_clients[subscriber_id] = pubsub

            logger.info(f"Subscribed to {channels} with subscriber {subscriber_id}")

            # Start subscription task
            task = asyncio.create_task(
                self._subscription_loop(pubsub, subscriber_id, callback)
            )
            self._subscription_tasks.add(task)
            task.add_done_callback(self._subscription_tasks.discard)

        except Exception as e:
            logger.warning(
                f"Failed to subscribe {subscriber_id}: {e}. "
                "Running in DEGRADED MODE"
            )
            self._degraded_mode = True

    async def _subscription_loop(
        self,
        pubsub: aioredis.client.PubSub,
        subscriber_id: str,
        callback: Callable[[HormoneMessage], None],
    ) -> None:
        """Subscription loop - process messages"""
        logger.info(f"Starting subscription loop for {subscriber_id}")

        try:
            async for message in pubsub.listen():
                if not self._running:
                    break

                # Skip control messages
                if message["type"] not in ["message", "pmessage"]:
                    continue

                try:
                    # Parse message
                    data = json.loads(message["data"])
                    hormone = HormoneMessage(**data)

                    logger.debug(
                        f"Hormone {hormone.tipo} received by {subscriber_id} "
                        f"(nivel={hormone.nivel})"
                    )

                    # Update metrics
                    try:
                        from main import cytokines_received_total  # Reuse metric

                        cytokines_received_total.labels(
                            type=f"hormone_{hormone.tipo}"
                        ).inc()
                    except ImportError:
                        pass

                    # Invoke callback
                    if asyncio.iscoroutinefunction(callback):
                        await callback(hormone)
                    else:
                        callback(hormone)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in hormone message: {e}")

                except Exception as e:
                    logger.error(
                        f"Error processing hormone in {subscriber_id}: {e}",
                        exc_info=True,
                    )

        except asyncio.CancelledError:
            logger.info(f"Subscription loop cancelled for {subscriber_id}")
            raise

        except Exception as e:
            logger.error(
                f"Fatal error in subscription loop {subscriber_id}: {e}", exc_info=True
            )

        finally:
            logger.info(f"Subscription loop ended for {subscriber_id}")

    async def unsubscribe(self, subscriber_id: str) -> None:
        """
        Unsubscribe subscriber.

        Args:
            subscriber_id: Subscriber ID to unsubscribe
        """
        if subscriber_id not in self._pubsub_clients:
            logger.warning(f"Subscriber {subscriber_id} not found")
            return

        pubsub = self._pubsub_clients[subscriber_id]

        try:
            await pubsub.unsubscribe()
            await pubsub.close()
            del self._pubsub_clients[subscriber_id]
            logger.info(f"Subscriber {subscriber_id} unsubscribed")

        except Exception as e:
            logger.error(f"Error unsubscribing {subscriber_id}: {e}")

    # ==================== STATE MANAGEMENT ====================

    async def set_agent_state(
        self, agent_id: str, state: Dict[str, Any], ttl: int = 60
    ) -> bool:
        """
        Store agent state in Redis (ephemeral).

        Args:
            agent_id: Agent ID
            state: Agent state dictionary
            ttl: Time-to-live in seconds

        Returns:
            True if stored successfully
        """
        if not self._redis_client:
            logger.error("Redis client not started")
            return False

        key = f"agent:{agent_id}:state"

        try:
            await self._redis_client.setex(key, ttl, json.dumps(state))
            return True

        except Exception as e:
            logger.error(f"Failed to set agent state for {agent_id}: {e}")
            return False

    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent state from Redis.

        Args:
            agent_id: Agent ID

        Returns:
            Agent state dictionary or None if not found
        """
        if not self._redis_client:
            logger.error("Redis client not started")
            return None

        key = f"agent:{agent_id}:state"

        try:
            state_json = await self._redis_client.get(key)

            if state_json:
                return json.loads(state_json)
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to get agent state for {agent_id}: {e}")
            return None

    async def delete_agent_state(self, agent_id: str) -> bool:
        """
        Delete agent state from Redis.

        Args:
            agent_id: Agent ID

        Returns:
            True if deleted successfully
        """
        if not self._redis_client:
            logger.error("Redis client not started")
            return False

        key = f"agent:{agent_id}:state"

        try:
            await self._redis_client.delete(key)
            return True

        except Exception as e:
            logger.error(f"Failed to delete agent state for {agent_id}: {e}")
            return False

    async def get_all_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all agent states from Redis.

        Returns:
            Dictionary mapping agent_id -> state
        """
        if not self._redis_client:
            logger.error("Redis client not started")
            return {}

        try:
            # Scan for all agent state keys
            keys = []
            async for key in self._redis_client.scan_iter(match="agent:*:state"):
                keys.append(key)

            # Get all states
            states = {}
            for key in keys:
                agent_id = key.split(":")[1]
                state_json = await self._redis_client.get(key)
                if state_json:
                    states[agent_id] = json.loads(state_json)

            return states

        except Exception as e:
            logger.error(f"Failed to get all agent states: {e}")
            return {}

    # ==================== UTILITY ====================

    def is_running(self) -> bool:
        """Check if messenger is running"""
        return self._running and self._redis_client is not None

    def get_active_subscribers(self) -> List[str]:
        """Get list of active subscriber IDs"""
        return list(self._pubsub_clients.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get messenger statistics"""
        return {
            "running": self._running,
            "client_active": self._redis_client is not None,
            "subscribers_active": len(self._pubsub_clients),
            "subscriber_ids": list(self._pubsub_clients.keys()),
            "subscription_tasks": len(self._subscription_tasks),
        }
