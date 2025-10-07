"""
Model Pruning for MAXIMUS

Prune neural networks for faster inference and smaller models:
- Structured pruning (remove filters/neurons)
- Unstructured pruning (remove individual weights)
- Magnitude-based pruning
- L1/L2 norm pruning
- Iterative pruning with fine-tuning
- Sparsity analysis

REGRA DE OURO: Zero mocks, production-ready pruning
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.utils.prune as prune
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PruningConfig:
    """Pruning configuration."""

    # Pruning type
    pruning_type: str = "unstructured"  # "unstructured", "structured"

    # Pruning method
    pruning_method: str = "l1"  # "l1", "random", "ln"

    # Sparsity
    target_sparsity: float = 0.5  # Target sparsity (0.0 to 1.0)

    # Iterative pruning
    iterative: bool = True
    num_iterations: int = 5

    # Fine-tuning
    finetune_epochs: int = 10

    # Layer selection
    skip_layers: List[str] = None

    # Output
    output_dir: Path = Path("models/pruned")

    def __post_init__(self):
        """Validate configuration."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.skip_layers is None:
            self.skip_layers = []

        if not 0.0 <= self.target_sparsity <= 1.0:
            raise ValueError(f"target_sparsity must be in [0, 1], got {self.target_sparsity}")


@dataclass
class PruningResult:
    """Pruning results."""

    # Sparsity metrics
    original_params: int
    pruned_params: int
    sparsity_achieved: float

    # Model size
    original_size_mb: float
    pruned_size_mb: float
    size_reduction_pct: float

    # Layer-wise sparsity
    layer_sparsity: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "original_params": self.original_params,
            "pruned_params": self.pruned_params,
            "sparsity_achieved": self.sparsity_achieved,
            "original_size_mb": self.original_size_mb,
            "pruned_size_mb": self.pruned_size_mb,
            "size_reduction_pct": self.size_reduction_pct,
            "layer_sparsity": self.layer_sparsity
        }


class ModelPruner:
    """Model pruning for inference optimization.

    Features:
    - Unstructured pruning (individual weights)
    - Structured pruning (entire filters/neurons)
    - Magnitude-based pruning (L1/L2)
    - Iterative pruning with gradual sparsity increase
    - Fine-tuning support
    - Sparsity analysis per layer

    Example:
        ```python
        # Simple unstructured pruning
        config = PruningConfig(
            pruning_type="unstructured",
            target_sparsity=0.5
        )

        pruner = ModelPruner(config=config)
        pruned_model = pruner.prune(model)

        # Iterative pruning with fine-tuning
        config = PruningConfig(
            pruning_type="unstructured",
            target_sparsity=0.7,
            iterative=True,
            num_iterations=5,
            finetune_epochs=10
        )

        pruner = ModelPruner(config=config)
        pruned_model = pruner.prune_iterative(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            loss_fn=loss_fn
        )
        ```
    """

    def __init__(self, config: PruningConfig = PruningConfig()):
        """Initialize pruner.

        Args:
            config: Pruning configuration
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required. Install with: pip install torch")

        self.config = config

        logger.info(f"ModelPruner initialized: type={config.pruning_type}, "
                   f"sparsity={config.target_sparsity}")

    def prune(self, model: nn.Module) -> nn.Module:
        """Prune model to target sparsity.

        Args:
            model: Model to prune

        Returns:
            Pruned model
        """
        logger.info(f"Pruning model with {self.config.pruning_type} pruning "
                   f"to {self.config.target_sparsity:.1%} sparsity")

        # Get pruneable layers
        layers_to_prune = self._get_pruneable_layers(model)

        # Apply pruning
        if self.config.pruning_type == "unstructured":
            model = self._unstructured_pruning(model, layers_to_prune)

        elif self.config.pruning_type == "structured":
            model = self._structured_pruning(model, layers_to_prune)

        else:
            raise ValueError(f"Unknown pruning type: {self.config.pruning_type}. "
                           f"Supported types: 'unstructured', 'structured'")

        # Make pruning permanent
        self._make_permanent(model, layers_to_prune)

        logger.info("Pruning complete")

        return model

    def prune_iterative(
        self,
        model: nn.Module,
        train_loader: Any,
        optimizer: Any,
        loss_fn: callable,
        device: str = "cpu"
    ) -> nn.Module:
        """Prune model iteratively with fine-tuning.

        Args:
            model: Model to prune
            train_loader: Training data loader
            optimizer: Optimizer for fine-tuning
            loss_fn: Loss function
            device: Device to train on

        Returns:
            Pruned model
        """
        logger.info(f"Starting iterative pruning: {self.config.num_iterations} iterations")

        model = model.to(device)

        # Calculate sparsity schedule
        sparsity_schedule = self._compute_sparsity_schedule()

        for iteration, target_sparsity in enumerate(sparsity_schedule, 1):
            logger.info(f"Iteration {iteration}/{self.config.num_iterations} - "
                       f"Target sparsity: {target_sparsity:.1%}")

            # Update config for this iteration
            original_sparsity = self.config.target_sparsity
            self.config.target_sparsity = target_sparsity

            # Prune
            model = self.prune(model)

            # Restore config
            self.config.target_sparsity = original_sparsity

            # Fine-tune
            if self.config.finetune_epochs > 0:
                logger.info(f"Fine-tuning for {self.config.finetune_epochs} epochs")
                model = self._finetune(
                    model=model,
                    train_loader=train_loader,
                    optimizer=optimizer,
                    loss_fn=loss_fn,
                    num_epochs=self.config.finetune_epochs,
                    device=device
                )

        logger.info("Iterative pruning complete")

        return model

    def analyze_sparsity(self, model: nn.Module) -> PruningResult:
        """Analyze model sparsity.

        Args:
            model: Model to analyze

        Returns:
            PruningResult with sparsity metrics
        """
        # Count parameters
        total_params = 0
        zero_params = 0
        layer_sparsity = {}

        for name, module in model.named_modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                if hasattr(module, "weight"):
                    weight = module.weight.data
                    total = weight.numel()
                    zeros = (weight == 0).sum().item()

                    total_params += total
                    zero_params += zeros

                    layer_sparsity[name] = zeros / total if total > 0 else 0.0

        # Calculate overall sparsity
        overall_sparsity = zero_params / total_params if total_params > 0 else 0.0

        # Calculate model sizes
        original_size = self._get_model_size(model)
        pruned_size = original_size * (1 - overall_sparsity)
        size_reduction = ((original_size - pruned_size) / original_size) * 100

        result = PruningResult(
            original_params=total_params,
            pruned_params=zero_params,
            sparsity_achieved=overall_sparsity,
            original_size_mb=original_size,
            pruned_size_mb=pruned_size,
            size_reduction_pct=size_reduction,
            layer_sparsity=layer_sparsity
        )

        return result

    def _get_pruneable_layers(self, model: nn.Module) -> List[Tuple[nn.Module, str]]:
        """Get layers that can be pruned.

        Args:
            model: Model

        Returns:
            List of (module, parameter_name) tuples
        """
        layers = []

        for name, module in model.named_modules():
            # Skip layers in skip list
            if any(skip in name for skip in self.config.skip_layers):
                continue

            # Only prune Linear and Conv layers
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                layers.append((module, "weight"))

        logger.debug(f"Found {len(layers)} pruneable layers")

        return layers

    def _unstructured_pruning(
        self,
        model: nn.Module,
        layers: List[Tuple[nn.Module, str]]
    ) -> nn.Module:
        """Apply unstructured pruning (individual weights).

        Args:
            model: Model
            layers: Layers to prune

        Returns:
            Pruned model
        """
        for module, param_name in layers:
            if self.config.pruning_method == "l1":
                prune.l1_unstructured(
                    module,
                    name=param_name,
                    amount=self.config.target_sparsity
                )

            elif self.config.pruning_method == "random":
                prune.random_unstructured(
                    module,
                    name=param_name,
                    amount=self.config.target_sparsity
                )

            elif self.config.pruning_method == "ln":
                prune.ln_structured(
                    module,
                    name=param_name,
                    amount=self.config.target_sparsity,
                    n=2,
                    dim=0
                )

            else:
                raise ValueError(f"Unknown pruning method: {self.config.pruning_method}")

        return model

    def _structured_pruning(
        self,
        model: nn.Module,
        layers: List[Tuple[nn.Module, str]]
    ) -> nn.Module:
        """Apply structured pruning (entire filters/neurons).

        Args:
            model: Model
            layers: Layers to prune

        Returns:
            Pruned model
        """
        for module, param_name in layers:
            # Structured pruning along dimension 0 (output channels/neurons)
            if self.config.pruning_method == "l1":
                prune.ln_structured(
                    module,
                    name=param_name,
                    amount=self.config.target_sparsity,
                    n=1,
                    dim=0
                )

            elif self.config.pruning_method == "ln":
                prune.ln_structured(
                    module,
                    name=param_name,
                    amount=self.config.target_sparsity,
                    n=2,
                    dim=0
                )

            elif self.config.pruning_method == "random":
                prune.random_structured(
                    module,
                    name=param_name,
                    amount=self.config.target_sparsity,
                    dim=0
                )

            else:
                raise ValueError(f"Pruning method {self.config.pruning_method} "
                               f"not supported for structured pruning")

        return model

    def _make_permanent(self, model: nn.Module, layers: List[Tuple[nn.Module, str]]):
        """Make pruning permanent by removing masks.

        Args:
            model: Model
            layers: Pruned layers
        """
        for module, param_name in layers:
            try:
                prune.remove(module, param_name)
            except ValueError:
                # Parameter was not pruned
                pass

    def _compute_sparsity_schedule(self) -> List[float]:
        """Compute sparsity schedule for iterative pruning.

        Returns:
            List of target sparsities for each iteration
        """
        # Linear schedule from 0 to target_sparsity
        schedule = np.linspace(
            0.0,
            self.config.target_sparsity,
            self.config.num_iterations + 1
        )[1:]  # Skip 0

        return schedule.tolist()

    def _finetune(
        self,
        model: nn.Module,
        train_loader: Any,
        optimizer: Any,
        loss_fn: callable,
        num_epochs: int,
        device: str
    ) -> nn.Module:
        """Fine-tune pruned model.

        Args:
            model: Pruned model
            train_loader: Training data
            optimizer: Optimizer
            loss_fn: Loss function
            num_epochs: Number of epochs
            device: Device

        Returns:
            Fine-tuned model
        """
        model.train()

        for epoch in range(1, num_epochs + 1):
            total_loss = 0.0
            num_batches = 0

            for batch in train_loader:
                # Move batch to device
                batch = self._batch_to_device(batch, device)

                # Forward pass
                loss = loss_fn(model, batch)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                num_batches += 1

            avg_loss = total_loss / num_batches if num_batches > 0 else 0.0

            logger.debug(f"Fine-tuning epoch {epoch}/{num_epochs} - Loss: {avg_loss:.4f}")

        return model

    def _batch_to_device(self, batch: Any, device: str) -> Any:
        """Move batch to device.

        Args:
            batch: Batch
            device: Device

        Returns:
            Batch on device
        """
        if isinstance(batch, torch.Tensor):
            return batch.to(device)

        elif isinstance(batch, (tuple, list)):
            return tuple(self._batch_to_device(x, device) for x in batch)

        elif isinstance(batch, dict):
            return {k: self._batch_to_device(v, device) for k, v in batch.items()}

        else:
            return batch

    def _get_model_size(self, model: nn.Module) -> float:
        """Get model size in MB.

        Args:
            model: Model

        Returns:
            Size in MB
        """
        import io

        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)

        size_mb = buffer.tell() / (1024 * 1024)

        return size_mb

    def save_model(self, model: nn.Module, filename: str):
        """Save pruned model.

        Args:
            model: Pruned model
            filename: Output filename
        """
        output_path = self.config.output_dir / filename

        torch.save(model.state_dict(), output_path)

        logger.info(f"Pruned model saved to {output_path}")

    def print_report(self, result: PruningResult):
        """Print pruning report.

        Args:
            result: Pruning result
        """
        print("\n" + "=" * 80)
        print("PRUNING REPORT")
        print("=" * 80)

        print(f"\nOverall:")
        print(f"  Total parameters: {result.original_params:,}")
        print(f"  Pruned parameters: {result.pruned_params:,}")
        print(f"  Sparsity achieved: {result.sparsity_achieved:.1%}")

        print(f"\nModel Size:")
        print(f"  Original: {result.original_size_mb:.2f} MB")
        print(f"  Pruned: {result.pruned_size_mb:.2f} MB")
        print(f"  Reduction: {result.size_reduction_pct:.1f}%")

        if result.layer_sparsity:
            print(f"\nLayer-wise Sparsity:")
            print(f"  {'Layer':>40} {'Sparsity':>15}")
            print("  " + "-" * 55)

            for layer_name, sparsity in sorted(result.layer_sparsity.items(),
                                              key=lambda x: x[1], reverse=True):
                print(f"  {layer_name:>40} {sparsity:>15.1%}")

        print("=" * 80)


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main pruning script."""
    import argparse

    parser = argparse.ArgumentParser(description="Prune MAXIMUS Models")

    parser.add_argument("--model_path", type=str, required=True, help="Path to model")
    parser.add_argument("--pruning_type", type=str, default="unstructured",
                       choices=["unstructured", "structured"],
                       help="Pruning type: unstructured (individual weights) or structured (filters)")
    parser.add_argument("--pruning_method", type=str, default="l1",
                       choices=["l1", "random", "ln"],
                       help="Pruning method: l1 (magnitude), random, or ln (norm)")
    parser.add_argument("--target_sparsity", type=float, default=0.5,
                       help="Target sparsity (0.0 to 1.0)")
    parser.add_argument("--output", type=str, default="model_pruned.pt",
                       help="Output filename")

    args = parser.parse_args()

    # Load model
    model = torch.load(args.model_path)

    # Create pruner
    config = PruningConfig(
        pruning_type=args.pruning_type,
        pruning_method=args.pruning_method,
        target_sparsity=args.target_sparsity
    )

    pruner = ModelPruner(config=config)

    # Prune
    pruned_model = pruner.prune(model)

    # Analyze
    result = pruner.analyze_sparsity(pruned_model)
    pruner.print_report(result)

    # Save
    pruner.save_model(pruned_model, args.output)


if __name__ == "__main__":
    main()
