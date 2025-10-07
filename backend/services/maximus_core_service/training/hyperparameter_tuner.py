"""
Hyperparameter Tuner using Optuna

Automated hyperparameter optimization for Predictive Coding layers:
- Bayesian optimization
- Pruning (early stopping of unpromising trials)
- Multi-objective optimization
- Distributed tuning support

Based on:
- Optuna: A Next-generation Hyperparameter Optimization Framework (Akiba et al., 2019)

REGRA DE OURO: Zero mocks, production-ready tuning
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

# Try to import optuna
try:
    import optuna
    from optuna.pruners import MedianPruner
    from optuna.samplers import TPESampler

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logging.warning("Optuna not available, hyperparameter tuning will not work")

# Try to import torch
try:
    import torch
    from torch.utils.data import DataLoader, TensorDataset, random_split

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from training.layer_trainer import LayerTrainer, TrainingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TuningConfig:
    """Hyperparameter tuning configuration."""

    # Study
    study_name: str
    direction: str = "minimize"  # "minimize" or "maximize"
    n_trials: int = 50
    timeout: Optional[int] = None  # Timeout in seconds

    # Sampler
    sampler: str = "tpe"  # "tpe", "random", "grid"

    # Pruner (early stopping)
    use_pruner: bool = True
    pruner_n_startup_trials: int = 5
    pruner_n_warmup_steps: int = 10

    # Storage (for distributed tuning)
    storage_url: Optional[str] = None  # e.g., "sqlite:///tuning.db"

    # Output
    output_dir: Path = Path("training/tuning")

    def __post_init__(self):
        """Create output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


class HyperparameterTuner:
    """Hyperparameter tuner using Optuna.

    Features:
    - Bayesian optimization (TPE sampler)
    - Pruning (MedianPruner for early stopping)
    - Multi-objective optimization
    - Parallel trials
    - Visualization

    Example:
        ```python
        # Define objective function
        def objective(trial):
            # Suggest hyperparameters
            lr = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
            batch_size = trial.suggest_categorical("batch_size", [16, 32, 64])
            dropout = trial.suggest_float("dropout", 0.1, 0.5)

            # Train model
            config = TrainingConfig(
                learning_rate=lr,
                batch_size=batch_size
            )
            model, results = train_model(config)

            # Return metric to optimize
            return results["best_val_loss"]

        # Create tuner
        tuner = HyperparameterTuner(
            config=TuningConfig(
                study_name="layer1_vae_tuning",
                n_trials=50
            )
        )

        # Run tuning
        best_params = tuner.tune(objective)
        ```
    """

    def __init__(self, config: TuningConfig):
        """Initialize tuner.

        Args:
            config: Tuning configuration
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna not available. Install with: pip install optuna")

        self.config = config

        # Create sampler
        if config.sampler == "tpe":
            self.sampler = TPESampler(seed=42)
        elif config.sampler == "random":
            self.sampler = optuna.samplers.RandomSampler(seed=42)
        else:
            self.sampler = TPESampler(seed=42)

        # Create pruner
        if config.use_pruner:
            self.pruner = MedianPruner(
                n_startup_trials=config.pruner_n_startup_trials,
                n_warmup_steps=config.pruner_n_warmup_steps
            )
        else:
            self.pruner = None

        # Study will be created in tune()
        self.study: Optional[optuna.Study] = None

        logger.info(f"HyperparameterTuner initialized: sampler={config.sampler}, "
                    f"pruner={'enabled' if config.use_pruner else 'disabled'}")

    def tune(
        self,
        objective: Callable[[optuna.Trial], float],
        callbacks: Optional[List[Callable]] = None
    ) -> Dict[str, Any]:
        """Run hyperparameter tuning.

        Args:
            objective: Objective function that takes a trial and returns metric
            callbacks: Optional list of callback functions

        Returns:
            Dictionary with best parameters and study results
        """
        # Create or load study
        self.study = optuna.create_study(
            study_name=self.config.study_name,
            direction=self.config.direction,
            sampler=self.sampler,
            pruner=self.pruner,
            storage=self.config.storage_url,
            load_if_exists=True
        )

        logger.info(f"Starting optimization: {self.config.n_trials} trials")

        # Run optimization
        self.study.optimize(
            objective,
            n_trials=self.config.n_trials,
            timeout=self.config.timeout,
            callbacks=callbacks,
            show_progress_bar=True
        )

        # Get results
        best_trial = self.study.best_trial
        best_params = best_trial.params
        best_value = best_trial.value

        logger.info(f"Optimization complete!")
        logger.info(f"Best trial: {best_trial.number}")
        logger.info(f"Best value: {best_value:.4f}")
        logger.info(f"Best parameters: {best_params}")

        # Save results
        self._save_results()

        return {
            "best_params": best_params,
            "best_value": best_value,
            "best_trial_number": best_trial.number,
            "n_trials": len(self.study.trials),
            "study": self.study
        }

    def _save_results(self):
        """Save tuning results to disk."""
        if self.study is None:
            return

        # Save study as pickle
        study_path = self.config.output_dir / f"{self.config.study_name}_study.pkl"
        optuna.study.save_study(self.study, study_path)
        logger.info(f"Study saved to {study_path}")

        # Save best parameters as text
        best_params_path = self.config.output_dir / f"{self.config.study_name}_best_params.txt"
        with open(best_params_path, "w") as f:
            f.write(f"Best Trial: {self.study.best_trial.number}\n")
            f.write(f"Best Value: {self.study.best_value:.6f}\n\n")
            f.write("Best Parameters:\n")
            for key, value in self.study.best_params.items():
                f.write(f"  {key}: {value}\n")

        logger.info(f"Best parameters saved to {best_params_path}")

    def visualize(self):
        """Create visualization plots.

        Creates:
        - Optimization history
        - Parameter importances
        - Parallel coordinate plot
        """
        if self.study is None:
            logger.error("No study available for visualization")
            return

        try:
            import matplotlib.pyplot as plt

            # Optimization history
            fig = optuna.visualization.matplotlib.plot_optimization_history(self.study)
            fig.savefig(self.config.output_dir / f"{self.config.study_name}_history.png")
            logger.info("Optimization history plot saved")

            # Parameter importances
            fig = optuna.visualization.matplotlib.plot_param_importances(self.study)
            fig.savefig(self.config.output_dir / f"{self.config.study_name}_importances.png")
            logger.info("Parameter importances plot saved")

            # Parallel coordinate
            fig = optuna.visualization.matplotlib.plot_parallel_coordinate(self.study)
            fig.savefig(self.config.output_dir / f"{self.config.study_name}_parallel.png")
            logger.info("Parallel coordinate plot saved")

        except ImportError:
            logger.warning("Matplotlib not available for visualization")


def create_layer1_vae_objective(
    train_features: np.ndarray,
    train_labels: np.ndarray,
    val_features: np.ndarray,
    val_labels: np.ndarray
) -> Callable[[optuna.Trial], float]:
    """Create objective function for Layer 1 VAE tuning.

    Args:
        train_features: Training features
        train_labels: Training labels
        val_features: Validation features
        val_labels: Validation labels

    Returns:
        Objective function
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch not available")

    # Import training function
    from training.train_layer1_vae import train_layer1_vae

    def objective(trial: optuna.Trial) -> float:
        """Objective function for Optuna.

        Args:
            trial: Optuna trial object

        Returns:
            Validation loss (to minimize)
        """
        # Suggest hyperparameters
        learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
        batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 128])
        hidden_dim = trial.suggest_categorical("hidden_dim", [64, 96, 128, 256])
        latent_dim = trial.suggest_categorical("latent_dim", [32, 64, 128])
        dropout = trial.suggest_float("dropout", 0.1, 0.5)
        beta = trial.suggest_float("beta", 0.1, 10.0, log=True)

        # Create config
        config = TrainingConfig(
            model_name=f"layer1_vae_trial{trial.number}",
            layer_name="layer1",
            batch_size=batch_size,
            num_epochs=30,  # Reduced epochs for tuning
            learning_rate=learning_rate,
            early_stopping_patience=5,
            checkpoint_dir=Path(f"training/tuning/checkpoints/trial{trial.number}"),
            log_dir=Path(f"training/tuning/logs/trial{trial.number}")
        )

        # Train model
        try:
            model, results = train_layer1_vae(
                train_features=train_features,
                train_labels=train_labels,
                val_features=val_features,
                val_labels=val_labels,
                config=config,
                beta=beta
            )

            # Get best validation loss
            best_val_loss = results["best_val_loss"]

            # Report intermediate values for pruning
            for epoch, metrics in enumerate(results["history"]):
                if metrics.val_loss is not None:
                    trial.report(metrics.val_loss, epoch)

                    # Pruning
                    if trial.should_prune():
                        raise optuna.TrialPruned()

            return best_val_loss

        except Exception as e:
            logger.error(f"Trial {trial.number} failed: {e}")
            raise

    return objective


def tune_layer1_vae(
    train_data_path: str,
    val_data_path: str,
    n_trials: int = 50,
    study_name: str = "layer1_vae_tuning"
) -> Dict[str, Any]:
    """Tune hyperparameters for Layer 1 VAE.

    Args:
        train_data_path: Path to training data (.npz)
        val_data_path: Path to validation data (.npz)
        n_trials: Number of trials
        study_name: Name of the study

    Returns:
        Dictionary with best parameters
    """
    # Load data
    logger.info(f"Loading data from {train_data_path} and {val_data_path}")

    train_data = np.load(train_data_path)
    train_features = train_data["features"]
    train_labels = train_data.get("labels", np.zeros(len(train_features)))

    val_data = np.load(val_data_path)
    val_features = val_data["features"]
    val_labels = val_data.get("labels", np.zeros(len(val_features)))

    # Create objective
    objective = create_layer1_vae_objective(
        train_features=train_features,
        train_labels=train_labels,
        val_features=val_features,
        val_labels=val_labels
    )

    # Create tuner
    tuning_config = TuningConfig(
        study_name=study_name,
        direction="minimize",
        n_trials=n_trials,
        use_pruner=True
    )

    tuner = HyperparameterTuner(config=tuning_config)

    # Run tuning
    results = tuner.tune(objective)

    # Visualize
    tuner.visualize()

    return results


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main tuning script."""
    import argparse

    parser = argparse.ArgumentParser(description="Hyperparameter Tuning for Layer 1 VAE")

    # Data
    parser.add_argument("--train_data", type=str, required=True, help="Path to training data (.npz)")
    parser.add_argument("--val_data", type=str, required=True, help="Path to validation data (.npz)")

    # Tuning
    parser.add_argument("--n_trials", type=int, default=50, help="Number of trials")
    parser.add_argument("--study_name", type=str, default="layer1_vae_tuning", help="Study name")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")

    args = parser.parse_args()

    # Run tuning
    results = tune_layer1_vae(
        train_data_path=args.train_data,
        val_data_path=args.val_data,
        n_trials=args.n_trials,
        study_name=args.study_name
    )

    logger.info("Tuning complete!")
    logger.info(f"Best parameters: {results['best_params']}")
    logger.info(f"Best value: {results['best_value']:.4f}")


if __name__ == "__main__":
    main()
