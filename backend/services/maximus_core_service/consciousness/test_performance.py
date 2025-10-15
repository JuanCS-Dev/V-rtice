"""Performance Tests - Production Benchmarks

Tests consciousness system performance characteristics:
- Stimulus → Response latency (<100ms target)
- Sustained operation stability (5min target)
- Memory stability (no leaks over 1000 ops)

This is PRODUCTION-CRITICAL performance validation.
Target: All benchmarks within requirements.

Authors: Claude Code + Juan
Date: 2025-10-14
"""

import pytest
import asyncio
import time
from consciousness.system import ConsciousnessSystem, ConsciousnessConfig


class TestConsciousnessLatency:
    """Test system response latency."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tig_activation_latency(self):
        """TIG activation should complete within 100ms.

        Target: <100ms for single node activation
        """
        config = ConsciousnessConfig(
            tig_node_count=100,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()
            await asyncio.sleep(0.1)  # Let system stabilize

            # Measure TIG activation latency
            start = time.time()
            await system.tig_fabric.activate_node(50, activation=0.8)
            elapsed = time.time() - start

            elapsed_ms = elapsed * 1000
            print(f"\nTIG activation latency: {elapsed_ms:.2f}ms")

            # Target: <100ms
            assert elapsed_ms < 100, f"TIG activation too slow: {elapsed_ms:.2f}ms"

        finally:
            await system.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_system_startup_latency(self):
        """System startup should complete within 5 seconds.

        Target: <5s for full system initialization
        """
        config = ConsciousnessConfig(
            tig_node_count=100,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        # Measure startup time
        start = time.time()
        await system.start()
        elapsed = time.time() - start

        elapsed_s = elapsed
        print(f"\nSystem startup latency: {elapsed_s:.2f}s")

        try:
            # Target: <5s
            assert elapsed_s < 5.0, f"Startup too slow: {elapsed_s:.2f}s"

        finally:
            await system.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_system_shutdown_latency(self):
        """System shutdown should complete within 2 seconds.

        Target: <2s for clean shutdown
        """
        config = ConsciousnessConfig(
            tig_node_count=100,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        await system.start()
        await asyncio.sleep(0.2)

        # Measure shutdown time
        start = time.time()
        await system.stop()
        elapsed = time.time() - start

        elapsed_s = elapsed
        print(f"\nSystem shutdown latency: {elapsed_s:.2f}s")

        # Target: <2s
        assert elapsed_s < 2.0, f"Shutdown too slow: {elapsed_s:.2f}s"


class TestSustainedOperation:
    """Test system stability under sustained operation."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(360)  # 6 minute timeout
    async def test_sustained_operation_5min(self):
        """System should operate stably for 5 minutes.

        Target: 5min continuous operation without crashes
        """
        config = ConsciousnessConfig(
            tig_node_count=100,
            esgt_min_salience=0.70,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Run for 5 minutes with periodic stimuli
            start = time.time()
            duration_target = 300  # 5 minutes

            stimulus_count = 0
            while time.time() - start < duration_target:
                # Inject stimulus every second
                node_id = stimulus_count % 100
                await system.tig_fabric.activate_node(node_id, activation=0.75)

                stimulus_count += 1
                await asyncio.sleep(1.0)

            elapsed = time.time() - start
            print(f"\nSustained operation: {elapsed:.1f}s, {stimulus_count} stimuli")

            # System should still be healthy after 5 minutes
            assert system.is_healthy(), "System degraded after sustained operation"

            # Should have processed stimuli
            assert stimulus_count >= 295, f"Too few stimuli processed: {stimulus_count}"

        finally:
            await system.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(120)  # 2 minute timeout
    async def test_sustained_operation_1min(self):
        """System should operate stably for 1 minute (fast version).

        Target: 1min continuous operation (faster test)
        """
        config = ConsciousnessConfig(
            tig_node_count=50,
            esgt_min_salience=0.70,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()

            # Run for 1 minute
            start = time.time()
            duration_target = 60  # 1 minute

            stimulus_count = 0
            while time.time() - start < duration_target:
                node_id = stimulus_count % 50
                await system.tig_fabric.activate_node(node_id, activation=0.75)

                stimulus_count += 1
                await asyncio.sleep(0.5)  # Faster stimuli

            elapsed = time.time() - start
            print(f"\nSustained operation (1min): {elapsed:.1f}s, {stimulus_count} stimuli")

            # System should still be healthy
            assert system.is_healthy()

            # Should have processed many stimuli
            assert stimulus_count >= 115, f"Too few stimuli: {stimulus_count}"

        finally:
            await system.stop()


class TestMemoryStability:
    """Test system memory usage over time."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_memory_stability_1000_ops(self):
        """System should not leak memory over 1000 operations.

        Target: <100MB increase over 1000 operations
        """
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available")

        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()
            await asyncio.sleep(0.2)  # Stabilize

            # Force garbage collection
            import gc
            gc.collect()

            # Measure initial memory
            process = psutil.Process(os.getpid())
            initial_memory_mb = process.memory_info().rss / 1024 / 1024

            print(f"\nInitial memory: {initial_memory_mb:.2f} MB")

            # Perform 1000 operations
            for i in range(1000):
                node_id = i % 50
                await system.tig_fabric.activate_node(node_id, activation=0.70)

                # Every 100 ops, collect garbage
                if i % 100 == 0:
                    gc.collect()

            # Final garbage collection
            gc.collect()
            await asyncio.sleep(0.1)

            # Measure final memory
            final_memory_mb = process.memory_info().rss / 1024 / 1024
            memory_increase_mb = final_memory_mb - initial_memory_mb

            print(f"Final memory: {final_memory_mb:.2f} MB")
            print(f"Memory increase: {memory_increase_mb:.2f} MB over 1000 ops")

            # Target: <100MB increase
            assert memory_increase_mb < 100, f"Potential memory leak: +{memory_increase_mb:.2f}MB"

        finally:
            await system.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_memory_stability_hot_restart(self):
        """System should not leak memory on restart cycles.

        Target: <50MB increase per restart cycle
        """
        try:
            import psutil
            import os
            import gc
        except ImportError:
            pytest.skip("psutil not available")

        config = ConsciousnessConfig(
            tig_node_count=50,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        # Measure baseline
        gc.collect()
        process = psutil.Process(os.getpid())
        baseline_memory_mb = process.memory_info().rss / 1024 / 1024

        print(f"\nBaseline memory: {baseline_memory_mb:.2f} MB")

        # Perform 3 restart cycles
        for cycle in range(3):
            system = ConsciousnessSystem(config)

            await system.start()
            await asyncio.sleep(0.1)

            # Do some work
            for i in range(10):
                await system.tig_fabric.activate_node(i, activation=0.7)

            await system.stop()
            del system

            gc.collect()

            # Measure after each cycle
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            increase = current_memory_mb - baseline_memory_mb
            print(f"After cycle {cycle+1}: {current_memory_mb:.2f} MB (+{increase:.2f} MB)")

        # Final measurement
        gc.collect()
        final_memory_mb = process.memory_info().rss / 1024 / 1024
        total_increase_mb = final_memory_mb - baseline_memory_mb

        print(f"Total increase after 3 cycles: {total_increase_mb:.2f} MB")

        # Target: <50MB increase after 3 cycles
        assert total_increase_mb < 50, f"Memory leak on restart: +{total_increase_mb:.2f}MB"


class TestThroughput:
    """Test system throughput characteristics."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tig_activation_throughput(self):
        """Measure TIG activation throughput.

        Target: >100 activations/second
        """
        config = ConsciousnessConfig(
            tig_node_count=100,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()
            await asyncio.sleep(0.1)

            # Measure throughput over 1 second
            start = time.time()
            count = 0

            while time.time() - start < 1.0:
                await system.tig_fabric.activate_node(count % 100, activation=0.7)
                count += 1

            throughput = count
            print(f"\nTIG activation throughput: {throughput} activations/sec")

            # Target: >100/sec
            assert throughput > 100, f"Throughput too low: {throughput}/sec"

        finally:
            await system.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_throughput(self):
        """Measure concurrent activation throughput.

        Target: Handle 50 concurrent activations
        """
        config = ConsciousnessConfig(
            tig_node_count=100,
            safety_enabled=False,
        )
        config.reactive.enable_data_orchestration = False

        system = ConsciousnessSystem(config)

        try:
            await system.start()
            await asyncio.sleep(0.1)

            # Fire 50 concurrent activations
            start = time.time()

            tasks = []
            for i in range(50):
                task = system.tig_fabric.activate_node(i, activation=0.75)
                tasks.append(task)

            await asyncio.gather(*tasks)

            elapsed = time.time() - start
            elapsed_ms = elapsed * 1000

            print(f"\n50 concurrent activations: {elapsed_ms:.2f}ms")

            # Target: <500ms for 50 concurrent
            assert elapsed_ms < 500, f"Concurrent throughput too slow: {elapsed_ms:.2f}ms"

        finally:
            await system.stop()
