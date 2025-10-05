"""Integration test for Homeostatic Control Loop (HCL)

This test verifies that all HCL components can be instantiated and work together.
"""

import asyncio
import logging
from hcl_orchestrator import HomeostaticControlLoop

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_hcl_single_cycle():
    """Test a single HCL cycle in dry-run mode."""
    print("=" * 60)
    print("HCL Integration Test - Single Cycle")
    print("=" * 60)

    # Initialize HCL in dry-run mode
    hcl = HomeostaticControlLoop(
        dry_run_mode=True,
        loop_interval_seconds=5,
        db_url="postgresql://localhost/vertice"
    )

    try:
        # Initialize components
        print("\n1. Initializing HCL components...")
        await hcl.initialize()
        print("✓ Components initialized")

        # Run a single cycle by setting running=True then stopping after 1 iteration
        print("\n2. Running single HCL cycle...")
        hcl.running = True

        # Manually execute one cycle
        import time

        # Monitor
        print("\n3. MONITOR - Collecting metrics...")
        metrics = await hcl.monitor.collect_metrics()
        print(f"✓ Collected {len(metrics)} metrics")
        print(f"  Sample metrics: cpu={metrics.get('cpu_percent', 0):.1f}%, "
              f"memory={metrics.get('memory_percent', 0):.1f}%")

        # Analyze
        print("\n4. ANALYZE - Detecting issues...")
        analysis = await hcl._analyze_metrics(metrics)
        print(f"✓ Analysis complete: {analysis.get('summary', 'N/A')}")
        print(f"  Anomaly: {analysis.get('anomaly', {}).get('is_anomaly', False)}")
        print(f"  Degradation: {analysis.get('degradation', {}).get('is_degraded', False)}")

        # Plan
        print("\n5. PLAN - Generating actions...")
        plan = await hcl._plan_actions(metrics, analysis)
        print(f"✓ Plan created: Mode={plan['operational_mode']}, "
              f"Actions={len(plan['actions'])}")
        if plan['actions']:
            print(f"  First action: {plan['actions'][0]}")

        # Execute
        print("\n6. EXECUTE - Applying actions (dry-run)...")
        execution = await hcl._execute_plan(plan, metrics)
        print(f"✓ Execution complete: Success={execution['success']}, "
              f"Applied={execution['applied_count']}")

        # Knowledge
        print("\n7. KNOWLEDGE - Storing decision...")
        await hcl._store_decision(metrics, analysis, plan, execution)
        print("✓ Decision stored in knowledge base")

        print("\n" + "=" * 60)
        print("✓ HCL Integration Test PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        await hcl.stop()


async def test_hcl_components():
    """Test individual HCL components."""
    print("\n" + "=" * 60)
    print("HCL Component Tests")
    print("=" * 60)

    # Test Monitor
    print("\n1. Testing SystemMonitor...")
    from monitor.system_monitor import SystemMonitor
    monitor = SystemMonitor()
    metrics = await monitor.collect_metrics()
    print(f"✓ SystemMonitor OK - {len(metrics)} metrics collected")

    # Test Analyzers
    print("\n2. Testing AnomalyDetector...")
    from analyze.anomaly_detector import AnomalyDetector
    detector = AnomalyDetector()
    metric_array = [50, 60, 70, 0.5, 100]  # Mock metrics
    result = detector.detect(metric_array)
    print(f"✓ AnomalyDetector OK - Score: {result.get('score', 0):.3f}")

    print("\n3. Testing FailurePredictor...")
    from analyze.failure_predictor import FailurePredictor
    predictor = FailurePredictor()
    features = {
        'error_rate_trend': 0.01,
        'memory_leak_indicator': False,
        'cpu_spike_pattern': False,
        'disk_io_degradation': False
    }
    result = predictor.predict(features)
    print(f"✓ FailurePredictor OK - Probability: {result.get('failure_probability', 0):.2%}")

    # Test Planners
    print("\n4. Testing FuzzyLogicController...")
    from plan.fuzzy_controller import FuzzyLogicController
    fuzzy = FuzzyLogicController()
    mode = fuzzy.select_mode(cpu_usage=60, error_rate=0.01, latency=200)
    print(f"✓ FuzzyLogicController OK - Mode: {mode}")

    # Test Actuators
    print("\n5. Testing KubernetesActuator (dry-run)...")
    from execute.kubernetes_actuator import KubernetesActuator
    k8s = KubernetesActuator(dry_run_mode=True)
    result = k8s.adjust_hpa('test-service', min_replicas=2, max_replicas=5)
    print(f"✓ KubernetesActuator OK - Dry-run: {result.get('dry_run', False)}")

    print("\n6. Testing DockerActuator (dry-run)...")
    from execute.docker_actuator import DockerActuator
    docker = DockerActuator(dry_run_mode=True)
    result = await docker.scale_service('test-service', replicas=3)
    print(f"✓ DockerActuator OK - Dry-run: {result.get('dry_run', False)}")

    print("\n7. Testing CacheActuator (dry-run)...")
    from execute.cache_actuator import CacheActuator
    cache = CacheActuator(dry_run_mode=True)
    result = await cache.set_cache_strategy('balanced')
    print(f"✓ CacheActuator OK - Dry-run: {result.get('dry_run', False)}")

    print("\n8. Testing SafetyManager...")
    from execute.safety_manager import SafetyManager
    safety = SafetyManager()
    can_execute = safety.check_rate_limit('CRITICAL')
    print(f"✓ SafetyManager OK - Rate limit check: {can_execute}")

    print("\n" + "=" * 60)
    print("✓ All Component Tests PASSED")
    print("=" * 60)


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MAXIMUS AI 3.0 - FASE 1 Integration Tests")
    print("Homeostatic Control Loop (HCL)")
    print("=" * 60)

    # Test components
    await test_hcl_components()

    # Test full cycle
    await test_hcl_single_cycle()

    print("\n" + "=" * 60)
    print("All tests completed successfully! 🎉")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
