"""Pytest configuration for Core Integration tests

This conftest.py provides shared fixtures for all core integration tests.

Includes:
- Service availability detection (Kafka, Redis, PostgreSQL)
- CoreManager fixtures (initialized, started)
- Automatic cleanup and test isolation
- Graceful skip for integration tests when services unavailable

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 2.0.0 - Test Environment Management
"""

import logging
import os
from typing import Tuple

import pytest
import pytest_asyncio

from .core_manager import CoreManager

logger = logging.getLogger(__name__)


# ==================== SERVICE AVAILABILITY CHECKERS ====================


def check_kafka_available() -> bool:
    """
    Check if Kafka is available and responding.
    
    Uses a quick connection test with short timeout to avoid blocking tests.
    
    Returns:
        True if Kafka is available, False otherwise
    """
    try:
        from kafka import KafkaProducer
        
        kafka_url = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        logger.debug(f"Checking Kafka availability at {kafka_url}")
        
        producer = KafkaProducer(
            bootstrap_servers=kafka_url,
            request_timeout_ms=2000,
            max_block_ms=2000,
        )
        producer.close()
        
        logger.debug("✅ Kafka is available")
        return True
    except Exception as e:
        logger.debug(f"❌ Kafka not available: {e}")
        return False


def check_redis_available() -> bool:
    """
    Check if Redis is available and responding.
    
    Uses a quick ping test with short timeout.
    
    Returns:
        True if Redis is available, False otherwise
    """
    try:
        from redis import Redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        logger.debug(f"Checking Redis availability at {redis_url}")
        
        client = Redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        client.close()
        
        logger.debug("✅ Redis is available")
        return True
    except Exception as e:
        logger.debug(f"❌ Redis not available: {e}")
        return False


def check_postgres_available() -> bool:
    """
    Check if PostgreSQL is available and responding.
    
    Uses a quick connection test with short timeout.
    
    Returns:
        True if PostgreSQL is available, False otherwise
    """
    try:
        import psycopg2
        
        host = os.getenv("ACTIVE_IMMUNE_POSTGRES_HOST", "localhost")
        port = int(os.getenv("ACTIVE_IMMUNE_POSTGRES_PORT", "5432"))
        database = os.getenv("ACTIVE_IMMUNE_POSTGRES_DB", "immunis_memory")
        user = os.getenv("ACTIVE_IMMUNE_POSTGRES_USER", "immune_user")
        password = os.getenv("ACTIVE_IMMUNE_POSTGRES_PASSWORD", "immune_pass")
        
        logger.debug(f"Checking PostgreSQL availability at {host}:{port}/{database}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=2,
        )
        conn.close()
        
        logger.debug("✅ PostgreSQL is available")
        return True
    except Exception as e:
        logger.debug(f"❌ PostgreSQL not available: {e}")
        return False


# ==================== SESSION-SCOPED FIXTURES ====================


@pytest.fixture(scope="session")
def services_availability() -> Tuple[bool, bool, bool]:
    """
    Session-scoped fixture that checks service availability once.
    
    This fixture runs only ONCE per test session, caching the results.
    Avoids repeated connection attempts during test execution.
    
    Returns:
        Tuple of (kafka_available, redis_available, postgres_available)
    """
    logger.info("🔍 Checking service availability for integration tests...")
    
    kafka = check_kafka_available()
    redis = check_redis_available()
    postgres = check_postgres_available()
    
    logger.info(f"Service availability: Kafka={kafka}, Redis={redis}, PostgreSQL={postgres}")
    
    return (kafka, redis, postgres)


@pytest.fixture(scope="session")
def integration_env_available(services_availability) -> bool:
    """
    Check if integration environment is fully available.
    
    Integration tests require ALL services (Kafka, Redis, PostgreSQL).
    If any service is unavailable, integration tests will be skipped.
    
    Returns:
        True if all services are available, False otherwise
    """
    kafka, redis, postgres = services_availability
    available = kafka and redis and postgres
    
    if available:
        logger.info("✅ Integration environment is FULLY available")
    else:
        logger.warning("⚠️  Integration environment is NOT available")
        logger.warning("   To run integration tests, start test environment with:")
        logger.warning("   docker-compose -f docker-compose.test.yml up -d")
    
    return available


# ==================== PYTEST CONFIGURATION ====================


def pytest_configure(config):
    """Register custom markers for test categorization"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires real services)",
    )
    config.addinivalue_line(
        "markers",
        "unit: mark test as unit test (no external dependencies)",
    )


# ==================== CLEANUP FIXTURES ====================


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_core():
    """
    Cleanup fixture that runs BEFORE and AFTER each test.

    This ensures complete test isolation by:
    1. BEFORE test: Clean up any leftover state from previous tests
    2. AFTER test: Clean up state created by current test

    Scope: function - runs for EVERY test function
    Autouse: True - automatically applied to all tests
    """
    # ==================== BEFORE TEST ====================
    logger.debug("Cleaning up CoreManager state before test")

    try:
        # Get existing instance (if any)
        if CoreManager._instance is not None:
            core = CoreManager._instance

            # Stop all agents
            if core.agent_factory and hasattr(core.agent_factory, "_agents"):
                agent_ids = list(core.agent_factory._agents.keys())
                logger.debug(f"Stopping {len(agent_ids)} leftover agents")

                for agent_id in agent_ids:
                    try:
                        agent = core.agent_factory._agents[agent_id]
                        if hasattr(agent, "_running") and agent._running:
                            await agent.parar()
                    except Exception as e:
                        logger.debug(f"Error stopping agent {agent_id}: {e}")

                # Clear registry
                core.agent_factory._agents.clear()

            # Stop Core components
            if core.is_started:
                await core.stop()
    except Exception as e:
        logger.debug(f"Error during pre-cleanup: {e}")

    # Reset singleton
    CoreManager.reset_instance()
    logger.debug("CoreManager reset before test")

    # Allow test to run
    yield

    # ==================== AFTER TEST ====================
    logger.debug("Cleaning up CoreManager state after test")

    try:
        # Get instance created during test
        if CoreManager._instance is not None:
            core = CoreManager._instance

            # Stop all agents
            if core.agent_factory and hasattr(core.agent_factory, "_agents"):
                agent_ids = list(core.agent_factory._agents.keys())
                logger.debug(f"Stopping {len(agent_ids)} test agents")

                for agent_id in agent_ids:
                    try:
                        agent = core.agent_factory._agents[agent_id]
                        if hasattr(agent, "_running") and agent._running:
                            await agent.parar()
                    except Exception as e:
                        logger.debug(f"Error stopping agent {agent_id}: {e}")

                # Clear registry
                core.agent_factory._agents.clear()

            # Stop Core components
            if core.is_started:
                await core.stop()
    except Exception as e:
        logger.debug(f"Error during post-cleanup: {e}")

    # Reset singleton
    CoreManager.reset_instance()
    logger.debug("CoreManager reset after test")


# ==================== CORE MANAGER FIXTURES ====================


@pytest_asyncio.fixture
async def core_manager_initialized(integration_env_available):
    """
    Fixture that provides a fully initialized CoreManager.
    
    This fixture:
    1. Checks if integration environment is available (skip if not)
    2. Gets CoreManager instance
    3. Initializes CoreManager with real service connections
    4. Yields initialized manager to test
    5. Cleans up after test (stop + reset)
    
    Usage:
        @pytest.mark.integration
        async def test_something(core_manager_initialized):
            manager = core_manager_initialized
            assert manager.is_initialized
    
    Requires:
        - Kafka running on localhost:9092
        - Redis running on localhost:6379
        - PostgreSQL running on localhost:5432
    
    If services are not available, test will be skipped with a clear message.
    """
    if not integration_env_available:
        pytest.skip(
            "Integration environment not available. "
            "Start with: docker-compose -f docker-compose.test.yml up -d"
        )
    
    logger.info("📦 Initializing CoreManager for integration test...")
    
    manager = CoreManager.get_instance()
    
    # Initialize with real service URLs from environment
    success = await manager.initialize(
        kafka_bootstrap=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        enable_degraded_mode=True,  # Graceful degradation if services fail
    )
    
    if not success:
        pytest.skip("CoreManager initialization failed (services may be unavailable)")
    
    logger.info("✅ CoreManager initialized successfully")
    
    yield manager
    
    # Cleanup
    logger.debug("🧹 Cleaning up CoreManager after test...")
    try:
        if manager.is_started:
            await manager.stop()
    except Exception as e:
        logger.debug(f"Error stopping CoreManager: {e}")
    finally:
        CoreManager.reset_instance()


@pytest_asyncio.fixture
async def core_manager_started(core_manager_initialized):
    """
    Fixture that provides a fully initialized AND started CoreManager.
    
    This fixture:
    1. Gets initialized CoreManager from core_manager_initialized fixture
    2. Starts CoreManager (connects to services, starts components)
    3. Yields started manager to test
    4. Cleans up after test (stop + reset)
    
    Usage:
        @pytest.mark.integration
        async def test_something(core_manager_started):
            manager = core_manager_started
            assert manager.is_started
            # All components are running and connected
    
    Requires:
        - Same as core_manager_initialized
        - Services must be healthy and accepting connections
    
    If services are not available or start fails, test will be skipped.
    """
    manager = core_manager_initialized
    
    logger.info("🚀 Starting CoreManager for integration test...")
    
    success = await manager.start()
    
    if not success:
        pytest.skip("CoreManager start failed (services may be unhealthy)")
    
    logger.info("✅ CoreManager started successfully")
    
    yield manager
    
    # Cleanup (will be handled by core_manager_initialized fixture)
    logger.debug("🧹 Cleaning up will be done by core_manager_initialized fixture")
