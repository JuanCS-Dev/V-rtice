"""API package for MAXIMUS Eureka service."""

from .ml_metrics import router as ml_metrics_router

__all__ = ["ml_metrics_router"]
