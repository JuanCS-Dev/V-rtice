"""
Message Compression for RabbitMQ.

Provides automatic compression/decompression for large messages:
- Gzip compression (standard, good compression ratio)
- Zstandard compression (faster, better ratio)
- LZ4 compression (fastest, lower ratio)
- Automatic algorithm selection
- Compression threshold (only compress if beneficial)

Features:
- Multiple compression algorithms
- Automatic decompression detection
- Compression headers for algorithm tracking
- Size-based automatic compression
- Performance metrics

Headers:
- x-compression: Algorithm used (gzip, zstd, lz4, none)
- x-original-size: Original message size before compression
- x-compressed-size: Size after compression
"""

import gzip
import json
import logging
from enum import Enum
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Optional compression libraries
try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False
    logger.debug("zstandard not available - falling back to gzip")

try:
    import lz4.frame as lz4
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False
    logger.debug("lz4 not available")


class CompressionAlgorithm(Enum):
    """Supported compression algorithms."""

    NONE = "none"  # No compression
    GZIP = "gzip"  # Standard gzip (always available)
    ZSTD = "zstd"  # Zstandard (better compression, faster)
    LZ4 = "lz4"  # LZ4 (fastest, lower compression ratio)


class CompressionConfig:
    """
    Configuration for message compression.

    Attributes:
        algorithm: Compression algorithm to use
        min_size_bytes: Minimum message size to compress (bytes)
        compression_level: Compression level (1-9 for gzip/zstd, 1-16 for lz4)
        auto_decompress: Automatically decompress messages
    """

    def __init__(
        self,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
        min_size_bytes: int = 1024,  # 1KB threshold
        compression_level: int = 6,  # Balanced
        auto_decompress: bool = True,
    ):
        self.algorithm = algorithm
        self.min_size_bytes = min_size_bytes
        self.compression_level = compression_level
        self.auto_decompress = auto_decompress

        # Validate algorithm availability
        if algorithm == CompressionAlgorithm.ZSTD and not ZSTD_AVAILABLE:
            logger.warning("Zstandard not available, falling back to GZIP")
            self.algorithm = CompressionAlgorithm.GZIP

        if algorithm == CompressionAlgorithm.LZ4 and not LZ4_AVAILABLE:
            logger.warning("LZ4 not available, falling back to GZIP")
            self.algorithm = CompressionAlgorithm.GZIP


class MessageCompressor:
    """
    Handles message compression and decompression.

    Automatically compresses large messages and adds compression metadata.
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        """
        Initialize message compressor.

        Args:
            config: Compression configuration
        """
        self.config = config or CompressionConfig()

    def compress_message(
        self,
        message_body: str,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress message body.

        Args:
            message_body: Message body (JSON string)

        Returns:
            (compressed_bytes, headers) tuple
        """
        # Convert to bytes
        original_bytes = message_body.encode("utf-8")
        original_size = len(original_bytes)

        # Check if compression beneficial
        if original_size < self.config.min_size_bytes:
            # Too small to compress
            headers = {
                "x-compression": CompressionAlgorithm.NONE.value,
                "x-original-size": original_size,
            }
            return original_bytes, headers

        # Compress
        if self.config.algorithm == CompressionAlgorithm.GZIP:
            compressed_bytes = self._compress_gzip(original_bytes)

        elif self.config.algorithm == CompressionAlgorithm.ZSTD:
            compressed_bytes = self._compress_zstd(original_bytes)

        elif self.config.algorithm == CompressionAlgorithm.LZ4:
            compressed_bytes = self._compress_lz4(original_bytes)

        else:
            # No compression
            compressed_bytes = original_bytes

        compressed_size = len(compressed_bytes)

        # Check if compression reduced size
        if compressed_size >= original_size:
            # Compression not beneficial
            logger.debug(
                f"Compression not beneficial: {original_size} → {compressed_size} bytes"
            )
            headers = {
                "x-compression": CompressionAlgorithm.NONE.value,
                "x-original-size": original_size,
            }
            return original_bytes, headers

        # Compression successful
        compression_ratio = (1 - compressed_size / original_size) * 100

        logger.debug(
            f"Compressed message: {original_size} → {compressed_size} bytes "
            f"({compression_ratio:.1f}% reduction) using {self.config.algorithm.value}"
        )

        headers = {
            "x-compression": self.config.algorithm.value,
            "x-original-size": original_size,
            "x-compressed-size": compressed_size,
        }

        return compressed_bytes, headers

    def decompress_message(
        self,
        message_bytes: bytes,
        headers: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Decompress message body.

        Args:
            message_bytes: Compressed message bytes
            headers: Message headers (must contain x-compression)

        Returns:
            Decompressed message body (JSON string)

        Raises:
            ValueError: If compression algorithm unknown or headers missing
        """
        if headers is None:
            # No headers - assume uncompressed
            return message_bytes.decode("utf-8")

        # Get compression algorithm from headers
        compression_alg = headers.get("x-compression", "none")

        if compression_alg == CompressionAlgorithm.NONE.value:
            # Not compressed
            return message_bytes.decode("utf-8")

        # Decompress
        if compression_alg == CompressionAlgorithm.GZIP.value:
            decompressed_bytes = self._decompress_gzip(message_bytes)

        elif compression_alg == CompressionAlgorithm.ZSTD.value:
            decompressed_bytes = self._decompress_zstd(message_bytes)

        elif compression_alg == CompressionAlgorithm.LZ4.value:
            decompressed_bytes = self._decompress_lz4(message_bytes)

        else:
            raise ValueError(f"Unknown compression algorithm: {compression_alg}")

        # Verify size if header present
        original_size = headers.get("x-original-size")
        if original_size is not None and len(decompressed_bytes) != original_size:
            logger.warning(
                f"Decompressed size mismatch: expected {original_size}, "
                f"got {len(decompressed_bytes)}"
            )

        return decompressed_bytes.decode("utf-8")

    # --- Compression Implementations ---

    def _compress_gzip(self, data: bytes) -> bytes:
        """Compress with gzip."""
        return gzip.compress(data, compresslevel=self.config.compression_level)

    def _decompress_gzip(self, data: bytes) -> bytes:
        """Decompress gzip."""
        return gzip.decompress(data)

    def _compress_zstd(self, data: bytes) -> bytes:
        """Compress with zstandard."""
        if not ZSTD_AVAILABLE:
            raise RuntimeError("Zstandard not available")

        compressor = zstd.ZstdCompressor(level=self.config.compression_level)
        return compressor.compress(data)

    def _decompress_zstd(self, data: bytes) -> bytes:
        """Decompress zstandard."""
        if not ZSTD_AVAILABLE:
            raise RuntimeError("Zstandard not available")

        decompressor = zstd.ZstdDecompressor()
        return decompressor.decompress(data)

    def _compress_lz4(self, data: bytes) -> bytes:
        """Compress with LZ4."""
        if not LZ4_AVAILABLE:
            raise RuntimeError("LZ4 not available")

        return lz4.compress(data, compression_level=self.config.compression_level)

    def _decompress_lz4(self, data: bytes) -> bytes:
        """Decompress LZ4."""
        if not LZ4_AVAILABLE:
            raise RuntimeError("LZ4 not available")

        return lz4.decompress(data)


# --- Auto-Select Best Compression ---


def auto_select_compression(
    message_size: int,
) -> CompressionAlgorithm:
    """
    Automatically select best compression algorithm.

    Selection criteria:
    - < 1KB: No compression
    - 1KB - 10KB: LZ4 (fast decompression)
    - 10KB - 100KB: GZIP (good balance)
    - > 100KB: Zstandard (best compression)

    Args:
        message_size: Message size in bytes

    Returns:
        Recommended compression algorithm
    """
    if message_size < 1024:  # < 1KB
        return CompressionAlgorithm.NONE

    elif message_size < 10 * 1024:  # < 10KB
        # Prefer LZ4 for fast decompression
        if LZ4_AVAILABLE:
            return CompressionAlgorithm.LZ4
        else:
            return CompressionAlgorithm.GZIP

    elif message_size < 100 * 1024:  # < 100KB
        # GZIP good balance
        return CompressionAlgorithm.GZIP

    else:  # > 100KB
        # Prefer Zstandard for best compression
        if ZSTD_AVAILABLE:
            return CompressionAlgorithm.ZSTD
        else:
            return CompressionAlgorithm.GZIP


# --- Compression Benchmarking ---


class CompressionBenchmark:
    """
    Benchmark compression algorithms.

    Useful for selecting optimal algorithm for specific workload.
    """

    @staticmethod
    def benchmark_algorithm(
        data: bytes,
        algorithm: CompressionAlgorithm,
        level: int = 6,
    ) -> Dict[str, Any]:
        """
        Benchmark compression algorithm.

        Args:
            data: Data to compress
            algorithm: Algorithm to test
            level: Compression level

        Returns:
            Dict with benchmark results
        """
        import time

        config = CompressionConfig(
            algorithm=algorithm,
            compression_level=level,
            min_size_bytes=0,  # Always compress for benchmark
        )

        compressor = MessageCompressor(config)

        # Compress
        start = time.time()
        compressed, headers = compressor.compress_message(data.decode("utf-8"))
        compress_time = time.time() - start

        # Decompress
        start = time.time()
        decompressed = compressor.decompress_message(compressed, headers)
        decompress_time = time.time() - start

        # Calculate metrics
        original_size = len(data)
        compressed_size = len(compressed)
        compression_ratio = (1 - compressed_size / original_size) * 100

        return {
            "algorithm": algorithm.value,
            "level": level,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "compress_time_ms": compress_time * 1000,
            "decompress_time_ms": decompress_time * 1000,
            "compress_throughput_mb_s": original_size / compress_time / 1024 / 1024,
            "decompress_throughput_mb_s": original_size / decompress_time / 1024 / 1024,
        }

    @staticmethod
    def compare_algorithms(data: bytes) -> Dict[str, Dict[str, Any]]:
        """
        Compare all available compression algorithms.

        Args:
            data: Data to compress

        Returns:
            Dict mapping algorithm to benchmark results
        """
        results = {}

        # Test GZIP (always available)
        results["gzip"] = CompressionBenchmark.benchmark_algorithm(
            data, CompressionAlgorithm.GZIP
        )

        # Test Zstandard if available
        if ZSTD_AVAILABLE:
            results["zstd"] = CompressionBenchmark.benchmark_algorithm(
                data, CompressionAlgorithm.ZSTD
            )

        # Test LZ4 if available
        if LZ4_AVAILABLE:
            results["lz4"] = CompressionBenchmark.benchmark_algorithm(
                data, CompressionAlgorithm.LZ4
            )

        return results


# --- Global Compressor ---

_global_compressor: Optional[MessageCompressor] = None


def get_message_compressor(
    config: Optional[CompressionConfig] = None,
) -> MessageCompressor:
    """
    Get global message compressor.

    Args:
        config: Compression configuration

    Returns:
        MessageCompressor instance
    """
    global _global_compressor

    if _global_compressor is None:
        _global_compressor = MessageCompressor(config)

    return _global_compressor


# --- Compression Utilities ---


def estimate_json_size(data: Dict[str, Any]) -> int:
    """
    Estimate size of JSON data.

    Args:
        data: Dict to estimate

    Returns:
        Estimated size in bytes
    """
    return len(json.dumps(data).encode("utf-8"))


def should_compress_message(
    message_size: int,
    threshold: int = 1024,
) -> bool:
    """
    Check if message should be compressed.

    Args:
        message_size: Message size in bytes
        threshold: Size threshold for compression

    Returns:
        True if should compress, False otherwise
    """
    return message_size >= threshold
