"""
Self Model - Targeted Coverage Tests

Objetivo: Cobrir consciousness/mea/self_model.py (123 lines, 0% → 60%+)

Testa FirstPersonPerspective, IntrospectiveSummary, SelfModel.update()

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from unittest.mock import Mock

from consciousness.mea.self_model import FirstPersonPerspective, IntrospectiveSummary, SelfModel


def test_first_person_perspective_initialization():
    perspective = FirstPersonPerspective(
        viewpoint=(1.0, 2.0, 3.0),
        orientation=(0.1, 0.2, 0.3),
    )

    assert perspective.viewpoint == (1.0, 2.0, 3.0)
    assert perspective.orientation == (0.1, 0.2, 0.3)
    assert perspective.timestamp is not None


def test_introspective_summary_initialization():
    perspective = FirstPersonPerspective(
        viewpoint=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0),
    )

    summary = IntrospectiveSummary(
        narrative="Test narrative",
        confidence=0.85,
        boundary_stability=0.9,
        focus_target="task1",
        perspective=perspective,
    )

    assert summary.narrative == "Test narrative"
    assert summary.confidence == 0.85
    assert summary.boundary_stability == 0.9
    assert summary.focus_target == "task1"
    assert summary.perspective == perspective


def test_self_model_initialization():
    model = SelfModel()

    assert model is not None
    assert hasattr(model, '_perspective_history')
    assert hasattr(model, '_attention_history')
    assert hasattr(model, '_boundary_history')
    assert model._identity_vector == (0.0, 0.0, 1.0)


def test_self_model_update():
    model = SelfModel()

    attention = Mock()
    boundary = Mock()

    model.update(
        attention_state=attention,
        boundary=boundary,
        proprio_center=(1.0, 2.0, 3.0),
        orientation=(0.1, 0.2, 0.3),
    )

    assert len(model._attention_history) == 1
    assert len(model._boundary_history) == 1
    assert len(model._perspective_history) == 1


def test_docstring_self_representation():
    import consciousness.mea.self_model as module

    assert "self-representation" in module.__doc__
    assert "attention state" in module.__doc__
    assert "first-person" in module.__doc__
