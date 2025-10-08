"""Debug script to test AgentService"""

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)

# Add current directory to path
sys.path.insert(0, ".")

from api.core_integration.agent_service import AgentService
from api.core_integration.core_manager import CoreManager


async def test_create_agent():
    """Test creating agent"""
    print("=" * 60)
    print("TEST: Creating Macrofago agent")
    print("=" * 60)

    try:
        # Reset Core
        CoreManager.reset_instance()

        # Get Core
        core = CoreManager.get_instance()
        print("✓ CoreManager singleton obtained")

        # Initialize
        print("\n1. Initializing Core...")
        await core.initialize(
            kafka_bootstrap="localhost:9999",
            redis_url="redis://localhost:9999",
            enable_degraded_mode=True,
        )
        print("✓ Core initialized")

        # Start
        print("\n2. Starting Core...")
        await core.start()
        print("✓ Core started")

        # Create service
        print("\n3. Creating AgentService...")
        service = AgentService()
        print("✓ AgentService created")

        # Create agent
        print("\n4. Creating Macrofago agent...")
        response = await service.create_agent(agent_type="macrofago", config={"area_patrulha": "test_area"})
        print(f"✓ Agent created: {response.agent_id}")
        print(f"  Type: {response.agent_type}")
        print(f"  Status: {response.status}")
        print(f"  Energia: {response.energia}")

        # Cleanup
        print("\n5. Stopping Core...")
        await core.stop()
        print("✓ Core stopped")

        print("\n" + "=" * 60)
        print("✓ TEST PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_create_agent())
