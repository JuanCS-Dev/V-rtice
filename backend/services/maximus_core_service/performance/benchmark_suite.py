"""
Benchmarking Suite for MAXIMUS Models

Comprehensive performance benchmarking:
- Inference latency measurement
- Throughput calculation
- Memory profiling
- GPU utilization tracking
- Multi-batch benchmarking
- Comparative analysis

REGRA DE OURO: Zero mocks, production-ready benchmarking
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# Try to import psutil for system metrics
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """Metrics from a single benchmark run."""

    # Latency metrics (milliseconds)
    mean_latency: float
    median_latency: float
    p95_latency: float
    p99_latency: float
    min_latency: float
    max_latency: float
    std_latency: float

    # Throughput metrics
    throughput_samples_per_sec: float
    throughput_batches_per_sec: float

    # Memory metrics (MB)
    peak_memory_mb: float | None = None
    avg_memory_mb: float | None = None

    # GPU metrics (if available)
    gpu_utilization_percent: float | None = None
    gpu_memory_mb: float | None = None

    # Additional info
    batch_size: int = 1
    num_iterations: int = 100
    device: str = "cpu"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "latency": {
                "mean_ms": self.mean_latency,
                "median_ms": self.median_latency,
                "p95_ms": self.p95_latency,
                "p99_ms": self.p99_latency,
                "min_ms": self.min_latency,
                "max_ms": self.max_latency,
                "std_ms": self.std_latency,
            },
            "throughput": {
                "samples_per_sec": self.throughput_samples_per_sec,
                "batches_per_sec": self.throughput_batches_per_sec,
            },
            "memory": {"peak_mb": self.peak_memory_mb, "avg_mb": self.avg_memory_mb},
            "gpu": {"utilization_percent": self.gpu_utilization_percent, "memory_mb": self.gpu_memory_mb},
            "config": {"batch_size": self.batch_size, "num_iterations": self.num_iterations, "device": self.device},
        }


@dataclass
class BenchmarkResult:
    """Complete benchmark results."""

    model_name: str
    timestamp: datetime
    metrics: BenchmarkMetrics
    hardware_info: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics.to_dict(),
            "hardware_info": self.hardware_info,
        }

    def save(self, output_path: Path):
        """Save results to JSON file.

        Args:
            output_path: Path to save results
        """
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Benchmark results saved to {output_path}")


class BenchmarkSuite:
    """Comprehensive benchmarking suite for models.

    Features:
    - Latency measurement (warmup, multiple iterations)
    - Throughput calculation
    - Memory profiling
    - GPU utilization tracking
    - Multi-batch size testing
    - Comparative analysis

    Example:
        ```python
        import torch

        model = MyModel()
        suite = BenchmarkSuite()

        # Benchmark single configuration
        result = suite.benchmark_model(
            model=model, input_shape=(1, 128), batch_sizes=[1, 8, 32, 64], num_iterations=1000, device="cuda"
        )

        suite.print_report(result)
        result.save("benchmark_results.json")
        ```
    """

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: list[BenchmarkResult] = []

        # Get hardware info
        self.hardware_info = self._get_hardware_info()

        logger.info("BenchmarkSuite initialized")

    def benchmark_model(
        self,
        model: Any,
        input_shape: tuple[int, ...],
        batch_sizes: list[int] = [1, 8, 32, 64],
        num_iterations: int = 1000,
        warmup_iterations: int = 100,
        device: str = "cpu",
    ) -> dict[int, BenchmarkMetrics]:
        """Benchmark model across multiple batch sizes.

        Args:
            model: Model to benchmark
            input_shape: Input tensor shape (excluding batch dimension)
            batch_sizes: List of batch sizes to test
            num_iterations: Number of iterations per batch size
            warmup_iterations: Number of warmup iterations
            device: Device to run on ("cpu" or "cuda")

        Returns:
            Dictionary mapping batch_size to BenchmarkMetrics
        """
        logger.info(f"Benchmarking model on {device} with batch sizes {batch_sizes}")

        # Move model to device
        model = self._prepare_model(model, device)

        results = {}

        for batch_size in batch_sizes:
            logger.info(f"Benchmarking batch_size={batch_size}")

            metrics = self._benchmark_single_config(
                model=model,
                input_shape=input_shape,
                batch_size=batch_size,
                num_iterations=num_iterations,
                warmup_iterations=warmup_iterations,
                device=device,
            )

            results[batch_size] = metrics

            # Log results
            logger.info(f"  Mean latency: {metrics.mean_latency:.2f} ms")
            logger.info(f"  Throughput: {metrics.throughput_samples_per_sec:.0f} samples/sec")

        return results

    def _benchmark_single_config(
        self,
        model: Any,
        input_shape: tuple[int, ...],
        batch_size: int,
        num_iterations: int,
        warmup_iterations: int,
        device: str,
    ) -> BenchmarkMetrics:
        """Benchmark single configuration.

        Args:
            model: Model to benchmark
            input_shape: Input shape
            batch_size: Batch size
            num_iterations: Number of iterations
            warmup_iterations: Warmup iterations
            device: Device

        Returns:
            BenchmarkMetrics
        """
        # Create dummy input
        full_input_shape = (batch_size,) + input_shape
        dummy_input = self._create_dummy_input(full_input_shape, device)

        # Warmup
        logger.debug(f"Warmup: {warmup_iterations} iterations")
        for _ in range(warmup_iterations):
            _ = self._run_inference(model, dummy_input)

        # Benchmark
        latencies = []
        memory_usage = []

        for i in range(num_iterations):
            # Memory before
            mem_before = self._get_memory_usage()

            # Run inference and measure time
            start = time.perf_counter()
            _ = self._run_inference(model, dummy_input)
            end = time.perf_counter()

            # Memory after
            mem_after = self._get_memory_usage()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

            if mem_before is not None and mem_after is not None:
                memory_usage.append(mem_after - mem_before)

        # Calculate statistics
        latencies = np.array(latencies)

        mean_latency = float(np.mean(latencies))
        median_latency = float(np.median(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        p99_latency = float(np.percentile(latencies, 99))
        min_latency = float(np.min(latencies))
        max_latency = float(np.max(latencies))
        std_latency = float(np.std(latencies))

        # Throughput
        throughput_samples_per_sec = (batch_size * 1000) / mean_latency
        throughput_batches_per_sec = 1000 / mean_latency

        # Memory statistics
        peak_memory_mb = None
        avg_memory_mb = None
        if memory_usage:
            peak_memory_mb = float(max(memory_usage))
            avg_memory_mb = float(np.mean(memory_usage))

        # GPU metrics
        gpu_utilization = None
        gpu_memory = None

        if device == "cuda":
            gpu_utilization, gpu_memory = self._get_gpu_metrics()

        return BenchmarkMetrics(
            mean_latency=mean_latency,
            median_latency=median_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            std_latency=std_latency,
            throughput_samples_per_sec=throughput_samples_per_sec,
            throughput_batches_per_sec=throughput_batches_per_sec,
            peak_memory_mb=peak_memory_mb,
            avg_memory_mb=avg_memory_mb,
            gpu_utilization_percent=gpu_utilization,
            gpu_memory_mb=gpu_memory,
            batch_size=batch_size,
            num_iterations=num_iterations,
            device=device,
        )

    def _prepare_model(self, model: Any, device: str) -> Any:
        """Prepare model for benchmarking.

        Args:
            model: Model
            device: Device

        Returns:
            Prepared model
        """
        try:
            # Try PyTorch model
            import torch

            if hasattr(model, "eval"):
                model.eval()

            if hasattr(model, "to"):
                model = model.to(device)

            # Disable gradient computation
            if hasattr(torch, "no_grad"):
                return model

        except ImportError:
            pass

        return model

    def _create_dummy_input(self, shape: tuple[int, ...], device: str) -> Any:
        """Create dummy input tensor.

        Args:
            shape: Input shape
            device: Device

        Returns:
            Dummy input
        """
        try:
            import torch

            return torch.randn(shape, device=device)
        except ImportError:
            return np.random.randn(*shape).astype(np.float32)

    def _run_inference(self, model: Any, input_tensor: Any) -> Any:
        """Run inference.

        Args:
            model: Model
            input_tensor: Input

        Returns:
            Output
        """
        try:
            import torch

            with torch.no_grad():
                output = model(input_tensor)

            # Synchronize for accurate timing
            if hasattr(torch.cuda, "synchronize"):
                torch.cuda.synchronize()

            return output

        except ImportError:
            # Fallback for non-PyTorch models
            if hasattr(model, "predict"):
                return model.predict(input_tensor)
            return model(input_tensor)

    def _get_memory_usage(self) -> float | None:
        """Get current memory usage in MB.

        Returns:
            Memory usage in MB or None
        """
        if not PSUTIL_AVAILABLE:
            return None

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def _get_gpu_metrics(self) -> tuple[float | None, float | None]:
        """Get GPU utilization and memory.

        Returns:
            Tuple of (utilization_percent, memory_mb)
        """
        try:
            import torch

            if torch.cuda.is_available():
                utilization = torch.cuda.utilization()
                memory_allocated = torch.cuda.memory_allocated() / (1024 * 1024)
                return float(utilization), float(memory_allocated)

        except ImportError:
            logger.debug("PyTorch not available for GPU monitoring")
        except Exception as e:
            logger.debug(f"GPU monitoring failed: {e}")

        return None, None

    def _get_hardware_info(self) -> dict[str, Any]:
        """Get hardware information.

        Returns:
            Hardware info dictionary
        """
        info = {}

        # CPU info
        if PSUTIL_AVAILABLE:
            info["cpu_count"] = psutil.cpu_count()
            info["cpu_freq_mhz"] = psutil.cpu_freq().current if psutil.cpu_freq() else None
            info["total_memory_gb"] = psutil.virtual_memory().total / (1024**3)

        # GPU info
        try:
            import torch

            if torch.cuda.is_available():
                info["gpu_available"] = True
                info["gpu_count"] = torch.cuda.device_count()
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            else:
                info["gpu_available"] = False

        except ImportError:
            info["gpu_available"] = False

        return info

    def print_report(self, results: dict[int, BenchmarkMetrics]):
        """Print benchmark report.

        Args:
            results: Benchmark results
        """
        print("\n" + "=" * 80)
        print("BENCHMARK REPORT")
        print("=" * 80)

        # Hardware info
        print("\nHardware:")
        for key, value in self.hardware_info.items():
            print(f"  {key}: {value}")

        # Results by batch size
        print("\nResults by Batch Size:")
        print("-" * 80)
        print(f"{'Batch':>8} {'Mean(ms)':>12} {'P95(ms)':>12} {'P99(ms)':>12} {'Throughput(samp/s)':>20}")
        print("-" * 80)

        for batch_size, metrics in sorted(results.items()):
            print(
                f"{batch_size:>8} {metrics.mean_latency:>12.2f} {metrics.p95_latency:>12.2f} "
                f"{metrics.p99_latency:>12.2f} {metrics.throughput_samples_per_sec:>20.0f}"
            )

        print("=" * 80)

    def compare_models(
        self,
        models: dict[str, Any],
        input_shape: tuple[int, ...],
        batch_size: int = 32,
        num_iterations: int = 1000,
        device: str = "cpu",
    ) -> dict[str, BenchmarkMetrics]:
        """Compare multiple models.

        Args:
            models: Dictionary mapping model_name to model
            input_shape: Input shape
            batch_size: Batch size
            num_iterations: Number of iterations
            device: Device

        Returns:
            Dictionary mapping model_name to BenchmarkMetrics
        """
        logger.info(f"Comparing {len(models)} models")

        results = {}

        for model_name, model in models.items():
            logger.info(f"Benchmarking {model_name}")

            model = self._prepare_model(model, device)

            metrics = self._benchmark_single_config(
                model=model,
                input_shape=input_shape,
                batch_size=batch_size,
                num_iterations=num_iterations,
                warmup_iterations=100,
                device=device,
            )

            results[model_name] = metrics

        # Print comparison
        self.print_comparison(results)

        return results

    def print_comparison(self, results: dict[str, BenchmarkMetrics]):
        """Print model comparison.

        Args:
            results: Results dictionary
        """
        print("\n" + "=" * 80)
        print("MODEL COMPARISON")
        print("=" * 80)

        print(f"\n{'Model':>20} {'Mean Latency(ms)':>20} {'Throughput(samp/s)':>20} {'Memory(MB)':>15}")
        print("-" * 80)

        for model_name, metrics in sorted(results.items(), key=lambda x: x[1].mean_latency):
            mem_str = f"{metrics.peak_memory_mb:.1f}" if metrics.peak_memory_mb else "N/A"
            print(
                f"{model_name:>20} {metrics.mean_latency:>20.2f} "
                f"{metrics.throughput_samples_per_sec:>20.0f} {mem_str:>15}"
            )

        print("=" * 80)


# =============================================================================
# CLI
# =============================================================================


def main():
    """Main benchmark script."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark MAXIMUS Models")

    parser.add_argument("--model_path", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--input_shape", type=str, default="128", help="Input shape (comma-separated)")
    parser.add_argument("--batch_sizes", type=str, default="1,8,32,64", help="Batch sizes (comma-separated)")
    parser.add_argument("--num_iterations", type=int, default=1000, help="Number of iterations")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu/cuda)")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Output file")

    args = parser.parse_args()

    # Parse input shape
    input_shape = tuple(int(x) for x in args.input_shape.split(","))
    batch_sizes = [int(x) for x in args.batch_sizes.split(",")]

    # Load model (example for PyTorch)
    try:
        import torch

        model = torch.load(args.model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    # Create suite
    suite = BenchmarkSuite()

    # Benchmark
    results = suite.benchmark_model(
        model=model,
        input_shape=input_shape,
        batch_sizes=batch_sizes,
        num_iterations=args.num_iterations,
        device=args.device,
    )

    # Print report
    suite.print_report(results)

    # Save results
    for batch_size, metrics in results.items():
        result = BenchmarkResult(
            model_name=Path(args.model_path).stem,
            timestamp=datetime.utcnow(),
            metrics=metrics,
            hardware_info=suite.hardware_info,
        )

        output_path = Path(args.output).parent / f"{Path(args.output).stem}_bs{batch_size}.json"
        result.save(output_path)


if __name__ == "__main__":
    main()
