"""
Kuramoto - Final 2 Lines to 100%
=================================

Target missing lines (98.80% → 100.00%):
- 165-167: compute_dissolution_rate() with >=10 samples

PADRÃO PAGANI ABSOLUTO - 100% MEANS 100%
"""

import pytest
from consciousness.esgt.kuramoto import SynchronizationDynamics


class TestKuramotoFinal2Lines:
    """Final 2 lines to achieve Kuramoto 100% coverage."""

    def test_compute_dissolution_rate_with_sufficient_history_lines_165_167(self):
        """Test compute_dissolution_rate with >=10 samples (lines 165-167)."""
        dynamics = SynchronizationDynamics()

        # Add 15 coherence samples to ensure len >= 10
        # Simulate decay pattern: high to low coherence
        for i in range(15):
            coherence = 0.9 - (i * 0.05)  # Decay from 0.9 to 0.2
            dynamics.add_coherence_sample(coherence, timestamp=float(i))

        # Compute dissolution rate (lines 165-167: polyfit and return)
        rate = dynamics.compute_dissolution_rate()

        # Should compute a positive decay rate (coherence is decreasing)
        assert rate > 0, f"Expected positive decay rate, got {rate}"
        assert isinstance(rate, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
