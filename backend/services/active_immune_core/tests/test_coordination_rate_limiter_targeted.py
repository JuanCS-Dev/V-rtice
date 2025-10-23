"""
Coordination Rate Limiter - Targeted Coverage Tests

Objetivo: Cobrir coordination/rate_limiter.py (274 lines, 0% → 30%+)

Testa RateLimiter + ClonalExpansionRateLimiter: initialization, token bucket, stats

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import asyncio
import sys
import importlib.util
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import rate_limiter.py directly
rate_limiter_path = Path(__file__).parent.parent / "coordination" / "rate_limiter.py"
spec = importlib.util.spec_from_file_location("coordination.rate_limiter", rate_limiter_path)
rate_limiter_module = importlib.util.module_from_spec(spec)

# Mock the exceptions import before loading module
import types
exceptions_mock = types.ModuleType('coordination.exceptions')

class LymphnodeRateLimitError(Exception):
    pass

class LymphnodeResourceExhaustedError(Exception):
    pass

exceptions_mock.LymphnodeRateLimitError = LymphnodeRateLimitError
exceptions_mock.LymphnodeResourceExhaustedError = LymphnodeResourceExhaustedError
sys.modules['coordination.exceptions'] = exceptions_mock
sys.modules['active_immune_core.coordination.exceptions'] = exceptions_mock

spec.loader.exec_module(rate_limiter_module)

# Extract classes
RateLimiter = rate_limiter_module.RateLimiter
ClonalExpansionRateLimiter = rate_limiter_module.ClonalExpansionRateLimiter


# ===== RATE LIMITER INITIALIZATION TESTS =====

def test_rate_limiter_initialization_default():
    """
    SCENARIO: RateLimiter created with defaults
    EXPECTED: Default values set (10 ops/sec, burst=20)
    """
    limiter = RateLimiter()

    assert limiter.max_rate == 10.0
    assert limiter.max_burst == 20
    assert limiter.refill_interval == 0.1


def test_rate_limiter_initialization_custom():
    """
    SCENARIO: RateLimiter created with custom params
    EXPECTED: Custom values stored
    """
    limiter = RateLimiter(max_rate=5.0, max_burst=10, refill_interval=0.2)

    assert limiter.max_rate == 5.0
    assert limiter.max_burst == 10
    assert limiter.refill_interval == 0.2


def test_rate_limiter_initial_tokens():
    """
    SCENARIO: RateLimiter just created
    EXPECTED: Tokens start at max_burst
    """
    limiter = RateLimiter(max_burst=15)

    assert limiter._tokens == 15.0


def test_rate_limiter_initial_statistics():
    """
    SCENARIO: RateLimiter just created
    EXPECTED: Statistics start at 0
    """
    limiter = RateLimiter()

    assert limiter.total_requests == 0
    assert limiter.total_accepted == 0
    assert limiter.total_rejected == 0


def test_rate_limiter_has_lock():
    """
    SCENARIO: RateLimiter instance
    EXPECTED: Has asyncio.Lock for thread-safety
    """
    limiter = RateLimiter()

    assert isinstance(limiter._lock, asyncio.Lock)


# ===== RATE LIMITER METHOD TESTS =====

def test_rate_limiter_has_acquire_method():
    """
    SCENARIO: RateLimiter instance
    EXPECTED: Has acquire method (async)
    """
    limiter = RateLimiter()

    assert hasattr(limiter, "acquire")
    assert callable(limiter.acquire)


def test_rate_limiter_has_acquire_or_raise_method():
    """
    SCENARIO: RateLimiter instance
    EXPECTED: Has acquire_or_raise method (async)
    """
    limiter = RateLimiter()

    assert hasattr(limiter, "acquire_or_raise")
    assert callable(limiter.acquire_or_raise)


def test_rate_limiter_has_wait_for_token_method():
    """
    SCENARIO: RateLimiter instance
    EXPECTED: Has wait_for_token method (async)
    """
    limiter = RateLimiter()

    assert hasattr(limiter, "wait_for_token")
    assert callable(limiter.wait_for_token)


def test_rate_limiter_has_get_available_tokens_method():
    """
    SCENARIO: RateLimiter instance
    EXPECTED: Has get_available_tokens method (sync)
    """
    limiter = RateLimiter()

    assert hasattr(limiter, "get_available_tokens")
    assert callable(limiter.get_available_tokens)


def test_rate_limiter_has_get_stats_method():
    """
    SCENARIO: RateLimiter instance
    EXPECTED: Has get_stats method (sync)
    """
    limiter = RateLimiter()

    assert hasattr(limiter, "get_stats")
    assert callable(limiter.get_stats)


def test_rate_limiter_has_reset_method():
    """
    SCENARIO: RateLimiter instance
    EXPECTED: Has reset method (sync)
    """
    limiter = RateLimiter()

    assert hasattr(limiter, "reset")
    assert callable(limiter.reset)


# ===== RATE LIMITER GET_AVAILABLE_TOKENS TESTS =====

def test_rate_limiter_get_available_tokens_initial():
    """
    SCENARIO: get_available_tokens() called on new limiter
    EXPECTED: Returns max_burst tokens
    """
    limiter = RateLimiter(max_burst=25)

    available = limiter.get_available_tokens()

    assert available == 25.0


# ===== RATE LIMITER GET_STATS TESTS =====

def test_rate_limiter_get_stats_returns_dict():
    """
    SCENARIO: get_stats() called
    EXPECTED: Returns dict with statistics
    """
    limiter = RateLimiter()

    stats = limiter.get_stats()

    assert isinstance(stats, dict)
    assert "max_rate" in stats
    assert "max_burst" in stats
    assert "available_tokens" in stats
    assert "total_requests" in stats
    assert "total_accepted" in stats
    assert "total_rejected" in stats
    assert "acceptance_rate" in stats


def test_rate_limiter_get_stats_initial_values():
    """
    SCENARIO: get_stats() called on new limiter
    EXPECTED: Statistics show initial state
    """
    limiter = RateLimiter(max_rate=5.0, max_burst=10)

    stats = limiter.get_stats()

    assert stats["max_rate"] == 5.0
    assert stats["max_burst"] == 10
    assert stats["total_requests"] == 0
    assert stats["acceptance_rate"] == 0.0


# ===== RATE LIMITER RESET TESTS =====

def test_rate_limiter_reset_restores_initial_state():
    """
    SCENARIO: reset() called after state change
    EXPECTED: Tokens and statistics reset
    """
    limiter = RateLimiter(max_burst=20)

    # Modify state
    limiter._tokens = 5.0
    limiter.total_requests = 100
    limiter.total_accepted = 80
    limiter.total_rejected = 20

    # Reset
    limiter.reset()

    assert limiter._tokens == 20.0
    assert limiter.total_requests == 0
    assert limiter.total_accepted == 0
    assert limiter.total_rejected == 0


# ===== CLONAL EXPANSION RATE LIMITER INITIALIZATION TESTS =====

def test_clonal_expansion_rate_limiter_initialization_default():
    """
    SCENARIO: ClonalExpansionRateLimiter created with defaults
    EXPECTED: Default limits set (200 clones/min, 50/spec, 1000 total)
    """
    limiter = ClonalExpansionRateLimiter()

    assert limiter.max_per_specialization == 50
    assert limiter.max_total_agents == 1000
    assert limiter._current_total_agents == 0


def test_clonal_expansion_rate_limiter_initialization_custom():
    """
    SCENARIO: ClonalExpansionRateLimiter created with custom params
    EXPECTED: Custom values stored
    """
    limiter = ClonalExpansionRateLimiter(
        max_clones_per_minute=100,
        max_per_specialization=25,
        max_total_agents=500,
    )

    assert limiter.max_per_specialization == 25
    assert limiter.max_total_agents == 500


def test_clonal_expansion_rate_limiter_has_global_limiter():
    """
    SCENARIO: ClonalExpansionRateLimiter instance
    EXPECTED: Has global_limiter (RateLimiter instance)
    """
    limiter = ClonalExpansionRateLimiter()

    assert isinstance(limiter.global_limiter, RateLimiter)


def test_clonal_expansion_rate_limiter_initial_specialization_counts():
    """
    SCENARIO: ClonalExpansionRateLimiter just created
    EXPECTED: Specialization counts dict is empty
    """
    limiter = ClonalExpansionRateLimiter()

    assert limiter._specialization_counts == {}


def test_clonal_expansion_rate_limiter_has_locks():
    """
    SCENARIO: ClonalExpansionRateLimiter instance
    EXPECTED: Has asyncio.Lock instances for thread-safety
    """
    limiter = ClonalExpansionRateLimiter()

    assert isinstance(limiter._specialization_lock, asyncio.Lock)
    assert isinstance(limiter._total_agents_lock, asyncio.Lock)


# ===== CLONAL EXPANSION RATE LIMITER METHOD TESTS =====

def test_clonal_expansion_rate_limiter_has_check_method():
    """
    SCENARIO: ClonalExpansionRateLimiter instance
    EXPECTED: Has check_clonal_expansion method (async)
    """
    limiter = ClonalExpansionRateLimiter()

    assert hasattr(limiter, "check_clonal_expansion")
    assert callable(limiter.check_clonal_expansion)


def test_clonal_expansion_rate_limiter_has_release_method():
    """
    SCENARIO: ClonalExpansionRateLimiter instance
    EXPECTED: Has release_clones method (async)
    """
    limiter = ClonalExpansionRateLimiter()

    assert hasattr(limiter, "release_clones")
    assert callable(limiter.release_clones)


def test_clonal_expansion_rate_limiter_has_get_stats_method():
    """
    SCENARIO: ClonalExpansionRateLimiter instance
    EXPECTED: Has get_stats method (sync)
    """
    limiter = ClonalExpansionRateLimiter()

    assert hasattr(limiter, "get_stats")
    assert callable(limiter.get_stats)


# ===== CLONAL EXPANSION RATE LIMITER GET_STATS TESTS =====

def test_clonal_expansion_rate_limiter_get_stats_returns_dict():
    """
    SCENARIO: get_stats() called
    EXPECTED: Returns dict with statistics
    """
    limiter = ClonalExpansionRateLimiter()

    stats = limiter.get_stats()

    assert isinstance(stats, dict)
    assert "global_limiter" in stats
    assert "specialization_counts" in stats
    assert "max_per_specialization" in stats
    assert "current_total_agents" in stats
    assert "max_total_agents" in stats


def test_clonal_expansion_rate_limiter_get_stats_initial_values():
    """
    SCENARIO: get_stats() called on new limiter
    EXPECTED: Statistics show initial state
    """
    limiter = ClonalExpansionRateLimiter(max_per_specialization=30, max_total_agents=800)

    stats = limiter.get_stats()

    assert stats["max_per_specialization"] == 30
    assert stats["max_total_agents"] == 800
    assert stats["current_total_agents"] == 0
    assert stats["specialization_counts"] == {}


def test_clonal_expansion_rate_limiter_get_stats_global_limiter_nested():
    """
    SCENARIO: get_stats() called
    EXPECTED: global_limiter stats is nested dict
    """
    limiter = ClonalExpansionRateLimiter()

    stats = limiter.get_stats()

    assert isinstance(stats["global_limiter"], dict)
    assert "max_rate" in stats["global_limiter"]


# ===== ASYNC TESTS (Basic) =====

@pytest.mark.asyncio
async def test_rate_limiter_acquire_success():
    """
    SCENARIO: acquire(1) called with available tokens
    EXPECTED: Returns True, tokens decremented, stats updated
    """
    limiter = RateLimiter(max_burst=10)

    result = await limiter.acquire(1)

    assert result is True
    assert limiter.total_requests == 1
    assert limiter.total_accepted == 1
    assert limiter.total_rejected == 0


@pytest.mark.asyncio
async def test_rate_limiter_acquire_validation_error_zero():
    """
    SCENARIO: acquire(0) called
    EXPECTED: ValueError raised
    """
    limiter = RateLimiter()

    with pytest.raises(ValueError, match="tokens must be >= 1"):
        await limiter.acquire(0)


@pytest.mark.asyncio
async def test_rate_limiter_acquire_validation_error_exceeds_burst():
    """
    SCENARIO: acquire() called with tokens > max_burst
    EXPECTED: ValueError raised
    """
    limiter = RateLimiter(max_burst=10)

    with pytest.raises(ValueError, match="exceeds max_burst"):
        await limiter.acquire(15)


@pytest.mark.asyncio
async def test_clonal_expansion_release_clones_basic():
    """
    SCENARIO: release_clones() called
    EXPECTED: Specialization count decremented
    """
    limiter = ClonalExpansionRateLimiter()

    # Manually set count
    limiter._specialization_counts["antigen-presentation"] = 10

    # Release 3 clones
    await limiter.release_clones("antigen-presentation", 3)

    assert limiter._specialization_counts["antigen-presentation"] == 7


@pytest.mark.asyncio
async def test_clonal_expansion_release_clones_no_negative():
    """
    SCENARIO: release_clones() called with more than current count
    EXPECTED: Count goes to 0 (not negative)
    """
    limiter = ClonalExpansionRateLimiter()

    # Set count to 5
    limiter._specialization_counts["test"] = 5

    # Try to release 10 (more than current)
    await limiter.release_clones("test", 10)

    assert limiter._specialization_counts["test"] == 0


# ===== DOCSTRING TESTS =====

def test_module_docstring():
    """
    SCENARIO: coordination.rate_limiter module
    EXPECTED: Has module docstring mentioning rate limiting
    """
    doc = rate_limiter_module.__doc__
    assert doc is not None
    assert "rate" in doc.lower() or "limiter" in doc.lower()


def test_rate_limiter_class_docstring():
    """
    SCENARIO: RateLimiter class
    EXPECTED: Has docstring mentioning token bucket
    """
    doc = RateLimiter.__doc__
    assert doc is not None
    assert "token bucket" in doc.lower() or "rate limit" in doc.lower()


def test_clonal_expansion_rate_limiter_class_docstring():
    """
    SCENARIO: ClonalExpansionRateLimiter class
    EXPECTED: Has docstring mentioning clonal expansion
    """
    doc = ClonalExpansionRateLimiter.__doc__
    assert doc is not None
    assert "clonal expansion" in doc.lower()
