"""Core Manager - PRODUCTION-READY

Singleton manager for Core System lifecycle and component access.

This module manages:
- AgentFactory initialization and lifecycle
- Lymphnode coordination hub
- HomeostaticController autonomic loop
- Graceful degradation when Core unavailable

Thread-safe singleton pattern ensures only one Core instance exists.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional

# Core imports (using absolute imports from package root)
from agents import AgentFactory
from coordination.homeostatic_controller import HomeostaticController
from coordination.lymphnode import LinfonodoDigital

logger = logging.getLogger(__name__)


class CoreManagerError(Exception):
    """Base exception for CoreManager errors"""

    pass


class CoreNotInitializedError(CoreManagerError):
    """Raised when Core operations attempted before initialization"""

    pass


class CoreManager:
    """
    Singleton manager for Active Immune Core System.

    Responsibilities:
    - Initialize Core components (AgentFactory, Lymphnode, Controller)
    - Manage Core lifecycle (start/stop)
    - Provide access to Core components
    - Handle graceful degradation
    - Track Core health status

    Thread-safe singleton pattern.

    Usage:
        # Get singleton instance
        core = CoreManager.get_instance()

        # Initialize (async)
        await core.initialize(
            kafka_bootstrap="localhost:9092",
            redis_url="redis://localhost:6379"
        )

        # Start Core
        await core.start()

        # Access components
        agent_factory = core.agent_factory
        lymphnode = core.lymphnode

        # Stop Core
        await core.stop()
    """

    _instance: Optional["CoreManager"] = None
    _lock: Lock = Lock()

    def __init__(self):
        """
        Private constructor (use get_instance() instead).

        Raises:
            RuntimeError: If instantiated directly instead of via get_instance()
        """
        # Prevent direct instantiation
        if CoreManager._instance is not None:
            raise RuntimeError("CoreManager is a singleton. Use CoreManager.get_instance()")

        # Core components (None until initialized)
        self._agent_factory: Optional[AgentFactory] = None
        self._lymphnode: Optional[LinfonodoDigital] = None
        self._homeostatic_controller: Optional[HomeostaticController] = None

        # Configuration
        self._config: Dict[str, Any] = {}

        # State tracking
        self._initialized: bool = False
        self._started: bool = False
        self._start_time: Optional[datetime] = None
        self._core_available: bool = False

        # Graceful degradation flag
        self._degraded_mode: bool = False

        logger.debug(f"CoreManager instance created (id={id(self)})")

    @classmethod
    def get_instance(cls) -> "CoreManager":
        """
        Get CoreManager singleton instance (thread-safe).

        Returns:
            CoreManager singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    logger.debug("Creating new CoreManager instance")
                    cls._instance = CoreManager()

        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton instance (for testing only).

        Warning:
            This should only be used in test teardown.
            Do not use in production code.
        """
        with cls._lock:
            if cls._instance is not None:
                logger.debug(
                    f"Resetting CoreManager singleton (initialized={cls._instance._initialized}, started={cls._instance._started})"
                )
                cls._instance = None

    async def initialize(
        self,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        rte_service_url: str = "http://localhost:8002",
        ethical_ai_url: str = "http://localhost:8100",
        lymphnode_id: str = "lymphnode_api_001",
        controller_id: str = "controller_api_001",
        enable_degraded_mode: bool = True,
    ) -> bool:
        """
        Initialize Core System components.

        Args:
            kafka_bootstrap: Kafka broker address
            redis_url: Redis connection URL
            rte_service_url: Reflex Triage Engine service URL
            ethical_ai_url: Ethical AI service URL
            lymphnode_id: Unique ID for Lymphnode
            controller_id: Unique ID for Homeostatic Controller
            enable_degraded_mode: Allow graceful degradation if Core fails

        Returns:
            True if successful, False if degraded mode enabled and Core failed

        Raises:
            CoreManagerError: If initialization fails and degraded mode disabled
        """
        if self._initialized:
            logger.warning("CoreManager already initialized")
            return True

        logger.info("Initializing CoreManager...")
        logger.info(f"  Kafka: {kafka_bootstrap}")
        logger.info(f"  Redis: {redis_url}")
        logger.info(f"  RTE Service: {rte_service_url}")
        logger.info(f"  Ethical AI: {ethical_ai_url}")

        # Store configuration
        self._config = {
            "kafka_bootstrap": kafka_bootstrap,
            "redis_url": redis_url,
            "rte_service_url": rte_service_url,
            "ethical_ai_url": ethical_ai_url,
            "lymphnode_id": lymphnode_id,
            "controller_id": controller_id,
            "enable_degraded_mode": enable_degraded_mode,
        }

        try:
            # Initialize AgentFactory
            logger.info("Initializing AgentFactory...")
            self._agent_factory = AgentFactory(
                kafka_bootstrap=kafka_bootstrap,
                redis_url=redis_url,
                rte_service_url=rte_service_url,
                ethical_ai_url=ethical_ai_url,
            )
            logger.info("✓ AgentFactory initialized")

            # Initialize Lymphnode
            logger.info("Initializing Lymphnode...")
            self._lymphnode = LinfonodoDigital(
                lymphnode_id=lymphnode_id,
                nivel="regional",
                area_responsabilidade="api_managed",
                kafka_bootstrap=kafka_bootstrap,
                redis_url=redis_url,
                agent_factory=self._agent_factory,
            )
            logger.info("✓ Lymphnode initialized")

            # Initialize Homeostatic Controller
            logger.info("Initializing HomeostaticController...")
            self._homeostatic_controller = HomeostaticController(
                controller_id=controller_id,
                lymphnode_url="http://localhost:8000",  # API's own URL
                metrics_url="http://localhost:9090",  # Prometheus
            )
            logger.info("✓ HomeostaticController initialized")

            self._initialized = True
            self._core_available = True
            self._degraded_mode = False

            logger.info("✓ CoreManager initialization complete")
            return True

        except Exception as e:
            logger.error(f"CoreManager initialization failed: {e}", exc_info=True)

            if enable_degraded_mode:
                logger.warning("Entering degraded mode (Core unavailable)")
                self._degraded_mode = True
                self._core_available = False
                self._initialized = True  # Mark as initialized but degraded
                return False
            else:
                raise CoreManagerError(f"Core initialization failed: {e}") from e

    async def start(self) -> bool:
        """
        Start Core System components.

        Starts background tasks for:
        - Lymphnode operations (cytokine aggregation, pattern detection)
        - Homeostatic Controller (MAPE-K loop)

        Returns:
            True if successful, False if in degraded mode

        Raises:
            CoreNotInitializedError: If not initialized
            CoreManagerError: If start fails and not in degraded mode
        """
        if not self._initialized:
            raise CoreNotInitializedError("CoreManager not initialized. Call initialize() first.")

        if self._started:
            logger.warning("CoreManager already started")
            return True

        if self._degraded_mode:
            logger.warning("Cannot start Core in degraded mode")
            return False

        logger.info("Starting CoreManager...")

        try:
            # Start Lymphnode
            if self._lymphnode:
                logger.info("Starting Lymphnode...")
                await self._lymphnode.iniciar()
                logger.info("✓ Lymphnode started")

            # Start Homeostatic Controller
            if self._homeostatic_controller:
                logger.info("Starting HomeostaticController...")
                await self._homeostatic_controller.iniciar()
                logger.info("✓ HomeostaticController started")

            self._started = True
            self._start_time = datetime.utcnow()

            logger.info("✓ CoreManager start complete")
            return True

        except Exception as e:
            logger.error(f"CoreManager start failed: {e}", exc_info=True)

            if self._config.get("enable_degraded_mode", True):
                logger.warning("Entering degraded mode (Core start failed)")
                self._degraded_mode = True
                self._core_available = False
                return False
            else:
                raise CoreManagerError(f"Core start failed: {e}") from e

    async def stop(self) -> None:
        """
        Stop Core System components gracefully.

        Stops:
        - Homeostatic Controller
        - Lymphnode
        - All active agents (via AgentFactory)
        """
        if not self._started:
            logger.warning("CoreManager not started, nothing to stop")
            return

        logger.info("Stopping CoreManager...")

        # Stop Homeostatic Controller
        if self._homeostatic_controller:
            try:
                logger.info("Stopping HomeostaticController...")
                await self._homeostatic_controller.parar()
                logger.info("✓ HomeostaticController stopped")
            except Exception as e:
                logger.error(f"Error stopping HomeostaticController: {e}", exc_info=True)

        # Stop Lymphnode
        if self._lymphnode:
            try:
                logger.info("Stopping Lymphnode...")
                await self._lymphnode.parar()
                logger.info("✓ Lymphnode stopped")
            except Exception as e:
                logger.error(f"Error stopping Lymphnode: {e}", exc_info=True)

        # Stop all agents (via AgentFactory)
        if self._agent_factory:
            try:
                logger.info("Stopping all agents...")
                await self._agent_factory.shutdown_all()
                logger.info("✓ All agents stopped")
            except Exception as e:
                logger.error(f"Error stopping agents: {e}", exc_info=True)

        self._started = False
        self._start_time = None

        logger.info("✓ CoreManager stop complete")

    # ==================== COMPONENT ACCESS ====================

    @property
    def agent_factory(self) -> Optional[AgentFactory]:
        """
        Get AgentFactory instance.

        Returns:
            AgentFactory instance or None if not initialized/degraded
        """
        return self._agent_factory

    @property
    def lymphnode(self) -> Optional[LinfonodoDigital]:
        """
        Get Lymphnode instance.

        Returns:
            Lymphnode instance or None if not initialized/degraded
        """
        return self._lymphnode

    @property
    def homeostatic_controller(self) -> Optional[HomeostaticController]:
        """
        Get HomeostaticController instance.

        Returns:
            HomeostaticController instance or None if not initialized/degraded
        """
        return self._homeostatic_controller

    # ==================== STATUS CHECKS ====================

    @property
    def is_initialized(self) -> bool:
        """Check if Core is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if Core is started."""
        return self._started

    @property
    def is_degraded(self) -> bool:
        """Check if Core is in degraded mode."""
        return self._degraded_mode

    @property
    def is_available(self) -> bool:
        """Check if Core is available (initialized, not degraded)."""
        return self._core_available and not self._degraded_mode

    @property
    def uptime_seconds(self) -> Optional[float]:
        """
        Get Core uptime in seconds.

        Returns:
            Uptime in seconds or None if not started
        """
        if not self._started or self._start_time is None:
            return None

        return (datetime.utcnow() - self._start_time).total_seconds()

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive Core status.

        Returns:
            Status dictionary with all relevant information
        """
        return {
            "initialized": self._initialized,
            "started": self._started,
            "degraded": self._degraded_mode,
            "available": self.is_available,
            "uptime_seconds": self.uptime_seconds,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "components": {
                "agent_factory": self._agent_factory is not None,
                "lymphnode": self._lymphnode is not None,
                "homeostatic_controller": self._homeostatic_controller is not None,
            },
            "config": {
                "kafka_bootstrap": self._config.get("kafka_bootstrap"),
                "redis_url": self._config.get("redis_url"),
                "degraded_mode_enabled": self._config.get("enable_degraded_mode", True),
            },
        }

    def __repr__(self) -> str:
        """String representation."""
        status = (
            "degraded"
            if self._degraded_mode
            else ("started" if self._started else "initialized" if self._initialized else "uninitialized")
        )
        return f"CoreManager(status={status}, available={self.is_available})"
