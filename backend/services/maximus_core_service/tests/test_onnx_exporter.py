"""
Tests for ONNX Exporter

REGRA DE OURO: Zero mocks, production-ready tests
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import pytest

try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnx

    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from performance.onnx_exporter import ONNXExportConfig, ONNXExporter, ONNXExportResult


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
def export_config(tmp_path):
    """Create export config."""
    return ONNXExportConfig(
        opset_version=14,
        optimize=True,
        validate_model=True,
        test_with_random_input=False,  # Disable ONNX Runtime test
        output_dir=tmp_path / "onnx",
    )


@pytest.mark.skipif(not TORCH_AVAILABLE or not ONNX_AVAILABLE, reason="PyTorch or ONNX not available")
def test_onnx_exporter_initialization(export_config):
    """Test ONNX exporter initialization."""
    exporter = ONNXExporter(config=export_config)

    assert exporter.config.opset_version == 14
    assert exporter.config.optimize is True


@pytest.mark.skipif(not TORCH_AVAILABLE or not ONNX_AVAILABLE, reason="PyTorch or ONNX not available")
def test_export_simple_model(simple_model, export_config, tmp_path):
    """Test exporting simple model to ONNX."""
    exporter = ONNXExporter(config=export_config)

    dummy_input = torch.randn(1, 128)

    result = exporter.export(model=simple_model, dummy_input=dummy_input, output_path="simple_model.onnx")

    assert isinstance(result, ONNXExportResult)
    assert result.onnx_path.exists()
    assert result.opset_version == 14


@pytest.mark.skipif(not TORCH_AVAILABLE or not ONNX_AVAILABLE, reason="PyTorch or ONNX not available")
def test_export_result_validation(simple_model, export_config):
    """Test ONNX model validation."""
    exporter = ONNXExporter(config=export_config)

    dummy_input = torch.randn(1, 128)

    result = exporter.export(model=simple_model, dummy_input=dummy_input, output_path="validated_model.onnx")

    # Model should pass validation
    assert result.validation_passed is True


@pytest.mark.skipif(not TORCH_AVAILABLE or not ONNX_AVAILABLE, reason="PyTorch or ONNX not available")
def test_export_result_to_dict(simple_model, export_config):
    """Test export result conversion to dict."""
    exporter = ONNXExporter(config=export_config)

    dummy_input = torch.randn(1, 128)

    result = exporter.export(model=simple_model, dummy_input=dummy_input, output_path="model_dict.onnx")

    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert "onnx_path" in result_dict
    assert "opset_version" in result_dict
    assert "validation_passed" in result_dict


@pytest.mark.skipif(not TORCH_AVAILABLE or not ONNX_AVAILABLE, reason="PyTorch or ONNX not available")
def test_export_with_dynamic_axes(simple_model, export_config):
    """Test export with dynamic batch size."""
    export_config.dynamic_axes = {"input": {0: "batch_size"}, "output": {0: "batch_size"}}

    exporter = ONNXExporter(config=export_config)

    dummy_input = torch.randn(1, 128)

    result = exporter.export(model=simple_model, dummy_input=dummy_input, output_path="dynamic_model.onnx")

    assert result.validation_passed is True

    # Check that input has dynamic dimension
    assert result.input_shapes[0][0] == -1  # Dynamic batch


def test_export_config_validation():
    """Test export config validation."""
    config = ONNXExportConfig(opset_version=14, optimize=True, validate_model=True)

    assert config.opset_version == 14
    assert config.input_names == ["input"]
    assert config.output_names == ["output"]
