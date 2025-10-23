"""
Boundary Detector - Targeted Coverage Tests

Objetivo: Cobrir consciousness/mea/boundary_detector.py (109 lines, 0% → 65%+)

Testa BoundaryAssessment, BoundaryDetector.evaluate(), self/other distinction

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest

from consciousness.mea.boundary_detector import BoundaryAssessment, BoundaryDetector


def test_boundary_assessment_initialization():
    assessment = BoundaryAssessment(
        strength=0.8,
        stability=0.9,
        proprioception_mean=0.6,
        exteroception_mean=0.4,
    )

    assert assessment.strength == 0.8
    assert assessment.stability == 0.9
    assert assessment.proprioception_mean == 0.6
    assert assessment.exteroception_mean == 0.4


def test_boundary_detector_initialization():
    detector = BoundaryDetector()

    assert detector is not None
    assert hasattr(detector, '_strength_history')
    assert hasattr(detector, '_proprio_history')
    assert hasattr(detector, '_extero_history')


def test_boundary_detector_window_size():
    assert BoundaryDetector.WINDOW == 100


def test_evaluate_returns_assessment():
    detector = BoundaryDetector()

    proprio = [0.8, 0.7, 0.9]
    extero = [0.2, 0.3, 0.1]

    assessment = detector.evaluate(proprio, extero)

    assert isinstance(assessment, BoundaryAssessment)


def test_evaluate_high_proprioception_strong_boundary():
    detector = BoundaryDetector()

    proprio = [0.9, 0.8, 0.85]
    extero = [0.1, 0.2, 0.15]

    assessment = detector.evaluate(proprio, extero)

    # High proprio / low extero = strong boundary
    assert assessment.strength > 0.5
    assert 0.0 <= assessment.stability <= 1.0


def test_evaluate_balanced_signals_weak_boundary():
    detector = BoundaryDetector()

    proprio = [0.5, 0.5, 0.5]
    extero = [0.5, 0.5, 0.5]

    assessment = detector.evaluate(proprio, extero)

    # Balanced = weak boundary
    assert assessment.strength < 0.6
    assert assessment.proprioception_mean == 0.5
    assert assessment.exteroception_mean == 0.5


def test_evaluate_stores_history():
    detector = BoundaryDetector()

    proprio = [0.8, 0.7, 0.9]
    extero = [0.2, 0.3, 0.1]

    detector.evaluate(proprio, extero)

    assert len(detector._proprio_history) > 0
    assert len(detector._extero_history) > 0
    assert len(detector._strength_history) > 0


def test_docstring_phenomenological_inspiration():
    import consciousness.mea.boundary_detector as module

    assert "phenomenological" in module.__doc__
    assert "self-other distinction" in module.__doc__
