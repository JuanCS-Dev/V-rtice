"""
Tests for Inference Engine

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest
import numpy as np

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from performance.inference_engine import InferenceEngine, InferenceConfig, LRUCache


@pytest.fixture
def simple_model():
    """Create simple model for testing."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(128, 64)

        def forward(self, x):
            return self.fc(x)

    return SimpleModel()


@pytest.fixture
def inference_config():
    """Create inference config."""
    return InferenceConfig(
        backend="pytorch",
        device="cpu",
        enable_cache=True,
        use_amp=False,  # Disable AMP for CPU
        compile_model=False,  # Disable compile for compatibility
        num_warmup_runs=2
    )


def test_lru_cache_basic_operations():
    """Test LRU cache basic operations."""
    cache = LRUCache(max_size=3)

    # Put items
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")

    # Get items
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert cache.get("key4") is None

    # Check stats
    stats = cache.get_stats()
    assert stats["hits"] == 3
    assert stats["misses"] == 1


def test_lru_cache_eviction():
    """Test LRU cache eviction."""
    cache = LRUCache(max_size=2)

    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")  # Should evict key1

    assert cache.get("key1") is None  # Evicted
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_lru_cache_clear():
    """Test cache clearing."""
    cache = LRUCache(max_size=10)

    cache.put("key1", "value1")
    cache.put("key2", "value2")

    cache.clear()

    assert cache.get("key1") is None
    assert cache.get("key2") is None
    assert cache.get_stats()["size"] == 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_inference_engine_initialization(simple_model, inference_config):
    """Test inference engine initialization."""
    engine = InferenceEngine(model=simple_model, config=inference_config)

    assert engine.config.backend == "pytorch"
    assert engine.config.device == "cpu"
    assert engine.cache is not None


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_single_inference(simple_model, inference_config):
    """Test single inference."""
    engine = InferenceEngine(model=simple_model, config=inference_config)

    input_tensor = torch.randn(1, 128)
    output = engine.predict(input_tensor)

    assert output.shape == (1, 64)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_batch_inference(simple_model, inference_config):
    """Test batch inference."""
    engine = InferenceEngine(model=simple_model, config=inference_config)

    inputs = [torch.randn(1, 128) for _ in range(5)]
    outputs = engine.predict_batch(inputs)

    assert len(outputs) == 5
    for output in outputs:
        assert output.shape == (1, 64)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_inference_caching(simple_model, inference_config):
    """Test inference result caching."""
    engine = InferenceEngine(model=simple_model, config=inference_config)

    input_tensor = torch.randn(1, 128)

    # First inference
    output1 = engine.predict(input_tensor)

    # Second inference (should hit cache)
    output2 = engine.predict(input_tensor)

    # Outputs should be identical (cached)
    assert torch.allclose(output1, output2)

    # Check cache stats
    stats = engine.get_stats()
    if "cache" in stats:
        assert stats["cache"]["hits"] >= 1


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_inference_stats(simple_model, inference_config):
    """Test inference statistics."""
    engine = InferenceEngine(model=simple_model, config=inference_config)

    # Run some inferences
    for _ in range(5):
        input_tensor = torch.randn(1, 128)
        engine.predict(input_tensor)

    stats = engine.get_stats()

    assert stats["total_inferences"] >= 5
    assert stats["avg_latency_ms"] > 0
    assert stats["backend"] == "pytorch"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_cache_clear(simple_model, inference_config):
    """Test cache clearing."""
    engine = InferenceEngine(model=simple_model, config=inference_config)

    input_tensor = torch.randn(1, 128)
    engine.predict(input_tensor)

    # Clear cache
    engine.clear_cache()

    # Predict again (should miss cache)
    engine.predict(input_tensor)

    stats = engine.get_stats()
    if "cache" in stats:
        assert stats["cache"]["misses"] >= 1


def test_inference_config_validation():
    """Test inference config validation."""
    config = InferenceConfig(
        backend="pytorch",
        device="cpu",
        max_batch_size=32,
        enable_cache=True
    )

    assert config.backend == "pytorch"
    assert config.max_batch_size == 32
    assert config.enable_cache is True
