"""
VScript AST Models & Types
"""

from typing import Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, field


class VScriptType(Enum):
    """VScript type system."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    NULL = "null"
    FUNCTION = "function"


# ========================================
# AST Node Base
# ========================================

@dataclass
class ASTNode:
    """Base class for AST nodes."""

    line: int = field(default=0, kw_only=True)
    column: int = field(default=0, kw_only=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(line={self.line})"


# ========================================
# Expressions
# ========================================

@dataclass
class Expression(ASTNode):
    """Base class for expressions."""
    pass


@dataclass
class Literal(Expression):
    """Literal value (string, int, etc)."""

    value: Any
    type: VScriptType

    def __repr__(self) -> str:
        return f"Literal({self.value!r})"


@dataclass
class Variable(Expression):
    """Variable reference."""

    name: str

    def __repr__(self) -> str:
        return f"Variable({self.name})"


@dataclass
class BinaryOp(Expression):
    """Binary operation (a + b, a == b, etc)."""

    left: Expression
    operator: str  # +, -, *, /, ==, !=, <, >, and, or
    right: Expression

    def __repr__(self) -> str:
        return f"BinaryOp({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOp(Expression):
    """Unary operation (not x, -x)."""

    operator: str  # not, -
    operand: Expression

    def __repr__(self) -> str:
        return f"UnaryOp({self.operator} {self.operand})"


@dataclass
class FunctionCall(Expression):
    """Function call expression."""

    name: str
    args: List[Expression] = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"FunctionCall({self.name})"


@dataclass
class AttributeAccess(Expression):
    """Attribute access (object.attribute)."""

    object: Expression
    attribute: str

    def __repr__(self) -> str:
        return f"AttributeAccess({self.object}.{self.attribute})"


@dataclass
class MethodCall(Expression):
    """Method call (object.method(args))."""

    object: Expression
    method: str
    args: List[Expression] = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"MethodCall({self.object}.{self.method})"


@dataclass
class IndexAccess(Expression):
    """Index access (obj[index])."""

    object: Expression
    index: Expression

    def __repr__(self) -> str:
        return f"IndexAccess({self.object}[{self.index}])"


@dataclass
class ListLiteral(Expression):
    """List literal [1, 2, 3]."""

    elements: List[Expression] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"List({len(self.elements)} elements)"


@dataclass
class DictLiteral(Expression):
    """Dict literal {key: value}."""

    pairs: List[tuple[Expression, Expression]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Dict({len(self.pairs)} pairs)"


@dataclass
class FString(Expression):
    """F-string (f"hello {name}")."""

    parts: List[Union[str, Expression]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"FString({len(self.parts)} parts)"


# ========================================
# Statements
# ========================================

@dataclass
class Statement(ASTNode):
    """Base class for statements."""
    pass


@dataclass
class Assignment(Statement):
    """Variable assignment (x = value)."""

    target: str
    value: Expression

    def __repr__(self) -> str:
        return f"Assignment({self.target} = {self.value})"


@dataclass
class IfStatement(Statement):
    """If/elif/else statement."""

    condition: Expression
    body: List[Statement] = field(default_factory=list)
    elif_branches: List[tuple[Expression, List[Statement]]] = field(default_factory=list)
    else_body: Optional[List[Statement]] = None

    def __repr__(self) -> str:
        return f"If({self.condition})"


@dataclass
class ForLoop(Statement):
    """For loop (for x in iterable:)."""

    variable: str
    iterable: Expression
    body: List[Statement] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"For({self.variable} in {self.iterable})"


@dataclass
class WhileLoop(Statement):
    """While loop (while condition:)."""

    condition: Expression
    body: List[Statement] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"While({self.condition})"


@dataclass
class ExpressionStatement(Statement):
    """Expression as statement (function call on its own line)."""

    expression: Expression

    def __repr__(self) -> str:
        return f"ExprStmt({self.expression})"


@dataclass
class Return(Statement):
    """Return statement."""

    value: Optional[Expression] = None

    def __repr__(self) -> str:
        return f"Return({self.value})"


@dataclass
class Break(Statement):
    """Break statement."""

    def __repr__(self) -> str:
        return "Break"


@dataclass
class Continue(Statement):
    """Continue statement."""

    def __repr__(self) -> str:
        return "Continue"


@dataclass
class Comment(Statement):
    """Comment (# text)."""

    text: str

    def __repr__(self) -> str:
        return f"Comment({self.text!r})"


# ========================================
# Program
# ========================================

@dataclass
class Program(ASTNode):
    """Complete VScript program (AST root)."""

    statements: List[Statement] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Program({len(self.statements)} statements)"
