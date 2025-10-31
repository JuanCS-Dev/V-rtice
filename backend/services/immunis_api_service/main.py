"""Maximus Immunis API Service - Entry Point.

This module serves as the main entry point for the Immunis API Service,
which acts as a central gateway for the Maximus AI Immune System.

The service orchestrates communication between all Immunis subsystems:
- Innate Immunity: Neutrophils, Macrophages, NK Cells
- Adaptive Immunity: Dendritic Cells, Helper T Cells, Cytotoxic T Cells, B Cells

It provides a unified REST API for:
- Threat detection and response coordination
- Immune system status monitoring
- Memory cell and antibody management
- Cytokine signaling and inflammation control
"""

from api import app

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


__all__ = ["app"]
