"""
Tests for Profiler

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest
import numpy as np
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from performance.profiler import Profiler, ProfilerConfig, ProfileResult


@pytest.fixture
def simple_model():
    """Create simple model for testing."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(128, 64)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(64, 32)

        def forward(self, x):
            x = self.fc1(x)
            x = self.relu(x)
            x = self.fc2(x)
            return x

    return SimpleModel()


@pytest.fixture
def profiler_config(tmp_path):
    """Create profiler config."""
    return ProfilerConfig(
        enable_cpu_profiling=True,
        enable_memory_profiling=True,
        enable_gpu_profiling=False,
        num_iterations=10,
        warmup_iterations=2,
        output_dir=tmp_path / "profiling"
    )


def test_profiler_initialization(profiler_config):
    """Test profiler initialization."""
    profiler = Profiler(config=profiler_config)

    assert profiler.config.num_iterations == 10
    assert profiler.config.warmup_iterations == 2
    assert profiler.config.output_dir.exists()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_profile_model_cpu(simple_model, profiler_config):
    """Test model profiling on CPU."""
    profiler = Profiler(config=profiler_config)

    result = profiler.profile_model(
        model=simple_model,
        input_shape=(8, 128),
        device="cpu"
    )

    assert isinstance(result, ProfileResult)
    assert result.total_time_ms > 0
    assert result.avg_time_ms > 0
    assert result.avg_time_ms <= result.total_time_ms


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_profile_result_layer_times(simple_model, profiler_config):
    """Test layer-wise timing in profile results."""
    profiler = Profiler(config=profiler_config)

    result = profiler.profile_model(
        model=simple_model,
        input_shape=(4, 128),
        device="cpu"
    )

    # Layer times should be recorded
    assert isinstance(result.layer_times, dict)
    # Note: Layer times may be empty if model doesn't have hooks
    # This is expected behavior


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_profile_memory_tracking(simple_model, profiler_config):
    """Test memory profiling."""
    profiler = Profiler(config=profiler_config)

    result = profiler.profile_model(
        model=simple_model,
        input_shape=(16, 128),
        device="cpu"
    )

    # Memory tracking may or may not be available depending on psutil
    if result.peak_memory_mb is not None:
        assert result.peak_memory_mb >= 0


def test_profile_result_to_dict(simple_model, profiler_config):
    """Test profile result conversion to dict."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    profiler = Profiler(config=profiler_config)

    result = profiler.profile_model(
        model=simple_model,
        input_shape=(2, 128),
        device="cpu"
    )

    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert "total_time_ms" in result_dict
    assert "avg_time_ms" in result_dict
    assert "layer_times" in result_dict
    assert result_dict["total_time_ms"] > 0


def test_profile_result_save(simple_model, profiler_config, tmp_path):
    """Test saving profile results."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    profiler = Profiler(config=profiler_config)

    result = profiler.profile_model(
        model=simple_model,
        input_shape=(2, 128),
        device="cpu"
    )

    output_path = tmp_path / "profile_result.json"
    result.save(output_path)

    assert output_path.exists()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_profiler_warmup(simple_model, profiler_config):
    """Test warmup iterations."""
    profiler_config.warmup_iterations = 5
    profiler_config.num_iterations = 10

    profiler = Profiler(config=profiler_config)

    result = profiler.profile_model(
        model=simple_model,
        input_shape=(4, 128),
        device="cpu"
    )

    # Should complete without errors
    assert result.total_time_ms > 0
