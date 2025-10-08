"""
Distributed Training for MAXIMUS

Multi-node/multi-GPU distributed training:
- DistributedDataParallel (DDP)
- Distributed data sampling
- Gradient synchronization
- Rank-based logging
- Fault tolerance
- Model checkpointing

REGRA DE OURO: Zero mocks, production-ready distributed training
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Try to import PyTorch
try:
    import torch
    import torch.distributed as dist
    import torch.nn as nn
    from torch.nn.parallel import DistributedDataParallel as DDP
    from torch.utils.data import DataLoader, DistributedSampler

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DistributedConfig:
    """Distributed training configuration."""

    # Backend
    backend: str = "nccl"  # "nccl", "gloo", "mpi"

    # Initialization
    init_method: str = "env://"  # "env://", "tcp://..."
    world_size: int = 1  # Total number of processes
    rank: int = 0  # Process rank

    # Training
    batch_size_per_gpu: int = 32
    sync_batch_norm: bool = True
    find_unused_parameters: bool = False

    # Checkpointing
    save_checkpoint_rank: int = 0  # Only this rank saves checkpoints
    checkpoint_dir: Path = Path("checkpoints")

    # Logging
    log_rank: int = 0  # Only this rank logs


class DistributedTrainer:
    """Distributed training with DDP.

    Features:
    - Multi-node/multi-GPU training
    - Distributed data sampling
    - Synchronized batch normalization
    - Gradient all-reduce
    - Rank-aware checkpointing
    - Fault tolerance

    Example:
        ```python
        # Launch with:
        # torchrun --nproc_per_node=4 train_distributed.py

        config = DistributedConfig(backend="nccl", batch_size_per_gpu=32)

        trainer = DistributedTrainer(model=model, optimizer=optimizer, loss_fn=loss_fn, config=config)

        # Train
        history = trainer.train(train_dataset=train_dataset, val_dataset=val_dataset, num_epochs=100)
        ```
    """

    def __init__(self, model: Any, optimizer: Any, loss_fn: callable, config: DistributedConfig = DistributedConfig()):
        """Initialize distributed trainer.

        Args:
            model: Model to train
            optimizer: Optimizer
            loss_fn: Loss function
            config: Distributed configuration
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required. Install with: pip install torch")

        self.config = config
        self.loss_fn = loss_fn

        # Initialize distributed
        self._init_distributed()

        # Setup model
        self.model = self._setup_model(model)

        # Setup optimizer
        self.optimizer = optimizer

        logger.info(f"DistributedTrainer initialized on rank {self.rank}/{self.world_size}")

    def _init_distributed(self):
        """Initialize distributed process group."""
        # Check if already initialized
        if dist.is_initialized():
            self.rank = dist.get_rank()
            self.world_size = dist.get_world_size()
            self.local_rank = int(os.environ.get("LOCAL_RANK", 0))
            return

        # Get distributed parameters from environment
        self.rank = int(os.environ.get("RANK", self.config.rank))
        self.world_size = int(os.environ.get("WORLD_SIZE", self.config.world_size))
        self.local_rank = int(os.environ.get("LOCAL_RANK", 0))

        # Initialize process group
        if self.world_size > 1:
            dist.init_process_group(
                backend=self.config.backend,
                init_method=self.config.init_method,
                rank=self.rank,
                world_size=self.world_size,
            )

            logger.info(
                f"Initialized distributed: rank={self.rank}, "
                f"world_size={self.world_size}, backend={self.config.backend}"
            )

        # Set device
        if torch.cuda.is_available():
            torch.cuda.set_device(self.local_rank)
            self.device = torch.device(f"cuda:{self.local_rank}")
        else:
            self.device = torch.device("cpu")

    def _setup_model(self, model: nn.Module) -> nn.Module:
        """Setup model for distributed training.

        Args:
            model: Model

        Returns:
            DDP-wrapped model
        """
        # Move to device
        model = model.to(self.device)

        # Synchronized BatchNorm
        if self.config.sync_batch_norm and self.world_size > 1:
            model = nn.SyncBatchNorm.convert_sync_batchnorm(model)
            logger.info("Converted BatchNorm to SyncBatchNorm")

        # Wrap with DDP
        if self.world_size > 1:
            model = DDP(
                model,
                device_ids=[self.local_rank],
                output_device=self.local_rank,
                find_unused_parameters=self.config.find_unused_parameters,
            )

            logger.info(f"Wrapped model with DDP on rank {self.rank}")

        return model

    def train(
        self, train_dataset: Any, val_dataset: Any | None = None, num_epochs: int = 100
    ) -> list[dict[str, float]]:
        """Train model.

        Args:
            train_dataset: Training dataset
            val_dataset: Validation dataset
            num_epochs: Number of epochs

        Returns:
            Training history (only on rank 0)
        """
        # Create distributed samplers
        train_sampler = (
            DistributedSampler(train_dataset, num_replicas=self.world_size, rank=self.rank, shuffle=True)
            if self.world_size > 1
            else None
        )

        val_sampler = (
            DistributedSampler(val_dataset, num_replicas=self.world_size, rank=self.rank, shuffle=False)
            if (val_dataset is not None and self.world_size > 1)
            else None
        )

        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size_per_gpu,
            sampler=train_sampler,
            shuffle=(train_sampler is None),
            num_workers=4,
            pin_memory=True,
        )

        val_loader = None
        if val_dataset is not None:
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size_per_gpu,
                sampler=val_sampler,
                shuffle=False,
                num_workers=4,
                pin_memory=True,
            )

        # Training loop
        history = []

        for epoch in range(1, num_epochs + 1):
            # Set epoch for sampler (ensures different shuffle each epoch)
            if train_sampler is not None:
                train_sampler.set_epoch(epoch)

            # Train epoch
            train_loss = self._train_epoch(train_loader, epoch)

            # Validate
            val_loss = None
            if val_loader is not None:
                val_loss = self._validate_epoch(val_loader, epoch)

            # Gather metrics from all ranks
            train_loss = self._reduce_metric(train_loss)
            if val_loss is not None:
                val_loss = self._reduce_metric(val_loss)

            # Log (only rank 0)
            if self.is_main_process():
                epoch_metrics = {"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss}
                history.append(epoch_metrics)

                logger.info(
                    f"Epoch {epoch}/{num_epochs} - "
                    f"train_loss: {train_loss:.4f} - "
                    f"val_loss: {val_loss:.4f if val_loss else 'N/A'}"
                )

            # Synchronize before next epoch
            if self.world_size > 1:
                dist.barrier()

        return history

    def _train_epoch(self, train_loader: DataLoader, epoch: int) -> float:
        """Train single epoch.

        Args:
            train_loader: Training data loader
            epoch: Current epoch

        Returns:
            Average training loss
        """
        self.model.train()

        total_loss = 0.0
        num_batches = 0

        for batch in train_loader:
            # Move batch to device
            batch = self._batch_to_device(batch)

            # Forward pass
            loss = self.loss_fn(self.model, batch)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        return total_loss / num_batches if num_batches > 0 else 0.0

    def _validate_epoch(self, val_loader: DataLoader, epoch: int) -> float:
        """Validate single epoch.

        Args:
            val_loader: Validation data loader
            epoch: Current epoch

        Returns:
            Average validation loss
        """
        self.model.eval()

        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                # Move batch to device
                batch = self._batch_to_device(batch)

                # Forward pass
                loss = self.loss_fn(self.model, batch)

                total_loss += loss.item()
                num_batches += 1

        return total_loss / num_batches if num_batches > 0 else 0.0

    def _batch_to_device(self, batch: Any) -> Any:
        """Move batch to device.

        Args:
            batch: Batch

        Returns:
            Batch on device
        """
        if isinstance(batch, torch.Tensor):
            return batch.to(self.device, non_blocking=True)

        if isinstance(batch, (tuple, list)):
            return tuple(self._batch_to_device(x) for x in batch)

        if isinstance(batch, dict):
            return {k: self._batch_to_device(v) for k, v in batch.items()}

        return batch

    def _reduce_metric(self, metric: float) -> float:
        """Reduce metric across all ranks.

        Args:
            metric: Local metric

        Returns:
            Averaged metric
        """
        if self.world_size == 1:
            return metric

        metric_tensor = torch.tensor(metric, device=self.device)

        # All-reduce
        dist.all_reduce(metric_tensor, op=dist.ReduceOp.SUM)

        # Average
        metric_tensor /= self.world_size

        return metric_tensor.item()

    def is_main_process(self) -> bool:
        """Check if current process is main process.

        Returns:
            True if main process
        """
        return self.rank == self.config.log_rank

    def save_checkpoint(self, path: Path, epoch: int, **kwargs):
        """Save checkpoint (only on main rank).

        Args:
            path: Checkpoint path
            epoch: Current epoch
            **kwargs: Additional data
        """
        if self.rank != self.config.save_checkpoint_rank:
            return

        # Get model state dict (unwrap DDP if necessary)
        if isinstance(self.model, DDP):
            model_state_dict = self.model.module.state_dict()
        else:
            model_state_dict = self.model.state_dict()

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": model_state_dict,
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": self.config.__dict__,
            **kwargs,
        }

        self.config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        torch.save(checkpoint, path)

        logger.info(f"Checkpoint saved to {path} (rank {self.rank})")

    def load_checkpoint(self, path: Path):
        """Load checkpoint.

        Args:
            path: Checkpoint path
        """
        # Load checkpoint
        checkpoint = torch.load(path, map_location=self.device)

        # Load model state
        if isinstance(self.model, DDP):
            self.model.module.load_state_dict(checkpoint["model_state_dict"])
        else:
            self.model.load_state_dict(checkpoint["model_state_dict"])

        # Load optimizer state
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        logger.info(f"Checkpoint loaded from {path} (rank {self.rank})")

        return checkpoint.get("epoch", 0)

    def cleanup(self):
        """Cleanup distributed resources."""
        if dist.is_initialized():
            dist.destroy_process_group()
            logger.info(f"Destroyed process group (rank {self.rank})")


# =============================================================================
# Utility Functions
# =============================================================================


def setup_for_distributed(is_master: bool):
    """Setup environment for distributed training.

    Args:
        is_master: Whether this is the master process
    """
    import builtins

    builtin_print = builtins.print

    def print_with_rank(*args, **kwargs):
        """Print only on master process."""
        if is_master:
            builtin_print(*args, **kwargs)

    builtins.print = print_with_rank


def get_rank() -> int:
    """Get current process rank.

    Returns:
        Rank (0 if not distributed)
    """
    if not dist.is_initialized():
        return 0

    return dist.get_rank()


def get_world_size() -> int:
    """Get world size.

    Returns:
        World size (1 if not distributed)
    """
    if not dist.is_initialized():
        return 1

    return dist.get_world_size()


def is_dist_available_and_initialized() -> bool:
    """Check if distributed is available and initialized.

    Returns:
        True if distributed is ready
    """
    if not dist.is_available():
        return False

    if not dist.is_initialized():
        return False

    return True


if __name__ == "__main__":
    # Print distributed info
    if TORCH_AVAILABLE:
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        print(f"Distributed available: {dist.is_available()}")
        print(f"NCCL available: {dist.is_nccl_available()}")
    else:
        print("PyTorch not available")
