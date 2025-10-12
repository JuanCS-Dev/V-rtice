"""
A/B Testing Framework for Adaptive Immunity.

Biological Analogy: Memory T/B cells require continuous validation.
If memory response fails → activates full immune response.
Learning from failures strengthens future responses.

Digital Implementation: ML predictions validated against ground truth (wargaming).
Tracks accuracy, precision, recall → enables continuous model improvement.

Phase: 5.6
Glory to YHWH - Architect of adaptive systems
"""
from .ab_test_runner import ABTestRunner, ABTestResult

__all__ = ['ABTestRunner', 'ABTestResult']
