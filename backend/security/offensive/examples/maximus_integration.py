"""
Integration Example - MAXIMUS-Enhanced Reconnaissance.

Demonstrates how to use offensive tools with MAXIMUS integration
for ethical, consciousness-aware security operations.
"""
import asyncio
from backend.security.offensive.core import (
    registry,
    get_tool,
    MAXIMUSToolContext,
    OperationMode,
    EthicalContext
)


async def defensive_scan_example():
    """Example: Defensive network scan."""
    print("=" * 60)
    print("DEFENSIVE SCAN EXAMPLE")
    print("=" * 60)
    
    scanner = get_tool("network_scanner", with_maximus=True)
    
    context = MAXIMUSToolContext(
        operation_mode=OperationMode.DEFENSIVE,
        ethical_context=EthicalContext(
            operation_type="defensive",
            risk_level="low"
        ),
        human_oversight_required=False
    )
    
    print("\nExecuting scan on localhost...")
    result = await scanner.execute_with_maximus(
        context,
        target="127.0.0.1",
        ports=[22, 80, 443, 8080]
    )
    
    print(f"\nScan completed: {result.message}")
    print(f"Ethical score: {result.ethical_score:.2f}")
    print(f"Threat indicators: {len(result.threat_indicators)}")
    
    return result


async def registry_exploration():
    """Example: Registry exploration."""
    print("\n" + "=" * 60)
    print("REGISTRY EXPLORATION")
    print("=" * 60)
    
    stats = registry.get_stats()
    print("\nRegistry Statistics:")
    print(f"  Total tools: {stats['total_tools']}")
    
    print("\nAvailable Tools:")
    for tool_info in registry.list_tools():
        print(f"\n  {tool_info.name}")
        print(f"    Category: {tool_info.category.value}")
        print(f"    Risk: {tool_info.risk_level}")


async def main():
    """Run examples."""
    print("MAXIMUS OFFENSIVE TOOLS - INTEGRATION EXAMPLES\n")
    
    await registry_exploration()
    await defensive_scan_example()
    
    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
