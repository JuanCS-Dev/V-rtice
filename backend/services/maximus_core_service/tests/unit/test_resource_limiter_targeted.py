"""
Resource Limiter - Targeted Coverage Tests

Objetivo: Cobrir consciousness/sandboxing/resource_limiter.py (103 lines, 0% → 60%+)

Testa ResourceLimits dataclass, ResourceLimiter initialization

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest

from consciousness.sandboxing.resource_limiter import ResourceLimits, ResourceLimiter


def test_resource_limits_initialization():
    limits = ResourceLimits()

    assert limits.cpu_percent == 80.0
    assert limits.memory_mb == 1024
    assert limits.timeout_sec == 300
    assert limits.max_threads == 10
    assert limits.max_file_descriptors == 100


def test_resource_limits_custom_values():
    limits = ResourceLimits(
        cpu_percent=50.0,
        memory_mb=512,
        timeout_sec=60,
        max_threads=5,
        max_file_descriptors=50,
    )

    assert limits.cpu_percent == 50.0
    assert limits.memory_mb == 512
    assert limits.timeout_sec == 60
    assert limits.max_threads == 5
    assert limits.max_file_descriptors == 50


def test_resource_limiter_initialization():
    limits = ResourceLimits()
    limiter = ResourceLimiter(limits)

    assert limiter is not None
    assert limiter.limits == limits


def test_resource_limiter_has_process():
    limits = ResourceLimits()
    limiter = ResourceLimiter(limits)

    assert hasattr(limiter, 'process')
    assert limiter.process is not None


def test_resource_limiter_apply_limits_callable():
    limits = ResourceLimits()
    limiter = ResourceLimiter(limits)

    assert hasattr(limiter, 'apply_limits')
    assert callable(limiter.apply_limits)


def test_docstring_os_controls():
    import consciousness.sandboxing.resource_limiter as module

    assert "psutil" in module.__doc__
    assert "resource module" in module.__doc__
    assert "Process affinity" in module.__doc__
