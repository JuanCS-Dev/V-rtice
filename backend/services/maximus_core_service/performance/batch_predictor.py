"""
Batch Prediction Engine for MAXIMUS

Intelligent batch processing with dynamic batching:
- Async batch prediction
- Dynamic batch sizing
- Queue management
- Adaptive batching
- Throughput optimization
- Request prioritization

REGRA DE OURO: Zero mocks, production-ready batch prediction
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from collections import deque
from dataclasses import dataclass
from enum import Enum
import logging
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

# Try to import PyTorch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Request priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class BatchRequest:
    """Batch prediction request."""
    request_id: str
    input_data: Any
    priority: Priority = Priority.NORMAL
    timestamp: float = None
    callback: Optional[Callable] = None

    def __post_init__(self):
        """Set timestamp."""
        if self.timestamp is None:
            self.timestamp = time.time()

    def __lt__(self, other):
        """Compare for priority queue."""
        # Higher priority first, then earlier timestamp
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.timestamp < other.timestamp


@dataclass
class BatchResponse:
    """Batch prediction response."""
    request_id: str
    output: Any
    latency_ms: float
    batch_size: int


@dataclass
class BatchConfig:
    """Batch predictor configuration."""

    # Batching
    max_batch_size: int = 64
    min_batch_size: int = 1
    batch_timeout_ms: float = 100.0  # Max wait time for batch

    # Dynamic batching
    adaptive_batching: bool = True
    target_latency_ms: float = 50.0

    # Queue
    max_queue_size: int = 1000
    use_priority_queue: bool = True

    # Performance
    num_workers: int = 1
    prefetch_batches: int = 2


class BatchPredictor:
    """Intelligent batch prediction engine.

    Features:
    - Async batch processing with queue
    - Dynamic batch sizing based on latency
    - Request prioritization
    - Adaptive batching
    - Multi-threaded workers
    - Throughput optimization

    Example:
        ```python
        # Create predictor
        config = BatchConfig(
            max_batch_size=32,
            batch_timeout_ms=50.0,
            adaptive_batching=True
        )

        def predict_fn(batch):
            # Your model inference
            return model(batch)

        predictor = BatchPredictor(
            predict_fn=predict_fn,
            config=config
        )

        # Start predictor
        predictor.start()

        # Submit requests
        future = predictor.submit(
            input_data=input_tensor,
            priority=Priority.HIGH
        )

        # Get result
        result = future.get(timeout=1.0)

        # Stop predictor
        predictor.stop()
        ```
    """

    def __init__(
        self,
        predict_fn: Callable[[Any], Any],
        config: BatchConfig = BatchConfig()
    ):
        """Initialize batch predictor.

        Args:
            predict_fn: Prediction function (batch -> outputs)
            config: Batch configuration
        """
        self.predict_fn = predict_fn
        self.config = config

        # Request queue
        if config.use_priority_queue:
            self.request_queue = queue.PriorityQueue(maxsize=config.max_queue_size)
        else:
            self.request_queue = queue.Queue(maxsize=config.max_queue_size)

        # Response futures
        self.futures: Dict[str, "ResponseFuture"] = {}
        self.futures_lock = threading.Lock()

        # Workers
        self.workers: List[threading.Thread] = []
        self.running = False

        # Statistics
        self.total_requests = 0
        self.total_batches = 0
        self.total_latency_ms = 0.0
        self.batch_sizes = deque(maxlen=100)  # Last 100 batch sizes
        self.stats_lock = threading.Lock()

        # Adaptive batching
        self.current_batch_size = config.max_batch_size
        self.recent_latencies = deque(maxlen=50)

        logger.info(f"BatchPredictor initialized: max_batch={config.max_batch_size}, "
                   f"workers={config.num_workers}")

    def start(self):
        """Start batch predictor workers."""
        if self.running:
            logger.warning("Predictor already running")
            return

        self.running = True

        # Start worker threads
        for i in range(self.config.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"BatchWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info(f"Started {self.config.num_workers} batch workers")

    def stop(self, timeout: float = 5.0):
        """Stop batch predictor workers.

        Args:
            timeout: Timeout to wait for workers
        """
        if not self.running:
            return

        logger.info("Stopping batch predictor...")

        self.running = False

        # Wait for workers
        for worker in self.workers:
            worker.join(timeout=timeout / len(self.workers))

        self.workers.clear()

        logger.info("Batch predictor stopped")

    def submit(
        self,
        input_data: Any,
        priority: Priority = Priority.NORMAL,
        request_id: Optional[str] = None
    ) -> "ResponseFuture":
        """Submit prediction request.

        Args:
            input_data: Input data
            priority: Request priority
            request_id: Optional request ID

        Returns:
            ResponseFuture for result
        """
        if not self.running:
            raise RuntimeError("Predictor not running. Call start() first.")

        # Generate request ID
        if request_id is None:
            request_id = f"req_{time.time()}_{id(input_data)}"

        # Create future
        future = ResponseFuture()

        with self.futures_lock:
            self.futures[request_id] = future

        # Create request
        request = BatchRequest(
            request_id=request_id,
            input_data=input_data,
            priority=priority
        )

        # Queue request
        try:
            if self.config.use_priority_queue:
                self.request_queue.put((request.priority.value, request), block=False)
            else:
                self.request_queue.put(request, block=False)

        except queue.Full:
            with self.futures_lock:
                del self.futures[request_id]
            raise RuntimeError("Request queue full")

        return future

    def _worker_loop(self):
        """Worker thread main loop."""
        while self.running:
            try:
                # Collect batch
                batch = self._collect_batch()

                if not batch:
                    continue

                # Process batch
                self._process_batch(batch)

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)

    def _collect_batch(self) -> List[BatchRequest]:
        """Collect batch of requests.

        Returns:
            List of batch requests
        """
        batch = []
        deadline = time.time() + (self.config.batch_timeout_ms / 1000.0)

        # Determine batch size
        target_batch_size = self._get_target_batch_size()

        while len(batch) < target_batch_size and time.time() < deadline:
            timeout = max(0, deadline - time.time())

            try:
                # Get request from queue
                if self.config.use_priority_queue:
                    _, request = self.request_queue.get(timeout=timeout)
                else:
                    request = self.request_queue.get(timeout=timeout)

                batch.append(request)

                # If we have min batch size, process immediately
                if len(batch) >= self.config.min_batch_size and not self.config.adaptive_batching:
                    break

            except queue.Empty:
                break

        return batch

    def _process_batch(self, batch: List[BatchRequest]):
        """Process batch of requests.

        Args:
            batch: List of requests
        """
        if not batch:
            return

        batch_size = len(batch)
        start_time = time.time()

        # Stack inputs
        inputs = [req.input_data for req in batch]

        try:
            # Stack into batch tensor/array
            if TORCH_AVAILABLE and isinstance(inputs[0], torch.Tensor):
                batch_input = torch.stack(inputs)
            elif isinstance(inputs[0], np.ndarray):
                batch_input = np.stack(inputs)
            else:
                batch_input = inputs

            # Run prediction
            batch_output = self.predict_fn(batch_input)

            # Split outputs
            if TORCH_AVAILABLE and isinstance(batch_output, torch.Tensor):
                outputs = [batch_output[i] for i in range(batch_size)]
            elif isinstance(batch_output, np.ndarray):
                outputs = [batch_output[i] for i in range(batch_size)]
            else:
                outputs = batch_output if isinstance(batch_output, list) else [batch_output] * batch_size

        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            outputs = [None] * batch_size

        # Calculate latency
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Update stats
        with self.stats_lock:
            self.total_requests += batch_size
            self.total_batches += 1
            self.total_latency_ms += latency_ms
            self.batch_sizes.append(batch_size)
            self.recent_latencies.append(latency_ms)

        # Update adaptive batch size
        if self.config.adaptive_batching:
            self._update_batch_size(latency_ms)

        # Send responses
        for request, output in zip(batch, outputs):
            response = BatchResponse(
                request_id=request.request_id,
                output=output,
                latency_ms=latency_ms,
                batch_size=batch_size
            )

            # Set future result
            with self.futures_lock:
                if request.request_id in self.futures:
                    future = self.futures[request.request_id]
                    future.set_result(response)
                    del self.futures[request.request_id]

            # Call callback
            if request.callback is not None:
                try:
                    request.callback(response)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

    def _get_target_batch_size(self) -> int:
        """Get target batch size.

        Returns:
            Target batch size
        """
        if self.config.adaptive_batching:
            return self.current_batch_size
        else:
            return self.config.max_batch_size

    def _update_batch_size(self, latency_ms: float):
        """Update batch size based on latency.

        Args:
            latency_ms: Recent batch latency
        """
        if len(self.recent_latencies) < 10:
            return

        # Calculate average latency
        avg_latency = sum(self.recent_latencies) / len(self.recent_latencies)

        # Adjust batch size
        if avg_latency > self.config.target_latency_ms * 1.2:
            # Too slow - decrease batch size
            self.current_batch_size = max(
                self.config.min_batch_size,
                int(self.current_batch_size * 0.8)
            )
            logger.debug(f"Decreased batch size to {self.current_batch_size}")

        elif avg_latency < self.config.target_latency_ms * 0.8:
            # Fast enough - increase batch size
            self.current_batch_size = min(
                self.config.max_batch_size,
                int(self.current_batch_size * 1.2)
            )
            logger.debug(f"Increased batch size to {self.current_batch_size}")

    def get_stats(self) -> Dict[str, Any]:
        """Get predictor statistics.

        Returns:
            Statistics dictionary
        """
        with self.stats_lock:
            avg_batch_size = sum(self.batch_sizes) / len(self.batch_sizes) if self.batch_sizes else 0
            avg_latency = self.total_latency_ms / self.total_batches if self.total_batches > 0 else 0
            throughput = self.total_requests / (self.total_latency_ms / 1000) if self.total_latency_ms > 0 else 0

            return {
                "total_requests": self.total_requests,
                "total_batches": self.total_batches,
                "avg_batch_size": avg_batch_size,
                "avg_latency_ms": avg_latency,
                "throughput_rps": throughput,
                "queue_size": self.request_queue.qsize(),
                "current_batch_size": self.current_batch_size
            }


class ResponseFuture:
    """Future for async batch response."""

    def __init__(self):
        """Initialize future."""
        self.result: Optional[BatchResponse] = None
        self.event = threading.Event()

    def set_result(self, result: BatchResponse):
        """Set result.

        Args:
            result: Batch response
        """
        self.result = result
        self.event.set()

    def get(self, timeout: Optional[float] = None) -> BatchResponse:
        """Get result (blocking).

        Args:
            timeout: Timeout in seconds

        Returns:
            Batch response

        Raises:
            TimeoutError: If timeout exceeded
        """
        if not self.event.wait(timeout=timeout):
            raise TimeoutError("Request timeout")

        return self.result

    def done(self) -> bool:
        """Check if result is ready.

        Returns:
            True if done
        """
        return self.event.is_set()


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main batch prediction demo."""
    import argparse

    parser = argparse.ArgumentParser(description="MAXIMUS Batch Predictor")

    parser.add_argument("--max_batch_size", type=int, default=32, help="Max batch size")
    parser.add_argument("--batch_timeout_ms", type=float, default=100.0, help="Batch timeout (ms)")
    parser.add_argument("--num_workers", type=int, default=2, help="Number of workers")
    parser.add_argument("--num_requests", type=int, default=100, help="Number of test requests")

    args = parser.parse_args()

    # Dummy prediction function
    def dummy_predict(batch):
        """Dummy prediction function."""
        time.sleep(0.01)  # Simulate processing
        if TORCH_AVAILABLE and isinstance(batch, torch.Tensor):
            return batch * 2
        elif isinstance(batch, np.ndarray):
            return batch * 2
        else:
            return [x * 2 for x in batch]

    # Create predictor
    config = BatchConfig(
        max_batch_size=args.max_batch_size,
        batch_timeout_ms=args.batch_timeout_ms,
        num_workers=args.num_workers,
        adaptive_batching=True
    )

    predictor = BatchPredictor(predict_fn=dummy_predict, config=config)

    # Start predictor
    predictor.start()

    print(f"Submitting {args.num_requests} requests...")

    # Submit requests
    futures = []
    for i in range(args.num_requests):
        if TORCH_AVAILABLE:
            input_data = torch.randn(10)
        else:
            input_data = np.random.randn(10)

        priority = Priority.HIGH if i % 10 == 0 else Priority.NORMAL

        future = predictor.submit(input_data=input_data, priority=priority)
        futures.append(future)

    # Wait for results
    print("Waiting for results...")
    results = []
    for future in futures:
        result = future.get(timeout=5.0)
        results.append(result)

    # Print stats
    stats = predictor.get_stats()
    print("\nBatch Prediction Stats:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Total batches: {stats['total_batches']}")
    print(f"  Avg batch size: {stats['avg_batch_size']:.1f}")
    print(f"  Avg latency: {stats['avg_latency_ms']:.2f} ms")
    print(f"  Throughput: {stats['throughput_rps']:.1f} req/s")

    # Stop predictor
    predictor.stop()


if __name__ == "__main__":
    main()
