"""
VScript Runtime - Execution Engine

Executes VScript AST with:
- Variable scoping
- Built-in function calls
- Error handling
- Execution context tracking
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import logging

from .models import *
from .stdlib import VScriptStdlib

# Import IndexAccess explicitly for type checking
from .models import IndexAccess

logger = logging.getLogger(__name__)


class BreakException(Exception):
    """Break statement exception."""
    pass


class ContinueException(Exception):
    """Continue statement exception."""
    pass


class ReturnException(Exception):
    """Return statement exception."""

    def __init__(self, value: Any = None):
        self.value = value
        super().__init__()


@dataclass
class ExecutionContext:
    """
    Execution context with variable scoping.

    Attributes:
        variables: Variable storage (scoped)
        parent: Parent context (for nested scopes)
        stdlib: Standard library functions
    """

    variables: Dict[str, Any] = field(default_factory=dict)
    parent: Optional["ExecutionContext"] = None
    stdlib: Optional[VScriptStdlib] = None

    def get(self, name: str) -> Any:
        """Get variable value."""
        if name in self.variables:
            return self.variables[name]

        if self.parent:
            return self.parent.get(name)

        raise NameError(f"Variable '{name}' is not defined")

    def set(self, name: str, value: Any) -> None:
        """Set variable value."""
        self.variables[name] = value

    def has(self, name: str) -> bool:
        """Check if variable exists."""
        return name in self.variables or (self.parent and self.parent.has(name))

    def create_child(self) -> "ExecutionContext":
        """Create child context (nested scope)."""
        return ExecutionContext(parent=self, stdlib=self.stdlib)


class VScriptRuntime:
    """
    VScript runtime executor.

    Example:
        runtime = VScriptRuntime()
        result = runtime.execute(program)
    """

    def __init__(self, stdlib: Optional[VScriptStdlib] = None):
        """
        Initialize runtime.

        Args:
            stdlib: Standard library (if None, creates default)
        """
        self.stdlib = stdlib or VScriptStdlib()
        self.global_context = ExecutionContext(stdlib=self.stdlib)

        # Inject global objects
        self.global_context.set("console", self.stdlib.console)
        self.global_context.set("workspace", self.stdlib.workspace)

    def execute(self, program: Program) -> Any:
        """
        Execute program.

        Args:
            program: Parsed AST

        Returns:
            Last statement result (or None)
        """
        logger.info(f"Executing VScript program ({len(program.statements)} statements)")

        result = None

        try:
            for stmt in program.statements:
                result = self.execute_statement(stmt, self.global_context)

        except ReturnException as e:
            result = e.value

        return result

    def execute_statement(self, stmt: Statement, context: ExecutionContext) -> Any:
        """Execute statement."""
        if isinstance(stmt, Assignment):
            return self.execute_assignment(stmt, context)

        elif isinstance(stmt, IfStatement):
            return self.execute_if(stmt, context)

        elif isinstance(stmt, ForLoop):
            return self.execute_for(stmt, context)

        elif isinstance(stmt, WhileLoop):
            return self.execute_while(stmt, context)

        elif isinstance(stmt, ExpressionStatement):
            return self.evaluate_expression(stmt.expression, context)

        elif isinstance(stmt, Return):
            value = None if stmt.value is None else self.evaluate_expression(stmt.value, context)
            raise ReturnException(value)

        elif isinstance(stmt, Break):
            raise BreakException()

        elif isinstance(stmt, Continue):
            raise ContinueException()

        elif isinstance(stmt, Comment):
            # Comments do nothing
            return None

        else:
            raise RuntimeError(f"Unknown statement type: {type(stmt)}")

    def execute_assignment(self, stmt: Assignment, context: ExecutionContext) -> None:
        """Execute assignment."""
        value = self.evaluate_expression(stmt.value, context)
        context.set(stmt.target, value)
        logger.debug(f"Assignment: {stmt.target} = {value}")

    def execute_if(self, stmt: IfStatement, context: ExecutionContext) -> Any:
        """Execute if/elif/else."""
        condition = self.evaluate_expression(stmt.condition, context)

        if self.is_truthy(condition):
            # Use same context - Python-like scoping
            for s in stmt.body:
                self.execute_statement(s, context)
            return None

        # Check elif branches
        for elif_cond, elif_body in stmt.elif_branches:
            elif_value = self.evaluate_expression(elif_cond, context)
            if self.is_truthy(elif_value):
                for s in elif_body:
                    self.execute_statement(s, context)
                return None

        # Else branch
        if stmt.else_body:
            for s in stmt.else_body:
                self.execute_statement(s, context)

        return None

    def execute_for(self, stmt: ForLoop, context: ExecutionContext) -> Any:
        """Execute for loop."""
        iterable = self.evaluate_expression(stmt.iterable, context)

        # Must be iterable
        if not isinstance(iterable, (list, tuple, range, str)):
            raise TypeError(f"Cannot iterate over {type(iterable)}")

        try:
            for item in iterable:
                # Use same context - Python-like scoping
                context.set(stmt.variable, item)

                try:
                    for s in stmt.body:
                        self.execute_statement(s, context)
                except ContinueException:
                    continue

        except BreakException:
            pass

        return None

    def execute_while(self, stmt: WhileLoop, context: ExecutionContext) -> Any:
        """Execute while loop."""
        try:
            while True:
                condition = self.evaluate_expression(stmt.condition, context)
                if not self.is_truthy(condition):
                    break

                try:
                    for s in stmt.body:
                        self.execute_statement(s, context)
                except ContinueException:
                    continue

        except BreakException:
            pass

        return None

    def evaluate_expression(self, expr: Expression, context: ExecutionContext) -> Any:
        """Evaluate expression."""
        if isinstance(expr, Literal):
            return expr.value

        elif isinstance(expr, Variable):
            return context.get(expr.name)

        elif isinstance(expr, BinaryOp):
            return self.evaluate_binary_op(expr, context)

        elif isinstance(expr, UnaryOp):
            return self.evaluate_unary_op(expr, context)

        elif isinstance(expr, FunctionCall):
            return self.evaluate_function_call(expr, context)

        elif isinstance(expr, AttributeAccess):
            return self.evaluate_attribute_access(expr, context)

        elif isinstance(expr, MethodCall):
            return self.evaluate_method_call(expr, context)

        elif isinstance(expr, ListLiteral):
            return [self.evaluate_expression(e, context) for e in expr.elements]

        elif isinstance(expr, DictLiteral):
            return {
                self.evaluate_expression(k, context): self.evaluate_expression(v, context)
                for k, v in expr.pairs
            }

        elif isinstance(expr, FString):
            return self.evaluate_fstring(expr, context)

        elif isinstance(expr, IndexAccess):
            return self.evaluate_index_access(expr, context)

        else:
            raise RuntimeError(f"Unknown expression type: {type(expr)}")

    def evaluate_binary_op(self, expr: BinaryOp, context: ExecutionContext) -> Any:
        """Evaluate binary operation."""
        left = self.evaluate_expression(expr.left, context)
        right = self.evaluate_expression(expr.right, context)

        op = expr.operator

        # Arithmetic
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            return left / right

        # Comparison
        elif op == "==":
            return left == right
        elif op == "!=":
            return left != right
        elif op == "<":
            return left < right
        elif op == ">":
            return left > right
        elif op == "<=":
            return left <= right
        elif op == ">=":
            return left >= right

        # Logical
        elif op == "and":
            return left and right
        elif op == "or":
            return left or right

        else:
            raise RuntimeError(f"Unknown operator: {op}")

    def evaluate_unary_op(self, expr: UnaryOp, context: ExecutionContext) -> Any:
        """Evaluate unary operation."""
        operand = self.evaluate_expression(expr.operand, context)

        if expr.operator == "not":
            return not self.is_truthy(operand)
        elif expr.operator == "-":
            return -operand
        else:
            raise RuntimeError(f"Unknown unary operator: {expr.operator}")

    def evaluate_function_call(self, expr: FunctionCall, context: ExecutionContext) -> Any:
        """Evaluate function call."""
        # Evaluate arguments
        args = [self.evaluate_expression(arg, context) for arg in expr.args]
        kwargs = {k: self.evaluate_expression(v, context) for k, v in expr.kwargs.items()}

        # Check stdlib
        if context.stdlib and hasattr(context.stdlib, expr.name):
            func = getattr(context.stdlib, expr.name)
            logger.debug(f"Calling stdlib.{expr.name}(*{args}, **{kwargs})")
            return func(*args, **kwargs)

        # Check builtins
        builtins = {"len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict}
        if expr.name in builtins:
            return builtins[expr.name](*args, **kwargs)

        raise NameError(f"Function '{expr.name}' is not defined")

    def evaluate_attribute_access(self, expr: AttributeAccess, context: ExecutionContext) -> Any:
        """Evaluate attribute access."""
        obj = self.evaluate_expression(expr.object, context)

        # Special handling for workspace object
        if isinstance(expr.object, Variable) and expr.object.name == "workspace":
            return getattr(context.stdlib.workspace, expr.attribute)

        # General attribute access
        if hasattr(obj, expr.attribute):
            return getattr(obj, expr.attribute)

        raise AttributeError(f"Object has no attribute '{expr.attribute}'")

    def evaluate_method_call(self, expr: MethodCall, context: ExecutionContext) -> Any:
        """Evaluate method call."""
        obj = self.evaluate_expression(expr.object, context)

        # Evaluate arguments
        args = [self.evaluate_expression(arg, context) for arg in expr.args]
        kwargs = {k: self.evaluate_expression(v, context) for k, v in expr.kwargs.items()}

        # Get method
        if hasattr(obj, expr.method):
            method = getattr(obj, expr.method)
            if callable(method):
                logger.debug(f"Calling {obj}.{expr.method}(*{args}, **{kwargs})")
                return method(*args, **kwargs)

        raise AttributeError(f"Object has no method '{expr.method}'")

    def evaluate_fstring(self, expr: FString, context: ExecutionContext) -> str:
        """Evaluate f-string."""
        result = ""

        for part in expr.parts:
            if isinstance(part, str):
                result += part
            else:
                # Evaluate expression
                value = self.evaluate_expression(part, context)
                result += str(value)

        return result

    def evaluate_index_access(self, expr: IndexAccess, context: ExecutionContext) -> Any:
        """Evaluate index access (obj[index])."""
        obj = self.evaluate_expression(expr.object, context)
        index = self.evaluate_expression(expr.index, context)

        # List/tuple indexing
        if isinstance(obj, (list, tuple)):
            if not isinstance(index, int):
                raise TypeError(f"List indices must be integers, not {type(index).__name__}")
            return obj[index]

        # Dict indexing
        elif isinstance(obj, dict):
            return obj[index]

        # String indexing
        elif isinstance(obj, str):
            if not isinstance(index, int):
                raise TypeError(f"String indices must be integers, not {type(index).__name__}")
            return obj[index]

        else:
            raise TypeError(f"'{type(obj).__name__}' object is not subscriptable")

    @staticmethod
    def is_truthy(value: Any) -> bool:
        """Check if value is truthy (Python semantics)."""
        if value is None or value is False:
            return False
        if value == 0 or value == "" or value == [] or value == {}:
            return False
        return True
