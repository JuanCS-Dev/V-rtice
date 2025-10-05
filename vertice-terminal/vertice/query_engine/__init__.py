"""
🔍 VÉRTICE QUERY ENGINE
Parser e executor de VeQL (Vértice Query Language)

VeQL é uma linguagem SQL-like para threat hunting em fleet de endpoints.

Exemplo:
    SELECT process.name, network.remote_ip
    FROM endpoints
    WHERE process.parent = "powershell.exe"
      AND network.remote_ip NOT IN private_ranges
    LIMIT 100
"""

from .parser import VeQLParser
from .planner import QueryPlanner
from .executor import QueryExecutor
from .ast_nodes import (
    SelectQuery,
    WhereClause,
    Field,
    Condition,
    Operator,
)

__all__ = [
    "VeQLParser",
    "QueryPlanner",
    "QueryExecutor",
    "SelectQuery",
    "WhereClause",
    "Field",
    "Condition",
    "Operator",
]
