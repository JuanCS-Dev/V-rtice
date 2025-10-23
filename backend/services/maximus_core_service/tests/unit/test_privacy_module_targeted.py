"""
Privacy Module - Targeted Coverage Tests

Objetivo: Cobrir privacy/__init__.py (77 lines, 0% → 90%+)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
"""

import pytest


def test_privacy_module_imports():
    import privacy
    assert privacy is not None


def test_version():
    import privacy
    assert privacy.__version__ == "1.0.0"


def test_author():
    import privacy
    assert "Claude Code" in privacy.__author__


# Base classes
def test_exports_privacy_budget():
    from privacy import PrivacyBudget
    assert PrivacyBudget is not None


def test_exports_privacy_level():
    from privacy import PrivacyLevel
    assert PrivacyLevel is not None


def test_exports_dp_result():
    from privacy import DPResult
    assert DPResult is not None


def test_exports_privacy_mechanism():
    from privacy import PrivacyMechanism
    assert PrivacyMechanism is not None


# DP Mechanisms
def test_exports_laplace_mechanism():
    from privacy import LaplaceMechanism
    assert LaplaceMechanism is not None


def test_exports_gaussian_mechanism():
    from privacy import GaussianMechanism
    assert GaussianMechanism is not None


def test_exports_exponential_mechanism():
    from privacy import ExponentialMechanism
    assert ExponentialMechanism is not None


# Aggregator
def test_exports_dp_aggregator():
    from privacy import DPAggregator
    assert DPAggregator is not None


def test_exports_dp_query_type():
    from privacy import DPQueryType
    assert DPQueryType is not None


# Accountant
def test_exports_privacy_accountant():
    from privacy import PrivacyAccountant
    assert PrivacyAccountant is not None


def test_exports_composition_type():
    from privacy import CompositionType
    assert CompositionType is not None


def test_all_exports():
    import privacy
    assert len(privacy.__all__) == 14


def test_all_exports_importable():
    import privacy
    for name in privacy.__all__:
        assert hasattr(privacy, name)


def test_docstring():
    import privacy
    assert "Differential Privacy" in privacy.__doc__
    assert "(ε, δ)" in privacy.__doc__
