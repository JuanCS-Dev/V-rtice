"""Benchmark test configuration.

Registers custom pytest markers for benchmark tests.
"""


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "benchmark: Performance benchmarks (biological plausibility validation)")
