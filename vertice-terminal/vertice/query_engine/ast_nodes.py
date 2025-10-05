"""
🌳 AST Nodes - Abstract Syntax Tree para VeQL
Define a estrutura hierárquica de uma query VeQL
"""

from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum


class Operator(Enum):
    """Operadores suportados no VeQL"""
    EQ = "="           # Igual
    NEQ = "!="         # Diferente
    GT = ">"           # Maior que
    GTE = ">="         # Maior ou igual
    LT = "<"           # Menor que
    LTE = "<="         # Menor ou igual
    IN = "IN"          # Pertence a lista
    NOT_IN = "NOT IN"  # Não pertence a lista
    LIKE = "LIKE"      # Pattern matching
    AND = "AND"        # E lógico
    OR = "OR"          # OU lógico


@dataclass
class Field:
    """Campo de uma tabela (ex: process.name)"""
    table: str
    column: str

    def __str__(self) -> str:
        return f"{self.table}.{self.column}"


@dataclass
class Value:
    """Valor literal (string, número, lista)"""
    value: Union[str, int, float, List]

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        elif isinstance(self.value, list):
            return f"[{', '.join(str(v) for v in self.value)}]"
        return str(self.value)


@dataclass
class Condition:
    """Condição WHERE (ex: process.name = "cmd.exe")"""
    left: Union[Field, Value]
    operator: Operator
    right: Union[Field, Value]

    def __str__(self) -> str:
        return f"{self.left} {self.operator.value} {self.right}"


@dataclass
class WhereClause:
    """Cláusula WHERE com múltiplas condições"""
    conditions: List[Union[Condition, "WhereClause"]]
    operator: Optional[Operator] = Operator.AND

    def __str__(self) -> str:
        op = f" {self.operator.value} "
        return f"({op.join(str(c) for c in self.conditions)})"


@dataclass
class SelectQuery:
    """Query SELECT completa"""
    fields: List[Field]
    from_table: str
    where: Optional[WhereClause] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

    def __str__(self) -> str:
        query = f"SELECT {', '.join(str(f) for f in self.fields)}\n"
        query += f"FROM {self.from_table}\n"
        if self.where:
            query += f"WHERE {self.where}\n"
        if self.limit:
            query += f"LIMIT {self.limit}\n"
        if self.offset:
            query += f"OFFSET {self.offset}"
        return query
