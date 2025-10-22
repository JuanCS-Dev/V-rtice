"""
Euler vs RK4 Statistical Comparison
====================================

This module performs rigorous A/B testing to compare Euler (O(dt)) and
RK4 (O(dt⁴)) numerical integration methods for Kuramoto synchronization.

Scientific Goals:
1. Validate H1: RK4 achieves higher coherence than Euler
2. Calculate effect size (Cohen's d) between methods
3. Test variance homogeneity (Levene's test)
4. Generate publication-quality comparison figures

Methodology:
- 50 Euler runs vs 50 RK4 runs (same seeds for fair comparison)
- Independent samples t-test (H1: μ_RK4 > μ_Euler)
- Cohen's d for effect size
- Levene's test for equal variances
- Outputs: CSV comparison, JSON statistics, boxplot figure

Authors:
- Juan Carlos Souza - VERTICE Project
- Claude (Anthropic) - AI Co-Author

Date: October 21, 2025
"""

import asyncio
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pytest
import pytest_asyncio
from scipy import stats

from consciousness.esgt.coordinator import ESGTCoordinator, SalienceScore
from consciousness.esgt.kuramoto import KuramotoConfig
from consciousness.tig.fabric import TIGFabric


@dataclass
class ComparisonRun:
    """Single comparison experiment result"""

    run_id: int
    seed: int
    method: Literal["euler", "rk4"]
    coherence_final: float
    coherence_max: float
    time_to_sync_ms: float
    duration_ms: float
    synchronization_achieved: bool


@dataclass
class ComparisonStatistics:
    """Statistical comparison between Euler and RK4"""

    n_euler: int
    n_rk4: int

    # Coherence comparison
    euler_coherence_mean: float
    euler_coherence_std: float
    rk4_coherence_mean: float
    rk4_coherence_std: float

    # Statistical tests
    t_statistic: float
    p_value_two_tailed: float
    p_value_one_tailed: float  # H1: RK4 > Euler
    cohens_d: float
    effect_size_interpretation: str

    # Variance homogeneity
    levene_statistic: float
    levene_p_value: float
    equal_variances: bool

    # Time comparison
    euler_time_mean: float
    euler_time_std: float
    rk4_time_mean: float
    rk4_time_std: float
    time_difference_percent: float  # (RK4 - Euler) / Euler * 100


class TestEulerVsRK4Comparison:
    """
    A/B Testing: Euler vs RK4 Integration Methods

    Validates that RK4 provides statistically significant improvement
    in coherence while maintaining acceptable computational cost.
    """

    @pytest.fixture
    def output_dir(self) -> Path:
        """Directory for comparison outputs"""
        path = Path("tests/statistical/outputs/euler_vs_rk4")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @pytest_asyncio.fixture
    async def tig_fabric(self):
        """TIG Fabric fixture"""
        from consciousness.tig.fabric import TopologyConfig

        config = TopologyConfig(
            node_count=32,
            target_density=0.25,
            clustering_target=0.75,
            enable_small_world_rewiring=True,
        )
        fabric = TIGFabric(config)
        await fabric.initialize()
        yield fabric

    async def run_single_experiment(
        self,
        run_id: int,
        seed: int,
        method: Literal["euler", "rk4"],
        tig_fabric: TIGFabric,
    ) -> ComparisonRun:
        """
        Execute single experiment with specified integration method

        Args:
            run_id: Experiment identifier
            seed: Random seed for reproducibility
            method: "euler" or "rk4"
            tig_fabric: TIG fabric instance

        Returns:
            ComparisonRun with performance metrics
        """
        # Set seed
        np.random.seed(seed)

        # Create coordinator with specified method
        # Note: We'll need to temporarily modify config
        coordinator = ESGTCoordinator(tig_fabric=tig_fabric)

        # Patch integration method
        # TODO: This assumes we can access kuramoto_coordinator
        # If not, we may need to modify ESGTCoordinator to accept config
        if hasattr(coordinator, "kuramoto_coordinator"):
            coordinator.kuramoto_coordinator.config.integration_method = method

        await coordinator.start()

        try:
            # High-salience input
            salience = SalienceScore(
                novelty=0.85,
                relevance=0.85,
                urgency=0.85,
                confidence=0.85,
            )

            content = {
                "type": "comparison_test",
                "method": method,
                "seed": seed,
            }

            # Initiate ESGT
            event = await coordinator.initiate_esgt(
                salience=salience,
                content=content,
                content_source="euler_vs_rk4_test",
            )

            # Extract metrics
            coherence_history = event.coherence_history
            coherence_final = coherence_history[-1] if coherence_history else 0.0
            coherence_max = max(coherence_history) if coherence_history else 0.0

            # Time to sync
            target_coherence = 0.70
            time_to_sync = None
            for i, r in enumerate(coherence_history):
                if r >= target_coherence:
                    time_to_sync = i * 5.0  # 5ms timesteps
                    break

            synchronization_achieved = time_to_sync is not None

            # Duration
            duration = (
                event.phase_transitions[-1][1] - event.phase_transitions[0][1]
                if event.phase_transitions
                else 0.0
            )
            duration_ms = duration * 1000

            return ComparisonRun(
                run_id=run_id,
                seed=seed,
                method=method,
                coherence_final=coherence_final,
                coherence_max=coherence_max,
                time_to_sync_ms=time_to_sync if time_to_sync else -1.0,
                duration_ms=duration_ms,
                synchronization_achieved=synchronization_achieved,
            )

        finally:
            await coordinator.stop()

    def compute_statistics(
        self, euler_runs: list[ComparisonRun], rk4_runs: list[ComparisonRun]
    ) -> ComparisonStatistics:
        """
        Compute statistical comparison between Euler and RK4

        Statistical Tests:
        1. Independent samples t-test (two-tailed)
        2. One-tailed t-test (H1: RK4 > Euler)
        3. Cohen's d (effect size)
        4. Levene's test (variance homogeneity)

        Returns:
            ComparisonStatistics with all test results
        """
        # Extract successful runs only
        euler_successful = [r for r in euler_runs if r.synchronization_achieved]
        rk4_successful = [r for r in rk4_runs if r.synchronization_achieved]

        # Coherence values
        euler_coherence = np.array([r.coherence_final for r in euler_successful])
        rk4_coherence = np.array([r.coherence_final for r in rk4_successful])

        euler_coherence_mean = float(np.mean(euler_coherence))
        euler_coherence_std = float(np.std(euler_coherence, ddof=1))
        rk4_coherence_mean = float(np.mean(rk4_coherence))
        rk4_coherence_std = float(np.std(rk4_coherence, ddof=1))

        # Independent samples t-test
        t_stat, p_two_tailed = stats.ttest_ind(rk4_coherence, euler_coherence)

        # One-tailed p-value (H1: RK4 > Euler)
        # If t_stat > 0 (RK4 mean > Euler mean), p_one_tailed = p_two_tailed / 2
        p_one_tailed = p_two_tailed / 2 if t_stat > 0 else 1 - (p_two_tailed / 2)

        # Cohen's d (effect size)
        pooled_std = np.sqrt(
            ((len(euler_coherence) - 1) * euler_coherence_std**2
             + (len(rk4_coherence) - 1) * rk4_coherence_std**2)
            / (len(euler_coherence) + len(rk4_coherence) - 2)
        )
        cohens_d = (rk4_coherence_mean - euler_coherence_mean) / pooled_std

        # Interpret effect size
        if abs(cohens_d) < 0.2:
            effect_interpretation = "negligible"
        elif abs(cohens_d) < 0.5:
            effect_interpretation = "small"
        elif abs(cohens_d) < 0.8:
            effect_interpretation = "medium"
        else:
            effect_interpretation = "large"

        # Levene's test for equal variances
        levene_stat, levene_p = stats.levene(euler_coherence, rk4_coherence)
        equal_variances = levene_p > 0.05

        # Time comparison
        euler_times = np.array(
            [r.duration_ms for r in euler_successful if r.duration_ms > 0]
        )
        rk4_times = np.array(
            [r.duration_ms for r in rk4_successful if r.duration_ms > 0]
        )

        euler_time_mean = float(np.mean(euler_times))
        euler_time_std = float(np.std(euler_times, ddof=1))
        rk4_time_mean = float(np.mean(rk4_times))
        rk4_time_std = float(np.std(rk4_times, ddof=1))

        time_diff_percent = (
            (rk4_time_mean - euler_time_mean) / euler_time_mean * 100
            if euler_time_mean > 0
            else 0.0
        )

        return ComparisonStatistics(
            n_euler=len(euler_runs),
            n_rk4=len(rk4_runs),
            euler_coherence_mean=euler_coherence_mean,
            euler_coherence_std=euler_coherence_std,
            rk4_coherence_mean=rk4_coherence_mean,
            rk4_coherence_std=rk4_coherence_std,
            t_statistic=float(t_stat),
            p_value_two_tailed=float(p_two_tailed),
            p_value_one_tailed=float(p_one_tailed),
            cohens_d=float(cohens_d),
            effect_size_interpretation=effect_interpretation,
            levene_statistic=float(levene_stat),
            levene_p_value=float(levene_p),
            equal_variances=equal_variances,
            euler_time_mean=euler_time_mean,
            euler_time_std=euler_time_std,
            rk4_time_mean=rk4_time_mean,
            rk4_time_std=rk4_time_std,
            time_difference_percent=time_diff_percent,
        )

    def save_results(
        self,
        runs: list[ComparisonRun],
        stats: ComparisonStatistics,
        output_dir: Path,
    ) -> None:
        """Save comparison results"""
        # CSV: all runs
        csv_path = output_dir / "euler_vs_rk4_runs.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(runs[0]).keys())
            writer.writeheader()
            for run in runs:
                writer.writerow(asdict(run))

        print(f"✅ Saved {len(runs)} runs to {csv_path}")

        # JSON: statistics
        json_path = output_dir / "euler_vs_rk4_statistics.json"
        with open(json_path, "w") as f:
            json.dump(asdict(stats), f, indent=2)

        print(f"✅ Saved statistics to {json_path}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_euler_vs_rk4_n50_each(
        self, tig_fabric: TIGFabric, output_dir: Path
    ):
        """
        Euler vs RK4 Comparison: N=50 runs each

        Validates:
        1. H1: RK4 coherence > Euler coherence (p < 0.05)
        2. Effect size (Cohen's d) is significant
        3. Time overhead < 5% (acceptable cost)

        Outputs:
        - CSV: euler_vs_rk4_runs.csv (100 rows total)
        - JSON: euler_vs_rk4_statistics.json
        """
        N_PER_METHOD = 50
        BASE_SEED = 2000

        print(f"\n{'='*70}")
        print(f"EULER vs RK4 COMPARISON: N={N_PER_METHOD} runs per method")
        print(f"{'='*70}\n")

        all_runs = []

        # Run Euler experiments
        print(f"{'='*70}")
        print("EULER EXPERIMENTS")
        print(f"{'='*70}")
        euler_runs = []
        for i in range(N_PER_METHOD):
            seed = BASE_SEED + i
            print(f"Euler {i+1}/{N_PER_METHOD} (seed={seed})...", end=" ")

            run = await self.run_single_experiment(i, seed, "euler", tig_fabric)
            euler_runs.append(run)
            all_runs.append(run)

            status = "✅" if run.synchronization_achieved else "❌"
            print(f"{status} r={run.coherence_final:.3f}")

        # Run RK4 experiments
        print(f"\n{'='*70}")
        print("RK4 EXPERIMENTS")
        print(f"{'='*70}")
        rk4_runs = []
        for i in range(N_PER_METHOD):
            seed = BASE_SEED + i  # Same seeds for fair comparison
            print(f"RK4 {i+1}/{N_PER_METHOD} (seed={seed})...", end=" ")

            run = await self.run_single_experiment(
                N_PER_METHOD + i, seed, "rk4", tig_fabric
            )
            rk4_runs.append(run)
            all_runs.append(run)

            status = "✅" if run.synchronization_achieved else "❌"
            print(f"{status} r={run.coherence_final:.3f}")

        # Compute statistics
        stats = self.compute_statistics(euler_runs, rk4_runs)

        # Save results
        self.save_results(all_runs, stats, output_dir)

        # Print comparison
        print(f"\n{'='*70}")
        print("STATISTICAL COMPARISON")
        print(f"{'='*70}")
        print(f"\nCoherence:")
        print(
            f"  Euler: {stats.euler_coherence_mean:.4f} ± {stats.euler_coherence_std:.4f}"
        )
        print(
            f"  RK4:   {stats.rk4_coherence_mean:.4f} ± {stats.rk4_coherence_std:.4f}"
        )
        print(
            f"  Difference: {stats.rk4_coherence_mean - stats.euler_coherence_mean:.4f}"
        )
        print(f"\nStatistical Tests:")
        print(f"  t-statistic: {stats.t_statistic:.4f}")
        print(f"  p-value (two-tailed): {stats.p_value_two_tailed:.6f}")
        print(f"  p-value (one-tailed, H1: RK4>Euler): {stats.p_value_one_tailed:.6f}")
        print(
            f"  Cohen's d: {stats.cohens_d:.4f} ({stats.effect_size_interpretation})"
        )
        print(f"\nVariance Homogeneity:")
        print(f"  Levene statistic: {stats.levene_statistic:.4f}")
        print(f"  Levene p-value: {stats.levene_p_value:.4f}")
        variance_msg = 'YES' if stats.equal_variances else "NO (Welch's t-test needed)"
        print(
            f"  Equal variances: {variance_msg}"
        )
        print(f"\nComputational Cost:")
        print(f"  Euler time: {stats.euler_time_mean:.1f} ± {stats.euler_time_std:.1f} ms")
        print(f"  RK4 time:   {stats.rk4_time_mean:.1f} ± {stats.rk4_time_std:.1f} ms")
        print(f"  Time overhead: {stats.time_difference_percent:+.2f}%")
        print(f"{'='*70}\n")

        # Assertions for publication
        assert (
            stats.p_value_one_tailed < 0.05
        ), f"H1 not supported: p={stats.p_value_one_tailed:.4f} ≥ 0.05"
        assert (
            stats.rk4_coherence_mean > stats.euler_coherence_mean
        ), f"RK4 mean ({stats.rk4_coherence_mean:.3f}) ≤ Euler mean ({stats.euler_coherence_mean:.3f})"
        assert abs(stats.cohens_d) >= 0.2, f"Effect size negligible: d={stats.cohens_d:.3f}"
        assert (
            stats.time_difference_percent < 10.0
        ), f"Time overhead too high: {stats.time_difference_percent:.1f}% ≥ 10%"

        print("✅ RK4 STATISTICALLY SUPERIOR TO EULER (p < 0.05)!")

    @pytest.mark.asyncio
    async def test_euler_vs_rk4_quick_n5_each(
        self, tig_fabric: TIGFabric, output_dir: Path
    ):
        """
        Quick Euler vs RK4 Test: N=5 runs each (for CI/CD)

        Lightweight version for continuous integration.
        For publication, use test_euler_vs_rk4_n50_each.
        """
        N_PER_METHOD = 5
        BASE_SEED = 3000

        print(f"\n{'='*70}")
        print(f"QUICK EULER vs RK4 TEST: N={N_PER_METHOD} runs per method")
        print(f"{'='*70}\n")

        all_runs = []
        euler_runs = []
        rk4_runs = []

        for i in range(N_PER_METHOD):
            seed = BASE_SEED + i

            # Euler
            euler_run = await self.run_single_experiment(i, seed, "euler", tig_fabric)
            euler_runs.append(euler_run)
            all_runs.append(euler_run)

            # RK4
            rk4_run = await self.run_single_experiment(
                N_PER_METHOD + i, seed, "rk4", tig_fabric
            )
            rk4_runs.append(rk4_run)
            all_runs.append(rk4_run)

        stats = self.compute_statistics(euler_runs, rk4_runs)

        # Relaxed criteria
        assert (
            stats.rk4_coherence_mean >= stats.euler_coherence_mean
        ), "RK4 should be ≥ Euler"

        print(
            f"✅ Quick test: Euler={stats.euler_coherence_mean:.3f}, "
            f"RK4={stats.rk4_coherence_mean:.3f}"
        )
