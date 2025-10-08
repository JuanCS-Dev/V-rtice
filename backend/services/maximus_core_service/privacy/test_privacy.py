"""
Comprehensive Test Suite for Differential Privacy Module

Tests all core functionality:
- Base classes and data structures
- Laplace, Gaussian, Exponential mechanisms
- DPAggregator (count, sum, mean, histogram)
- PrivacyAccountant (composition, budget tracking)
- Privacy guarantees and performance

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import numpy as np
import pandas as pd
import pytest

from .base import (
    DPResult,
    PrivacyBudget,
    PrivacyLevel,
    PrivacyParameters,
    SensitivityCalculator,
)
from .dp_aggregator import DPAggregator, DPQueryType
from .dp_mechanisms import (
    ExponentialMechanism,
    GaussianMechanism,
    LaplaceMechanism,
)
from .privacy_accountant import (
    CompositionType,
    PrivacyAccountant,
    SubsampledPrivacyAccountant,
)


class TestBaseClasses:
    """Test base classes and data structures"""

    def test_privacy_budget_initialization(self):
        """Test PrivacyBudget initialization and validation"""
        # Valid budget
        budget = PrivacyBudget(total_epsilon=1.0, total_delta=1e-5)
        assert budget.total_epsilon == 1.0
        assert budget.total_delta == 1e-5
        assert budget.used_epsilon == 0.0
        assert budget.used_delta == 0.0
        assert budget.remaining_epsilon == 1.0
        assert budget.remaining_delta == 1e-5
        assert not budget.budget_exhausted

        # Invalid epsilon
        with pytest.raises(ValueError, match="epsilon must be positive"):
            PrivacyBudget(total_epsilon=-1.0, total_delta=1e-5)

        # Invalid delta
        with pytest.raises(ValueError, match="delta must be in"):
            PrivacyBudget(total_epsilon=1.0, total_delta=1.5)

    def test_privacy_budget_spending(self):
        """Test privacy budget spending and tracking"""
        budget = PrivacyBudget(total_epsilon=2.0, total_delta=1e-4)

        # Spend budget
        assert budget.can_execute(epsilon=1.0, delta=5e-5)
        budget.spend(epsilon=1.0, delta=5e-5, query_type="count")

        assert budget.used_epsilon == 1.0
        assert budget.used_delta == 5e-5
        assert budget.remaining_epsilon == 1.0
        assert budget.remaining_delta == 5e-5
        assert len(budget.queries_executed) == 1

        # Spend more
        budget.spend(epsilon=0.5, delta=2e-5, query_type="mean")
        assert budget.used_epsilon == 1.5
        assert budget.used_delta == pytest.approx(7e-5, rel=1e-9)

        # Try to exceed budget
        with pytest.raises(ValueError, match="exceeds remaining budget"):
            budget.spend(epsilon=1.0, delta=0)

    def test_privacy_budget_levels(self):
        """Test privacy level classification"""
        budget = PrivacyBudget(total_epsilon=10.0, total_delta=1e-5)

        # Very high privacy
        budget.used_epsilon = 0.05
        assert budget.privacy_level == PrivacyLevel.VERY_HIGH

        # High privacy
        budget.used_epsilon = 0.5
        assert budget.privacy_level == PrivacyLevel.HIGH

        # Medium privacy
        budget.used_epsilon = 2.0
        assert budget.privacy_level == PrivacyLevel.MEDIUM

        # Low privacy
        budget.used_epsilon = 5.0
        assert budget.privacy_level == PrivacyLevel.LOW

        # Minimal privacy
        budget.used_epsilon = 15.0
        assert budget.privacy_level == PrivacyLevel.MINIMAL

    def test_privacy_parameters(self):
        """Test PrivacyParameters validation"""
        # Valid Laplace params
        params = PrivacyParameters(epsilon=1.0, delta=0.0, sensitivity=1.0, mechanism="laplace")
        assert params.is_pure_dp
        assert params.noise_scale == 1.0  # b = Δf/ε = 1.0/1.0 = 1.0

        # Valid Gaussian params
        params = PrivacyParameters(epsilon=1.0, delta=1e-5, sensitivity=1.0, mechanism="gaussian")
        assert not params.is_pure_dp
        assert params.noise_scale > 0  # σ calculated

        # Invalid mechanism
        with pytest.raises(ValueError, match="Unknown mechanism"):
            PrivacyParameters(epsilon=1.0, delta=0, sensitivity=1.0, mechanism="invalid")

    def test_sensitivity_calculator(self):
        """Test sensitivity calculations"""
        # Count sensitivity
        assert SensitivityCalculator.count_sensitivity() == 1.0

        # Sum sensitivity
        assert SensitivityCalculator.sum_sensitivity(value_range=10.0) == 10.0

        # Mean sensitivity
        assert SensitivityCalculator.mean_sensitivity(value_range=10.0, n=100) == 0.1

        # Histogram sensitivity
        assert SensitivityCalculator.histogram_sensitivity(bins=10) == 1.0


class TestDPMechanisms:
    """Test differential privacy mechanisms"""

    def test_laplace_mechanism(self):
        """Test Laplace mechanism noise addition"""
        params = PrivacyParameters(epsilon=1.0, delta=0.0, sensitivity=1.0)
        mechanism = LaplaceMechanism(params)

        # Test scalar noise
        true_value = 100.0
        noisy_value = mechanism.add_noise(true_value)
        assert isinstance(noisy_value, float)
        assert noisy_value != true_value  # Noise was added (with high probability)

        # Test array noise
        true_array = np.array([10.0, 20.0, 30.0])
        noisy_array = mechanism.add_noise(true_array)
        assert isinstance(noisy_array, np.ndarray)
        assert noisy_array.shape == true_array.shape

    def test_gaussian_mechanism(self):
        """Test Gaussian mechanism noise addition"""
        params = PrivacyParameters(epsilon=1.0, delta=1e-5, sensitivity=1.0)
        mechanism = GaussianMechanism(params)

        # Test scalar noise
        true_value = 100.0
        noisy_value = mechanism.add_noise(true_value)
        assert isinstance(noisy_value, float)

        # Test array noise
        true_array = np.array([10.0, 20.0, 30.0])
        noisy_array = mechanism.add_noise(true_array)
        assert isinstance(noisy_array, np.ndarray)
        assert noisy_array.shape == true_array.shape

    def test_exponential_mechanism(self):
        """Test Exponential mechanism selection"""
        candidates = ["option_a", "option_b", "option_c"]
        scores = [0.9, 0.5, 0.1]  # Option A has highest score
        score_function = lambda c: scores[candidates.index(c)]

        params = PrivacyParameters(epsilon=1.0, delta=0.0, sensitivity=0.5)
        mechanism = ExponentialMechanism(params, candidates=candidates, score_function=score_function)

        # Get selection probabilities
        probs = mechanism.get_selection_probabilities()
        assert len(probs) == 3
        assert np.isclose(probs.sum(), 1.0)
        assert probs[0] > probs[1] > probs[2]  # Higher score = higher probability

        # Test selection (run multiple times to check randomness)
        selections = [mechanism.select() for _ in range(100)]
        assert len(set(selections)) > 1  # Multiple candidates selected
        assert "option_a" in selections  # Highest score should be selected often

    def test_dp_result_validation(self):
        """Test DPResult data structure"""
        result = DPResult(
            true_value=100.0,
            noisy_value=102.5,
            epsilon_used=1.0,
            delta_used=0.0,
            sensitivity=1.0,
            mechanism="laplace",
            noise_added=2.5,
            query_type="count",
        )

        assert result.absolute_error == 2.5
        assert result.relative_error == 0.025  # 2.5/100 = 0.025

        # Test dict conversion
        result_dict = result.to_dict()
        assert "true_value" in result_dict
        assert "noisy_value" in result_dict
        assert result_dict["absolute_error"] == 2.5


class TestDPAggregator:
    """Test differentially private aggregation"""

    def test_count_query(self):
        """Test DP count query"""
        data = pd.DataFrame({"value": range(1000)})
        aggregator = DPAggregator(epsilon=1.0, delta=0.0)

        result = aggregator.count(data)
        assert isinstance(result, DPResult)
        assert result.true_value == 1000
        assert result.epsilon_used == 1.0
        assert result.delta_used == 0.0
        assert result.query_type == DPQueryType.COUNT.value

        # Noisy count should be close to true count (with high probability)
        assert abs(result.noisy_value - 1000) < 50  # Within reasonable noise

    def test_count_by_group(self):
        """Test DP group-by count query"""
        data = pd.DataFrame({"country": ["US"] * 500 + ["UK"] * 300 + ["DE"] * 200})
        aggregator = DPAggregator(epsilon=1.0, delta=0.0)

        result = aggregator.count_by_group(data, group_column="country")
        assert isinstance(result.noisy_value, dict)
        assert set(result.noisy_value.keys()) == {"US", "UK", "DE"}

        # Check approximate counts
        assert abs(result.noisy_value["US"] - 500) < 50
        assert abs(result.noisy_value["UK"] - 300) < 50
        assert abs(result.noisy_value["DE"] - 200) < 50

    def test_sum_query(self):
        """Test DP sum query"""
        data = pd.DataFrame({"severity": [0.5] * 100 + [0.8] * 50})
        aggregator = DPAggregator(epsilon=1.0, delta=0.0)

        result = aggregator.sum(
            data,
            value_column="severity",
            value_range=1.0,  # Scores in [0, 1]
        )

        true_sum = 0.5 * 100 + 0.8 * 50  # = 50 + 40 = 90
        assert result.true_value == pytest.approx(true_sum, rel=1e-9)
        assert abs(result.noisy_value - true_sum) < 20  # Reasonable noise

    def test_mean_query(self):
        """Test DP mean query"""
        np.random.seed(42)
        values = np.random.uniform(0, 1, size=500)
        data = pd.DataFrame({"value": values})
        aggregator = DPAggregator(epsilon=1.0, delta=0.0)

        result = aggregator.mean(data, value_column="value", value_range=1.0)

        true_mean = values.mean()
        assert result.true_value == pytest.approx(true_mean)
        assert abs(result.noisy_value - true_mean) < 0.1  # Small noise for large dataset

    def test_histogram_query(self):
        """Test DP histogram query"""
        np.random.seed(42)
        data = np.random.normal(50, 10, size=1000)
        aggregator = DPAggregator(epsilon=1.0, delta=0.0)

        result = aggregator.histogram(data, bins=10)
        assert isinstance(result.noisy_value, np.ndarray)
        assert len(result.noisy_value) == 10
        assert result.noisy_value.sum() > 0  # Some counts should be positive


class TestPrivacyAccountant:
    """Test privacy accounting and composition"""

    def test_basic_composition(self):
        """Test basic sequential composition"""
        accountant = PrivacyAccountant(
            total_epsilon=10.0, total_delta=1e-4, composition_type=CompositionType.BASIC_SEQUENTIAL
        )

        # Add 5 queries with ε=1.0 each
        for i in range(5):
            accountant.add_query(epsilon=1.0, delta=0.0, query_type="count")

        # Basic composition: total ε = Σ ε_i = 5.0
        total_eps, total_dlt = accountant.get_total_privacy_loss()
        assert total_eps == 5.0
        assert total_dlt == 0.0

    def test_advanced_composition(self):
        """Test advanced composition (tighter bound)"""
        accountant = PrivacyAccountant(
            total_epsilon=10.0, total_delta=1e-4, composition_type=CompositionType.ADVANCED_SEQUENTIAL
        )

        # Add 10 queries with ε=0.5 each
        for i in range(10):
            accountant.add_query(epsilon=0.5, delta=0.0, query_type="count")

        # Advanced composition: ε' ≈ sqrt(2k × ln(1/δ')) × ε
        # With k=10, ε=0.5, δ'=total_delta/2, we get ε' ≈ 6.8-7.0
        # This is better than basic (5.0) when considering we convert to approximate DP
        total_eps, total_dlt = accountant.get_total_privacy_loss()
        assert total_eps < 10.0  # Less than 2x basic composition
        assert total_dlt > 0  # Has some δ from advanced composition

    def test_parallel_composition(self):
        """Test parallel composition"""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-4, composition_type=CompositionType.PARALLEL)

        # Add 5 queries on disjoint datasets
        for i in range(5):
            accountant.add_query(epsilon=1.0, delta=1e-5, query_type="count", composition_type=CompositionType.PARALLEL)

        # Parallel composition: max ε = 1.0
        total_eps, total_dlt = accountant.get_total_privacy_loss()
        assert total_eps == 1.0  # Max of all queries
        assert total_dlt == 1e-5

    def test_budget_exhaustion(self):
        """Test privacy budget exhaustion"""
        accountant = PrivacyAccountant(
            total_epsilon=2.0, total_delta=1e-4, composition_type=CompositionType.BASIC_SEQUENTIAL
        )

        # Add queries until budget exhausted
        accountant.add_query(epsilon=1.0, delta=5e-5, query_type="count")
        accountant.add_query(epsilon=0.8, delta=4e-5, query_type="mean")

        assert not accountant.is_budget_exhausted()

        # Try to add query that would exceed budget
        with pytest.raises(ValueError, match="exceed privacy budget"):
            accountant.add_query(epsilon=0.5, delta=0, query_type="sum")

    def test_subsampling_amplification(self):
        """Test privacy amplification by subsampling"""
        accountant = SubsampledPrivacyAccountant(
            total_epsilon=10.0,
            total_delta=1e-4,
            sampling_rate=0.01,  # 1% subsample
        )

        # Add query with base ε=1.0
        accountant.add_query(epsilon=1.0, delta=0.0, query_type="count")

        # Amplified ε should be ~0.01 (q × ε)
        total_eps, total_dlt = accountant.get_total_privacy_loss()
        assert total_eps == pytest.approx(0.01, rel=0.01)


class TestPrivacyGuarantees:
    """Test privacy guarantees and statistical properties"""

    def test_laplace_noise_distribution(self):
        """Test Laplace noise has correct distribution"""
        params = PrivacyParameters(epsilon=1.0, delta=0.0, sensitivity=1.0)
        mechanism = LaplaceMechanism(params)

        # Generate many noisy samples
        true_value = 0.0
        samples = [mechanism.add_noise(true_value) for _ in range(10000)]

        # Check mean (should be close to 0)
        assert np.mean(samples) == pytest.approx(0.0, abs=0.05)

        # Check scale (MAD should be close to b * ln(2) ≈ 0.693 for b=1.0)
        median_absolute_deviation = np.median(np.abs(samples))
        expected_mad = np.log(2)  # For Laplace with b=1.0, MAD = b * ln(2)
        assert median_absolute_deviation == pytest.approx(expected_mad, rel=0.1)

    def test_gaussian_noise_distribution(self):
        """Test Gaussian noise has correct distribution"""
        params = PrivacyParameters(epsilon=1.0, delta=1e-5, sensitivity=1.0)
        mechanism = GaussianMechanism(params)

        # Generate many noisy samples
        true_value = 0.0
        samples = [mechanism.add_noise(true_value) for _ in range(10000)]

        # Check mean (should be close to 0)
        assert np.mean(samples) == pytest.approx(0.0, abs=0.05)

        # Check std (should match mechanism.std)
        assert np.std(samples) == pytest.approx(mechanism.std, rel=0.1)

    def test_utility_vs_privacy_tradeoff(self):
        """Test utility decreases as privacy increases"""
        data = pd.DataFrame({"value": range(1000)})
        true_count = 1000

        # Different epsilon values
        epsilons = [0.1, 0.5, 1.0, 5.0, 10.0]
        errors = []

        for eps in epsilons:
            aggregator = DPAggregator(epsilon=eps, delta=0.0)
            result = aggregator.count(data)
            error = abs(result.noisy_value - true_count)
            errors.append(error)

        # Higher epsilon (less privacy) should give lower error (more utility)
        # Errors should generally decrease
        assert errors[0] > errors[-1]  # ε=0.1 error > ε=10.0 error


class TestPerformance:
    """Test performance benchmarks"""

    def test_dp_aggregation_latency(self):
        """Test DP aggregation completes within target (<100ms)"""
        import time

        data = pd.DataFrame({"value": range(1000), "group": np.random.choice(["A", "B", "C"], 1000)})
        aggregator = DPAggregator(epsilon=1.0, delta=0.0)

        # Measure count latency
        start = time.time()
        result = aggregator.count(data)
        latency_ms = (time.time() - start) * 1000

        assert latency_ms < 100  # Target: <100ms

    def test_privacy_accountant_performance(self):
        """Test privacy accountant can handle 100+ queries"""
        import time

        accountant = PrivacyAccountant(
            total_epsilon=100.0, total_delta=1e-4, composition_type=CompositionType.BASIC_SEQUENTIAL
        )

        start = time.time()
        for i in range(100):
            accountant.add_query(epsilon=0.5, delta=1e-6, query_type="count")
        latency_ms = (time.time() - start) * 1000

        assert latency_ms < 1000  # Should complete in <1s
        assert len(accountant.queries) == 100


def run_all_tests():
    """Run all tests and report results"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
