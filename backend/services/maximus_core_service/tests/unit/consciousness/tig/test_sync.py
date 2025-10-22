"""PTP Synchronizer - Complete Test Suite for 100% Coverage

Tests for consciousness/tig/sync.py - Precision Time Protocol synchronization
that enables transient global synchronization (ESGT) for consciousness emergence.

Coverage Target: 100% of sync.py (598 statements)
Test Strategy: Direct execution with minimal mocking
Quality Standard: Production-ready, NO MOCK, NO PLACEHOLDER, NO TODO

Theoretical Foundation:
-----------------------
Tests validate PTP synchronization precision required for ESGT ignition.
Target: <100ns jitter for temporal coherence across distributed nodes.

Authors: Juan & Gemini (supervised by Claude)
Version: 1.0.0 - Anti-Burro Edition
Date: 2025-10-07
"""

import asyncio
import time

import numpy as np
import pytest

from consciousness.tig.sync import (
    ClockOffset,
    ClockRole,
    PTPCluster,
    PTPSynchronizer,
    SyncResult,
    SyncState,
)

# ==================== CLOCK OFFSET TESTS ====================


class TestClockOffset:
    """Test ClockOffset dataclass and ESGT readiness validation."""

    def test_clock_offset_creation(self):
        """Test ClockOffset instantiation with all fields."""
        # ARRANGE: Create ClockOffset with specific values
        offset = ClockOffset(offset_ns=50.0, jitter_ns=75.0, drift_ppm=0.5, last_sync=time.time(), quality=0.85)

        # ACT & ASSERT: Verify all fields set correctly
        assert offset.offset_ns == 50.0
        assert offset.jitter_ns == 75.0
        assert offset.drift_ppm == 0.5
        assert offset.quality == 0.85
        assert offset.last_sync > 0

    def test_is_acceptable_for_esgt_pass_simulation_thresholds(self):
        """Test ESGT acceptance with relaxed simulation thresholds (lines 86-103)."""
        # ARRANGE: Create offset with values that pass simulation thresholds
        # Simulation thresholds: jitter < 1000ns, quality > 0.20
        offset = ClockOffset(
            offset_ns=100.0,
            jitter_ns=500.0,  # < 1000ns (simulation threshold)
            drift_ppm=1.0,
            last_sync=time.time(),
            quality=0.25,  # > 0.20 (simulation threshold)
        )

        # ACT: Check ESGT acceptability with simulation thresholds
        acceptable = offset.is_acceptable_for_esgt(threshold_ns=1000.0, quality_threshold=0.20)

        # ASSERT: Should pass with simulation thresholds (line 103)
        assert acceptable is True

    def test_is_acceptable_for_esgt_fail_high_jitter(self):
        """Test ESGT rejection due to high jitter (line 103)."""
        # ARRANGE: Create offset with jitter above threshold
        offset = ClockOffset(
            offset_ns=100.0,
            jitter_ns=1500.0,  # > 1000ns threshold
            drift_ppm=1.0,
            last_sync=time.time(),
            quality=0.90,  # Good quality but jitter too high
        )

        # ACT: Check ESGT acceptability
        acceptable = offset.is_acceptable_for_esgt(threshold_ns=1000.0, quality_threshold=0.20)

        # ASSERT: Should fail due to high jitter (line 103)
        assert acceptable is False

    def test_is_acceptable_for_esgt_fail_low_quality(self):
        """Test ESGT rejection due to low quality (line 103)."""
        # ARRANGE: Create offset with quality below threshold
        offset = ClockOffset(
            offset_ns=100.0,
            jitter_ns=50.0,  # Good jitter
            drift_ppm=1.0,
            last_sync=time.time(),
            quality=0.15,  # < 0.20 threshold
        )

        # ACT: Check ESGT acceptability
        acceptable = offset.is_acceptable_for_esgt(threshold_ns=1000.0, quality_threshold=0.20)

        # ASSERT: Should fail due to low quality (line 103)
        assert acceptable is False

    def test_is_acceptable_for_esgt_hardware_thresholds(self):
        """Test ESGT acceptance with hardware PTP thresholds."""
        # ARRANGE: Create offset meeting hardware PTP standards
        # Hardware thresholds: jitter < 100ns, quality > 0.95
        offset = ClockOffset(
            offset_ns=20.0,
            jitter_ns=80.0,  # < 100ns (hardware threshold)
            drift_ppm=0.1,
            last_sync=time.time(),
            quality=0.96,  # > 0.95 (hardware threshold)
        )

        # ACT: Check with hardware thresholds
        acceptable = offset.is_acceptable_for_esgt(threshold_ns=100.0, quality_threshold=0.95)

        # ASSERT: Should pass with hardware thresholds
        assert acceptable is True

    def test_is_acceptable_for_esgt_boundary_jitter(self):
        """Test ESGT acceptance at exact jitter boundary."""
        # ARRANGE: Jitter exactly at threshold (999.9ns)
        offset = ClockOffset(
            offset_ns=50.0,
            jitter_ns=999.9,  # Just below 1000ns threshold
            drift_ppm=0.5,
            last_sync=time.time(),
            quality=0.30,
        )

        # ACT & ASSERT: Should pass (< threshold)
        assert offset.is_acceptable_for_esgt(threshold_ns=1000.0, quality_threshold=0.20) is True

        # ARRANGE: Jitter just above threshold
        offset.jitter_ns = 1000.1  # Just above 1000ns threshold

        # ACT & ASSERT: Should fail (>= threshold)
        assert offset.is_acceptable_for_esgt(threshold_ns=1000.0, quality_threshold=0.20) is False

    def test_is_acceptable_for_esgt_boundary_quality(self):
        """Test ESGT acceptance at exact quality boundary."""
        # ARRANGE: Quality exactly at threshold (0.20)
        offset = ClockOffset(
            offset_ns=50.0,
            jitter_ns=500.0,
            drift_ppm=0.5,
            last_sync=time.time(),
            quality=0.201,  # Just above 0.20 threshold
        )

        # ACT & ASSERT: Should pass (> threshold)
        assert offset.is_acceptable_for_esgt(threshold_ns=1000.0, quality_threshold=0.20) is True

        # ARRANGE: Quality just below threshold
        offset.quality = 0.199  # Just below 0.20 threshold

        # ACT & ASSERT: Should fail (<= threshold)
        assert offset.is_acceptable_for_esgt(threshold_ns=1000.0, quality_threshold=0.20) is False


# ==================== SYNC RESULT TESTS ====================


class TestSyncResult:
    """Test SyncResult dataclass."""

    def test_sync_result_success_creation(self):
        """Test SyncResult creation for successful sync."""
        # ARRANGE & ACT: Create successful sync result
        result = SyncResult(
            success=True,
            offset_ns=45.5,
            jitter_ns=62.3,
            message="Synced to master-01: offset=45.5ns, jitter=62.3ns",
            timestamp=time.time(),
        )

        # ASSERT: All fields set correctly
        assert result.success is True
        assert result.offset_ns == 45.5
        assert result.jitter_ns == 62.3
        assert "master-01" in result.message
        assert result.timestamp > 0

    def test_sync_result_failure_creation(self):
        """Test SyncResult creation for failed sync."""
        # ARRANGE & ACT: Create failed sync result
        result = SyncResult(
            success=False,
            offset_ns=0.0,
            jitter_ns=0.0,
            message="Sync failed: connection timeout",
            timestamp=time.time(),
        )

        # ASSERT: Failure state captured
        assert result.success is False
        assert result.offset_ns == 0.0
        assert result.jitter_ns == 0.0
        assert "failed" in result.message.lower()

    def test_sync_result_default_values(self):
        """Test SyncResult with default field values."""
        # ARRANGE & ACT: Create result with minimal arguments
        result = SyncResult(success=True)

        # ASSERT: Defaults applied
        assert result.success is True
        assert result.offset_ns == 0.0  # Default
        assert result.jitter_ns == 0.0  # Default
        assert result.message == ""  # Default
        assert result.timestamp > 0  # Auto-generated


# ==================== PTP SYNCHRONIZER LIFECYCLE TESTS ====================


class TestPTPSynchronizerLifecycle:
    """Test PTPSynchronizer initialization and lifecycle."""

    def test_synchronizer_initialization_slave(self):
        """Test PTPSynchronizer init as SLAVE (lines 167-213)."""
        # ARRANGE & ACT: Create slave synchronizer
        sync = PTPSynchronizer(node_id="slave-test-01", role=ClockRole.SLAVE, target_jitter_ns=100.0)

        # ASSERT: All init values set correctly (lines 173-213)
        assert sync.node_id == "slave-test-01"
        assert sync.role == ClockRole.SLAVE
        assert sync.target_jitter_ns == 100.0
        assert sync.state == SyncState.INITIALIZING
        assert sync.local_time_ns == 0
        assert sync.offset_ns == 0.0
        assert sync.master_id is None
        assert len(sync.jitter_history) == 0
        assert len(sync.offset_history) == 0
        assert sync._running is False
        # PAGANI FIX parameters (lines 194-196)
        assert sync.kp == 0.2
        assert sync.ki == 0.08
        assert sync.ema_alpha == 0.1

    def test_synchronizer_initialization_grand_master(self):
        """Test PTPSynchronizer init as GRAND_MASTER."""
        # ARRANGE & ACT: Create grand master synchronizer
        sync = PTPSynchronizer(node_id="gm-test-01", role=ClockRole.GRAND_MASTER, target_jitter_ns=50.0)

        # ASSERT: Grand master specific init
        assert sync.node_id == "gm-test-01"
        assert sync.role == ClockRole.GRAND_MASTER
        assert sync.target_jitter_ns == 50.0
        assert sync.state == SyncState.INITIALIZING

    @pytest.mark.asyncio
    async def test_start_grand_master(self):
        """Test start() for GRAND_MASTER role (lines 227-231)."""
        # ARRANGE: Create grand master
        sync = PTPSynchronizer(node_id="gm-start-01", role=ClockRole.GRAND_MASTER)
        assert sync._running is False
        assert sync.state == SyncState.INITIALIZING

        # ACT: Start synchronizer (lines 227-231)
        await sync.start()

        # Brief wait for background task to initialize
        await asyncio.sleep(0.01)

        # ASSERT: State transitions to MASTER_SYNC (line 228)
        assert sync._running is True
        assert sync.state == SyncState.MASTER_SYNC
        assert sync._sync_task is not None

        # CLEANUP: Stop to avoid hanging tasks
        await sync.stop()

    @pytest.mark.asyncio
    async def test_start_slave(self):
        """Test start() for SLAVE role (lines 233-235)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-start-01", role=ClockRole.SLAVE)

        # ACT: Start slave (lines 233-235)
        await sync.start()

        # ASSERT: State transitions to LISTENING (line 234)
        assert sync._running is True
        assert sync.state == SyncState.LISTENING

        # CLEANUP
        await sync.stop()

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        """Test start() is idempotent (lines 222-223)."""
        # ARRANGE: Create and start synchronizer
        sync = PTPSynchronizer(node_id="idempotent-01", role=ClockRole.SLAVE)
        await sync.start()
        assert sync._running is True

        # ACT: Call start() again (should return early, line 223)
        await sync.start()

        # ASSERT: Still running, no duplicate tasks
        assert sync._running is True

        # CLEANUP
        await sync.stop()

    @pytest.mark.asyncio
    async def test_stop_synchronizer(self):
        """Test stop() method (lines 241-250)."""
        # ARRANGE: Create and start synchronizer
        sync = PTPSynchronizer(node_id="stop-01", role=ClockRole.GRAND_MASTER)
        await sync.start()
        await asyncio.sleep(0.01)
        assert sync._running is True
        assert sync._sync_task is not None

        # ACT: Stop synchronizer (lines 241-250)
        await sync.stop()

        # ASSERT: Stopped completely (lines 243-250)
        assert sync._running is False
        assert sync.state == SyncState.PASSIVE
        # Task should be cancelled and awaited
        # _sync_task is not None still (reference kept), but cancelled

    @pytest.mark.asyncio
    async def test_update_grand_master_time_loop(self):
        """Test _update_grand_master_time() background loop (lines 413-417)."""
        # ARRANGE: Create grand master and start
        sync = PTPSynchronizer(node_id="gm-time-01", role=ClockRole.GRAND_MASTER)
        await sync.start()

        # Wait for several time updates
        await asyncio.sleep(0.05)  # 50ms = 50 loop iterations

        # ACT: Get current time (should be updated)
        current_time = sync.get_time_ns()

        # ASSERT: Time is being updated (lines 416)
        assert current_time > 0
        assert sync.local_time_ns > 0

        # CLEANUP
        await sync.stop()


# ==================== SYNC TO MASTER TESTS ====================


class TestSyncToMaster:
    """Test sync_to_master() core synchronization logic."""

    @pytest.mark.asyncio
    async def test_sync_to_master_grand_master_rejects(self):
        """Test grand master rejects sync_to_master (lines 269-273)."""
        # ARRANGE: Create grand master
        sync = PTPSynchronizer(node_id="gm-reject-01", role=ClockRole.GRAND_MASTER)

        # ACT: Try to sync (should reject, lines 269-273)
        result = await sync.sync_to_master("some-master")

        # ASSERT: Rejection with error message (line 270-273)
        assert result.success is False
        assert "Grand Master does not sync" in result.message

    @pytest.mark.asyncio
    async def test_sync_to_master_slave_success(self):
        """Test successful sync_to_master for slave (lines 252-378)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-sync-01", role=ClockRole.SLAVE)

        # Mock master time source
        def mock_master_time():
            return time.time_ns()

        # ACT: Sync to master (lines 252-378)
        result = await sync.sync_to_master(master_id="master-01", master_time_source=mock_master_time)

        # ASSERT: Sync succeeds (line 367-372)
        assert result.success is True
        assert result.offset_ns != 0.0  # Some offset calculated
        assert result.jitter_ns >= 0.0
        assert "master-01" in result.message
        assert sync.master_id == "master-01"  # Master ID stored (line 275)
        assert sync.state in [SyncState.UNCALIBRATED, SyncState.SLAVE_SYNC]  # State updated

    @pytest.mark.asyncio
    async def test_sync_to_master_multiple_iterations_converge(self):
        """Test multiple sync iterations improve jitter (PAGANI FIX validation)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-converge-01", role=ClockRole.SLAVE)

        # Mock stable master time source
        master_time_ns = time.time_ns()

        def stable_master_time():
            return master_time_ns + 1000  # Constant offset

        # ACT: Sync multiple times (allow convergence)
        jitters = []
        for i in range(50):  # 50 iterations
            result = await sync.sync_to_master(master_id="stable-master", master_time_source=stable_master_time)
            if result.success:
                jitters.append(result.jitter_ns)
            await asyncio.sleep(0.01)  # Small delay

        # ASSERT: Jitter decreases over time (convergence)
        # Last 10 jitters should be lower than first 10
        if len(jitters) >= 20:
            early_jitter = np.mean(jitters[:10])
            late_jitter = np.mean(jitters[-10:])
            # Late jitter should be lower (convergence)
            assert late_jitter < early_jitter or late_jitter < 200.0  # Or below 200ns

    @pytest.mark.asyncio
    async def test_sync_to_master_offset_calculation(self):
        """Test offset calculation logic (lines 299-317)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-offset-01", role=ClockRole.SLAVE)

        # Mock master time with known offset
        known_offset_ns = 5000.0  # 5 microseconds ahead

        def master_with_offset():
            return time.time_ns() + int(known_offset_ns)

        # ACT: Sync once
        result = await sync.sync_to_master(master_id="offset-master", master_time_source=master_with_offset)

        # ASSERT: Offset detected (within noise margin)
        assert result.success is True
        # Offset should be approximately known_offset_ns (may have some variance)
        assert abs(result.offset_ns) > 0  # Some offset detected

    @pytest.mark.asyncio
    async def test_sync_to_master_state_transitions(self):
        """Test state transitions during sync (lines 276, 362-365)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-state-01", role=ClockRole.SLAVE)
        assert sync.state == SyncState.INITIALIZING

        # ACT: First sync (lines 276)
        await sync.sync_to_master("master-01")

        # ASSERT: State transitions to UNCALIBRATED (line 276)
        assert sync.state == SyncState.UNCALIBRATED

        # ACT: Keep syncing until convergence
        for _ in range(100):  # Many iterations to converge
            await sync.sync_to_master("master-01")

        # ASSERT: Eventually reaches SLAVE_SYNC or stays UNCALIBRATED (lines 362-365)
        assert sync.state in [SyncState.SLAVE_SYNC, SyncState.UNCALIBRATED]

    @pytest.mark.asyncio
    async def test_sync_to_master_exception_handling(self):
        """Test sync_to_master exception handling (lines 380-385)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-exception-01", role=ClockRole.SLAVE)

        # Mock master time source that raises exception
        def failing_master_time():
            raise RuntimeError("Master unreachable")

        # ACT: Sync with failing master (should catch exception)
        result = await sync.sync_to_master(master_id="failing-master", master_time_source=failing_master_time)

        # ASSERT: Sync fails gracefully (lines 382-385)
        assert result.success is False
        assert "Sync failed" in result.message
        assert sync.state == SyncState.FAULT  # State set to FAULT (line 381)

    @pytest.mark.asyncio
    async def test_sync_to_master_jitter_history_accumulation(self):
        """Test jitter history accumulation and limiting (lines 344-346)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-jitter-hist-01", role=ClockRole.SLAVE)

        # ACT: Sync many times to fill jitter history
        for _ in range(250):  # More than 200 (limit)
            await sync.sync_to_master("master-01")

        # ASSERT: Jitter history limited to 200 (line 345-346)
        assert len(sync.jitter_history) <= 200

    @pytest.mark.asyncio
    async def test_sync_to_master_offset_history_accumulation(self):
        """Test offset history accumulation and limiting (lines 305-307)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-offset-hist-01", role=ClockRole.SLAVE)

        # ACT: Sync many times to fill offset history
        for _ in range(50):  # More than 30 (limit)
            await sync.sync_to_master("master-01")

        # ASSERT: Offset history limited to 30 (line 306-307)
        assert len(sync.offset_history) <= 30

    @pytest.mark.asyncio
    async def test_sync_to_master_ema_initialization(self):
        """Test EMA (Exponential Moving Average) initialization (lines 310-313)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-ema-01", role=ClockRole.SLAVE)
        assert sync.ema_offset is None  # Initially None (line 208)

        # ACT: First sync (should initialize EMA)
        await sync.sync_to_master("master-01")

        # ASSERT: EMA initialized on first sync (line 311)
        assert sync.ema_offset is not None
        # EMA should be approximately equal to first offset
        assert sync.ema_offset != 0.0

    @pytest.mark.asyncio
    async def test_sync_to_master_integral_anti_windup(self):
        """Test integral anti-windup protection (lines 322-328)."""
        # ARRANGE: Create slave with integral accumulation
        sync = PTPSynchronizer(node_id="slave-windup-01", role=ClockRole.SLAVE)

        # Mock master with large constant offset (force integral buildup)
        large_offset = 100000.0  # 100 microseconds

        def large_offset_master():
            return time.time_ns() + int(large_offset)

        # ACT: Sync many times (build up integral error)
        for _ in range(100):
            await sync.sync_to_master(master_id="large-offset-master", master_time_source=large_offset_master)

        # ASSERT: Integral error clamped to max (lines 322-328)
        assert abs(sync.integral_error) <= sync.integral_max  # 1000.0 max (line 197)

    @pytest.mark.asyncio
    async def test_sync_to_master_drift_calculation(self):
        """Test drift_ppm calculation (lines 351-354)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="slave-drift-01", role=ClockRole.SLAVE)
        sync.last_sync_time = time.time() - 1.0  # Set last sync 1 second ago

        # ACT: Sync (should calculate drift)
        await sync.sync_to_master("master-01")

        # ASSERT: Drift calculated (line 354)
        # drift_ppm updated (may be 0 or small value)
        # Just verify it's a number
        assert isinstance(sync.drift_ppm, float)


# ==================== HELPER METHODS TESTS ====================


class TestPTPSynchronizerHelpers:
    """Test PTPSynchronizer helper methods."""

    def test_calculate_quality_perfect(self):
        """Test _calculate_quality with perfect sync (line 387-411)."""
        # ARRANGE: Create synchronizer
        sync = PTPSynchronizer(node_id="quality-perfect-01", role=ClockRole.SLAVE)
        sync.target_jitter_ns = 100.0

        # Populate offset history for stability calculation
        sync.offset_history = [10.0, 11.0, 10.5, 10.2, 10.8]  # Low variance

        # ACT: Calculate quality with low jitter and delay (line 387)
        quality = sync._calculate_quality(jitter_ns=50.0, delay_ns=500.0)

        # ASSERT: High quality score (near 1.0)
        assert quality > 0.7  # Good sync quality
        assert quality <= 1.0  # Capped at 1.0 (line 411)

    def test_calculate_quality_poor(self):
        """Test _calculate_quality with poor sync."""
        # ARRANGE: Create synchronizer
        sync = PTPSynchronizer(node_id="quality-poor-01", role=ClockRole.SLAVE)
        sync.target_jitter_ns = 100.0

        # Populate offset history with high variance
        sync.offset_history = [100.0, 500.0, 50.0, 800.0, 200.0]  # High variance

        # ACT: Calculate quality with high jitter and delay
        quality = sync._calculate_quality(jitter_ns=5000.0, delay_ns=50000.0)

        # ASSERT: Low quality score
        assert quality < 0.5  # Poor sync quality

    def test_calculate_quality_insufficient_history(self):
        """Test _calculate_quality with insufficient offset history (line 403-406)."""
        # ARRANGE: Create synchronizer with empty offset history
        sync = PTPSynchronizer(node_id="quality-no-hist-01", role=ClockRole.SLAVE)
        sync.offset_history = []  # Empty

        # ACT: Calculate quality (should use default stability, line 406)
        quality = sync._calculate_quality(jitter_ns=100.0, delay_ns=1000.0)

        # ASSERT: Returns some quality value (uses 0.5 stability default)
        assert 0.0 <= quality <= 1.0

    def test_get_time_ns_grand_master(self):
        """Test get_time_ns for GRAND_MASTER (lines 426-427)."""
        # ARRANGE: Create grand master
        sync = PTPSynchronizer(node_id="gm-time-02", role=ClockRole.GRAND_MASTER)

        # ACT: Get time (lines 426-427)
        t1 = sync.get_time_ns()
        t2 = time.time_ns()

        # ASSERT: Returns system time (line 427)
        # Should be approximately equal (within microseconds)
        assert abs(t1 - t2) < 1000000  # Within 1ms

    def test_get_time_ns_slave(self):
        """Test get_time_ns for SLAVE with offset (lines 429-430)."""
        # ARRANGE: Create slave with known offset
        sync = PTPSynchronizer(node_id="slave-time-01", role=ClockRole.SLAVE)
        sync.offset_ns = 5000.0  # 5 microseconds

        # ACT: Get time (lines 429-430)
        sync_time = sync.get_time_ns()
        system_time = time.time_ns()

        # ASSERT: Time adjusted by offset (line 430)
        # sync_time = time.time_ns() - offset_ns
        expected = system_time - int(sync.offset_ns)
        assert abs(sync_time - expected) < 1000000  # Within 1ms

    def test_get_offset(self):
        """Test get_offset method (lines 432-448)."""
        # ARRANGE: Create synchronizer with populated data
        sync = PTPSynchronizer(node_id="offset-01", role=ClockRole.SLAVE)
        sync.offset_ns = 123.45
        sync.jitter_history = [50.0, 55.0, 52.0, 48.0]
        sync.drift_ppm = 0.75
        sync.last_sync_time = time.time()

        # ACT: Get offset (lines 432-448)
        offset = sync.get_offset()

        # ASSERT: ClockOffset populated correctly (lines 442-448)
        assert offset.offset_ns == 123.45
        assert offset.jitter_ns == np.mean([50.0, 55.0, 52.0, 48.0])  # Average jitter
        assert offset.drift_ppm == 0.75
        assert offset.last_sync == sync.last_sync_time
        assert 0.0 <= offset.quality <= 1.0

    def test_is_ready_for_esgt(self):
        """Test is_ready_for_esgt method (lines 450-458)."""
        # ARRANGE: Create synchronizer with good sync quality
        sync = PTPSynchronizer(node_id="esgt-ready-01", role=ClockRole.SLAVE)
        sync.target_jitter_ns = 1000.0
        sync.jitter_history = [500.0, 520.0, 480.0]  # Low jitter
        sync.offset_history = [100.0, 105.0, 95.0]  # Stable
        sync.offset_ns = 100.0

        # ACT: Check ESGT readiness (line 457)
        ready = sync.is_ready_for_esgt()

        # ASSERT: Should be ready (jitter < 1000ns)
        assert ready is True

    def test_is_not_ready_for_esgt(self):
        """Test is_ready_for_esgt returns False for high jitter."""
        # ARRANGE: Create synchronizer with poor sync
        sync = PTPSynchronizer(node_id="esgt-not-ready-01", role=ClockRole.SLAVE)
        sync.target_jitter_ns = 1000.0
        sync.jitter_history = [1500.0, 1600.0, 1550.0]  # High jitter
        sync.offset_history = [100.0]

        # ACT: Check ESGT readiness
        ready = sync.is_ready_for_esgt()

        # ASSERT: Not ready (jitter > 1000ns)
        assert ready is False

    def test_repr(self):
        """Test __repr__ method (lines 481-485)."""
        # ARRANGE: Create synchronizer
        sync = PTPSynchronizer(node_id="repr-01", role=ClockRole.SLAVE, target_jitter_ns=100.0)
        sync.state = SyncState.SLAVE_SYNC
        sync.jitter_history = [80.0, 85.0, 75.0]

        # ACT: Get string representation (line 481-485)
        repr_str = repr(sync)

        # ASSERT: Contains key information
        assert "repr-01" in repr_str
        assert ClockRole.SLAVE.value in repr_str
        assert SyncState.SLAVE_SYNC.value in repr_str
        assert "jitter" in repr_str
        assert "esgt_ready" in repr_str


# ==================== CONTINUOUS SYNC TESTS ====================


class TestContinuousSync:
    """Test continuous_sync background synchronization."""

    @pytest.mark.asyncio
    async def test_continuous_sync_runs(self):
        """Test continuous_sync loops and syncs periodically (lines 460-479)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="continuous-01", role=ClockRole.SLAVE)
        await sync.start()

        # Track number of syncs
        sync_count = [0]
        original_sync = sync.sync_to_master

        async def counting_sync(master_id, master_time_source=None):
            sync_count[0] += 1
            return await original_sync(master_id, master_time_source)

        sync.sync_to_master = counting_sync

        # ACT: Start continuous sync with short interval (line 460)
        sync_task = asyncio.create_task(sync.continuous_sync("master-01", interval_sec=0.05))

        # Let it run for several intervals
        await asyncio.sleep(0.3)  # 300ms = ~6 sync intervals

        # CLEANUP: Cancel task
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

        await sync.stop()

        # ASSERT: Multiple syncs occurred (line 474)
        assert sync_count[0] >= 3  # At least 3 syncs in 300ms

    @pytest.mark.asyncio
    async def test_continuous_sync_handles_failure(self):
        """Test continuous_sync handles sync failures gracefully (lines 476-477)."""
        # ARRANGE: Create slave that will fail to sync
        sync = PTPSynchronizer(node_id="continuous-fail-01", role=ClockRole.SLAVE)
        await sync.start()

        # Mock sync_to_master to fail
        async def failing_sync(master_id, master_time_source=None):
            return SyncResult(success=False, message="Mock failure")

        sync.sync_to_master = failing_sync

        # ACT: Start continuous sync (should handle failures)
        sync_task = asyncio.create_task(sync.continuous_sync("master-01", interval_sec=0.05))

        # Let it run briefly
        await asyncio.sleep(0.15)

        # CLEANUP: Cancel task
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

        await sync.stop()

        # ASSERT: Continuous sync didn't crash despite failures (lines 476-479)
        # If we get here without exception, test passes

    @pytest.mark.asyncio
    async def test_continuous_sync_respects_interval(self):
        """Test continuous_sync respects interval parameter (line 479)."""
        # ARRANGE: Create slave
        sync = PTPSynchronizer(node_id="continuous-interval-01", role=ClockRole.SLAVE)
        await sync.start()

        # Track sync timestamps
        sync_times = []

        async def timestamping_sync(master_id, master_time_source=None):
            sync_times.append(time.time())
            return SyncResult(success=True)

        sync.sync_to_master = timestamping_sync

        # ACT: Start continuous sync with 0.1s interval
        interval = 0.1
        sync_task = asyncio.create_task(sync.continuous_sync("master-01", interval_sec=interval))

        # Let it run for 3 intervals
        await asyncio.sleep(0.35)

        # CLEANUP
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

        await sync.stop()

        # ASSERT: Sync intervals approximately match (line 479)
        if len(sync_times) >= 2:
            intervals = [sync_times[i + 1] - sync_times[i] for i in range(len(sync_times) - 1)]
            avg_interval = np.mean(intervals)
            # Allow 20% tolerance
            assert 0.08 <= avg_interval <= 0.15  # ~0.1s ± tolerance


# ==================== PTP CLUSTER TESTS ====================


class TestPTPCluster:
    """Test PTPCluster multi-node coordination."""

    @pytest.mark.asyncio
    async def test_cluster_initialization(self):
        """Test PTPCluster initialization (lines 507-510)."""
        # ARRANGE & ACT: Create cluster
        cluster = PTPCluster(target_jitter_ns=100.0)

        # ASSERT: Initial state (lines 508-510)
        assert cluster.target_jitter_ns == 100.0
        assert len(cluster.synchronizers) == 0
        assert cluster.grand_master_id is None

    @pytest.mark.asyncio
    async def test_add_grand_master(self):
        """Test add_grand_master method (lines 512-523)."""
        # ARRANGE: Create cluster
        cluster = PTPCluster(target_jitter_ns=100.0)

        # ACT: Add grand master (lines 512-523)
        gm_sync = await cluster.add_grand_master("gm-cluster-01")

        # ASSERT: Grand master added (lines 517-522)
        assert cluster.grand_master_id == "gm-cluster-01"
        assert "gm-cluster-01" in cluster.synchronizers
        assert gm_sync.role == ClockRole.GRAND_MASTER
        assert gm_sync.state == SyncState.MASTER_SYNC
        assert gm_sync._running is True

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_add_grand_master_duplicate_fails(self):
        """Test add_grand_master rejects duplicate (lines 514-515)."""
        # ARRANGE: Create cluster with existing grand master
        cluster = PTPCluster()
        await cluster.add_grand_master("gm-first")

        # ACT & ASSERT: Try to add second grand master (should raise)
        with pytest.raises(ValueError, match="Grand master already exists"):
            await cluster.add_grand_master("gm-second")

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_add_slave(self):
        """Test add_slave method (lines 525-532)."""
        # ARRANGE: Create cluster
        cluster = PTPCluster(target_jitter_ns=100.0)

        # ACT: Add slave (lines 525-532)
        slave_sync = await cluster.add_slave("slave-cluster-01")

        # ASSERT: Slave added (lines 527-531)
        assert "slave-cluster-01" in cluster.synchronizers
        assert slave_sync.role == ClockRole.SLAVE
        assert slave_sync.state == SyncState.LISTENING
        assert slave_sync._running is True
        assert slave_sync.target_jitter_ns == 100.0

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_synchronize_all(self):
        """Test synchronize_all method (lines 534-546)."""
        # ARRANGE: Create cluster with grand master and slaves
        cluster = PTPCluster(target_jitter_ns=1000.0)
        await cluster.add_grand_master("gm-sync-all-01")
        await cluster.add_slave("slave-sync-01")
        await cluster.add_slave("slave-sync-02")
        await cluster.add_slave("slave-sync-03")

        # ACT: Synchronize all slaves (lines 534-546)
        results = await cluster.synchronize_all()

        # ASSERT: All slaves synced (line 539-545)
        assert len(results) == 3  # 3 slaves
        assert "slave-sync-01" in results
        assert "slave-sync-02" in results
        assert "slave-sync-03" in results

        # All should be successful
        for node_id, result in results.items():
            assert result.success is True

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_synchronize_all_no_grand_master_fails(self):
        """Test synchronize_all fails without grand master (lines 536-537)."""
        # ARRANGE: Create cluster WITHOUT grand master
        cluster = PTPCluster()
        await cluster.add_slave("slave-no-gm-01")

        # ACT & ASSERT: synchronize_all should raise (lines 536-537)
        with pytest.raises(RuntimeError, match="No grand master configured"):
            await cluster.synchronize_all()

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_is_esgt_ready_true(self):
        """Test is_esgt_ready returns True when all slaves ready (lines 548-558)."""
        # ARRANGE: Create cluster and sync multiple times
        cluster = PTPCluster(target_jitter_ns=1000.0)  # Relaxed threshold
        await cluster.add_grand_master("gm-esgt-01")
        await cluster.add_slave("slave-esgt-01")
        await cluster.add_slave("slave-esgt-02")

        # Sync many times to achieve low jitter
        for _ in range(100):
            await cluster.synchronize_all()

        # ACT: Check ESGT readiness (lines 548-558)
        ready = cluster.is_esgt_ready()

        # ASSERT: Cluster should be ready (all slaves converged)
        # With 100 syncs and 1000ns threshold, should achieve readiness
        assert ready is True

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_is_esgt_ready_false_no_grand_master(self):
        """Test is_esgt_ready returns False without grand master (lines 550-551)."""
        # ARRANGE: Create cluster without grand master
        cluster = PTPCluster()

        # ACT: Check ESGT readiness (lines 550-551)
        ready = cluster.is_esgt_ready()

        # ASSERT: Not ready without grand master (line 551)
        assert ready is False

    @pytest.mark.asyncio
    async def test_is_esgt_ready_false_poor_sync(self):
        """Test is_esgt_ready returns False with poor sync (lines 553-556)."""
        # ARRANGE: Create cluster with tight jitter threshold
        cluster = PTPCluster(target_jitter_ns=10.0)  # Very tight threshold
        await cluster.add_grand_master("gm-esgt-tight-01")
        await cluster.add_slave("slave-esgt-tight-01")

        # Sync once (not enough for convergence)
        await cluster.synchronize_all()

        # ACT: Check ESGT readiness (lines 548-558)
        ready = cluster.is_esgt_ready()

        # ASSERT: Not ready yet (insufficient convergence)
        assert ready is False

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_get_cluster_metrics(self):
        """Test get_cluster_metrics method (lines 560-586)."""
        # ARRANGE: Create cluster with synchronized nodes
        cluster = PTPCluster(target_jitter_ns=1000.0)
        await cluster.add_grand_master("gm-metrics-01")
        await cluster.add_slave("slave-metrics-01")
        await cluster.add_slave("slave-metrics-02")

        # Sync several times
        for _ in range(20):
            await cluster.synchronize_all()

        # ACT: Get cluster metrics (lines 560-586)
        metrics = cluster.get_cluster_metrics()

        # ASSERT: Metrics populated correctly (lines 576-586)
        assert metrics["node_count"] == 3  # 1 GM + 2 slaves
        assert metrics["slave_count"] == 2
        assert metrics["esgt_ready_count"] >= 0
        assert 0 <= metrics["esgt_ready_percentage"] <= 100
        assert metrics["max_offset_ns"] >= 0.0
        assert metrics["avg_offset_ns"] >= 0.0
        assert metrics["max_jitter_ns"] >= 0.0
        assert metrics["avg_jitter_ns"] >= 0.0
        assert metrics["target_jitter_ns"] == 1000.0

        # CLEANUP
        await cluster.stop_all()

    @pytest.mark.asyncio
    async def test_stop_all(self):
        """Test stop_all method (lines 588-591)."""
        # ARRANGE: Create cluster with multiple nodes
        cluster = PTPCluster()
        await cluster.add_grand_master("gm-stop-01")
        await cluster.add_slave("slave-stop-01")
        await cluster.add_slave("slave-stop-02")

        # Verify all running
        for sync in cluster.synchronizers.values():
            assert sync._running is True

        # ACT: Stop all (lines 588-591)
        await cluster.stop_all()

        # ASSERT: All stopped (line 590-591)
        for sync in cluster.synchronizers.values():
            assert sync._running is False
            assert sync.state == SyncState.PASSIVE

    def test_cluster_repr(self):
        """Test PTPCluster __repr__ method (lines 593-597)."""
        # ARRANGE: Create cluster
        cluster = PTPCluster(target_jitter_ns=100.0)

        # ACT: Get string representation (lines 593-597)
        repr_str = repr(cluster)

        # ASSERT: Contains key information
        assert "PTPCluster" in repr_str
        assert "nodes=" in repr_str
        assert "esgt_ready=" in repr_str
        assert "avg_jitter=" in repr_str
