"""
Performance Module - Targeted Coverage Tests

Objetivo: Cobrir performance/__init__.py (65 lines, 0% → 90%+)

Testa exports, __all__, metadata

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
"""

import pytest


def test_performance_module_imports():
    import performance
    assert performance is not None


def test_version():
    import performance
    assert performance.__version__ == "1.0.0"


def test_author():
    import performance
    assert "Claude Code" in performance.__author__


def test_regra_de_ouro():
    import performance
    assert performance.__regra_de_ouro__ == "10/10"


# Benchmarking exports
def test_exports_benchmark_suite():
    from performance import BenchmarkSuite
    assert BenchmarkSuite is not None


def test_exports_benchmark_result():
    from performance import BenchmarkResult
    assert BenchmarkResult is not None


def test_exports_benchmark_metrics():
    from performance import BenchmarkMetrics
    assert BenchmarkMetrics is not None


# Profiling exports
def test_exports_profiler():
    from performance import Profiler
    assert Profiler is not None


def test_exports_profile_result():
    from performance import ProfileResult
    assert ProfileResult is not None


# GPU Training
def test_exports_gpu_trainer():
    from performance import GPUTrainer
    assert GPUTrainer is not None


# Distributed Training
def test_exports_distributed_trainer():
    from performance import DistributedTrainer
    assert DistributedTrainer is not None


# Quantization
def test_exports_model_quantizer():
    from performance import ModelQuantizer
    assert ModelQuantizer is not None


# Pruning
def test_exports_model_pruner():
    from performance import ModelPruner
    assert ModelPruner is not None


# ONNX
def test_exports_onnx_exporter():
    from performance import ONNXExporter
    assert ONNXExporter is not None


# Inference
def test_exports_inference_engine():
    from performance import InferenceEngine
    assert InferenceEngine is not None


# Batch Prediction
def test_exports_batch_predictor():
    from performance import BatchPredictor
    assert BatchPredictor is not None


def test_exports_priority():
    from performance import Priority
    assert Priority is not None


def test_all_exports():
    import performance
    assert len(performance.__all__) == 21


def test_all_exports_importable():
    import performance
    for name in performance.__all__:
        assert hasattr(performance, name)
