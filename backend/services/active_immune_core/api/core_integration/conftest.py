"""Pytest configuration for Core Integration tests

This conftest.py provides shared fixtures for all core integration tests.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import logging
import pytest
import pytest_asyncio

from .core_manager import CoreManager

logger = logging.getLogger(__name__)


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
            if core.agent_factory and hasattr(core.agent_factory, '_agents'):
                agent_ids = list(core.agent_factory._agents.keys())
                logger.debug(f"Stopping {len(agent_ids)} leftover agents")

                for agent_id in agent_ids:
                    try:
                        agent = core.agent_factory._agents[agent_id]
                        if hasattr(agent, '_running') and agent._running:
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
            if core.agent_factory and hasattr(core.agent_factory, '_agents'):
                agent_ids = list(core.agent_factory._agents.keys())
                logger.debug(f"Stopping {len(agent_ids)} test agents")

                for agent_id in agent_ids:
                    try:
                        agent = core.agent_factory._agents[agent_id]
                        if hasattr(agent, '_running') and agent._running:
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
