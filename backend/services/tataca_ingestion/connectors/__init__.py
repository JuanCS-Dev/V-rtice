"""Tatacá Ingestion - Data Source Connectors.

This module provides connectors to various external data sources for criminal
investigation data ingestion.
"""

from .sinesp_connector import SinespConnector

__all__ = ["SinespConnector"]
