#!/usr/bin/env python3
"""
AI-Assisted Test Generator for MAXIMUS AI 3.0
Generates pytest test files using Claude API following DOUTRINA VÉRTICE

Author: Claude Code + JuanCS-Dev
Date: 2025-10-20
Usage: python scripts/generate_tests.py <module_path> [--test-type unit|integration|e2e]
"""

import argparse
import ast
import inspect
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import anthropic
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGenerator:
    """AI-powered test generator using Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize test generator.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def analyze_module(self, module_path: Path) -> Dict[str, Any]:
        """
        Analyze Python module to extract classes, functions, dependencies.

        Args:
            module_path: Path to Python module

        Returns:
            Dict with module analysis
        """
        with open(module_path, 'r') as f:
            source = f.read()

        tree = ast.parse(source)

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                classes.append({
                    'name': node.name,
                    'methods': methods,
                    'line': node.lineno
                })
            elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions
                if isinstance(getattr(node, 'parent', None), ast.Module):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno
                    })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))

        return {
            'source': source,
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'path': str(module_path)
        }

    def generate_test_prompt(
        self,
        module_info: Dict[str, Any],
        test_type: str = "unit",
        coverage_target: int = 90
    ) -> str:
        """
        Generate Claude prompt for test creation.

        Args:
            module_info: Module analysis from analyze_module()
            test_type: "unit", "integration", or "e2e"
            coverage_target: Desired coverage percentage

        Returns:
            Prompt string for Claude API
        """
        module_path = module_info['path']
        module_name = Path(module_path).stem

        prompt = f"""You are an expert Python test engineer following DOUTRINA VÉRTICE (Zero mocks, production-ready).

TASK: Generate comprehensive {test_type} tests for the following Python module.

MODULE: {module_path}
TARGET COVERAGE: {coverage_target}%
TEST TYPE: {test_type}

MODULE SOURCE CODE:
```python
{module_info['source']}
```

CLASSES FOUND: {len(module_info['classes'])}
{json.dumps(module_info['classes'], indent=2)}

FUNCTIONS FOUND: {len(module_info['functions'])}
{json.dumps(module_info['functions'], indent=2)}

REQUIREMENTS:
1. Generate pytest tests following existing pattern in tests/test_constitutional_validator_100pct.py
2. Use Testcontainers for external dependencies (Kafka, Redis, PostgreSQL)
3. NO MOCKS for integration/e2e tests - use real services via fixtures
4. Achieve {coverage_target}%+ coverage (statements + branches)
5. Include edge cases, error paths, and boundary conditions
6. Use descriptive test names and docstrings
7. Follow AAA pattern (Arrange, Act, Assert)
8. Add appropriate markers (@pytest.mark.unit, @pytest.mark.integration, etc.)

TEST FILE STRUCTURE:
- Import the module under test
- Import required fixtures from conftest.py
- Organize tests by class/function being tested
- Include test class docstrings
- Each test should have a docstring with SCENARIO and EXPECTED

EXAMPLE TEST STRUCTURE:
```python
\"\"\"
{module_name.title()} - {test_type.title()} Test Suite
Coverage Target: {coverage_target}%+

Author: AI-Generated via Claude Code
Date: 2025-10-20
\"\"\"

import pytest
from {module_name} import YourClass

class TestYourClass:
    \"\"\"Tests for YourClass.\"\"\"

    @pytest.mark.{test_type}
    def test_method_name_success_case(self):
        \"\"\"
        SCENARIO: Clear description
        EXPECTED: Expected outcome
        \"\"\"
        # Arrange
        instance = YourClass()

        # Act
        result = instance.method()

        # Assert
        assert result == expected_value
```

Generate ONLY the test file content. Do not include explanations outside the code.
Ensure all imports are correct and all edge cases are covered.
"""
        return prompt

    def generate_tests(
        self,
        module_path: Path,
        test_type: str = "unit",
        coverage_target: int = 90,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate test file for given module using Claude API.

        Args:
            module_path: Path to module to test
            test_type: Type of tests to generate
            coverage_target: Target coverage percentage
            output_path: Where to save test file (defaults to tests/)

        Returns:
            Generated test code as string
        """
        print(f"📝 Analyzing module: {module_path}")
        module_info = self.analyze_module(module_path)

        print(f"🤖 Generating {test_type} tests with Claude API...")
        prompt = self.generate_test_prompt(module_info, test_type, coverage_target)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.3,  # Lower temperature for more consistent code
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        test_code = response.content[0].text

        # Extract code from markdown if present
        if "```python" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0].strip()

        # Determine output path
        if output_path is None:
            module_name = module_path.stem
            test_dir = Path(__file__).parent.parent / "tests" / test_type
            test_dir.mkdir(parents=True, exist_ok=True)
            output_path = test_dir / f"test_{module_name}_{test_type}.py"

        # Save test file
        with open(output_path, 'w') as f:
            f.write(test_code)

        print(f"✅ Test file generated: {output_path}")
        return test_code

    def validate_test_file(self, test_path: Path) -> bool:
        """
        Validate generated test file (syntax, imports).

        Args:
            test_path: Path to test file

        Returns:
            True if valid, False otherwise
        """
        try:
            with open(test_path, 'r') as f:
                source = f.read()

            # Check syntax
            ast.parse(source)

            # Check imports
            # TODO: Could import test module and check for missing dependencies

            print(f"✅ Test file validation passed: {test_path}")
            return True

        except SyntaxError as e:
            print(f"❌ Syntax error in {test_path}: {e}")
            return False
        except Exception as e:
            print(f"⚠️  Validation warning for {test_path}: {e}")
            return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AI-assisted tests for MAXIMUS modules"
    )
    parser.add_argument(
        "module_path",
        type=Path,
        help="Path to Python module to test"
    )
    parser.add_argument(
        "--test-type",
        choices=["unit", "integration", "e2e"],
        default="unit",
        help="Type of tests to generate (default: unit)"
    )
    parser.add_argument(
        "--coverage-target",
        type=int,
        default=90,
        help="Target coverage percentage (default: 90)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for test file (default: tests/<test_type>/test_<module>_<type>.py)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated test file"
    )

    args = parser.parse_args()

    # Validate module path
    if not args.module_path.exists():
        print(f"❌ Module not found: {args.module_path}")
        sys.exit(1)

    # Generate tests
    generator = TestGenerator()

    try:
        test_code = generator.generate_tests(
            module_path=args.module_path,
            test_type=args.test_type,
            coverage_target=args.coverage_target,
            output_path=args.output
        )

        # Validate if requested
        if args.validate:
            output_path = args.output or (
                Path(__file__).parent.parent / "tests" / args.test_type /
                f"test_{args.module_path.stem}_{args.test_type}.py"
            )
            if not generator.validate_test_file(output_path):
                print("⚠️  Validation failed - please review generated tests")
                sys.exit(1)

        print(f"\n🎉 SUCCESS! Test generation complete.")
        print(f"   Next steps:")
        print(f"   1. Review generated tests")
        print(f"   2. Run: pytest {args.output or 'tests/'} -v")
        print(f"   3. Check coverage: pytest --cov")

    except Exception as e:
        print(f"❌ Test generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
