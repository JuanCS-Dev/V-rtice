"""
Simplified Social Memory Tests - Debug
"""

import pytest
from compassion.social_memory_sqlite import (
    SocialMemorySQLite,
    SocialMemorySQLiteConfig,
    PatternNotFoundError,
)


@pytest.mark.asyncio
async def test_store_and_retrieve():
    """Simple test: store and retrieve pattern."""
    config = SocialMemorySQLiteConfig(db_path=":memory:", cache_size=100)
    memory = SocialMemorySQLite(config)
    await memory.initialize()

    # Store
    agent_id = "user_test"
    patterns = {"confusion_history": 0.5}
    await memory.store_pattern(agent_id, patterns)

    # Retrieve
    retrieved = await memory.retrieve_patterns(agent_id)

    assert retrieved == patterns

    await memory.close()


@pytest.mark.asyncio
async def test_pattern_not_found():
    """Test PatternNotFoundError for non-existent agent."""
    config = SocialMemorySQLiteConfig(db_path=":memory:")
    memory = SocialMemorySQLite(config)
    await memory.initialize()

    with pytest.raises(PatternNotFoundError):
        await memory.retrieve_patterns("nonexistent")

    await memory.close()
