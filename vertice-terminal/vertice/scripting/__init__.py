"""
🔧 VÉRTICE SCRIPTING ENGINE
Domain-Specific Language (DSL) for workflow automation

Componentes:
- VScriptParser: Lexer + AST parser
- VScriptRuntime: Execution engine
- VScriptStdlib: Built-in functions
- VScriptValidator: Security & syntax validation

Example VScript:
```vscript
project = create_project("client-pentest")

hosts = scan_network("10.10.1.0/24", type="ping")
console.log(f"Discovered {len(hosts)} hosts")

for host in hosts:
    services = scan_ports(host, type="full")
    workspace.store(services)

generate_report(format="pdf", output="report.pdf")
```
"""

from .parser import VScriptParser, ASTNode
from .runtime import VScriptRuntime, ExecutionContext
from .stdlib import VScriptStdlib
from .validator import VScriptValidator, ValidationError, ValidationLevel
from .models import (
    Program,
    Statement,
    Expression,
    Assignment,
    FunctionCall,
    ForLoop,
    IfStatement,
    Variable,
    Literal,
    BinaryOp,
    VScriptType,
)

__all__ = [
    "VScriptParser",
    "ASTNode",
    "VScriptRuntime",
    "ExecutionContext",
    "VScriptStdlib",
    "VScriptValidator",
    "ValidationError",
    "ValidationLevel",
    "Program",
    "Statement",
    "Expression",
    "Assignment",
    "FunctionCall",
    "ForLoop",
    "IfStatement",
    "Variable",
    "Literal",
    "BinaryOp",
    "VScriptType",
]
