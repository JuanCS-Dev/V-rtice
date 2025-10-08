"""Maximus RTE Service - Latency Test Module.

This module contains tests specifically designed to measure and validate the
low-latency performance of components within the Maximus AI's Real-Time
Execution (RTE) Service. It focuses on ensuring that critical operations
and data processing pipelines meet their stringent real-time requirements.

Key functionalities include:
- Benchmarking the execution time of Fast ML predictions.
- Measuring the latency of data fusion processes.
- Validating the speed of Hyperscan pattern matching.
- Assessing the end-to-end latency of real-time playbook execution.

These tests are crucial for guaranteeing that Maximus AI can react instantaneously
to dynamic environmental changes or emerging threats, maintaining its responsiveness
and effectiveness in real-time scenarios.
"""

from datetime import datetime

import pytest

from fast_ml import FastML
from fusion_engine import FusionEngine
from hyperscan_matcher import HyperscanMatcher
from playbooks import RealTimePlaybookExecutor


@pytest.fixture
def fast_ml_instance():
    """Fixture for a FastML instance."""
    return FastML()


@pytest.fixture
def fusion_engine_instance():
    """Fixture for a FusionEngine instance."""
    return FusionEngine()


@pytest.fixture
def hyperscan_matcher_instance():
    """Fixture for a HyperscanMatcher instance."""
    return HyperscanMatcher()


@pytest.fixture
def rt_playbook_executor(fast_ml_instance, hyperscan_matcher_instance):
    """Fixture for a RealTimePlaybookExecutor instance."""
    return RealTimePlaybookExecutor(fast_ml_instance, hyperscan_matcher_instance)


@pytest.mark.asyncio
async def test_fast_ml_latency(fast_ml_instance):
    """Tests the latency of a FastML prediction."""
    start_time = datetime.now()
    await fast_ml_instance.predict({"features": {"malicious_indicators": 0.5}}, "threat_score")
    end_time = datetime.now()
    latency_ms = (end_time - start_time).total_seconds() * 1000
    assert latency_ms < 50  # Expect prediction to be very fast, e.g., under 50ms


@pytest.mark.asyncio
async def test_fusion_engine_latency(fusion_engine_instance):
    """Tests the latency of data fusion in the FusionEngine."""
    data_sources = [
        {"ip_address": "1.1.1.1", "event": "login"},
        {"username": "testuser", "event": "access"},
    ]
    start_time = datetime.now()
    await fusion_engine_instance.fuse_data(data_sources)
    end_time = datetime.now()
    latency_ms = (end_time - start_time).total_seconds() * 1000
    assert latency_ms < 100  # Expect fusion to be fast, e.g., under 100ms


@pytest.mark.asyncio
async def test_hyperscan_matcher_latency(hyperscan_matcher_instance):
    """Tests the latency of Hyperscan pattern matching."""
    await hyperscan_matcher_instance.compile_patterns(["test_pattern", "another_pattern"])
    data = b"some data with a test_pattern inside"
    start_time = datetime.now()
    await hyperscan_matcher_instance.scan_data(data)
    end_time = datetime.now()
    latency_ms = (end_time - start_time).total_seconds() * 1000
    assert latency_ms < 20  # Expect hyperscan to be extremely fast, e.g., under 20ms


@pytest.mark.asyncio
async def test_real_time_playbook_execution_latency(rt_playbook_executor):
    """Tests the end-to-end latency of a real-time playbook execution."""
    command_name = "block_ip"
    parameters = {"ip_address": "192.168.1.1"}
    start_time = datetime.now()
    await rt_playbook_executor.execute_command(command_name, parameters)
    end_time = datetime.now()
    latency_ms = (end_time - start_time).total_seconds() * 1000
    assert latency_ms < 150  # Expect playbook execution to be fast, e.g., under 150ms
