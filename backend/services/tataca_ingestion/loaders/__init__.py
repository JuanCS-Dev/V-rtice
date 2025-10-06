"""Tatacá Ingestion - Data Loaders.

This module provides loaders for persisting transformed entities to various
data stores (PostgreSQL, Neo4j).
"""

from .postgres_loader import PostgresLoader
from .neo4j_loader import Neo4jLoader

__all__ = ["PostgresLoader", "Neo4jLoader"]
