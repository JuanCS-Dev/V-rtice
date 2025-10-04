"""
Unit Tests: VScript Workflow Automation (Phase 2.4)
===================================================

Tests for VScript DSL system:
- Parser (Lexer + AST)
- Runtime (Execution engine)
- Stdlib (Built-in functions)
- Validator (Security & syntax)
"""

import pytest
from pathlib import Path
import tempfile

from vertice.scripting import (
    VScriptParser,
    VScriptRuntime,
    VScriptValidator,
    VScriptStdlib,
    ValidationLevel,
    ValidationError,
    # AST Nodes
    Program,
    Assignment,
    IfStatement,
    ForLoop,
    FunctionCall,
    Variable,
    Literal,
    BinaryOp,
    VScriptType,
)


# ========================================
# Test Parser
# ========================================

class TestVScriptParser:
    """Test VScript parser."""

    def test_parse_assignment(self):
        """Test parsing variable assignment."""
        source = "x = 5"
        parser = VScriptParser(source)
        program = parser.parse()

        assert len(program.statements) == 1
        stmt = program.statements[0]

        assert isinstance(stmt, Assignment)
        assert stmt.target == "x"
        assert isinstance(stmt.value, Literal)
        assert stmt.value.value == 5

    def test_parse_string_literal(self):
        """Test parsing string literal."""
        source = 'message = "hello world"'
        parser = VScriptParser(source)
        program = parser.parse()

        assert len(program.statements) == 1
        assert program.statements[0].value.value == "hello world"

    def test_parse_list_literal(self):
        """Test parsing list literal."""
        source = "hosts = [1, 2, 3]"
        parser = VScriptParser(source)
        program = parser.parse()

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert stmt.target == "hosts"

    def test_parse_function_call(self):
        """Test parsing function call."""
        source = 'result = scan_network("10.0.0.0/24", type="ping")'
        parser = VScriptParser(source)
        program = parser.parse()

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt.value, FunctionCall)
        assert stmt.value.name == "scan_network"
        assert len(stmt.value.args) == 1
        assert "type" in stmt.value.kwargs

    def test_parse_if_statement(self):
        """Test parsing if statement."""
        source = """
if x > 5:
    y = 10
"""
        parser = VScriptParser(source)
        program = parser.parse()

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, IfStatement)
        assert isinstance(stmt.condition, BinaryOp)
        assert len(stmt.body) >= 1

    def test_parse_for_loop(self):
        """Test parsing for loop."""
        source = """
for host in hosts:
    console.log(host)
"""
        parser = VScriptParser(source)
        program = parser.parse()

        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, ForLoop)
        assert stmt.variable == "host"

    def test_parse_fstring(self):
        """Test parsing f-string."""
        source = 'message = f"Found {count} hosts"'
        parser = VScriptParser(source)
        program = parser.parse()

        # Should parse without errors
        assert len(program.statements) == 1

    def test_parse_method_call(self):
        """Test parsing method call."""
        source = "workspace.store(data)"
        parser = VScriptParser(source)
        program = parser.parse()

        assert len(program.statements) == 1

    def test_parse_comment(self):
        """Test parsing comments."""
        source = """
# This is a comment
x = 5  # Inline comment supported by parsing line-by-line
"""
        parser = VScriptParser(source)
        program = parser.parse()

        # Comments are parsed but can be ignored during execution
        assert len(program.statements) >= 1


# ========================================
# Test Runtime
# ========================================

class TestVScriptRuntime:
    """Test VScript runtime execution."""

    @pytest.fixture
    def runtime(self):
        return VScriptRuntime()

    def test_execute_assignment(self, runtime):
        """Test executing assignment."""
        source = "x = 42"
        parser = VScriptParser(source)
        program = parser.parse()

        runtime.execute(program)

        assert runtime.global_context.get("x") == 42

    def test_execute_arithmetic(self, runtime):
        """Test arithmetic operations."""
        source = """
a = 10
b = 5
c = a + b
d = a - b
e = a * b
f = a / b
"""
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        assert runtime.global_context.get("c") == 15
        assert runtime.global_context.get("d") == 5
        assert runtime.global_context.get("e") == 50
        assert runtime.global_context.get("f") == 2.0

    def test_execute_comparison(self, runtime):
        """Test comparison operations."""
        source = """
a = 10
b = 5
greater = a > b
less = a < b
equal = a == a
not_equal = a != b
"""
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        assert runtime.global_context.get("greater") is True
        assert runtime.global_context.get("less") is False
        assert runtime.global_context.get("equal") is True
        assert runtime.global_context.get("not_equal") is True

    def test_execute_if_statement(self, runtime):
        """Test if statement execution."""
        source = """
x = 10
if x > 5:
    result = "greater"
"""
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        assert runtime.global_context.get("result") == "greater"

    def test_execute_if_else(self, runtime):
        """Test if/else execution."""
        source = """
x = 3
if x > 5:
    result = "greater"
else:
    result = "less_or_equal"
"""
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        assert runtime.global_context.get("result") == "less_or_equal"

    def test_execute_for_loop(self, runtime):
        """Test for loop execution."""
        source = """
total = 0
for i in [1, 2, 3, 4, 5]:
    total = total + i
"""
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        assert runtime.global_context.get("total") == 15

    def test_execute_list_operations(self, runtime):
        """Test list operations."""
        source = """
hosts = [1, 2, 3]
count = len(hosts)
"""
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        assert runtime.global_context.get("count") == 3

    def test_execute_stdlib_function(self, runtime):
        """Test standard library function call."""
        source = """
project = create_project("test")
"""
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        project = runtime.global_context.get("project")
        assert project is not None
        assert project["name"] == "test"


# ========================================
# Test Standard Library
# ========================================

class TestVScriptStdlib:
    """Test VScript standard library."""

    @pytest.fixture
    def stdlib(self):
        return VScriptStdlib()

    def test_create_project(self, stdlib):
        """Test project creation."""
        project = stdlib.create_project("pentest-1")

        assert project["name"] == "pentest-1"
        assert "hosts" in project
        assert "findings" in project

    def test_scan_network(self, stdlib):
        """Test network scanning."""
        hosts = stdlib.scan_network("10.0.0.0/24", type="ping")

        assert isinstance(hosts, list)
        assert len(hosts) > 0
        assert all("ip" in h for h in hosts)

    def test_scan_ports(self, stdlib):
        """Test port scanning."""
        result = stdlib.scan_ports("10.0.0.1", type="quick")

        assert "host" in result
        assert "ports" in result
        assert isinstance(result["ports"], list)

    def test_web_scan(self, stdlib):
        """Test web scanning."""
        result = stdlib.web_scan("10.0.0.1", tool="nikto")

        assert "host" in result
        assert "tool" in result
        assert "vulns" in result

    def test_workspace_store(self, stdlib):
        """Test workspace storage."""
        data = {"test": "value"}
        stdlib.workspace.store(data)

        assert len(stdlib.workspace.data) == 1
        assert stdlib.workspace.data[0] == data

    def test_generate_report(self, stdlib):
        """Test report generation."""
        stdlib.create_project("test-report")
        report = stdlib.generate_report(format="markdown")

        assert isinstance(report, str)
        assert "# VScript Report" in report

    def test_console_log(self, stdlib, capsys):
        """Test console logging."""
        stdlib.console.log("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.out


# ========================================
# Test Validator
# ========================================

class TestVScriptValidator:
    """Test VScript validator."""

    def test_validate_valid_code(self):
        """Test validation of valid code."""
        source = """
x = 5
y = 10
result = x + y
"""
        validator = VScriptValidator()
        issues = validator.validate(source)

        assert len([i for i in issues if i.level == ValidationLevel.ERROR]) == 0

    def test_validate_syntax_error(self):
        """Test syntax error detection."""
        source = "x = "  # Incomplete assignment
        validator = VScriptValidator()
        issues = validator.validate(source)

        assert len(issues) > 0
        assert any(i.level == ValidationLevel.ERROR for i in issues)

    def test_validate_dangerous_function(self):
        """Test dangerous function detection."""
        source = """
result = execute_command("rm -rf /")
"""
        validator = VScriptValidator()
        issues = validator.validate(source)

        # Should have security error
        assert any(
            i.level == ValidationLevel.ERROR and "execute_command" in i.message
            for i in issues
        )

    def test_validate_restricted_function_warning(self):
        """Test restricted function warning."""
        source = """
web_scan("10.0.0.1")
"""
        validator = VScriptValidator(strict=False)
        issues = validator.validate(source)

        # Should have warning (not error in non-strict mode)
        assert any(
            i.level == ValidationLevel.WARNING and "web_scan" in i.message
            for i in issues
        )

    def test_validate_reserved_word(self):
        """Test reserved word as variable name."""
        source = "if = 5"  # 'if' is reserved
        validator = VScriptValidator()
        issues = validator.validate(source)

        assert any(i.level == ValidationLevel.ERROR for i in issues)

    def test_has_errors(self):
        """Test error checking."""
        source = "x = "
        validator = VScriptValidator()
        validator.validate(source)

        assert validator.has_errors() is True

    def test_has_warnings(self):
        """Test warning checking."""
        source = "web_scan('10.0.0.1')"
        validator = VScriptValidator(strict=False)
        validator.validate(source)

        assert validator.has_warnings() is True


# ========================================
# Integration Tests
# ========================================

class TestVScriptIntegration:
    """Integration tests combining multiple components."""

    def test_full_workflow_execution(self):
        """Test complete workflow from parse to execute."""
        source = """
# Create project
project = create_project("integration-test")

# Scan network
hosts = scan_network("10.0.0.0/24", type="ping")

# Count results
count = len(hosts)
console.log(f"Found {count} hosts")
"""
        # Validate
        validator = VScriptValidator()
        issues = validator.validate(source)
        assert not validator.has_errors()

        # Parse
        parser = VScriptParser(source)
        program = parser.parse()
        assert len(program.statements) > 0

        # Execute
        runtime = VScriptRuntime()
        runtime.execute(program)

        # Check results
        assert runtime.global_context.has("project")
        assert runtime.global_context.has("hosts")
        assert runtime.global_context.has("count")

    def test_conditional_workflow(self):
        """Test workflow with conditional logic."""
        source = """
hosts = scan_network("10.0.0.0/24")

critical_count = 0

for host in hosts:
    services = scan_ports(host)

    if len(services['ports']) > 5:
        critical_count = critical_count + 1

result = critical_count
"""
        runtime = VScriptRuntime()
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        assert runtime.global_context.has("result")
        assert isinstance(runtime.global_context.get("result"), int)

    def test_workspace_integration(self):
        """Test workspace integration in workflow."""
        source = """
project = create_project("workspace-test")

hosts = scan_network("10.0.0.0/24")

for host in hosts:
    services = scan_ports(host)
    workspace.store(services)

stored_count = len(workspace.data)
"""
        runtime = VScriptRuntime()
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        stored = runtime.global_context.get("stored_count")
        assert stored > 0

    def test_complex_expression(self):
        """Test complex expressions."""
        source = """
x = 10
y = 5
z = 3

result = (x + y) * z - (x / y)
"""
        runtime = VScriptRuntime()
        parser = VScriptParser(source)
        program = parser.parse()
        runtime.execute(program)

        # (10 + 5) * 3 - (10 / 5) = 15 * 3 - 2 = 45 - 2 = 43
        assert runtime.global_context.get("result") == 43.0

    def test_error_handling(self):
        """Test error handling in runtime."""
        source = """
x = undefined_variable
"""
        runtime = VScriptRuntime()
        parser = VScriptParser(source)
        program = parser.parse()

        with pytest.raises(NameError):
            runtime.execute(program)


# ========================================
# File-based Tests
# ========================================

class TestVScriptFileExecution:
    """Test VScript file execution."""

    def test_execute_script_file(self):
        """Test executing script from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vscript", delete=False) as f:
            f.write("""
# Test script
x = 42
y = x * 2
result = y
""")
            script_path = f.name

        try:
            # Read and execute
            source = Path(script_path).read_text()

            runtime = VScriptRuntime()
            parser = VScriptParser(source)
            program = parser.parse()
            runtime.execute(program)

            assert runtime.global_context.get("result") == 84

        finally:
            Path(script_path).unlink()
