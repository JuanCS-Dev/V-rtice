"""
Layer 4 Tactical - Targeted Coverage Tests

Objetivo: Cobrir consciousness/predictive_coding/layer4_tactical_hardened.py (223 lines, 0% → 55%+)

Testa GNN-based tactical layer, relational reasoning, entity embeddings

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import numpy as np

from consciousness.predictive_coding.layer4_tactical_hardened import Layer4Tactical
from consciousness.predictive_coding.layer_base_hardened import LayerConfig


# ===== INITIALIZATION TESTS =====

def test_layer4_tactical_initialization():
    """
    SCENARIO: Layer4Tactical created with valid config
    EXPECTED: Layer initialized with empty entity_embeddings, relations
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)
    layer = Layer4Tactical(config)

    assert layer is not None
    assert layer.config == config
    assert layer._entity_embeddings == {}
    assert layer._relations == {}


def test_layer4_wrong_layer_id_raises():
    """
    SCENARIO: Layer4Tactical created with layer_id != 4
    EXPECTED: AssertionError raised
    """
    config = LayerConfig(layer_id=3, input_dim=16, hidden_dim=8)

    with pytest.raises(AssertionError, match="Layer4Tactical requires layer_id=4"):
        Layer4Tactical(config)


def test_layer4_with_kill_switch():
    """
    SCENARIO: Layer4Tactical created with kill_switch_callback
    EXPECTED: Kill switch callback stored
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)

    def mock_kill_switch():
        pass

    layer = Layer4Tactical(config, kill_switch_callback=mock_kill_switch)

    assert layer.kill_switch_callback == mock_kill_switch


# ===== GET_LAYER_NAME TESTS =====

def test_get_layer_name():
    """
    SCENARIO: Layer4Tactical.get_layer_name()
    EXPECTED: Returns "Layer4_Tactical"
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)
    layer = Layer4Tactical(config)

    assert layer.get_layer_name() == "Layer4_Tactical"


# ===== PREDICTION TESTS =====

@pytest.mark.asyncio
async def test_predict_impl_returns_correct_shape():
    """
    SCENARIO: Layer4Tactical._predict_impl() with input_dim=16
    EXPECTED: Returns prediction [input_dim=16]
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)
    layer = Layer4Tactical(config)

    input_data = np.random.randn(16).astype(np.float32)

    prediction = await layer._predict_impl(input_data)

    assert prediction.shape == (16,)


@pytest.mark.asyncio
async def test_predict_impl_with_list_input():
    """
    SCENARIO: Layer4Tactical._predict_impl() with Python list input
    EXPECTED: Converts to numpy array, returns prediction
    """
    config = LayerConfig(layer_id=4, input_dim=10, hidden_dim=4)
    layer = Layer4Tactical(config)

    input_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    prediction = await layer._predict_impl(input_data)

    assert isinstance(prediction, np.ndarray)
    assert prediction.shape == (10,)


# ===== ERROR COMPUTATION TESTS =====

def test_compute_error_impl_mse():
    """
    SCENARIO: Layer4Tactical._compute_error_impl() computes MSE
    EXPECTED: Returns mean squared error (scalar)
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)
    layer = Layer4Tactical(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([1.0, 2.0, 3.0])

    error = layer._compute_error_impl(predicted, actual)

    assert error == 0.0  # Perfect prediction


def test_compute_error_impl_non_zero():
    """
    SCENARIO: Layer4Tactical._compute_error_impl() with different vectors
    EXPECTED: MSE > 0
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)
    layer = Layer4Tactical(config)

    predicted = np.array([1.0, 2.0, 3.0])
    actual = np.array([2.0, 3.0, 4.0])

    error = layer._compute_error_impl(predicted, actual)

    assert abs(error - 1.0) < 1e-6


# ===== ENTITY EMBEDDINGS TESTS =====

def test_entity_embeddings_empty_initially():
    """
    SCENARIO: Layer4Tactical initialized
    EXPECTED: _entity_embeddings empty dict
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)
    layer = Layer4Tactical(config)

    assert isinstance(layer._entity_embeddings, dict)
    assert len(layer._entity_embeddings) == 0


def test_relations_empty_initially():
    """
    SCENARIO: Layer4Tactical initialized
    EXPECTED: _relations empty dict
    """
    config = LayerConfig(layer_id=4, input_dim=16, hidden_dim=8)
    layer = Layer4Tactical(config)

    assert isinstance(layer._relations, dict)
    assert len(layer._relations) == 0


# ===== DOCSTRING TESTS =====

def test_docstring_free_energy_principle():
    """
    SCENARIO: Module documents Free Energy Principle for tactical objectives
    EXPECTED: Mentions relational reasoning, tactical shifts
    """
    import consciousness.predictive_coding.layer4_tactical_hardened as module

    assert "Free Energy Principle" in module.__doc__
    assert "relational" in module.__doc__
    assert "tactical" in module.__doc__


def test_docstring_regra_de_ouro():
    """
    SCENARIO: Module declares REGRA DE OURO compliance
    EXPECTED: NO MOCK, NO PLACEHOLDER, NO TODO
    """
    import consciousness.predictive_coding.layer4_tactical_hardened as module

    assert "NO MOCK" in module.__doc__
    assert "NO PLACEHOLDER" in module.__doc__
    assert "NO TODO" in module.__doc__


def test_docstring_gnn():
    """
    SCENARIO: Module documents GNN architecture
    EXPECTED: Mentions Graph Neural Network, timescale (days)
    """
    import consciousness.predictive_coding.layer4_tactical_hardened as module

    assert "Graph Neural Network" in module.__doc__
    assert "days timescale" in module.__doc__
