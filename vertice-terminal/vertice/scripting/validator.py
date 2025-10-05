"""
VScript Validator - Security & Syntax Validation

Validates VScript code for:
- Syntax errors
- Security issues (dangerous functions)
- Best practices
- Type checking (basic)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .models import *
from .parser import VScriptParser


class ValidationLevel(Enum):
    """Validation severity levels."""

    ERROR = "error"  # Will prevent execution
    WARNING = "warning"  # Should fix but won't prevent execution
    INFO = "info"  # Informational only


@dataclass
class ValidationIssue:
    """
    Validation issue.

    Attributes:
        level: Severity level
        message: Issue description
        line: Line number
        column: Column number
        code: Issue code (e.g., "SEC001")
    """

    level: ValidationLevel
    message: str
    line: int
    column: int = 0
    code: str = ""

    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] Line {self.line}: {self.message}"


class ValidationError(Exception):
    """Validation error exception."""

    def __init__(self, issues: List[ValidationIssue]):
        self.issues = issues
        super().__init__(f"{len(issues)} validation issue(s)")


class VScriptValidator:
    """
    VScript code validator.

    Performs security and syntax validation on VScript code.

    Example:
        validator = VScriptValidator()
        issues = validator.validate(source_code)
        if any(i.level == ValidationLevel.ERROR for i in issues):
            raise ValidationError(issues)
    """

    # Dangerous functions that require approval
    DANGEROUS_FUNCTIONS = {
        "execute_command": "Shell command execution",
        "eval": "Dynamic code evaluation",
        "exec": "Dynamic code execution",
        "__import__": "Dynamic import",
    }

    # Functions requiring special permissions
    RESTRICTED_FUNCTIONS = {
        "notify_email": "Email notifications",
        "notify_slack": "Slack notifications",
        "web_scan": "Web vulnerability scanning",
    }

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: Strict mode (warnings become errors)
        """
        self.strict = strict
        self.issues: List[ValidationIssue] = []

    def validate(self, source: str) -> List[ValidationIssue]:
        """
        Validate VScript source code.

        Args:
            source: VScript source code

        Returns:
            List of validation issues

        Raises:
            SyntaxError: If code has syntax errors
        """
        self.issues = []

        # Parse code
        try:
            parser = VScriptParser(source)
            program = parser.parse()
        except SyntaxError as e:
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=str(e),
                    line=0,
                    code="SYN001"
                )
            )
            return self.issues

        # Validate AST
        self._validate_program(program)

        return self.issues

    def _validate_program(self, program: Program) -> None:
        """Validate entire program."""
        for stmt in program.statements:
            self._validate_statement(stmt)

    def _validate_statement(self, stmt: Statement) -> None:
        """Validate statement."""
        if isinstance(stmt, Assignment):
            self._validate_expression(stmt.value)
            self._check_variable_naming(stmt.target, stmt.line)

        elif isinstance(stmt, IfStatement):
            self._validate_expression(stmt.condition)
            for s in stmt.body:
                self._validate_statement(s)
            for cond, body in stmt.elif_branches:
                self._validate_expression(cond)
                for s in body:
                    self._validate_statement(s)
            if stmt.else_body:
                for s in stmt.else_body:
                    self._validate_statement(s)

        elif isinstance(stmt, ForLoop):
            self._validate_expression(stmt.iterable)
            self._check_variable_naming(stmt.variable, stmt.line)
            for s in stmt.body:
                self._validate_statement(s)

        elif isinstance(stmt, WhileLoop):
            self._validate_expression(stmt.condition)
            for s in stmt.body:
                self._validate_statement(s)

        elif isinstance(stmt, ExpressionStatement):
            self._validate_expression(stmt.expression)

        elif isinstance(stmt, Return):
            if stmt.value:
                self._validate_expression(stmt.value)

    def _validate_expression(self, expr: Expression) -> None:
        """Validate expression."""
        if isinstance(expr, BinaryOp):
            self._validate_expression(expr.left)
            self._validate_expression(expr.right)

        elif isinstance(expr, UnaryOp):
            self._validate_expression(expr.operand)

        elif isinstance(expr, FunctionCall):
            self._validate_function_call(expr)
            for arg in expr.args:
                self._validate_expression(arg)
            for value in expr.kwargs.values():
                self._validate_expression(value)

        elif isinstance(expr, AttributeAccess):
            self._validate_expression(expr.object)

        elif isinstance(expr, MethodCall):
            self._validate_expression(expr.object)
            for arg in expr.args:
                self._validate_expression(arg)
            for value in expr.kwargs.values():
                self._validate_expression(value)

        elif isinstance(expr, ListLiteral):
            for elem in expr.elements:
                self._validate_expression(elem)

        elif isinstance(expr, DictLiteral):
            for key, value in expr.pairs:
                self._validate_expression(key)
                self._validate_expression(value)

        elif isinstance(expr, FString):
            for part in expr.parts:
                if isinstance(part, Expression):
                    self._validate_expression(part)

        elif isinstance(expr, IndexAccess):
            self._validate_expression(expr.object)
            self._validate_expression(expr.index)

    def _validate_function_call(self, expr: FunctionCall) -> None:
        """Validate function call for security issues."""
        # Check dangerous functions
        if expr.name in self.DANGEROUS_FUNCTIONS:
            reason = self.DANGEROUS_FUNCTIONS[expr.name]
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Dangerous function '{expr.name}': {reason}",
                    line=expr.line,
                    code="SEC001"
                )
            )

        # Check restricted functions
        if expr.name in self.RESTRICTED_FUNCTIONS:
            reason = self.RESTRICTED_FUNCTIONS[expr.name]
            level = ValidationLevel.ERROR if self.strict else ValidationLevel.WARNING
            self.issues.append(
                ValidationIssue(
                    level=level,
                    message=f"Restricted function '{expr.name}': {reason}",
                    line=expr.line,
                    code="SEC002"
                )
            )

    def _check_variable_naming(self, name: str, line: int) -> None:
        """Check variable naming conventions."""
        # Check reserved names
        reserved = {"True", "False", "None", "if", "else", "for", "while", "return"}
        if name in reserved:
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Cannot use reserved word '{name}' as variable name",
                    line=line,
                    code="NAM001"
                )
            )

        # Check Python naming conventions
        if not name.isidentifier():
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Invalid variable name '{name}'",
                    line=line,
                    code="NAM002"
                )
            )

        # Check snake_case convention
        if name.replace("_", "").isalnum() and not name.islower():
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Variable '{name}' should use snake_case",
                    line=line,
                    code="STY001"
                )
            )

    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return any(issue.level == ValidationLevel.ERROR for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if validation found any warnings."""
        return any(issue.level == ValidationLevel.WARNING for issue in self.issues)

    def print_issues(self) -> None:
        """Print all validation issues."""
        if not self.issues:
            print("✅ No validation issues found")
            return

        print(f"\n{len(self.issues)} validation issue(s):\n")

        for issue in self.issues:
            symbol = "❌" if issue.level == ValidationLevel.ERROR else "⚠️" if issue.level == ValidationLevel.WARNING else "ℹ️"
            print(f"{symbol} {issue}")

        # Summary
        errors = sum(1 for i in self.issues if i.level == ValidationLevel.ERROR)
        warnings = sum(1 for i in self.issues if i.level == ValidationLevel.WARNING)
        infos = sum(1 for i in self.issues if i.level == ValidationLevel.INFO)

        print(f"\nSummary: {errors} error(s), {warnings} warning(s), {infos} info(s)")


def validate_script(source: str, strict: bool = False) -> List[ValidationIssue]:
    """
    Convenience function to validate VScript code.

    Args:
        source: VScript source code
        strict: Strict mode (warnings become errors)

    Returns:
        List of validation issues

    Example:
        issues = validate_script(code)
        if any(i.level == ValidationLevel.ERROR for i in issues):
            print("Validation failed")
    """
    validator = VScriptValidator(strict=strict)
    return validator.validate(source)
