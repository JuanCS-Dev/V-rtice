"""
Layer 3 Operational - Targeted Coverage Tests

Objetivo: Cobrir consciousness/predictive_coding/layer3_operational_hardened.py (176 lines, 0% → 65%+)

Testa Transformer-based operational layer, self-attention, long-range dependencies

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6

🎯 MODULE #45 - 90% MILESTONE! 🎯
"""

import pytest
import numpy as np

from consciousness.predictive_coding.layer3_operational_hardened import Layer3Operational
from consciousness.predictive_coding.layer_base_hardened import LayerConfig


# ===== LAYER3 INITIALIZATION TESTS =====

def test_layer3_operational_initialization():
    """
    SCENARIO: Layer3Operational created with valid config
    EXPECTED: Layer initialized with empty context_window, max_context_length=10
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    assert layer is not None
    assert layer.config == config
    assert layer._context_window == []
    assert layer._max_context_length == 10


def test_layer3_wrong_layer_id_raises():
    """
    SCENARIO: Layer3Operational created with layer_id != 3
    EXPECTED: AssertionError raised
    """
    config = LayerConfig(layer_id=2, input_dim=32, hidden_dim=16)

    with pytest.raises(AssertionError, match="Layer3Operational requires layer_id=3"):
        Layer3Operational(config)


def test_layer3_with_kill_switch():
    """
    SCENARIO: Layer3Operational created with kill_switch_callback
    EXPECTED: Kill switch callback stored
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)

    def mock_kill_switch():
        pass

    layer = Layer3Operational(config, kill_switch_callback=mock_kill_switch)

    assert layer.kill_switch_callback == mock_kill_switch


# ===== GET_LAYER_NAME TESTS =====

def test_get_layer_name():
    """
    SCENARIO: Layer3Operational.get_layer_name()
    EXPECTED: Returns "Layer3_Operational"
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    assert layer.get_layer_name() == "Layer3_Operational"


# ===== CONTEXT WINDOW TESTS =====

@pytest.mark.asyncio
async def test_predict_impl_adds_to_context_window():
    """
    SCENARIO: Layer3Operational._predict_impl() adds input to context window
    EXPECTED: Context window grows
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    input_data = np.random.randn(32).astype(np.float32)
    await layer._predict_impl(input_data)

    assert len(layer._context_window) == 1


@pytest.mark.asyncio
async def test_context_window_max_length():
    """
    SCENARIO: Layer3Operational with 12 predictions (max=10)
    EXPECTED: Context window capped at 10, oldest evicted (FIFO)
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    for i in range(12):
        input_data = np.random.randn(32).astype(np.float32)
        await layer._predict_impl(input_data)

    assert len(layer._context_window) == 10


@pytest.mark.asyncio
async def test_predict_impl_returns_correct_shape():
    """
    SCENARIO: Layer3Operational._predict_impl() with input_dim=32
    EXPECTED: Returns prediction [input_dim=32]
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    input_data = np.random.randn(32).astype(np.float32)

    prediction = await layer._predict_impl(input_data)

    assert prediction.shape == (32,)


@pytest.mark.asyncio
async def test_predict_impl_with_list_input():
    """
    SCENARIO: Layer3Operational._predict_impl() with Python list input
    EXPECTED: Converts to numpy array, returns prediction
    """
    config = LayerConfig(layer_id=3, input_dim=10, hidden_dim=4)
    layer = Layer3Operational(config)

    input_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    prediction = await layer._predict_impl(input_data)

    assert isinstance(prediction, np.ndarray)
    assert prediction.shape == (10,)


# ===== ERROR COMPUTATION TESTS =====

def test_compute_error_impl_mse():
    """
    SCENARIO: Layer3Operational._compute_error_impl() computes MSE
    EXPECTED: Returns mean squared error (scalar)
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([1.0, 2.0, 3.0])

    error = layer._compute_error_impl(predicted, actual)

    assert error == 0.0  # Perfect prediction


def test_compute_error_impl_non_zero():
    """
    SCENARIO: Layer3Operational._compute_error_impl() with different vectors
    EXPECTED: MSE > 0
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([2.0, 3.0, 4.0])

    error = layer._compute_error_impl(predicted, actual)

    # MSE = mean((1-2)^2, (2-3)^2, (3-4)^2) = mean(1, 1, 1) = 1.0
    assert abs(error - 1.0) < 1e-6


# ===== SELF-ATTENTION TESTS =====

def test_self_attention_empty_context():
    """
    SCENARIO: Layer3Operational._self_attention([]) with empty context
    EXPECTED: Returns zeros [hidden_dim]
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    attended = layer._self_attention([])

    assert attended.shape == (16,)
    assert np.allclose(attended, 0.0)


def test_self_attention_single_pattern():
    """
    SCENARIO: Layer3Operational._self_attention() with 1 pattern
    EXPECTED: Returns attended context [hidden_dim]
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    pattern = np.random.randn(32).astype(np.float32)

    attended = layer._self_attention([pattern])

    assert attended.shape == (16,)


def test_self_attention_multiple_patterns():
    """
    SCENARIO: Layer3Operational._self_attention() with 5 patterns
    EXPECTED: Returns weighted attended context [hidden_dim]
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    patterns = [np.random.randn(32).astype(np.float32) for _ in range(5)]

    attended = layer._self_attention(patterns)

    assert attended.shape == (16,)


# ===== PROJECT TO OUTPUT TESTS =====

def test_project_to_output_returns_prediction():
    """
    SCENARIO: Layer3Operational._project_to_output() with attended context
    EXPECTED: Returns prediction [input_dim]
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    attended_context = np.random.randn(16).astype(np.float32)

    prediction = layer._project_to_output(attended_context)

    assert prediction.shape == (32,)
    assert prediction.dtype == np.float32


# ===== RESET CONTEXT TESTS =====

@pytest.mark.asyncio
async def test_reset_context():
    """
    SCENARIO: Layer3Operational.reset_context() after 5 predictions
    EXPECTED: Context window cleared
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    # Add 5 patterns
    for _ in range(5):
        input_data = np.random.randn(32).astype(np.float32)
        await layer._predict_impl(input_data)

    assert len(layer._context_window) == 5

    layer.reset_context()

    assert len(layer._context_window) == 0


# ===== LONG-RANGE DEPENDENCIES TESTS =====

@pytest.mark.asyncio
async def test_long_range_dependencies():
    """
    SCENARIO: Multiple predictions build up context for long-range dependencies
    EXPECTED: Context window maintains history up to max_context_length
    """
    config = LayerConfig(layer_id=3, input_dim=32, hidden_dim=16)
    layer = Layer3Operational(config)

    # Simulate 15 predictions
    for i in range(15):
        input_data = np.random.randn(32).astype(np.float32)
        await layer._predict_impl(input_data)

    # Should cap at 10
    assert len(layer._context_window) == 10


# ===== DOCSTRING TESTS =====

def test_docstring_free_energy_principle():
    """
    SCENARIO: Module documents Free Energy Principle for operational sequences
    EXPECTED: Mentions long-range dependencies, prediction error
    """
    import consciousness.predictive_coding.layer3_operational_hardened as module

    assert "Free Energy Principle" in module.__doc__
    assert "long-range dependencies" in module.__doc__
    assert "prediction error" in module.__doc__


def test_docstring_regra_de_ouro():
    """
    SCENARIO: Module declares REGRA DE OURO compliance
    EXPECTED: NO MOCK, NO PLACEHOLDER, NO TODO
    """
    import consciousness.predictive_coding.layer3_operational_hardened as module

    assert "NO MOCK" in module.__doc__
    assert "NO PLACEHOLDER" in module.__doc__
    assert "NO TODO" in module.__doc__


def test_docstring_operational_sequences():
    """
    SCENARIO: Module documents operational sequence prediction
    EXPECTED: Mentions multi-stage attacks, business workflows
    """
    import consciousness.predictive_coding.layer3_operational_hardened as module

    assert "Operational sequences" in module.__doc__
    assert "multi-stage attacks" in module.__doc__
    assert "business workflows" in module.__doc__


def test_docstring_transformer():
    """
    SCENARIO: Module documents Transformer architecture
    EXPECTED: Mentions Transformer, timescale (hours)
    """
    import consciousness.predictive_coding.layer3_operational_hardened as module

    assert "Transformer" in module.__doc__
    assert "hours timescale" in module.__doc__
