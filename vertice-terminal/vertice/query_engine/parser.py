"""
📝 VeQL Parser - Transforma string query em AST

Gramática VeQL:
    query     → SELECT fields FROM table [WHERE conditions] [LIMIT num] [OFFSET num]
    fields    → field | field, fields
    field     → IDENTIFIER.IDENTIFIER | *
    table     → IDENTIFIER
    conditions→ condition | condition AND/OR conditions
    condition → field OPERATOR value
"""

import re
from typing import List, Optional
from .ast_nodes import (
    SelectQuery,
    WhereClause,
    Field,
    Value,
    Condition,
    Operator,
)


class VeQLParseError(Exception):
    """Erro de parsing do VeQL"""
    pass


class VeQLParser:
    """Parser VeQL - transforma query string em AST"""

    # Regex patterns (sem capturing groups)
    KEYWORDS = r'\b(?:SELECT|FROM|WHERE|AND|OR|NOT|IN|LIKE|LIMIT|OFFSET)\b'
    IDENTIFIER = r'[a-zA-Z_][a-zA-Z0-9_]*'
    NUMBER = r'\d+\.?\d*'
    STRING = r'"[^"]*"|\'[^\']*\''
    OPERATOR_PATTERN = r'(?:!=|>=|<=|=|>|<)'

    def __init__(self):
        self.tokens: List[str] = []
        self.pos: int = 0

    def parse(self, query: str) -> SelectQuery:
        """
        Parseia uma query VeQL e retorna AST

        Args:
            query: String VeQL (ex: "SELECT * FROM endpoints")

        Returns:
            SelectQuery: AST da query

        Raises:
            VeQLParseError: Se a query for inválida
        """
        # Tokeniza a query
        self.tokens = self._tokenize(query)
        self.pos = 0

        # Parse SELECT clause
        if not self._consume("SELECT"):
            raise VeQLParseError("Query must start with SELECT")

        fields = self._parse_fields()

        # Parse FROM clause
        if not self._consume("FROM"):
            raise VeQLParseError("Missing FROM clause")

        from_table = self._consume_identifier()
        if not from_table:
            raise VeQLParseError("Invalid table name")

        # Parse WHERE clause (opcional)
        where_clause = None
        if self._peek() == "WHERE":
            self._consume("WHERE")
            where_clause = self._parse_where()

        # Parse LIMIT (opcional)
        limit = None
        if self._peek() == "LIMIT":
            self._consume("LIMIT")
            limit = self._consume_number()

        # Parse OFFSET (opcional)
        offset = None
        if self._peek() == "OFFSET":
            self._consume("OFFSET")
            offset = self._consume_number()

        return SelectQuery(
            fields=fields,
            from_table=from_table,
            where=where_clause,
            limit=limit,
            offset=offset,
        )

    def _tokenize(self, query: str) -> List[str]:
        """Quebra query em tokens"""
        # Remove comentários
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)

        # Tokeniza - usa non-capturing groups
        pattern = f'(?:{self.KEYWORDS})|(?:{self.STRING})|(?:{self.NUMBER})|(?:{self.OPERATOR_PATTERN})|[(),.*]|(?:{self.IDENTIFIER})'

        tokens = re.findall(pattern, query, re.IGNORECASE)
        return [t.strip() for t in tokens if t and t.strip()]

    def _peek(self) -> Optional[str]:
        """Retorna próximo token sem consumir"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _consume(self, expected: str) -> bool:
        """Consome token esperado"""
        if self._peek() and self._peek().upper() == expected.upper():
            self.pos += 1
            return True
        return False

    def _consume_identifier(self) -> Optional[str]:
        """Consome um identificador"""
        token = self._peek()
        if token and re.match(f'^{self.IDENTIFIER}$', token):
            self.pos += 1
            return token
        return None

    def _consume_number(self) -> Optional[int]:
        """Consome um número"""
        token = self._peek()
        if token and re.match(f'^{self.NUMBER}$', token):
            self.pos += 1
            return int(float(token))
        return None

    def _consume_string(self) -> Optional[str]:
        """Consome uma string"""
        token = self._peek()
        if token and re.match(f'^{self.STRING}$', token):
            self.pos += 1
            return token.strip('"').strip("'")
        return None

    def _parse_fields(self) -> List[Field]:
        """Parse lista de campos (ex: process.name, network.ip)"""
        fields = []

        while True:
            # Wildcard (*)
            if self._peek() == "*":
                self.pos += 1
                fields.append(Field("*", "*"))
                break

            # Campo específico (table.column)
            table = self._consume_identifier()
            if not table:
                break

            if self._consume("."):
                column = self._consume_identifier()
                if not column:
                    raise VeQLParseError(f"Invalid field after {table}.")
                fields.append(Field(table, column))
            else:
                raise VeQLParseError(f"Expected '.' after {table}")

            # Próximo campo?
            if not self._consume(","):
                break

        if not fields:
            raise VeQLParseError("No fields specified in SELECT")

        return fields

    def _parse_where(self) -> WhereClause:
        """Parse cláusula WHERE"""
        conditions = []

        # Parse primeira condição
        conditions.append(self._parse_condition())

        # Parse condições adicionais (AND/OR)
        while self._peek() in ["AND", "OR"]:
            operator = Operator.AND if self._peek() == "AND" else Operator.OR
            self._consume(self._peek())
            conditions.append(self._parse_condition())

        return WhereClause(conditions=conditions)

    def _parse_condition(self) -> Condition:
        """Parse condição individual (ex: process.name = "cmd.exe")"""
        # Left side (field)
        left_table = self._consume_identifier()
        if not left_table:
            raise VeQLParseError("Expected field in condition")

        if not self._consume("."):
            raise VeQLParseError(f"Expected '.' after {left_table}")

        left_column = self._consume_identifier()
        if not left_column:
            raise VeQLParseError(f"Expected column after {left_table}.")

        left = Field(left_table, left_column)

        # Operator
        operator = self._parse_operator()
        if not operator:
            raise VeQLParseError(f"Expected operator after {left}")

        # Right side (value)
        right = self._parse_value()
        if not right:
            raise VeQLParseError(f"Expected value after {operator.value}")

        return Condition(left=left, operator=operator, right=right)

    def _parse_operator(self) -> Optional[Operator]:
        """Parse operador"""
        token = self._peek()

        if token == "=":
            self.pos += 1
            return Operator.EQ
        elif token == "!=":
            self.pos += 1
            return Operator.NEQ
        elif token == ">":
            self.pos += 1
            if self._consume("="):
                return Operator.GTE
            return Operator.GT
        elif token == "<":
            self.pos += 1
            if self._consume("="):
                return Operator.LTE
            return Operator.LT
        elif token and token.upper() == "IN":
            self.pos += 1
            return Operator.IN
        elif token and token.upper() == "NOT":
            self.pos += 1
            if self._consume("IN"):
                return Operator.NOT_IN
        elif token and token.upper() == "LIKE":
            self.pos += 1
            return Operator.LIKE

        return None

    def _parse_value(self) -> Optional[Value]:
        """Parse valor (string, número, lista)"""
        # String
        string_val = self._consume_string()
        if string_val is not None:
            return Value(string_val)

        # Número
        num_val = self._consume_number()
        if num_val is not None:
            return Value(num_val)

        # Lista (para IN)
        if self._consume("("):
            values = []
            while True:
                val = self._consume_string() or self._consume_number()
                if val is not None:
                    values.append(val)

                if not self._consume(","):
                    break

            if not self._consume(")"):
                raise VeQLParseError("Expected ')' to close list")

            return Value(values)

        return None
