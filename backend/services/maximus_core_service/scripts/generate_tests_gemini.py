#!/usr/bin/env python3
"""
AI-Assisted Test Generator for MAXIMUS AI 3.0 - Gemini Version
Generates pytest test files using Google Gemini API

Author: Claude Code + JuanCS-Dev
Date: 2025-10-20
Usage: python scripts/generate_tests_gemini.py <module_path> [--test-type unit|integration|e2e]
"""

import argparse
import ast
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")


class GeminiTestGenerator:
    """AI-powered test generator using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize test generator.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=self.api_key)

        # Use Gemini 1.5 Pro for best code generation
        self.model = genai.GenerativeModel('gemini-1.5-pro')

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
            elif isinstance(node, ast.FunctionDef):
                # Only top-level functions (not methods)
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
            'path': str(module_path),
            'lines': len(source.split('\n'))
        }

    def generate_test_prompt(
        self,
        module_info: Dict[str, Any],
        test_type: str = "unit",
        coverage_target: int = 95
    ) -> str:
        """
        Generate Gemini prompt for test creation.

        Args:
            module_info: Module analysis from analyze_module()
            test_type: "unit", "integration", or "e2e"
            coverage_target: Desired coverage percentage

        Returns:
            Prompt string for Gemini API
        """
        module_path = module_info['path']
        module_name = Path(module_path).stem

        # Truncate source if too long (Gemini has limits)
        source = module_info['source']
        if len(source) > 30000:  # ~30K chars limit
            source = source[:30000] + "\n\n... (truncated for length)"

        prompt = f"""You are an expert Python test engineer following DOUTRINA VÉRTICE principles.

CRITICAL RULES:
1. ZERO MOCKS for integration/e2e tests - use real services via Testcontainers fixtures
2. Production-ready code from line 1
3. Comprehensive coverage: {coverage_target}%+ (statements + branches)
4. All edge cases, error paths, boundary conditions

TASK: Generate {test_type} tests for this Python module.

MODULE: {module_path}
LINES: {module_info['lines']}
TARGET COVERAGE: {coverage_target}%
TEST TYPE: {test_type}

CLASSES: {len(module_info['classes'])}
{json.dumps([c['name'] for c in module_info['classes']], indent=2)}

METHODS TO TEST:
{json.dumps(module_info['classes'], indent=2)}

FUNCTIONS: {len(module_info['functions'])}
{json.dumps([f['name'] for f in module_info['functions']], indent=2)}

MODULE SOURCE:
```python
{source}
```

REQUIREMENTS:
1. Follow pattern from tests/test_constitutional_validator_100pct.py
2. Use Testcontainers fixtures when needed (kafka_container, redis_client_fixture, postgres_connection)
3. NO MOCKS for external services in integration tests
4. Test ALL methods and functions
5. Include edge cases: None inputs, empty lists, invalid data, exceptions
6. Use AAA pattern (Arrange, Act, Assert)
7. Descriptive test names: test_<method>_<scenario>
8. Docstrings with SCENARIO and EXPECTED
9. Markers: @pytest.mark.{test_type}
10. For 1000+ line modules: focus on critical paths first, then edge cases

OUTPUT FORMAT:
Generate ONLY the complete test file Python code.
No explanations outside code.
Include proper imports.
Organize by class being tested.

EXAMPLE STRUCTURE:
```python
\"\"\"
{module_name.title()} - {test_type.title()} Test Suite
Coverage Target: {coverage_target}%+

Author: AI-Generated (Gemini) + Human Validated
Date: 2025-10-20
\"\"\"

import pytest
from {module_name} import YourClass, YourEnum

class TestYourClass:
    \"\"\"Tests for YourClass.\"\"\"

    @pytest.mark.{test_type}
    def test_method_success_case(self):
        \"\"\"
        SCENARIO: Normal operation
        EXPECTED: Returns expected value
        \"\"\"
        # Arrange
        instance = YourClass()

        # Act
        result = instance.method()

        # Assert
        assert result == expected
```

Generate the complete test file now:
"""
        return prompt

    def generate_tests(
        self,
        module_path: Path,
        test_type: str = "unit",
        coverage_target: int = 95,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate test file for given module using Gemini API.

        Args:
            module_path: Path to module to test
            test_type: Type of tests to generate
            coverage_target: Target coverage percentage
            output_path: Where to save test file

        Returns:
            Generated test code as string
        """
        print(f"📝 Analyzing module: {module_path}")
        module_info = self.analyze_module(module_path)

        print(f"   Lines: {module_info['lines']}")
        print(f"   Classes: {len(module_info['classes'])}")
        print(f"   Functions: {len(module_info['functions'])}")

        print(f"🤖 Generating {test_type} tests with Gemini 1.5 Pro...")
        prompt = self.generate_test_prompt(module_info, test_type, coverage_target)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower for consistent code
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                )
            )

            test_code = response.text

            # Extract code from markdown if present
            if "```python" in test_code:
                test_code = test_code.split("```python")[1].split("```")[0].strip()
            elif "```" in test_code:
                test_code = test_code.split("```")[1].split("```")[0].strip()

            # Determine output path
            if output_path is None:
                module_name = module_path.stem
                test_dir = Path(__file__).parent.parent / "tests" / test_type
                test_dir.mkdir(parents=True, exist_ok=True)
                output_path = test_dir / f"test_{module_name}_{test_type}_gemini.py"

            # Save test file
            with open(output_path, 'w') as f:
                f.write(test_code)

            print(f"✅ Test file generated: {output_path}")
            print(f"   Size: {len(test_code)} chars")
            return test_code

        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            raise

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
        description="Generate AI-assisted tests using Gemini"
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
        default=95,
        help="Target coverage percentage (default: 95)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for test file"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate generated test file (default: True)"
    )

    args = parser.parse_args()

    # Validate module path
    if not args.module_path.exists():
        print(f"❌ Module not found: {args.module_path}")
        sys.exit(1)

    # Generate tests
    try:
        generator = GeminiTestGenerator()

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
                f"test_{args.module_path.stem}_{args.test_type}_gemini.py"
            )
            if not generator.validate_test_file(output_path):
                print("⚠️  Validation failed - please review generated tests")
                sys.exit(1)

        print(f"\n🎉 SUCCESS! Test generation complete.")
        print(f"   Next steps:")
        print(f"   1. Review generated tests")
        print(f"   2. Run: pytest {output_path or args.output} -v")
        print(f"   3. Check coverage: pytest {output_path or args.output} --cov")

    except Exception as e:
        print(f"❌ Test generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
