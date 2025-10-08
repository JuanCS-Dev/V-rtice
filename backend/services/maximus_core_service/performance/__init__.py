"""
Performance & Optimization Tools for MAXIMUS

GPU acceleration, model optimization, and inference acceleration:
- Benchmarking suite
- GPU training
- Distributed training
- Model quantization
- Model pruning
- ONNX export
- Inference engines

REGRA DE OURO: Zero mocks, production-ready optimization
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from .batch_predictor import BatchConfig, BatchPredictor, Priority
from .benchmark_suite import BenchmarkMetrics, BenchmarkResult, BenchmarkSuite
from .distributed_trainer import DistributedConfig, DistributedTrainer
from .gpu_trainer import GPUTrainer, GPUTrainingConfig
from .inference_engine import InferenceConfig, InferenceEngine
from .onnx_exporter import ONNXExportConfig, ONNXExporter, ONNXExportResult
from .profiler import Profiler, ProfilerConfig, ProfileResult
from .pruner import ModelPruner, PruningConfig, PruningResult
from .quantizer import ModelQuantizer, QuantizationConfig

__all__ = [
    # Benchmarking
    "BenchmarkSuite",
    "BenchmarkResult",
    "BenchmarkMetrics",
    # Profiling
    "Profiler",
    "ProfileResult",
    "ProfilerConfig",
    # GPU Training
    "GPUTrainer",
    "GPUTrainingConfig",
    # Distributed Training
    "DistributedTrainer",
    "DistributedConfig",
    # Quantization
    "ModelQuantizer",
    "QuantizationConfig",
    # Pruning
    "ModelPruner",
    "PruningConfig",
    "PruningResult",
    # ONNX Export
    "ONNXExporter",
    "ONNXExportConfig",
    "ONNXExportResult",
    # Inference
    "InferenceEngine",
    "InferenceConfig",
    # Batch Prediction
    "BatchPredictor",
    "BatchConfig",
    "Priority",
]

__version__ = "1.0.0"
__author__ = "Claude Code + JuanCS-Dev"
__regra_de_ouro__ = "10/10"
