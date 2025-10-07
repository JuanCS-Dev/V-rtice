"""
Differential Privacy Module - Example Usage

This file demonstrates 5 practical use cases for differential privacy
in threat intelligence analytics:

1. Basic Private Count - Counting threats with DP
2. Geographic Threat Distribution - Count by country/region
3. Severity Statistics - Private mean threat score
4. Attack Vector Histogram - Distribution analysis
5. Budget Tracking - Multi-query privacy accounting

Run this file to see all examples:
    python example_usage.py

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import numpy as np
import pandas as pd

from .dp_aggregator import DPAggregator
from .dp_mechanisms import LaplaceMechanism
from .base import PrivacyBudget, PrivacyParameters
from .privacy_accountant import PrivacyAccountant, CompositionType


def print_header(title: str):
    """Print example header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_basic_count():
    """
    Example 1: Basic Private Count

    Count the total number of threats detected in the last 24h
    with differential privacy guarantee.
    """
    print_header("EXAMPLE 1: Basic Private Count")

    # Simulate threat data
    np.random.seed(42)
    num_threats = 1523  # True count
    threat_data = pd.DataFrame({
        "threat_id": range(num_threats),
        "timestamp": np.random.uniform(0, 86400, num_threats),
        "severity": np.random.uniform(0, 1, num_threats)
    })

    print(f"📊 True threat count: {len(threat_data)}")

    # Create DP aggregator with ε=1.0 (Google-level privacy)
    aggregator = DPAggregator(epsilon=1.0, delta=1e-5)

    # Execute private count query
    result = aggregator.count(threat_data)

    # Display results
    print(f"\n🔒 Privacy Parameters:")
    print(f"   ε (epsilon): {result.epsilon_used}")
    print(f"   δ (delta): {result.delta_used:.6e}")
    print(f"   Mechanism: {result.mechanism}")

    print(f"\n📈 Query Results:")
    print(f"   True count: {result.true_value}")
    print(f"   Noisy count: {result.noisy_value:.0f}")
    print(f"   Absolute error: {result.absolute_error:.0f}")
    print(f"   Relative error: {result.relative_error:.2%}")

    print(f"\n✅ Privacy guarantee: Anyone analyzing this result cannot determine")
    print(f"   with high certainty whether any specific threat was present or not.")


def example_2_geographic_distribution():
    """
    Example 2: Geographic Threat Distribution

    Count threats by country/region with differential privacy.
    Useful for sharing aggregate statistics without revealing
    specific organization locations.
    """
    print_header("EXAMPLE 2: Geographic Threat Distribution")

    # Simulate threat data with geographic distribution
    np.random.seed(42)
    countries = {
        "US": 500,
        "UK": 300,
        "DE": 200,
        "FR": 150,
        "JP": 100,
        "BR": 80,
        "CA": 70,
        "AU": 50
    }

    data_rows = []
    for country, count in countries.items():
        data_rows.extend([{"country": country} for _ in range(count)])

    threat_data = pd.DataFrame(data_rows)

    print(f"📊 True distribution:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        print(f"   {country}: {count}")

    # Create DP aggregator
    aggregator = DPAggregator(epsilon=1.0, delta=1e-5)

    # Execute private count by country
    result = aggregator.count_by_group(threat_data, group_column="country")

    print(f"\n🔒 Privacy: (ε={result.epsilon_used}, δ={result.delta_used:.6e})")

    print(f"\n📈 Noisy distribution:")
    noisy_sorted = sorted(result.noisy_value.items(), key=lambda x: x[1], reverse=True)
    for country, count in noisy_sorted:
        true_count = countries[country]
        error = abs(count - true_count)
        print(f"   {country}: {count:.0f} (true: {true_count}, error: {error:.0f})")

    print(f"\n✅ Can share this distribution publicly without revealing exact counts!")


def example_3_severity_statistics():
    """
    Example 3: Severity Statistics

    Compute average threat severity score with differential privacy.
    """
    print_header("EXAMPLE 3: Severity Statistics - Private Mean")

    # Simulate threat severity data
    np.random.seed(42)
    n_threats = 1000
    # Mix of low, medium, high severity threats
    severities = np.concatenate([
        np.random.beta(2, 8, 400),  # Low severity (skewed low)
        np.random.beta(5, 5, 400),  # Medium severity (balanced)
        np.random.beta(8, 2, 200)   # High severity (skewed high)
    ])

    threat_data = pd.DataFrame({"severity": severities})

    true_mean = severities.mean()
    print(f"📊 True statistics:")
    print(f"   Count: {n_threats}")
    print(f"   Mean severity: {true_mean:.4f}")
    print(f"   Std deviation: {severities.std():.4f}")
    print(f"   Min: {severities.min():.4f}, Max: {severities.max():.4f}")

    # Create DP aggregator
    aggregator = DPAggregator(epsilon=1.0, delta=1e-5)

    # Execute private mean query
    result = aggregator.mean(
        threat_data,
        value_column="severity",
        value_range=1.0,  # Severity in [0, 1]
        clamp_bounds=(0.0, 1.0)  # Ensure valid range
    )

    print(f"\n🔒 Privacy: (ε={result.epsilon_used}, δ={result.delta_used:.6e})")

    print(f"\n📈 Private statistics:")
    print(f"   Noisy mean severity: {result.noisy_value:.4f}")
    print(f"   Absolute error: {result.absolute_error:.4f}")
    print(f"   Relative error: {result.relative_error:.2%}")

    print(f"\n✅ Can report mean severity without revealing individual threat details!")


def example_4_attack_vector_histogram():
    """
    Example 4: Attack Vector Histogram

    Analyze distribution of attack types with differential privacy.
    """
    print_header("EXAMPLE 4: Attack Vector Histogram")

    # Simulate attack severity distribution
    np.random.seed(42)
    # Bimodal distribution: many low-severity, some high-severity
    severities = np.concatenate([
        np.random.beta(2, 5, 600),  # Low severity cluster
        np.random.beta(7, 2, 400)   # High severity cluster
    ])

    print(f"📊 Analyzing {len(severities)} threats")

    # Create DP aggregator
    aggregator = DPAggregator(epsilon=1.0, delta=1e-5)

    # Execute private histogram query
    result = aggregator.histogram(
        severities,
        bins=10  # 10 bins in [0, 1]
    )

    print(f"\n🔒 Privacy: (ε={result.epsilon_used}, δ={result.delta_used:.6e})")

    print(f"\n📈 Severity distribution (noisy histogram):")
    bin_edges = result.metadata["bin_edges"]
    for i, count in enumerate(result.noisy_value):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        bar = "#" * int(count / 10)  # Visual bar
        print(f"   [{bin_start:.1f}-{bin_end:.1f}): {count:6.0f}  {bar}")

    print(f"\n✅ Can publish distribution without revealing individual threats!")


def example_5_budget_tracking():
    """
    Example 5: Privacy Budget Tracking

    Demonstrate privacy accounting across multiple queries.
    Track cumulative privacy loss and prevent budget exhaustion.
    """
    print_header("EXAMPLE 5: Privacy Budget Tracking")

    # Simulate threat data
    np.random.seed(42)
    threat_data = pd.DataFrame({
        "country": np.random.choice(["US", "UK", "DE", "FR"], 1000),
        "severity": np.random.uniform(0, 1, 1000),
        "attack_type": np.random.choice(["malware", "phishing", "ddos"], 1000)
    })

    # Create privacy budget tracker
    print(f"📊 Initializing privacy budget:")
    budget = PrivacyBudget(total_epsilon=5.0, total_delta=1e-4)
    print(f"   Total budget: (ε={budget.total_epsilon}, δ={budget.total_delta:.6e})")

    # Create aggregator with budget tracking
    aggregator = DPAggregator(
        epsilon=1.0,
        delta=1e-5,
        privacy_budget=budget
    )

    # Execute multiple queries
    print(f"\n🔍 Executing queries...")

    # Query 1: Total count
    print(f"\n   Query 1: Total threat count")
    result1 = aggregator.count(threat_data)
    print(f"   Result: {result1.noisy_value:.0f}")
    print(f"   Budget used: (ε={budget.used_epsilon}, δ={budget.used_delta:.6e})")
    print(f"   Budget remaining: (ε={budget.remaining_epsilon}, δ={budget.remaining_delta:.6e})")

    # Query 2: Count by country
    print(f"\n   Query 2: Threats by country")
    result2 = aggregator.count_by_group(threat_data, group_column="country")
    print(f"   Result: {len(result2.noisy_value)} countries")
    print(f"   Budget used: (ε={budget.used_epsilon}, δ={budget.used_delta:.6e})")
    print(f"   Budget remaining: (ε={budget.remaining_epsilon}, δ={budget.remaining_delta:.6e})")

    # Query 3: Mean severity
    print(f"\n   Query 3: Average severity")
    result3 = aggregator.mean(threat_data, value_column="severity", value_range=1.0)
    print(f"   Result: {result3.noisy_value:.4f}")
    print(f"   Budget used: (ε={budget.used_epsilon}, δ={budget.used_delta:.6e})")
    print(f"   Budget remaining: (ε={budget.remaining_epsilon}, δ={budget.remaining_delta:.6e})")

    # Query 4: Count by attack type
    print(f"\n   Query 4: Threats by attack type")
    result4 = aggregator.count_by_group(threat_data, group_column="attack_type")
    print(f"   Result: {len(result4.noisy_value)} attack types")
    print(f"   Budget used: (ε={budget.used_epsilon}, δ={budget.used_delta:.6e})")
    print(f"   Budget remaining: (ε={budget.remaining_epsilon}, δ={budget.remaining_delta:.6e})")

    # Check if we can execute another query
    print(f"\n📊 Budget status:")
    print(f"   Queries executed: {len(budget.queries_executed)}")
    print(f"   Privacy level: {budget.privacy_level.value.upper()}")
    print(f"   Budget exhausted: {budget.budget_exhausted}")

    if budget.can_execute(epsilon=1.0, delta=1e-5):
        print(f"\n✅ Can execute another query with (ε=1.0, δ=1e-5)")
    else:
        print(f"\n❌ Cannot execute another query - budget exhausted!")

    # Get detailed statistics
    stats = budget.get_statistics()
    print(f"\n📈 Detailed statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            if 'epsilon' in key or 'delta' in key:
                print(f"   {key}: {value:.6e}")
            else:
                print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")


def run_all_examples():
    """Run all 5 examples"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "DIFFERENTIAL PRIVACY - EXAMPLE USAGE" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")

    example_1_basic_count()
    example_2_geographic_distribution()
    example_3_severity_statistics()
    example_4_attack_vector_histogram()
    example_5_budget_tracking()

    print("\n" + "=" * 80)
    print("  All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_examples()
