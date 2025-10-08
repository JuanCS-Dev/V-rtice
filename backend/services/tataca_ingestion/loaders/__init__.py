"""Tatacá Ingestion - Data Loaders.

This module provides loaders for persisting transformed entities to various
data stores (PostgreSQL, Neo4j).
"""

from .neo4j_loader import Neo4jLoader
from .postgres_loader import PostgresLoader

__all__ = ["PostgresLoader", "Neo4jLoader"]
