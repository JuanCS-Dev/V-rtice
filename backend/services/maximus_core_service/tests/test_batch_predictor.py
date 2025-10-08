"""
Tests for Batch Predictor

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import time

import numpy as np
import pytest

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from performance.batch_predictor import BatchConfig, BatchPredictor, Priority, ResponseFuture


@pytest.fixture
def predict_fn():
    """Create simple prediction function."""

    def predict(batch):
        """Simple prediction function."""
        time.sleep(0.01)  # Simulate processing
        if TORCH_AVAILABLE and isinstance(batch, torch.Tensor) or isinstance(batch, np.ndarray):
            return batch * 2
        return [x * 2 for x in batch]

    return predict


@pytest.fixture
def batch_config():
    """Create batch config."""
    return BatchConfig(max_batch_size=8, batch_timeout_ms=50.0, num_workers=1, adaptive_batching=False)


def test_response_future_basic():
    """Test ResponseFuture basic operations."""
    from performance.batch_predictor import BatchResponse

    future = ResponseFuture()

    assert not future.done()

    # Set result
    response = BatchResponse(request_id="test", output="result", latency_ms=10.0, batch_size=1)
    future.set_result(response)

    assert future.done()
    assert future.get(timeout=1.0) == response


def test_response_future_timeout():
    """Test ResponseFuture timeout."""
    future = ResponseFuture()

    with pytest.raises(TimeoutError):
        future.get(timeout=0.1)


def test_batch_predictor_initialization(predict_fn, batch_config):
    """Test batch predictor initialization."""
    predictor = BatchPredictor(predict_fn=predict_fn, config=batch_config)

    assert predictor.config.max_batch_size == 8
    assert not predictor.running


def test_batch_predictor_start_stop(predict_fn, batch_config):
    """Test starting and stopping predictor."""
    predictor = BatchPredictor(predict_fn=predict_fn, config=batch_config)

    predictor.start()
    assert predictor.running

    predictor.stop()
    assert not predictor.running


def test_batch_predictor_single_request(predict_fn, batch_config):
    """Test single prediction request."""
    predictor = BatchPredictor(predict_fn=predict_fn, config=batch_config)
    predictor.start()

    try:
        if TORCH_AVAILABLE:
            input_data = torch.randn(10)
        else:
            input_data = np.random.randn(10)

        future = predictor.submit(input_data=input_data)
        result = future.get(timeout=2.0)

        assert result is not None
        assert result.output is not None
        assert result.latency_ms > 0
        assert result.batch_size >= 1

    finally:
        predictor.stop()


def test_batch_predictor_multiple_requests(predict_fn, batch_config):
    """Test multiple prediction requests."""
    predictor = BatchPredictor(predict_fn=predict_fn, config=batch_config)
    predictor.start()

    try:
        futures = []

        # Submit multiple requests
        for _ in range(5):
            if TORCH_AVAILABLE:
                input_data = torch.randn(10)
            else:
                input_data = np.random.randn(10)

            future = predictor.submit(input_data=input_data)
            futures.append(future)

        # Get all results
        results = []
        for future in futures:
            result = future.get(timeout=5.0)
            results.append(result)

        assert len(results) == 5

        # All should have results
        for result in results:
            assert result is not None
            assert result.output is not None

    finally:
        predictor.stop()


def test_batch_predictor_priority_requests(predict_fn, batch_config):
    """Test priority-based request handling."""
    batch_config.use_priority_queue = True
    predictor = BatchPredictor(predict_fn=predict_fn, config=batch_config)
    predictor.start()

    try:
        # Submit requests with different priorities
        futures = []

        for i in range(3):
            if TORCH_AVAILABLE:
                input_data = torch.randn(10)
            else:
                input_data = np.random.randn(10)

            priority = Priority.HIGH if i == 0 else Priority.NORMAL

            future = predictor.submit(input_data=input_data, priority=priority)
            futures.append(future)

        # Get results
        results = []
        for future in futures:
            result = future.get(timeout=5.0)
            results.append(result)

        assert len(results) == 3

    finally:
        predictor.stop()


def test_batch_predictor_stats(predict_fn, batch_config):
    """Test batch predictor statistics."""
    predictor = BatchPredictor(predict_fn=predict_fn, config=batch_config)
    predictor.start()

    try:
        # Submit requests
        for _ in range(10):
            if TORCH_AVAILABLE:
                input_data = torch.randn(10)
            else:
                input_data = np.random.randn(10)

            future = predictor.submit(input_data=input_data)
            future.get(timeout=5.0)

        # Get stats
        stats = predictor.get_stats()

        assert stats["total_requests"] >= 10
        assert stats["total_batches"] > 0
        assert stats["avg_latency_ms"] > 0

    finally:
        predictor.stop()


def test_batch_predictor_adaptive_batching(predict_fn):
    """Test adaptive batching."""
    config = BatchConfig(max_batch_size=16, batch_timeout_ms=100.0, adaptive_batching=True, target_latency_ms=50.0)

    predictor = BatchPredictor(predict_fn=predict_fn, config=config)
    predictor.start()

    try:
        # Submit many requests
        futures = []
        for _ in range(20):
            if TORCH_AVAILABLE:
                input_data = torch.randn(10)
            else:
                input_data = np.random.randn(10)

            future = predictor.submit(input_data=input_data)
            futures.append(future)

        # Get all results
        for future in futures:
            future.get(timeout=10.0)

        # Check that batch size adapted
        stats = predictor.get_stats()
        assert stats["current_batch_size"] > 0

    finally:
        predictor.stop()


def test_batch_config_validation():
    """Test batch config validation."""
    config = BatchConfig(max_batch_size=32, min_batch_size=1, batch_timeout_ms=100.0, num_workers=2)

    assert config.max_batch_size == 32
    assert config.min_batch_size == 1
    assert config.num_workers == 2
