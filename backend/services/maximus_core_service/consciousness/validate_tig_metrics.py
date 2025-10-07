"""
Quick validation script for TIG metrics
No pytest overhead - just direct fabric initialization and metrics check
"""
import asyncio
import sys
from tig.fabric import TIGFabric, TopologyConfig

async def validate_tig_metrics():
    print("=" * 60)
    print("TIG METRICS VALIDATION - PAGANI 100%")
    print("=" * 60)
    print()

    # Initialize fabric with default config
    config = TopologyConfig(node_count=16, min_degree=6)
    fabric = TIGFabric(config)

    print("Initializing TIG Fabric...")
    await fabric.initialize()

    # Get metrics
    metrics = fabric.get_metrics()

    print()
    print("📊 METRICS RESULTS:")
    print("-" * 60)
    print(f"Clustering Coefficient: {metrics.avg_clustering_coefficient:.3f} (target: ≥0.70)")
    print(f"ECI (Φ Proxy):          {metrics.effective_connectivity_index:.3f} (target: ≥0.85)")
    print(f"Avg Path Length:        {metrics.avg_path_length:.2f} (target: ≤7)")
    print(f"Algebraic Connectivity: {metrics.algebraic_connectivity:.3f} (target: ≥0.30)")
    print(f"Bottlenecks:            {'YES ❌' if metrics.has_feed_forward_bottlenecks else 'NO ✅'}")
    print(f"Graph Density:          {metrics.density:.3f}")
    print()

    # Validate IIT compliance
    is_compliant, violations = metrics.validate_iit_compliance()

    print("🎯 IIT COMPLIANCE:")
    print("-" * 60)
    if is_compliant:
        print("✅ ALL CHECKS PASSED - IIT COMPLIANT")
        print()
        print("🏎️ PAGANI TARGET ACHIEVED!")
        return 0
    else:
        print("❌ IIT VIOLATIONS DETECTED:")
        for v in violations:
            print(f"   - {v}")
        print()
        print(f"Clustering: {'✅' if metrics.avg_clustering_coefficient >= 0.70 else '❌'}")
        print(f"ECI:        {'✅' if metrics.effective_connectivity_index >= 0.85 else '❌'}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(validate_tig_metrics())
    sys.exit(exit_code)
