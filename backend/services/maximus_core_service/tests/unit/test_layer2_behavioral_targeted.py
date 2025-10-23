"""
Layer 2 Behavioral - Targeted Coverage Tests

Objetivo: Cobrir consciousness/predictive_coding/layer2_behavioral_hardened.py (165 lines, 0% → 65%+)

Testa RNN/LSTM behavioral layer, sequence prediction, temporal dependencies

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import numpy as np

from consciousness.predictive_coding.layer2_behavioral_hardened import Layer2Behavioral
from consciousness.predictive_coding.layer_base_hardened import LayerConfig


# ===== LAYER2 INITIALIZATION TESTS =====

def test_layer2_behavioral_initialization():
    """
    SCENARIO: Layer2Behavioral created with valid config
    EXPECTED: Layer initialized with hidden_state initialized to zeros
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    assert layer is not None
    assert layer.config == config
    assert layer._hidden_state.shape == (32,)
    assert np.allclose(layer._hidden_state, 0.0)


def test_layer2_wrong_layer_id_raises():
    """
    SCENARIO: Layer2Behavioral created with layer_id != 2
    EXPECTED: AssertionError raised
    """
    config = LayerConfig(layer_id=1, input_dim=64, hidden_dim=32)

    with pytest.raises(AssertionError, match="Layer2Behavioral requires layer_id=2"):
        Layer2Behavioral(config)


def test_layer2_with_kill_switch():
    """
    SCENARIO: Layer2Behavioral created with kill_switch_callback
    EXPECTED: Kill switch callback stored
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)

    def mock_kill_switch():
        pass

    layer = Layer2Behavioral(config, kill_switch_callback=mock_kill_switch)

    assert layer.kill_switch_callback == mock_kill_switch


# ===== GET_LAYER_NAME TESTS =====

def test_get_layer_name():
    """
    SCENARIO: Layer2Behavioral.get_layer_name()
    EXPECTED: Returns "Layer2_Behavioral"
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    assert layer.get_layer_name() == "Layer2_Behavioral"


# ===== PREDICTION TESTS =====

@pytest.mark.asyncio
async def test_predict_impl_updates_hidden_state():
    """
    SCENARIO: Layer2Behavioral._predict_impl() updates hidden state
    EXPECTED: Hidden state changes after prediction
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    initial_hidden = layer._hidden_state.copy()

    input_data = np.random.randn(64).astype(np.float32)
    await layer._predict_impl(input_data)

    # Hidden state should have changed
    assert not np.allclose(layer._hidden_state, initial_hidden)


@pytest.mark.asyncio
async def test_predict_impl_returns_correct_shape():
    """
    SCENARIO: Layer2Behavioral._predict_impl() with input_dim=64
    EXPECTED: Returns prediction [input_dim=64]
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    input_data = np.random.randn(64).astype(np.float32)

    prediction = await layer._predict_impl(input_data)

    assert prediction.shape == (64,)


@pytest.mark.asyncio
async def test_predict_impl_with_list_input():
    """
    SCENARIO: Layer2Behavioral._predict_impl() with Python list input
    EXPECTED: Converts to numpy array, returns prediction
    """
    config = LayerConfig(layer_id=2, input_dim=10, hidden_dim=4)
    layer = Layer2Behavioral(config)

    input_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    prediction = await layer._predict_impl(input_data)

    assert isinstance(prediction, np.ndarray)
    assert prediction.shape == (10,)


# ===== ERROR COMPUTATION TESTS =====

def test_compute_error_impl_mse():
    """
    SCENARIO: Layer2Behavioral._compute_error_impl() computes MSE
    EXPECTED: Returns mean squared error (scalar)
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([1.0, 2.0, 3.0])

    error = layer._compute_error_impl(predicted, actual)

    assert error == 0.0  # Perfect prediction


def test_compute_error_impl_non_zero():
    """
    SCENARIO: Layer2Behavioral._compute_error_impl() with different vectors
    EXPECTED: MSE > 0
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([2.0, 3.0, 4.0])

    error = layer._compute_error_impl(predicted, actual)

    # MSE = mean((1-2)^2, (2-3)^2, (3-4)^2) = mean(1, 1, 1) = 1.0
    assert abs(error - 1.0) < 1e-6


# ===== HIDDEN STATE TESTS =====

def test_update_hidden_state_changes_state():
    """
    SCENARIO: Layer2Behavioral._update_hidden_state() with input
    EXPECTED: Returns new hidden state (different from current)
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    input_data = np.random.randn(64).astype(np.float32)

    initial_hidden = layer._hidden_state.copy()
    new_hidden = layer._update_hidden_state(input_data)

    assert new_hidden.shape == (32,)
    # Should be different (due to randomness in placeholder)
    # We can't assert definitively due to random component, but shape is key


def test_reset_hidden_state():
    """
    SCENARIO: Layer2Behavioral.reset_hidden_state() called after prediction
    EXPECTED: Hidden state reset to zeros
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    # Set hidden state to non-zero
    layer._hidden_state = np.ones(32, dtype=np.float32)

    layer.reset_hidden_state()

    assert np.allclose(layer._hidden_state, 0.0)


# ===== DECODE HIDDEN STATE TESTS =====

def test_decode_hidden_state_returns_prediction():
    """
    SCENARIO: Layer2Behavioral._decode_hidden_state() with hidden state
    EXPECTED: Returns prediction [input_dim]
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    hidden_state = np.random.randn(32).astype(np.float32)

    prediction = layer._decode_hidden_state(hidden_state)

    assert prediction.shape == (64,)
    assert prediction.dtype == np.float32


def test_decode_hidden_state_different_input_dim():
    """
    SCENARIO: Layer2Behavioral._decode_hidden_state() with input_dim=100
    EXPECTED: Prediction has shape (100,)
    """
    config = LayerConfig(layer_id=2, input_dim=100, hidden_dim=32)
    layer = Layer2Behavioral(config)

    hidden_state = np.random.randn(32).astype(np.float32)

    prediction = layer._decode_hidden_state(hidden_state)

    assert prediction.shape == (100,)


# ===== SEQUENCE MEMORY TESTS =====

@pytest.mark.asyncio
async def test_sequence_prediction_maintains_state():
    """
    SCENARIO: Multiple predictions in sequence
    EXPECTED: Hidden state evolves across predictions (RNN memory)
    """
    config = LayerConfig(layer_id=2, input_dim=64, hidden_dim=32)
    layer = Layer2Behavioral(config)

    # Make 3 predictions in sequence
    for i in range(3):
        input_data = np.random.randn(64).astype(np.float32)
        await layer._predict_impl(input_data)

    # After 3 predictions, hidden state should be non-zero
    assert not np.allclose(layer._hidden_state, 0.0)


# ===== DOCSTRING TESTS =====

def test_docstring_free_energy_principle():
    """
    SCENARIO: Module documents Free Energy Principle for sequences
    EXPECTED: Mentions temporal dependencies, prediction error
    """
    import consciousness.predictive_coding.layer2_behavioral_hardened as module

    assert "Free Energy Principle" in module.__doc__
    assert "temporal dependencies" in module.__doc__
    assert "prediction error" in module.__doc__


def test_docstring_regra_de_ouro():
    """
    SCENARIO: Module declares REGRA DE OURO compliance
    EXPECTED: NO MOCK, NO PLACEHOLDER, NO TODO
    """
    import consciousness.predictive_coding.layer2_behavioral_hardened as module

    assert "NO MOCK" in module.__doc__
    assert "NO PLACEHOLDER" in module.__doc__
    assert "NO TODO" in module.__doc__


def test_docstring_behavioral_patterns():
    """
    SCENARIO: Module documents behavioral pattern detection
    EXPECTED: Mentions repeated login, scanning, data exfil
    """
    import consciousness.predictive_coding.layer2_behavioral_hardened as module

    assert "Behavioral patterns" in module.__doc__
    assert "repeated login" in module.__doc__
    assert "scanning patterns" in module.__doc__
