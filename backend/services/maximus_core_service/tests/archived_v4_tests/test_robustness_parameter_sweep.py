"""
Robustness Analysis: Parameter Space Sweep
===========================================

This module validates that Kuramoto synchronization is robust across
a range of parameter values, not just optimally tuned settings.

Scientific Goals:
1. Map coherence landscape across parameter space (K, noise)
2. Identify stability regions where r ≥ 0.70 (conscious threshold)
3. Quantify sensitivity to parameter variations
4. Generate phase diagrams for publication

Methodology:
- Parameter grid: K ∈ [15, 20, 25], noise ∈ [0.0001, 0.001, 0.01]
- 9 combinations × 10 runs each = 90 total experiments
- For each combination: calculate mean ± std of coherence
- Validate robustness: mean r ≥ 0.70, std < 0.10
- Output: Parameter sweep CSV, phase diagram heatmap

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
from typing import Any

import numpy as np
import pytest
import pytest_asyncio
from scipy import stats

from consciousness.esgt.coordinator import ESGTCoordinator, SalienceScore
from consciousness.tig.fabric import TIGFabric


@dataclass
class ParameterSweepRun:
    """Single parameter sweep experiment"""

    coupling_k: float
    phase_noise: float
    run_id: int
    seed: int
    coherence_final: float
    coherence_max: float
    time_to_sync_ms: float
    synchronization_achieved: bool


@dataclass
class ParameterCombinationStats:
    """Statistics for a single (K, noise) combination"""

    coupling_k: float
    phase_noise: float
    n_runs: int
    n_successful: int
    success_rate: float
    coherence_mean: float
    coherence_std: float
    coherence_min: float
    coherence_max: float
    time_to_sync_mean: float
    time_to_sync_std: float
    robust: bool  # True if mean ≥ 0.70 and std < 0.10


@dataclass
class RobustnessAnalysis:
    """Overall robustness analysis"""

    total_combinations: int
    robust_combinations: int
    robustness_score: float  # Percentage of robust combinations
    optimal_k: float
    optimal_noise: float
    optimal_coherence: float


class TestRobustnessParameterSweep:
    """
    Parameter Space Robustness Validation

    Tests validate that synchronization is robust across parameter variations,
    not just a lucky tuning artifact.
    """

    @pytest.fixture
    def output_dir(self) -> Path:
        """Directory for robustness outputs"""
        path = Path("tests/statistical/outputs/robustness")
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
        coupling_k: float,
        phase_noise: float,
        run_id: int,
        seed: int,
        tig_fabric: TIGFabric,
    ) -> ParameterSweepRun:
        """
        Execute single experiment with specified parameters

        Args:
            coupling_k: Coupling strength K
            phase_noise: Phase noise magnitude
            run_id: Experiment identifier
            seed: Random seed
            tig_fabric: TIG fabric instance

        Returns:
            ParameterSweepRun with results
        """
        np.random.seed(seed)

        # Create coordinator
        coordinator = ESGTCoordinator(tig_fabric=tig_fabric)

        # Patch parameters
        if hasattr(coordinator, "kuramoto_coordinator"):
            coordinator.kuramoto_coordinator.config.coupling_strength = coupling_k
            coordinator.kuramoto_coordinator.config.phase_noise = phase_noise

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
                "type": "parameter_sweep",
                "K": coupling_k,
                "noise": phase_noise,
                "seed": seed,
            }

            # Initiate ESGT
            event = await coordinator.initiate_esgt(
                salience=salience,
                content=content,
                content_source="robustness_test",
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
                    time_to_sync = i * 5.0
                    break

            synchronization_achieved = time_to_sync is not None

            return ParameterSweepRun(
                coupling_k=coupling_k,
                phase_noise=phase_noise,
                run_id=run_id,
                seed=seed,
                coherence_final=coherence_final,
                coherence_max=coherence_max,
                time_to_sync_ms=time_to_sync if time_to_sync else -1.0,
                synchronization_achieved=synchronization_achieved,
            )

        finally:
            await coordinator.stop()

    def compute_combination_stats(
        self, runs: list[ParameterSweepRun]
    ) -> ParameterCombinationStats:
        """Compute statistics for a single parameter combination"""
        if not runs:
            raise ValueError("No runs provided")

        coupling_k = runs[0].coupling_k
        phase_noise = runs[0].phase_noise
        n_runs = len(runs)

        successful_runs = [r for r in runs if r.synchronization_achieved]
        n_successful = len(successful_runs)
        success_rate = n_successful / n_runs if n_runs > 0 else 0.0

        if successful_runs:
            coherence_values = [r.coherence_final for r in successful_runs]
            coherence_mean = float(np.mean(coherence_values))
            coherence_std = float(np.std(coherence_values, ddof=1))
            coherence_min = float(np.min(coherence_values))
            coherence_max = float(np.max(coherence_values))

            time_values = [
                r.time_to_sync_ms for r in successful_runs if r.time_to_sync_ms > 0
            ]
            time_to_sync_mean = float(np.mean(time_values)) if time_values else -1.0
            time_to_sync_std = (
                float(np.std(time_values, ddof=1)) if len(time_values) > 1 else 0.0
            )

            # Robustness criteria
            robust = coherence_mean >= 0.70 and coherence_std < 0.10
        else:
            coherence_mean = 0.0
            coherence_std = 0.0
            coherence_min = 0.0
            coherence_max = 0.0
            time_to_sync_mean = -1.0
            time_to_sync_std = 0.0
            robust = False

        return ParameterCombinationStats(
            coupling_k=coupling_k,
            phase_noise=phase_noise,
            n_runs=n_runs,
            n_successful=n_successful,
            success_rate=success_rate,
            coherence_mean=coherence_mean,
            coherence_std=coherence_std,
            coherence_min=coherence_min,
            coherence_max=coherence_max,
            time_to_sync_mean=time_to_sync_mean,
            time_to_sync_std=time_to_sync_std,
            robust=robust,
        )

    def compute_robustness_analysis(
        self, combination_stats: list[ParameterCombinationStats]
    ) -> RobustnessAnalysis:
        """Compute overall robustness analysis"""
        total_combinations = len(combination_stats)
        robust_combinations = sum(1 for s in combination_stats if s.robust)
        robustness_score = (
            robust_combinations / total_combinations if total_combinations > 0 else 0.0
        )

        # Find optimal parameters (highest coherence)
        optimal = max(combination_stats, key=lambda s: s.coherence_mean)
        optimal_k = optimal.coupling_k
        optimal_noise = optimal.phase_noise
        optimal_coherence = optimal.coherence_mean

        return RobustnessAnalysis(
            total_combinations=total_combinations,
            robust_combinations=robust_combinations,
            robustness_score=robustness_score,
            optimal_k=optimal_k,
            optimal_noise=optimal_noise,
            optimal_coherence=optimal_coherence,
        )

    def save_results(
        self,
        all_runs: list[ParameterSweepRun],
        combination_stats: list[ParameterCombinationStats],
        robustness: RobustnessAnalysis,
        output_dir: Path,
    ) -> None:
        """Save robustness results"""
        # CSV: all individual runs
        csv_runs_path = output_dir / "parameter_sweep_runs.csv"
        with open(csv_runs_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(all_runs[0]).keys())
            writer.writeheader()
            for run in all_runs:
                writer.writerow(asdict(run))

        print(f"✅ Saved {len(all_runs)} runs to {csv_runs_path}")

        # CSV: combination statistics
        csv_stats_path = output_dir / "parameter_combination_stats.csv"
        with open(csv_stats_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(combination_stats[0]).keys())
            writer.writeheader()
            for stat in combination_stats:
                writer.writerow(asdict(stat))

        print(f"✅ Saved {len(combination_stats)} combinations to {csv_stats_path}")

        # JSON: robustness analysis
        json_path = output_dir / "robustness_analysis.json"
        with open(json_path, "w") as f:
            json.dump(asdict(robustness), f, indent=2)

        print(f"✅ Saved robustness analysis to {json_path}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_parameter_sweep_3x3_grid_n10_each(
        self, tig_fabric: TIGFabric, output_dir: Path
    ):
        """
        Parameter Space Sweep: 3×3 grid, N=10 runs per combination

        Grid:
        - K (coupling): [15, 20, 25]
        - noise: [0.0001, 0.001, 0.01]
        - Total: 9 combinations × 10 runs = 90 experiments

        Validates:
        1. Robustness score ≥ 70% (at least 6/9 combinations are robust)
        2. Optimal parameters identified
        3. Coherence landscape mapped

        Outputs:
        - CSV: parameter_sweep_runs.csv (90 rows)
        - CSV: parameter_combination_stats.csv (9 rows)
        - JSON: robustness_analysis.json
        """
        # Parameter grid
        K_VALUES = [15.0, 20.0, 25.0]
        NOISE_VALUES = [0.0001, 0.001, 0.01]
        N_RUNS_PER_COMBINATION = 10
        BASE_SEED = 4000

        print(f"\n{'='*70}")
        print(
            f"PARAMETER SPACE SWEEP: {len(K_VALUES)}×{len(NOISE_VALUES)} grid, "
            f"N={N_RUNS_PER_COMBINATION} runs each"
        )
        print(f"{'='*70}\n")

        all_runs = []
        combination_stats = []

        run_counter = 0

        for k in K_VALUES:
            for noise in NOISE_VALUES:
                print(f"\n{'='*70}")
                print(f"K={k:.1f}, noise={noise:.4f}")
                print(f"{'='*70}")

                combination_runs = []

                for i in range(N_RUNS_PER_COMBINATION):
                    seed = BASE_SEED + run_counter
                    print(
                        f"  Run {i+1}/{N_RUNS_PER_COMBINATION} (seed={seed})...", end=" "
                    )

                    run = await self.run_single_experiment(
                        k, noise, run_counter, seed, tig_fabric
                    )
                    combination_runs.append(run)
                    all_runs.append(run)
                    run_counter += 1

                    status = "✅" if run.synchronization_achieved else "❌"
                    print(f"{status} r={run.coherence_final:.3f}")

                # Compute stats for this combination
                stats = self.compute_combination_stats(combination_runs)
                combination_stats.append(stats)

                robust_symbol = "🟢 ROBUST" if stats.robust else "🔴 NOT ROBUST"
                print(
                    f"\n  Summary: r_mean={stats.coherence_mean:.3f} ± {stats.coherence_std:.3f} "
                    f"({stats.n_successful}/{stats.n_runs} successful) {robust_symbol}"
                )

        # Overall robustness analysis
        robustness = self.compute_robustness_analysis(combination_stats)

        # Save results
        self.save_results(all_runs, combination_stats, robustness, output_dir)

        # Print robustness analysis
        print(f"\n{'='*70}")
        print("ROBUSTNESS ANALYSIS")
        print(f"{'='*70}")
        print(f"Total combinations tested: {robustness.total_combinations}")
        print(f"Robust combinations: {robustness.robust_combinations}")
        print(f"Robustness score: {robustness.robustness_score*100:.1f}%")
        print(f"\nOptimal parameters:")
        print(f"  K = {robustness.optimal_k:.1f}")
        print(f"  noise = {robustness.optimal_noise:.4f}")
        print(f"  coherence = {robustness.optimal_coherence:.3f}")
        print(f"\nRobustness Matrix:")
        header = "K \\ noise"
        print(f"{header:<12}", end="")
        for noise in NOISE_VALUES:
            print(f"{noise:>10.4f}", end="")
        print()

        for k in K_VALUES:
            print(f"{k:<12.1f}", end="")
            for noise in NOISE_VALUES:
                stat = next(
                    s for s in combination_stats if s.coupling_k == k and s.phase_noise == noise
                )
                symbol = "✅" if stat.robust else "❌"
                print(f"{stat.coherence_mean:>8.3f} {symbol}", end="")
            print()

        print(f"{'='*70}\n")

        # Assertions for publication
        assert (
            robustness.robustness_score >= 0.70
        ), f"Robustness score {robustness.robustness_score:.1%} < 70%"
        assert (
            robustness.optimal_coherence >= 0.90
        ), f"Optimal coherence {robustness.optimal_coherence:.3f} < 0.90"

        print("✅ SYSTEM IS ROBUST ACROSS PARAMETER VARIATIONS!")

    @pytest.mark.asyncio
    async def test_parameter_sweep_quick_2x2_n3_each(
        self, tig_fabric: TIGFabric, output_dir: Path
    ):
        """
        Quick Parameter Sweep: 2×2 grid, N=3 runs per combination (for CI/CD)

        Grid:
        - K: [18, 22]
        - noise: [0.001, 0.005]
        - Total: 4 combinations × 3 runs = 12 experiments

        Lightweight version for continuous integration.
        For publication, use test_parameter_sweep_3x3_grid_n10_each.
        """
        K_VALUES = [18.0, 22.0]
        NOISE_VALUES = [0.001, 0.005]
        N_RUNS_PER_COMBINATION = 3
        BASE_SEED = 5000

        print(f"\n{'='*70}")
        print(f"QUICK PARAMETER SWEEP: {len(K_VALUES)}×{len(NOISE_VALUES)} grid")
        print(f"{'='*70}\n")

        all_runs = []
        combination_stats = []
        run_counter = 0

        for k in K_VALUES:
            for noise in NOISE_VALUES:
                combination_runs = []
                for i in range(N_RUNS_PER_COMBINATION):
                    seed = BASE_SEED + run_counter
                    run = await self.run_single_experiment(
                        k, noise, run_counter, seed, tig_fabric
                    )
                    combination_runs.append(run)
                    all_runs.append(run)
                    run_counter += 1

                stats = self.compute_combination_stats(combination_runs)
                combination_stats.append(stats)

        robustness = self.compute_robustness_analysis(combination_stats)

        # Relaxed criteria
        assert robustness.robustness_score >= 0.50, "At least 50% should be robust"

        print(
            f"✅ Quick test: {robustness.robust_combinations}/{robustness.total_combinations} "
            f"robust ({robustness.robustness_score:.0%})"
        )
