"""Thread-Safe Data Structures for Lymphnode

Async-safe structures to prevent race conditions in concurrent operations.

Authors: Juan + Claude
Date: 2025-10-07
"""

import asyncio
from collections import defaultdict, deque
from typing import Dict, Generic, List, TypeVar

T = TypeVar("T")


class ThreadSafeBuffer(Generic[T]):
    """
    Thread-safe circular buffer with max size.

    Safe for concurrent append/read operations.
    """

    def __init__(self, maxsize: int = 1000):
        """
        Initialize buffer.

        Args:
            maxsize: Maximum buffer size (oldest items dropped when full)
        """
        self._buffer: deque[T] = deque(maxlen=maxsize)
        self._lock = asyncio.Lock()
        self._maxsize = maxsize

        # Statistics
        self._total_appended = 0
        self._total_dropped = 0

    async def append(self, item: T) -> None:
        """
        Append item to buffer (thread-safe).

        Args:
            item: Item to append
        """
        async with self._lock:
            if len(self._buffer) >= self._maxsize:
                self._total_dropped += 1

            self._buffer.append(item)
            self._total_appended += 1

    async def get_recent(self, n: int) -> List[T]:
        """
        Get last N items from buffer (thread-safe).

        Args:
            n: Number of recent items to get

        Returns:
            List of up to N most recent items
        """
        async with self._lock:
            # Return copy to avoid external mutation
            return list(self._buffer)[-n:]

    async def get_all(self) -> List[T]:
        """Get all items from buffer (thread-safe copy)"""
        async with self._lock:
            return list(self._buffer)

    async def clear(self) -> int:
        """
        Clear buffer and return number of items cleared.

        Returns:
            Number of items removed
        """
        async with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            return count

    async def size(self) -> int:
        """Get current buffer size"""
        async with self._lock:
            return len(self._buffer)

    def maxsize(self) -> int:
        """Get maximum buffer size"""
        return self._maxsize

    async def stats(self) -> Dict[str, int]:
        """Get buffer statistics"""
        async with self._lock:
            return {
                "current_size": len(self._buffer),
                "maxsize": self._maxsize,
                "total_appended": self._total_appended,
                "total_dropped": self._total_dropped,
            }


class AtomicCounter:
    """
    Thread-safe atomic counter.

    Supports increment, decrement, get, set operations safely.
    """

    def __init__(self, initial: int = 0):
        """
        Initialize counter.

        Args:
            initial: Initial counter value
        """
        self._value = initial
        self._lock = asyncio.Lock()

    async def increment(self, delta: int = 1) -> int:
        """
        Increment counter atomically.

        Args:
            delta: Amount to increment

        Returns:
            New value after increment
        """
        async with self._lock:
            self._value += delta
            return self._value

    async def decrement(self, delta: int = 1) -> int:
        """
        Decrement counter atomically.

        Args:
            delta: Amount to decrement

        Returns:
            New value after decrement
        """
        async with self._lock:
            self._value -= delta
            return self._value

    async def get(self) -> int:
        """Get current value"""
        async with self._lock:
            return self._value

    async def set(self, value: int) -> int:
        """
        Set counter to specific value.

        Args:
            value: New value

        Returns:
            Previous value
        """
        async with self._lock:
            old_value = self._value
            self._value = value
            return old_value

    async def compare_and_set(self, expected: int, new: int) -> bool:
        """
        Compare-and-set (CAS) operation.

        Args:
            expected: Expected current value
            new: New value to set if current == expected

        Returns:
            True if value was updated, False otherwise
        """
        async with self._lock:
            if self._value == expected:
                self._value = new
                return True
            return False


class ThreadSafeTemperature:
    """
    Thread-safe temperature management with bounds checking.

    Ensures temperature stays within safe ranges.
    """

    def __init__(self, initial: float = 37.0, min_temp: float = 36.0, max_temp: float = 42.0):
        """
        Initialize temperature.

        Args:
            initial: Initial temperature
            min_temp: Minimum allowed temperature
            max_temp: Maximum allowed temperature
        """
        self._value = initial
        self._min = min_temp
        self._max = max_temp
        self._lock = asyncio.Lock()

        # Statistics
        self._history: List[float] = [initial]
        self._max_history = 100

    async def adjust(self, delta: float) -> float:
        """
        Adjust temperature by delta (clamped to bounds).

        Args:
            delta: Temperature change

        Returns:
            New temperature value
        """
        async with self._lock:
            old_value = self._value
            self._value = max(self._min, min(self._max, self._value + delta))

            # Track history
            self._history.append(self._value)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            return self._value

    async def set(self, value: float) -> float:
        """
        Set temperature directly (clamped to bounds).

        Args:
            value: New temperature

        Returns:
            Actual temperature set (after clamping)
        """
        async with self._lock:
            self._value = max(self._min, min(self._max, value))

            # Track history
            self._history.append(self._value)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            return self._value

    async def get(self) -> float:
        """Get current temperature"""
        async with self._lock:
            return self._value

    async def multiply(self, factor: float) -> float:
        """
        Multiply temperature by factor (clamped).

        Args:
            factor: Multiplication factor

        Returns:
            New temperature
        """
        async with self._lock:
            self._value = max(self._min, min(self._max, self._value * factor))

            # Track history
            self._history.append(self._value)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            return self._value

    async def get_stats(self) -> Dict[str, float]:
        """Get temperature statistics"""
        async with self._lock:
            if not self._history:
                return {
                    "current": self._value,
                    "min": self._min,
                    "max": self._max,
                    "avg": self._value,
                    "variance": 0.0,
                }

            avg = sum(self._history) / len(self._history)
            variance = sum((x - avg) ** 2 for x in self._history) / len(self._history)

            return {
                "current": self._value,
                "min": self._min,
                "max": self._max,
                "avg": avg,
                "variance": variance,
                "history_size": len(self._history),
            }


class ThreadSafeCounter(Generic[T]):
    """
    Thread-safe defaultdict-style counter.

    Safe for concurrent increment/get operations.
    """

    def __init__(self):
        """Initialize counter"""
        self._counts: Dict[T, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def increment(self, key: T, delta: int = 1) -> int:
        """
        Increment counter for key.

        Args:
            key: Counter key
            delta: Amount to increment

        Returns:
            New count for key
        """
        async with self._lock:
            self._counts[key] += delta
            return self._counts[key]

    async def get(self, key: T) -> int:
        """Get count for key"""
        async with self._lock:
            return self._counts.get(key, 0)

    async def get_all(self) -> Dict[T, int]:
        """Get all counts (copy)"""
        async with self._lock:
            return dict(self._counts)

    async def clear(self) -> None:
        """Clear all counts"""
        async with self._lock:
            self._counts.clear()

    async def items(self) -> List[tuple[T, int]]:
        """Get all items as list of tuples"""
        async with self._lock:
            return list(self._counts.items())

    async def size(self) -> int:
        """Get number of unique keys"""
        async with self._lock:
            return len(self._counts)
