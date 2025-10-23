"""
Layer 1 Sensory - Targeted Coverage Tests

Objetivo: Cobrir consciousness/predictive_coding/layer1_sensory_hardened.py (159 lines, 0% → 65%+)

Testa VAE-based sensory layer, Free Energy Principle, reconstruction error

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import numpy as np

from consciousness.predictive_coding.layer1_sensory_hardened import Layer1Sensory
from consciousness.predictive_coding.layer_base_hardened import LayerConfig


# ===== LAYER CONFIG TESTS =====

def test_layer_config_for_layer1():
    """
    SCENARIO: LayerConfig with layer_id=1
    EXPECTED: Config valid for Layer1Sensory
    """
    config = LayerConfig(
        layer_id=1,
        input_dim=100,
        hidden_dim=16,
    )

    assert config.layer_id == 1
    assert config.input_dim == 100
    assert config.hidden_dim == 16


# ===== LAYER1 INITIALIZATION TESTS =====

def test_layer1_sensory_initialization():
    """
    SCENARIO: Layer1Sensory created with valid config
    EXPECTED: Layer initialized, inherits from PredictiveCodingLayerBase
    """
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=16)
    layer = Layer1Sensory(config)

    assert layer is not None
    assert layer.config == config


def test_layer1_sensory_with_kill_switch():
    """
    SCENARIO: Layer1Sensory created with kill_switch_callback
    EXPECTED: Kill switch callback stored
    """
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=16)

    def mock_kill_switch():
        pass

    layer = Layer1Sensory(config, kill_switch_callback=mock_kill_switch)

    assert layer.kill_switch_callback == mock_kill_switch


def test_layer1_wrong_layer_id_raises():
    """
    SCENARIO: Layer1Sensory created with layer_id != 1
    EXPECTED: AssertionError raised
    """
    config = LayerConfig(layer_id=2, input_dim=100, hidden_dim=16)

    with pytest.raises(AssertionError, match="Layer1Sensory requires layer_id=1"):
        Layer1Sensory(config)


# ===== GET_LAYER_NAME TESTS =====

def test_get_layer_name():
    """
    SCENARIO: Layer1Sensory.get_layer_name()
    EXPECTED: Returns "Layer1_Sensory"
    """
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=16)
    layer = Layer1Sensory(config)

    assert layer.get_layer_name() == "Layer1_Sensory"


# ===== PREDICTION TESTS =====

@pytest.mark.asyncio
async def test_predict_impl_with_numpy_array():
    """
    SCENARIO: Layer1Sensory._predict_impl() with numpy array input
    EXPECTED: Returns reconstructed event (numpy array)
    """
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=4)
    layer = Layer1Sensory(config)

    input_data = np.random.randn(10).astype(np.float32)

    reconstruction = await layer._predict_impl(input_data)

    assert isinstance(reconstruction, np.ndarray)
    assert reconstruction.shape == (10,)


@pytest.mark.asyncio
async def test_predict_impl_with_list_input():
    """
    SCENARIO: Layer1Sensory._predict_impl() with Python list input
    EXPECTED: Converts to numpy array, returns reconstruction
    """
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=4)
    layer = Layer1Sensory(config)

    input_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    reconstruction = await layer._predict_impl(input_data)

    assert isinstance(reconstruction, np.ndarray)
    assert reconstruction.shape == (10,)


# ===== ERROR COMPUTATION TESTS =====

def test_compute_error_impl_mse():
    """
    SCENARIO: Layer1Sensory._compute_error_impl() computes MSE
    EXPECTED: Returns mean squared error (scalar)
    """
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=4)
    layer = Layer1Sensory(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([1.0, 2.0, 3.0])

    error = layer._compute_error_impl(predicted, actual)

    assert error == 0.0  # Perfect reconstruction


def test_compute_error_impl_non_zero():
    """
    SCENARIO: Layer1Sensory._compute_error_impl() with different vectors
    EXPECTED: MSE > 0
    """
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=4)
    layer = Layer1Sensory(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([2.0, 3.0, 4.0])

    error = layer._compute_error_impl(predicted, actual)

    # MSE = mean((1-2)^2, (2-3)^2, (3-4)^2) = mean(1, 1, 1) = 1.0
    assert abs(error - 1.0) < 1e-6


def test_compute_error_impl_returns_float():
    """
    SCENARIO: Layer1Sensory._compute_error_impl() return type
    EXPECTED: Returns Python float (not numpy.float32)
    """
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=4)
    layer = Layer1Sensory(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([1.5, 2.5, 3.5])

    error = layer._compute_error_impl(predicted, actual)

    assert isinstance(error, float)


# ===== ENCODE TESTS =====

def test_encode_returns_latent():
    """
    SCENARIO: Layer1Sensory._encode() compresses input to latent space
    EXPECTED: Returns latent vector [hidden_dim]
    """
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=16)
    layer = Layer1Sensory(config)

    input_data = np.random.randn(100).astype(np.float32)

    latent = layer._encode(input_data)

    assert latent.shape == (16,)
    assert latent.dtype == np.float32


def test_encode_different_hidden_dim():
    """
    SCENARIO: Layer1Sensory._encode() with hidden_dim=8
    EXPECTED: Latent vector has shape (8,)
    """
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=8)
    layer = Layer1Sensory(config)

    input_data = np.random.randn(100).astype(np.float32)

    latent = layer._encode(input_data)

    assert latent.shape == (8,)


# ===== DECODE TESTS =====

def test_decode_returns_reconstruction():
    """
    SCENARIO: Layer1Sensory._decode() expands latent to input space
    EXPECTED: Returns reconstruction [input_dim]
    """
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=16)
    layer = Layer1Sensory(config)

    latent = np.random.randn(16).astype(np.float32)

    reconstruction = layer._decode(latent)

    assert reconstruction.shape == (100,)
    assert reconstruction.dtype == np.float32


def test_decode_different_input_dim():
    """
    SCENARIO: Layer1Sensory._decode() with input_dim=50
    EXPECTED: Reconstruction has shape (50,)
    """
    config = LayerConfig(layer_id=1, input_dim=50, hidden_dim=16)
    layer = Layer1Sensory(config)

    latent = np.random.randn(16).astype(np.float32)

    reconstruction = layer._decode(latent)

    assert reconstruction.shape == (50,)


# ===== END-TO-END TESTS =====

@pytest.mark.asyncio
async def test_predict_encode_decode_pipeline():
    """
    SCENARIO: Full predict() pipeline: input → encode → decode → output
    EXPECTED: Output has same shape as input
    """
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=16)
    layer = Layer1Sensory(config)

    input_data = np.random.randn(100).astype(np.float32)

    reconstruction = await layer._predict_impl(input_data)

    assert reconstruction.shape == input_data.shape


def test_docstring_free_energy_principle():
    """
    SCENARIO: Module documents Free Energy Principle
    EXPECTED: Mentions compression, prediction error, bounded errors
    """
    import consciousness.predictive_coding.layer1_sensory_hardened as module

    assert "Free Energy Principle" in module.__doc__
    assert "compression" in module.__doc__
    assert "prediction error" in module.__doc__
    assert "reconstruction error" in module.__doc__


def test_docstring_regra_de_ouro():
    """
    SCENARIO: Module declares REGRA DE OURO compliance
    EXPECTED: NO MOCK, NO PLACEHOLDER, NO TODO
    """
    import consciousness.predictive_coding.layer1_sensory_hardened as module

    assert "NO MOCK" in module.__doc__
    assert "NO PLACEHOLDER" in module.__doc__
    assert "NO TODO" in module.__doc__


def test_docstring_safety_features():
    """
    SCENARIO: Module documents inherited safety features
    EXPECTED: Bounded errors, timeout, circuit breaker
    """
    import consciousness.predictive_coding.layer1_sensory_hardened as module

    assert "Safety Features" in module.__doc__
    assert "Bounded prediction errors" in module.__doc__
    assert "Timeout protection" in module.__doc__
    assert "Circuit breaker protection" in module.__doc__
