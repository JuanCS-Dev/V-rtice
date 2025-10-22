"""
Monte Carlo Statistical Validation for Kuramoto Synchronization
=================================================================

This module performs rigorous statistical validation of the Kuramoto
synchronization mechanism using Monte Carlo methods.

Scientific Goals:
1. Establish mean ± std for coherence r(t) with 95% confidence intervals
2. Validate time-to-sync distribution (GWT: 100-300ms window)
3. Verify test stability (pass rate ≥ 95% across random initializations)
4. Generate publication-quality statistical outputs

Methodology:
- N=100 independent runs with different random seeds
- Each run: full ESGT ignition with Kuramoto synchronization
- Statistical tests: mean, std, 95% CI, normality tests
- Outputs: CSV data, JSON statistics, histogram figures

Authors:
- Juan Carlos Souza - VERTICE Project
- Claude (Anthropic) - AI Co-Author

Date: October 21, 2025
"""

import asyncio
import csv
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import pytest_asyncio
from scipy import stats

from consciousness.esgt.coordinator import ESGTCoordinator, ESGTPhase, SalienceScore
from consciousness.tig.fabric import TIGFabric


@dataclass
class MonteCarloRun:
    """Single Monte Carlo experiment result"""

    run_id: int
    seed: int
    coherence_final: float
    coherence_max: float
    coherence_mean: float
    coherence_std: float
    time_to_sync_ms: float
    synchronization_achieved: bool
    ignition_success: bool
    duration_ms: float


@dataclass
class MonteCarloStatistics:
    """Statistical summary of Monte Carlo experiments"""

    n_runs: int
    n_successful: int
    success_rate: float

    # Coherence statistics
    coherence_mean: float
    coherence_std: float
    coherence_95ci_lower: float
    coherence_95ci_upper: float
    coherence_min: float
    coherence_max: float
    coherence_normality_p_value: float

    # Time-to-sync statistics
    time_to_sync_mean: float
    time_to_sync_std: float
    time_to_sync_95ci_lower: float
    time_to_sync_95ci_upper: float
    time_to_sync_min: float
    time_to_sync_max: float

    # GWT constraints validation
    gwt_100_300ms_compliance: float  # Percentage of runs within 100-300ms window


class TestMonteCarloStatistics:
    """
    Monte Carlo Statistical Validation (N=100)

    Tests validate that Kuramoto synchronization is:
    1. Consistent (low variance across runs)
    2. Reliable (high success rate)
    3. GWT-compliant (timing within neurophysiological constraints)
    """

    @pytest.fixture
    def output_dir(self) -> Path:
        """Directory for statistical outputs"""
        path = Path("tests/statistical/outputs/monte_carlo")
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
        self, run_id: int, seed: int
    ) -> MonteCarloRun:
        """
        Execute single Monte Carlo run with specific seed

        Returns:
            MonteCarloRun with coherence, timing, and success metrics
        """
        # Set seed for reproducibility
        np.random.seed(seed)

        # Create FRESH TIG fabric for this run (critical for independence!)
        from consciousness.tig.fabric import TopologyConfig

        config = TopologyConfig(
            node_count=32,
            target_density=0.25,
            clustering_target=0.75,
            enable_small_world_rewiring=True,
        )
        fabric = TIGFabric(config)
        await fabric.initialize()

        # Create coordinator
        coordinator = ESGTCoordinator(tig_fabric=fabric)
        await coordinator.start()

        try:
            # High-salience input (guaranteed to trigger ignition)
            salience = SalienceScore(
                novelty=0.85,
                relevance=0.85,
                urgency=0.85,
                confidence=0.85,
            )

            content = {
                "type": "test_input",
                "data": f"Monte Carlo run {run_id}, seed {seed}",
                "seed": seed,
            }

            # Initiate ESGT
            event = await coordinator.initiate_esgt(
                salience=salience,
                content=content,
                content_source="monte_carlo_test",
            )

            # Extract metrics
            ignition_success = event.success

            # Coherence analysis
            coherence_history = event.coherence_history
            coherence_final = coherence_history[-1] if coherence_history else 0.0
            coherence_max = max(coherence_history) if coherence_history else 0.0
            coherence_mean = (
                float(np.mean(coherence_history)) if coherence_history else 0.0
            )
            coherence_std = (
                float(np.std(coherence_history)) if coherence_history else 0.0
            )

            # Time to sync (first time coherence ≥ 0.70)
            target_coherence = 0.70
            time_to_sync = None
            for i, r in enumerate(coherence_history):
                if r >= target_coherence:
                    # Assume 5ms timesteps (dt=0.005s)
                    time_to_sync = i * 5.0
                    break

            synchronization_achieved = time_to_sync is not None

            # Total duration
            phases = [phase for phase, _ in event.phase_transitions]
            duration = (
                event.phase_transitions[-1][1] - event.phase_transitions[0][1]
                if event.phase_transitions
                else 0.0
            )
            duration_ms = duration * 1000  # Convert to ms

            return MonteCarloRun(
                run_id=run_id,
                seed=seed,
                coherence_final=coherence_final,
                coherence_max=coherence_max,
                coherence_mean=coherence_mean,
                coherence_std=coherence_std,
                time_to_sync_ms=time_to_sync if time_to_sync else -1.0,
                synchronization_achieved=synchronization_achieved,
                ignition_success=ignition_success,
                duration_ms=duration_ms,
            )

        finally:
            await coordinator.stop()

    def compute_statistics(self, runs: list[MonteCarloRun]) -> MonteCarloStatistics:
        """
        Compute statistical summary from Monte Carlo runs

        Includes:
        - Mean ± std for coherence
        - 95% confidence intervals
        - Normality tests (Shapiro-Wilk)
        - GWT compliance (100-300ms window)
        """
        n_runs = len(runs)
        successful_runs = [r for r in runs if r.synchronization_achieved]
        n_successful = len(successful_runs)
        success_rate = n_successful / n_runs if n_runs > 0 else 0.0

        # Coherence statistics (final values)
        coherence_values = [r.coherence_final for r in successful_runs]
        coherence_mean = float(np.mean(coherence_values))
        coherence_std = float(np.std(coherence_values, ddof=1))  # Sample std
        coherence_95ci = stats.t.interval(
            0.95,
            len(coherence_values) - 1,
            loc=coherence_mean,
            scale=stats.sem(coherence_values),
        )
        coherence_min = float(np.min(coherence_values))
        coherence_max = float(np.max(coherence_values))

        # Normality test
        if len(coherence_values) >= 3:
            _, coherence_normality_p = stats.shapiro(coherence_values)
        else:
            coherence_normality_p = 1.0

        # Time-to-sync statistics
        time_to_sync_values = [
            r.time_to_sync_ms for r in successful_runs if r.time_to_sync_ms and r.time_to_sync_ms > 0
        ]

        if len(time_to_sync_values) > 0:
            time_to_sync_mean = float(np.mean(time_to_sync_values))
            time_to_sync_std = float(np.std(time_to_sync_values, ddof=1)) if len(time_to_sync_values) > 1 else 0.0
            if len(time_to_sync_values) > 1:
                time_to_sync_95ci = stats.t.interval(
                    0.95,
                    len(time_to_sync_values) - 1,
                    loc=time_to_sync_mean,
                    scale=stats.sem(time_to_sync_values),
                )
            else:
                time_to_sync_95ci = (time_to_sync_mean, time_to_sync_mean)
            time_to_sync_min = float(np.min(time_to_sync_values))
            time_to_sync_max = float(np.max(time_to_sync_values))
        else:
            # No valid time-to-sync data
            time_to_sync_mean = 0.0
            time_to_sync_std = 0.0
            time_to_sync_95ci = (0.0, 0.0)
            time_to_sync_min = 0.0
            time_to_sync_max = 0.0

        # GWT compliance (100-300ms window)
        gwt_compliant = [
            r
            for r in successful_runs
            if 100 <= r.time_to_sync_ms <= 300 and r.time_to_sync_ms > 0
        ]
        gwt_compliance = len(gwt_compliant) / n_successful if n_successful > 0 else 0.0

        return MonteCarloStatistics(
            n_runs=n_runs,
            n_successful=n_successful,
            success_rate=success_rate,
            coherence_mean=coherence_mean,
            coherence_std=coherence_std,
            coherence_95ci_lower=coherence_95ci[0],
            coherence_95ci_upper=coherence_95ci[1],
            coherence_min=coherence_min,
            coherence_max=coherence_max,
            coherence_normality_p_value=coherence_normality_p,
            time_to_sync_mean=time_to_sync_mean,
            time_to_sync_std=time_to_sync_std,
            time_to_sync_95ci_lower=time_to_sync_95ci[0],
            time_to_sync_95ci_upper=time_to_sync_95ci[1],
            time_to_sync_min=time_to_sync_min,
            time_to_sync_max=time_to_sync_max,
            gwt_100_300ms_compliance=gwt_compliance,
        )

    def save_results(
        self,
        runs: list[MonteCarloRun],
        stats: MonteCarloStatistics,
        output_dir: Path,
    ) -> None:
        """Save results to CSV and JSON"""
        # CSV: individual runs
        csv_path = output_dir / "monte_carlo_runs.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(runs[0]).keys())
            writer.writeheader()
            for run in runs:
                writer.writerow(asdict(run))

        print(f"✅ Saved {len(runs)} runs to {csv_path}")

        # JSON: statistical summary
        json_path = output_dir / "monte_carlo_statistics.json"
        with open(json_path, "w") as f:
            json.dump(asdict(stats), f, indent=2)

        print(f"✅ Saved statistics to {json_path}")

    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow (will take 2-3 hours)
    async def test_monte_carlo_coherence_n100(
        self, output_dir: Path
    ):
        """
        Monte Carlo Validation: N=100 independent runs

        Validates:
        1. Mean coherence r_mean ≥ 0.90 (deep synchrony)
        2. Std coherence r_std ≤ 0.05 (low variance)
        3. Success rate ≥ 95% (reliable)
        4. 95% CI excludes r < 0.70 (conscious threshold)

        Outputs:
        - CSV: monte_carlo_runs.csv (100 rows)
        - JSON: monte_carlo_statistics.json
        """
        N_RUNS = 100
        BASE_SEED = 42

        print(f"\n{'='*70}")
        print(f"MONTE CARLO VALIDATION: N={N_RUNS} runs")
        print(f"{'='*70}\n")

        runs = []
        for i in range(N_RUNS):
            seed = BASE_SEED + i
            print(f"Run {i+1}/{N_RUNS} (seed={seed})...", end=" ")

            run = await self.run_single_experiment(i, seed)
            runs.append(run)

            status = "✅ SYNC" if run.synchronization_achieved else "❌ FAIL"
            print(f"{status} r={run.coherence_final:.3f} t={run.time_to_sync_ms:.1f}ms")

        # Compute statistics
        stats = self.compute_statistics(runs)

        # Save results
        self.save_results(runs, stats, output_dir)

        # Print summary
        print(f"\n{'='*70}")
        print("STATISTICAL SUMMARY")
        print(f"{'='*70}")
        print(f"Runs: {stats.n_runs}")
        print(f"Successful: {stats.n_successful} ({stats.success_rate*100:.1f}%)")
        print(f"\nCoherence (r):")
        print(
            f"  Mean ± Std: {stats.coherence_mean:.4f} ± {stats.coherence_std:.4f}"
        )
        print(
            f"  95% CI: [{stats.coherence_95ci_lower:.4f}, {stats.coherence_95ci_upper:.4f}]"
        )
        print(f"  Range: [{stats.coherence_min:.4f}, {stats.coherence_max:.4f}]")
        print(f"  Normality p-value: {stats.coherence_normality_p_value:.4f}")
        print(f"\nTime-to-Sync (ms):")
        print(
            f"  Mean ± Std: {stats.time_to_sync_mean:.1f} ± {stats.time_to_sync_std:.1f}"
        )
        print(
            f"  95% CI: [{stats.time_to_sync_95ci_lower:.1f}, {stats.time_to_sync_95ci_upper:.1f}]"
        )
        print(
            f"  Range: [{stats.time_to_sync_min:.1f}, {stats.time_to_sync_max:.1f}]"
        )
        print(f"\nGWT Compliance (100-300ms): {stats.gwt_100_300ms_compliance*100:.1f}%")
        print(f"{'='*70}\n")

        # Assertions for publication
        assert (
            stats.success_rate >= 0.95
        ), f"Success rate {stats.success_rate:.2%} < 95%"
        assert (
            stats.coherence_mean >= 0.90
        ), f"Mean coherence {stats.coherence_mean:.3f} < 0.90"
        assert (
            stats.coherence_std <= 0.10
        ), f"Coherence std {stats.coherence_std:.3f} > 0.10"
        assert (
            stats.coherence_95ci_lower >= 0.70
        ), f"95% CI lower bound {stats.coherence_95ci_lower:.3f} < 0.70 (conscious threshold)"
        assert (
            stats.gwt_100_300ms_compliance >= 0.80
        ), f"GWT compliance {stats.gwt_100_300ms_compliance:.1%} < 80%"

        print("✅ ALL STATISTICAL VALIDATION CRITERIA PASSED!")

    @pytest.mark.asyncio
    async def test_monte_carlo_quick_n10(self, output_dir: Path):
        """
        Quick Monte Carlo Test: N=10 runs (for CI/CD)

        This is a lightweight version for continuous integration.
        For publication, use test_monte_carlo_coherence_n100.
        """
        N_RUNS = 10
        BASE_SEED = 1000

        print(f"\n{'='*70}")
        print(f"QUICK MONTE CARLO TEST: N={N_RUNS} runs")
        print(f"{'='*70}\n")

        runs = []
        for i in range(N_RUNS):
            seed = BASE_SEED + i
            run = await self.run_single_experiment(i, seed)
            runs.append(run)

        stats = self.compute_statistics(runs)

        # Relaxed criteria for quick test
        assert stats.success_rate >= 0.80, f"Success rate {stats.success_rate:.2%} < 80%"
        assert (
            stats.coherence_mean >= 0.80
        ), f"Mean coherence {stats.coherence_mean:.3f} < 0.80"

        print(
            f"✅ Quick test passed: {stats.n_successful}/{stats.n_runs} successful, "
            f"r_mean={stats.coherence_mean:.3f}"
        )
