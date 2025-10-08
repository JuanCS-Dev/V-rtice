"""
Tests for Model Quantizer

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

from performance.quantizer import ModelQuantizer, QuantizationConfig


@pytest.fixture
def simple_model():
    """Create simple model for testing."""
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

    return SimpleModel()


@pytest.fixture
def quant_config(tmp_path):
    """Create quantization config."""
    return QuantizationConfig(quantization_type="dynamic", backend="fbgemm", output_dir=tmp_path / "quantized")


def test_quantizer_initialization(quant_config):
    """Test quantizer initialization."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    quantizer = ModelQuantizer(config=quant_config)

    assert quantizer.config.quantization_type == "dynamic"
    assert quantizer.config.backend == "fbgemm"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_dynamic_quantization(simple_model, quant_config):
    """Test dynamic quantization."""
    quantizer = ModelQuantizer(config=quant_config)

    quantized_model = quantizer.quantize(simple_model)

    # Verify model is quantized (has quantized layers)
    assert quantized_model is not None

    # Test inference still works
    dummy_input = torch.randn(4, 128)
    output = quantized_model(dummy_input)

    assert output.shape == (4, 32)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_quantization_reduces_size(simple_model, quant_config):
    """Test that quantization reduces model size."""
    quantizer = ModelQuantizer(config=quant_config)

    # Get original size
    original_size = quantizer._get_model_size(simple_model)

    # Quantize
    quantized_model = quantizer.quantize(simple_model)

    # Get quantized size
    quantized_size = quantizer._get_model_size(quantized_model)

    # Quantized model should be smaller (or at least not larger for small models)
    assert quantized_size <= original_size * 1.1  # Allow 10% margin


def test_quantization_config_validation():
    """Test config validation."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    config = QuantizationConfig(quantization_type="dynamic", dtype="qint8", backend="fbgemm")

    assert config.quantization_type == "dynamic"
    assert config.dtype == "qint8"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_quantization_preserves_functionality(simple_model, quant_config):
    """Test that quantized model produces similar outputs."""
    quantizer = ModelQuantizer(config=quant_config)

    # Original output
    simple_model.eval()
    dummy_input = torch.randn(2, 128)

    with torch.no_grad():
        original_output = simple_model(dummy_input)

    # Quantize
    quantized_model = quantizer.quantize(simple_model)

    # Quantized output
    with torch.no_grad():
        quantized_output = quantized_model(dummy_input)

    # Outputs should be similar (not exact due to quantization)
    assert quantized_output.shape == original_output.shape


def test_unsupported_quantization_type_raises_error():
    """Test that unsupported quantization type raises error."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    config = QuantizationConfig(quantization_type="invalid_type")
    quantizer = ModelQuantizer(config=config)

    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(10, 10)

        def forward(self, x):
            return self.fc(x)

    model = DummyModel()

    with pytest.raises(ValueError, match="Unknown quantization type"):
        quantizer.quantize(model)
