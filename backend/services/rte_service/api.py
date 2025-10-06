"""Maximus RTE Service - API Entry Point.

This module serves as the API entry point for the Real-Time Execution (RTE) Service.
It imports the FastAPI application from the main module.

The actual implementation is in main.py, which orchestrates:
- FusionEngine for data correlation
- FastML for rapid predictions
- HyperscanMatcher for high-speed pattern detection
- RealTimePlaybookExecutor for immediate threat response
"""

from main import app

__all__ = ["app"]
