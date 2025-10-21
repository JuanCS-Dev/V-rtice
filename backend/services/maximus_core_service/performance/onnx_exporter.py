"""
ONNX Model Exporter for MAXIMUS

Export PyTorch models to ONNX format for optimized inference:
- PyTorch to ONNX conversion
- Model optimization (constant folding, operator fusion)
- Shape inference and validation
- Dynamic axes support
- Opset version management
- Model validation and testing

REGRA DE OURO: Zero mocks, production-ready ONNX export
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations


import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

# Try to import ONNX
try:
    import onnx
    from onnx import numpy_helper

    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    if TYPE_CHECKING:
        import torch
        import torch.nn as nn

logger = logging.getLogger(__name__)


@dataclass
class ONNXExportConfig:
    """ONNX export configuration."""

    # Export options
    opset_version: int = 14  # ONNX opset version
    do_constant_folding: bool = True
    optimize: bool = True

    # Input/Output
    input_names: list[str] = None
    output_names: list[str] = None
    dynamic_axes: dict[str, dict[int, str]] = None

    # Validation
    validate_model: bool = True
    test_with_random_input: bool = True

    # Output
    output_dir: Path = Path("models/onnx")

    def __post_init__(self):
        """Set defaults."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.input_names is None:
            self.input_names = ["input"]

        if self.output_names is None:
            self.output_names = ["output"]

        if self.dynamic_axes is None:
            self.dynamic_axes = {}


@dataclass
class ONNXExportResult:
    """ONNX export result."""

    # Export info
    onnx_path: Path
    opset_version: int

    # Model info
    num_parameters: int
    model_size_mb: float

    # Input/Output shapes
    input_shapes: list[tuple[int, ...]]
    output_shapes: list[tuple[int, ...]]

    # Validation
    validation_passed: bool
    inference_test_passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "onnx_path": str(self.onnx_path),
            "opset_version": self.opset_version,
            "num_parameters": self.num_parameters,
            "model_size_mb": self.model_size_mb,
            "input_shapes": [list(s) for s in self.input_shapes],
            "output_shapes": [list(s) for s in self.output_shapes],
            "validation_passed": self.validation_passed,
            "inference_test_passed": self.inference_test_passed,
        }


class ONNXExporter:
    """ONNX model exporter.

    Features:
    - PyTorch to ONNX conversion
    - Model optimization (constant folding, fusion)
    - Dynamic axes for variable input sizes
    - Model validation with ONNX checker
    - Inference testing to verify correctness
    - Shape inference

    Example:
        ```python
        # Simple export
        config = ONNXExportConfig(opset_version=14, optimize=True)

        exporter = ONNXExporter(config=config)
        result = exporter.export(model=model, dummy_input=torch.randn(1, 3, 224, 224), output_path="model.onnx")

        # Export with dynamic axes (batch size)
        config = ONNXExportConfig(dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}})

        exporter = ONNXExporter(config=config)
        result = exporter.export(model=model, dummy_input=torch.randn(1, 3, 224, 224), output_path="model_dynamic.onnx")
        ```
    """

    def __init__(self, config: ONNXExportConfig = ONNXExportConfig()):
        """Initialize exporter.

        Args:
            config: ONNX export configuration
        """
        if not ONNX_AVAILABLE:
            raise ImportError("ONNX is required. Install with: pip install onnx")

        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required. Install with: pip install torch")

        self.config = config

        logger.info(f"ONNXExporter initialized: opset={config.opset_version}")

    def export(self, model: nn.Module, dummy_input: torch.Tensor, output_path: str) -> ONNXExportResult:
        """Export PyTorch model to ONNX.

        Args:
            model: PyTorch model
            dummy_input: Example input tensor
            output_path: Output ONNX file path

        Returns:
            ONNXExportResult
        """
        output_path = self.config.output_dir / output_path

        logger.info(f"Exporting model to ONNX: {output_path}")

        # Set model to eval mode
        model.eval()

        # Export to ONNX
        with torch.no_grad():
            torch.onnx.export(
                model,
                dummy_input,
                str(output_path),
                export_params=True,
                opset_version=self.config.opset_version,
                do_constant_folding=self.config.do_constant_folding,
                input_names=self.config.input_names,
                output_names=self.config.output_names,
                dynamic_axes=self.config.dynamic_axes,
                verbose=False,
            )

        logger.info(f"Model exported to {output_path}")

        # Load ONNX model
        onnx_model = onnx.load(str(output_path))

        # Optimize
        if self.config.optimize:
            onnx_model = self._optimize_model(onnx_model)
            onnx.save(onnx_model, str(output_path))
            logger.info("Model optimized")

        # Validate
        validation_passed = False
        if self.config.validate_model:
            validation_passed = self._validate_model(onnx_model)

        # Test inference
        inference_test_passed = False
        if self.config.test_with_random_input:
            inference_test_passed = self._test_inference(model, onnx_model, dummy_input)

        # Get model info
        model_info = self._get_model_info(onnx_model, output_path)

        result = ONNXExportResult(
            onnx_path=output_path,
            opset_version=self.config.opset_version,
            validation_passed=validation_passed,
            inference_test_passed=inference_test_passed,
            **model_info,
        )

        logger.info("Export complete")

        return result

    def _optimize_model(self, onnx_model: Any) -> Any:
        """Optimize ONNX model.

        Args:
            onnx_model: ONNX model

        Returns:
            Optimized ONNX model
        """
        from onnx import optimizer

        # Available optimizations
        passes = [
            "eliminate_deadend",
            "eliminate_identity",
            "eliminate_nop_dropout",
            "eliminate_nop_monotone_argmax",
            "eliminate_nop_pad",
            "extract_constant_to_initializer",
            "eliminate_unused_initializer",
            "fuse_add_bias_into_conv",
            "fuse_bn_into_conv",
            "fuse_consecutive_concats",
            "fuse_consecutive_reduce_unsqueeze",
            "fuse_consecutive_squeezes",
            "fuse_consecutive_transposes",
            "fuse_matmul_add_bias_into_gemm",
            "fuse_pad_into_conv",
            "fuse_transpose_into_gemm",
        ]

        logger.debug(f"Applying {len(passes)} optimization passes")

        optimized_model = optimizer.optimize(onnx_model, passes)

        return optimized_model

    def _validate_model(self, onnx_model: Any) -> bool:
        """Validate ONNX model.

        Args:
            onnx_model: ONNX model

        Returns:
            True if valid
        """
        try:
            onnx.checker.check_model(onnx_model)
            logger.info("Model validation: PASSED")
            return True

        except Exception as e:
            logger.error(f"Model validation: FAILED - {e}")
            return False

    def _test_inference(self, pytorch_model: nn.Module, onnx_model: Any, dummy_input: torch.Tensor) -> bool:
        """Test ONNX inference against PyTorch.

        Args:
            pytorch_model: Original PyTorch model
            onnx_model: ONNX model
            dummy_input: Test input

        Returns:
            True if outputs match
        """
        try:
            import onnxruntime as ort

            # PyTorch inference
            pytorch_model.eval()
            with torch.no_grad():
                pytorch_output = pytorch_model(dummy_input)

            if isinstance(pytorch_output, tuple):
                pytorch_output = pytorch_output[0]

            pytorch_output = pytorch_output.cpu().numpy()

            # ONNX inference
            session = ort.InferenceSession(onnx_model.SerializeToString(), providers=["CPUExecutionProvider"])

            onnx_input = {self.config.input_names[0]: dummy_input.cpu().numpy()}
            onnx_output = session.run(None, onnx_input)[0]

            # Compare outputs
            max_diff = np.abs(pytorch_output - onnx_output).max()

            if max_diff < 1e-5:
                logger.info(f"Inference test: PASSED (max diff: {max_diff:.2e})")
                return True
            logger.warning(f"Inference test: FAILED (max diff: {max_diff:.2e})")
            return False

        except ImportError:
            logger.warning("onnxruntime not available, skipping inference test")
            return False

        except Exception as e:
            logger.error(f"Inference test failed: {e}")
            return False

    def _get_model_info(self, onnx_model: Any, model_path: Path) -> dict[str, Any]:
        """Get ONNX model information.

        Args:
            onnx_model: ONNX model
            model_path: Path to ONNX file

        Returns:
            Model info dictionary
        """
        # Count parameters
        num_params = 0
        for initializer in onnx_model.graph.initializer:
            tensor = numpy_helper.to_array(initializer)
            num_params += tensor.size

        # Get file size
        model_size_mb = model_path.stat().st_size / (1024 * 1024)

        # Get input shapes
        input_shapes = []
        for input_tensor in onnx_model.graph.input:
            shape = []
            for dim in input_tensor.type.tensor_type.shape.dim:
                if dim.dim_value:
                    shape.append(dim.dim_value)
                else:
                    shape.append(-1)  # Dynamic dimension
            input_shapes.append(tuple(shape))

        # Get output shapes
        output_shapes = []
        for output_tensor in onnx_model.graph.output:
            shape = []
            for dim in output_tensor.type.tensor_type.shape.dim:
                if dim.dim_value:
                    shape.append(dim.dim_value)
                else:
                    shape.append(-1)  # Dynamic dimension
            output_shapes.append(tuple(shape))

        return {
            "num_parameters": num_params,
            "model_size_mb": model_size_mb,
            "input_shapes": input_shapes,
            "output_shapes": output_shapes,
        }

    def print_report(self, result: ONNXExportResult):
        """Print export report.

        Args:
            result: Export result
        """
        print("\n" + "=" * 80)
        print("ONNX EXPORT REPORT")
        print("=" * 80)

        print("\nModel Info:")
        print(f"  ONNX file: {result.onnx_path}")
        print(f"  Opset version: {result.opset_version}")
        print(f"  Model size: {result.model_size_mb:.2f} MB")
        print(f"  Parameters: {result.num_parameters:,}")

        print("\nInput Shapes:")
        for i, shape in enumerate(result.input_shapes):
            shape_str = str(shape).replace("-1", "dynamic")
            print(f"  {self.config.input_names[i]}: {shape_str}")

        print("\nOutput Shapes:")
        for i, shape in enumerate(result.output_shapes):
            shape_str = str(shape).replace("-1", "dynamic")
            print(f"  {self.config.output_names[i]}: {shape_str}")

        print("\nValidation:")
        print(f"  Model validation: {'✓ PASSED' if result.validation_passed else '✗ FAILED'}")
        print(f"  Inference test: {'✓ PASSED' if result.inference_test_passed else '✗ FAILED'}")

        print("=" * 80)


# =============================================================================
# Utility Functions
# =============================================================================


def simplify_onnx_model(input_path: str, output_path: str) -> bool:
    """Simplify ONNX model using onnx-simplifier.

    Args:
        input_path: Input ONNX file
        output_path: Output ONNX file

    Returns:
        True if successful
    """
    try:
        from onnxsim import simplify

        # Load model
        model = onnx.load(input_path)

        # Simplify
        simplified_model, check = simplify(model)

        if check:
            # Save simplified model
            onnx.save(simplified_model, output_path)
            logger.info(f"Model simplified and saved to {output_path}")
            return True
        logger.warning("Model simplification failed validation")
        return False

    except ImportError:
        logger.warning("onnx-simplifier not available. Install with: pip install onnx-simplifier")
        return False

    except Exception as e:
        logger.error(f"Simplification failed: {e}")
        return False


def convert_to_onnx_with_quantization(
    model: nn.Module, dummy_input: torch.Tensor, output_path: str, quantization_type: str = "dynamic"
) -> bool:
    """Export model to ONNX with quantization.

    Args:
        model: PyTorch model
        dummy_input: Example input
        output_path: Output path
        quantization_type: "dynamic" or "static"

    Returns:
        True if successful
    """
    try:
        # First export to ONNX
        exporter = ONNXExporter()
        result = exporter.export(model, dummy_input, output_path)

        if not result.validation_passed:
            logger.error("ONNX export failed validation")
            return False

        # Quantize ONNX model
        from onnxruntime.quantization import QuantType, quantize_dynamic

        quantized_path = output_path.replace(".onnx", "_quantized.onnx")

        if quantization_type == "dynamic":
            quantize_dynamic(str(result.onnx_path), quantized_path, weight_type=QuantType.QUInt8)

            logger.info(f"Quantized model saved to {quantized_path}")
            return True

        logger.warning(f"Quantization type {quantization_type} not implemented")
        return False

    except ImportError:
        logger.warning("onnxruntime not available for quantization")
        return False

    except Exception as e:
        logger.error(f"Quantization failed: {e}")
        return False


# =============================================================================
# CLI
# =============================================================================


def main():
    """Main ONNX export script."""
    import argparse

    parser = argparse.ArgumentParser(description="Export MAXIMUS Models to ONNX")

    parser.add_argument("--model_path", type=str, required=True, help="Path to PyTorch model")
    parser.add_argument("--input_shape", type=str, default="1,3,224,224", help="Input shape (comma-separated)")
    parser.add_argument("--output", type=str, default="model.onnx", help="Output ONNX filename")
    parser.add_argument("--opset_version", type=int, default=14, help="ONNX opset version")
    parser.add_argument("--optimize", action="store_true", help="Optimize ONNX model")
    parser.add_argument("--dynamic_batch", action="store_true", help="Use dynamic batch size")

    args = parser.parse_args()

    # Parse input shape
    input_shape = tuple(int(x) for x in args.input_shape.split(","))

    # Load model
    try:
        model = torch.load(args.model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    # Create dummy input
    dummy_input = torch.randn(input_shape)

    # Configure dynamic axes
    dynamic_axes = None
    if args.dynamic_batch:
        dynamic_axes = {"input": {0: "batch_size"}, "output": {0: "batch_size"}}

    # Create exporter
    config = ONNXExportConfig(opset_version=args.opset_version, optimize=args.optimize, dynamic_axes=dynamic_axes)

    exporter = ONNXExporter(config=config)

    # Export
    result = exporter.export(model=model, dummy_input=dummy_input, output_path=args.output)

    # Print report
    exporter.print_report(result)


if __name__ == "__main__":
    main()
