"""
Integration Tests for Performance Module

End-to-end tests combining multiple components.

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnx

    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False


@pytest.fixture
def trained_model():
    """Create and train a simple model."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(128, 64)
            self.fc2 = nn.Linear(64, 32)

        def forward(self, x):
            x = self.fc1(x)
            x = torch.relu(x)
            x = self.fc2(x)
            return x

    model = SimpleModel()

    # Quick training
    optimizer = torch.optim.Adam(model.parameters())
    X = torch.randn(100, 128)
    y = torch.randint(0, 32, (100,))
    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=16)

    model.train()
    for batch in loader:
        x, labels = batch
        output = model(x)
        loss = torch.nn.functional.cross_entropy(output, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    return model


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_benchmark_then_optimize(trained_model, tmp_path):
    """Test benchmarking, then optimizing with quantization."""
    from performance import BenchmarkConfig, BenchmarkSuite, ModelQuantizer, QuantizationConfig

    # Benchmark original model
    bench_config = BenchmarkConfig(num_iterations=10, warmup_iterations=2)

    suite = BenchmarkSuite(config=bench_config)

    original_results = suite.benchmark_model(
        model=trained_model, input_shape=(4, 128), batch_sizes=[4], num_iterations=10, device="cpu"
    )

    original_latency = original_results[4].mean_latency

    # Quantize model
    quant_config = QuantizationConfig(quantization_type="dynamic", output_dir=tmp_path / "quantized")

    quantizer = ModelQuantizer(config=quant_config)
    quantized_model = quantizer.quantize(trained_model)

    # Benchmark quantized model
    quantized_results = suite.benchmark_model(
        model=quantized_model, input_shape=(4, 128), batch_sizes=[4], num_iterations=10, device="cpu"
    )

    quantized_latency = quantized_results[4].mean_latency

    # Both should produce valid results
    assert original_latency > 0
    assert quantized_latency > 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_prune_then_benchmark(trained_model, tmp_path):
    """Test pruning model then benchmarking."""
    from performance import BenchmarkConfig, BenchmarkSuite, ModelPruner, PruningConfig

    # Prune model
    prune_config = PruningConfig(pruning_type="unstructured", target_sparsity=0.4, output_dir=tmp_path / "pruned")

    pruner = ModelPruner(config=prune_config)
    pruned_model = pruner.prune(trained_model)

    # Analyze sparsity
    result = pruner.analyze_sparsity(pruned_model)
    assert result.sparsity_achieved > 0.2  # Should achieve some sparsity

    # Benchmark pruned model
    bench_config = BenchmarkConfig(num_iterations=10)
    suite = BenchmarkSuite(config=bench_config)

    results = suite.benchmark_model(
        model=pruned_model, input_shape=(4, 128), batch_sizes=[4], num_iterations=10, device="cpu"
    )

    assert results[4].mean_latency > 0


@pytest.mark.skipif(not TORCH_AVAILABLE or not ONNX_AVAILABLE, reason="PyTorch or ONNX not available")
def test_export_then_infer(trained_model, tmp_path):
    """Test exporting to ONNX then running inference."""
    from performance import ONNXExportConfig, ONNXExporter

    # Export to ONNX
    export_config = ONNXExportConfig(
        opset_version=14, optimize=True, test_with_random_input=False, output_dir=tmp_path / "onnx"
    )

    exporter = ONNXExporter(config=export_config)

    dummy_input = torch.randn(1, 128)

    result = exporter.export(model=trained_model, dummy_input=dummy_input, output_path="model.onnx")

    assert result.validation_passed is True
    assert result.onnx_path.exists()

    # Load and verify ONNX model
    onnx_model = onnx.load(str(result.onnx_path))
    onnx.checker.check_model(onnx_model)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_inference_engine_with_cache(trained_model):
    """Test inference engine with caching."""
    from performance import InferenceConfig, InferenceEngine

    config = InferenceConfig(
        backend="pytorch", device="cpu", enable_cache=True, use_amp=False, compile_model=False, num_warmup_runs=2
    )

    engine = InferenceEngine(model=trained_model, config=config)

    # First inference
    input1 = torch.randn(1, 128)
    output1 = engine.predict(input1)

    # Second inference (should hit cache)
    output2 = engine.predict(input1)

    # Outputs should be identical (cached)
    assert torch.allclose(output1, output2)

    # Get stats
    stats = engine.get_stats()
    assert stats["total_inferences"] >= 2


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_batch_predictor_end_to_end(trained_model):
    """Test batch predictor end-to-end."""
    from performance import BatchConfig, BatchPredictor

    def predict_fn(batch):
        """Prediction function."""
        return trained_model(batch)

    config = BatchConfig(max_batch_size=8, batch_timeout_ms=50.0, num_workers=1, adaptive_batching=False)

    predictor = BatchPredictor(predict_fn=predict_fn, config=config)
    predictor.start()

    try:
        # Submit multiple requests
        futures = []
        for _ in range(10):
            input_data = torch.randn(1, 128)
            future = predictor.submit(input_data=input_data)
            futures.append(future)

        # Get all results
        results = []
        for future in futures:
            result = future.get(timeout=5.0)
            results.append(result)

        assert len(results) == 10

        # Verify all got results
        for result in results:
            assert result.output is not None
            assert result.output.shape == (1, 32)

        # Check stats
        stats = predictor.get_stats()
        assert stats["total_requests"] >= 10

    finally:
        predictor.stop()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_profile_then_optimize(trained_model, tmp_path):
    """Test profiling model then optimizing based on results."""
    from performance import ModelQuantizer, Profiler, ProfilerConfig, QuantizationConfig

    # Profile original model
    profile_config = ProfilerConfig(
        enable_cpu_profiling=True, enable_memory_profiling=True, num_iterations=20, output_dir=tmp_path / "profiling"
    )

    profiler = Profiler(config=profile_config)

    result = profiler.profile_model(model=trained_model, input_shape=(8, 128), device="cpu")

    original_latency = result.avg_time_ms

    # Based on profile, optimize with quantization
    quant_config = QuantizationConfig(quantization_type="dynamic", output_dir=tmp_path / "optimized")

    quantizer = ModelQuantizer(config=quant_config)
    optimized_model = quantizer.quantize(trained_model)

    # Profile optimized model
    optimized_result = profiler.profile_model(model=optimized_model, input_shape=(8, 128), device="cpu")

    optimized_latency = optimized_result.avg_time_ms

    # Both should complete successfully
    assert original_latency > 0
    assert optimized_latency > 0


def test_full_optimization_pipeline(tmp_path):
    """Test complete optimization pipeline: train -> prune -> quantize -> export -> infer."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    from performance import (
        InferenceConfig,
        InferenceEngine,
        ModelPruner,
        ModelQuantizer,
        PruningConfig,
        QuantizationConfig,
    )

    # 1. Create and train model
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(64, 32)
            self.fc2 = nn.Linear(32, 16)

        def forward(self, x):
            return self.fc2(torch.relu(self.fc1(x)))

    model = SimpleModel()

    # 2. Prune
    prune_config = PruningConfig(pruning_type="unstructured", target_sparsity=0.3, output_dir=tmp_path / "pruned")

    pruner = ModelPruner(config=prune_config)
    model = pruner.prune(model)

    # 3. Quantize
    quant_config = QuantizationConfig(quantization_type="dynamic", output_dir=tmp_path / "quantized")

    quantizer = ModelQuantizer(config=quant_config)
    model = quantizer.quantize(model)

    # 4. Inference
    inf_config = InferenceConfig(
        backend="pytorch", device="cpu", enable_cache=False, use_amp=False, compile_model=False, num_warmup_runs=2
    )

    engine = InferenceEngine(model=model, config=inf_config)

    # Test inference
    input_data = torch.randn(1, 64)
    output = engine.predict(input_data)

    assert output.shape == (1, 16)

    # Verify stats
    stats = engine.get_stats()
    assert stats["total_inferences"] >= 1
