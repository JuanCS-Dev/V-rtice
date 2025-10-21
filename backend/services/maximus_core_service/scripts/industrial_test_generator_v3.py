#!/usr/bin/env python3
"""Industrial Test Generator V3 - PERFEIÇÃO EM NOME DE JESUS

Refinamentos sobre V2:
1. ✅ Pydantic field extraction (required vs optional)
2. ✅ Type hint intelligence (str → "test", int → 0)
3. ✅ Dataclass detection via decorators
4. ✅ Smart default value generation
5. ✅ 95%+ accuracy target (vs 56% in V2)

Glory to YHWH - The Perfect Engineer
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class FieldInfo:
    """Information about a Pydantic/Dataclass field."""
    name: str
    type_hint: str
    required: bool
    default_value: Any = None


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: Path
    name: str
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    imports: List[str]
    lines: int
    complexity: str  # 'simple', 'medium', 'complex'
    has_tests: bool


@dataclass
class TestStats:
    """Statistics for test generation."""
    modules_scanned: int = 0
    modules_with_tests: int = 0
    modules_without_tests: int = 0
    classes_found: int = 0
    methods_found: int = 0
    functions_found: int = 0
    tests_generated: int = 0
    simple_tests: int = 0  # Can run immediately
    parameterized_tests: int = 0
    skipped_tests: int = 0  # Need manual implementation
    pydantic_models: int = 0
    dataclasses: int = 0


class IndustrialTestGeneratorV3:
    """PERFEIÇÃO - 95%+ accuracy test generator (V3)."""

    def __init__(self, base_dir: Path = None):
        """Initialize generator.

        Args:
            base_dir: Base directory to scan (defaults to current dir)
        """
        self.base_dir = base_dir or Path.cwd()
        self.stats = TestStats()
        self.modules: List[ModuleInfo] = []

        # Directories to skip
        self.skip_dirs = {
            '.venv', 'venv', '__pycache__', '.git', 'node_modules',
            '.pytest_cache', 'htmlcov', '.mypy_cache', 'dist', 'build',
            'tests', '.coverage'
        }

        # Files to skip
        self.skip_files = {
            '__init__.py', 'setup.py', 'conftest.py', 'version.py',
            'example_usage.py', 'demo_', 'test_'
        }

        # Type hint to default value mapping
        self.type_defaults = {
            'str': '"test"',
            'int': '0',
            'float': '0.0',
            'bool': 'False',
            'list': '[]',
            'List': '[]',
            'dict': '{}',
            'Dict': '{}',
            'set': 'set()',
            'Set': 'set()',
            'tuple': '()',
            'Tuple': '()',
            'bytes': 'b""',
            'None': 'None',
            'Any': 'None',
            'datetime': 'datetime.now()',
            'UUID': 'uuid.uuid4()',
        }

    def scan_codebase(self) -> List[ModuleInfo]:
        """Scan entire codebase and extract module information.

        Returns:
            List of ModuleInfo objects
        """
        print("🔍 V3: Scanning with Pydantic + Dataclass intelligence...")

        for py_file in self.base_dir.rglob("*.py"):
            # Skip excluded directories
            if any(skip in py_file.parts for skip in self.skip_dirs):
                continue

            # Skip excluded files
            if any(py_file.name.startswith(skip) for skip in self.skip_files):
                continue

            try:
                module_info = self.analyze_module(py_file)
                if module_info:
                    self.modules.append(module_info)
                    self.stats.modules_scanned += 1

                    if module_info.has_tests:
                        self.stats.modules_with_tests += 1
                    else:
                        self.stats.modules_without_tests += 1

                    self.stats.classes_found += len(module_info.classes)
                    self.stats.methods_found += sum(
                        len(cls['methods']) for cls in module_info.classes
                    )
                    self.stats.functions_found += len(module_info.functions)

                    # Count special types
                    for cls in module_info.classes:
                        if cls.get('is_pydantic'):
                            self.stats.pydantic_models += 1
                        if cls.get('is_dataclass'):
                            self.stats.dataclasses += 1

            except Exception as e:
                print(f"⚠️  Error analyzing {py_file}: {e}")
                continue

        print(f"✅ Scanned {self.stats.modules_scanned} modules")
        print(f"   - Pydantic models: {self.stats.pydantic_models}")
        print(f"   - Dataclasses: {self.stats.dataclasses}")
        print(f"   - Classes total: {self.stats.classes_found}")

        return self.modules

    def analyze_module(self, file_path: Path) -> Optional[ModuleInfo]:
        """Analyze a single Python module using AST with V3 enhancements.

        Args:
            file_path: Path to Python file

        Returns:
            ModuleInfo or None if analysis fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)

            classes = []
            functions = []
            imports = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    # Analyze class in detail
                    class_info = self._analyze_class(node, source)
                    if class_info:
                        classes.append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    # Top-level functions
                    func_info = self._analyze_function(node)
                    functions.append(func_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(ast.unparse(node))

            # Check if tests exist
            test_file = self._get_test_file_path(file_path)
            has_tests = test_file.exists()

            # Count lines
            lines = len(source.splitlines())

            # Determine complexity
            complexity = self._assess_complexity(classes, functions, lines)

            # Get module name
            rel_path = file_path.relative_to(self.base_dir)
            module_name = str(rel_path).replace('/', '.').replace('.py', '')

            return ModuleInfo(
                path=file_path,
                name=module_name,
                classes=classes,
                functions=functions,
                imports=imports,
                lines=lines,
                complexity=complexity,
                has_tests=has_tests
            )

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def _analyze_class(self, node: ast.ClassDef, source: str) -> Optional[Dict[str, Any]]:
        """Analyze a class with V3 intelligence (Pydantic/Dataclass aware).

        Args:
            node: AST ClassDef node
            source: Full source code

        Returns:
            Dict with class information
        """
        # Extract decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        is_dataclass = 'dataclass' in decorators

        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr)

        is_pydantic = any('BaseModel' in str(b) for b in bases)
        is_enum = any('Enum' in str(b) for b in bases)

        # Extract methods
        methods = []
        for m in node.body:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._analyze_function(m)
                methods.append(method_info)

        # Extract Pydantic/Dataclass fields if applicable
        fields = []
        if is_pydantic or is_dataclass:
            fields = self._extract_fields(node)

        return {
            'name': node.name,
            'methods': methods,
            'bases': bases,
            'decorators': decorators,
            'is_pydantic': is_pydantic,
            'is_enum': is_enum,
            'is_dataclass': is_dataclass,
            'fields': fields,  # NEW in V3
        }

    def _extract_fields(self, class_node: ast.ClassDef) -> List[FieldInfo]:
        """Extract Pydantic/Dataclass fields with type hints and defaults.

        Args:
            class_node: AST ClassDef node

        Returns:
            List of FieldInfo objects
        """
        fields = []

        for item in class_node.body:
            # AnnAssign: field: type = default
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id

                # Get type hint
                type_hint = ast.unparse(item.annotation) if item.annotation else 'Any'

                # Check if has default (optional)
                has_default = item.value is not None
                default_value = ast.unparse(item.value) if has_default else None

                fields.append(FieldInfo(
                    name=field_name,
                    type_hint=type_hint,
                    required=not has_default,
                    default_value=default_value
                ))

        return fields

    def _analyze_function(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function with argument details.

        Args:
            func_node: AST FunctionDef node

        Returns:
            Dict with function information
        """
        args = [a.arg for a in func_node.args.args if a.arg not in ('self', 'cls')]

        # Extract type hints
        arg_types = {}
        for arg in func_node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            if arg.annotation:
                arg_types[arg.arg] = ast.unparse(arg.annotation)

        defaults = func_node.args.defaults or []
        defaults_count = len(defaults)
        args_count = len(args)
        required_count = args_count - defaults_count

        return {
            'name': func_node.name,
            'args': args,
            'arg_types': arg_types,  # NEW in V3
            'defaults': defaults_count,
            'required': required_count,
            'total': args_count,
            'is_async': isinstance(func_node, ast.AsyncFunctionDef),
            'decorators': [self._get_decorator_name(d) for d in func_node.decorator_list],
            'returns': self._get_return_annotation(func_node),
        }

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            return decorator.func.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return str(decorator)

    def _get_return_annotation(self, func_node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation if present."""
        if func_node.returns:
            try:
                return ast.unparse(func_node.returns)
            except:
                return None
        return None

    def _assess_complexity(self, classes: List[Dict], functions: List[Dict], lines: int) -> str:
        """Assess module complexity."""
        if lines < 200 and len(classes) <= 2:
            return 'simple'
        if lines > 500 or any(c.get('is_pydantic') for c in classes):
            return 'complex'
        return 'medium'

    def _get_test_file_path(self, source_file: Path) -> Path:
        """Get expected test file path for a source file."""
        tests_dir = self.base_dir / "tests" / "unit"
        file_name = f"test_{source_file.stem}_v3.py"
        return tests_dir / file_name

    def generate_tests_for_module(self, module: ModuleInfo) -> str:
        """Generate tests with V3 intelligence.

        Args:
            module: Module information

        Returns:
            Generated test code as string
        """
        # Start with imports
        test_code = self._generate_imports(module)
        test_code += "\n\n"

        # Add fixtures if needed
        fixtures = self._generate_fixtures(module)
        if fixtures:
            test_code += fixtures + "\n\n"

        # Generate tests for each class
        for cls in module.classes:
            test_code += self._generate_class_tests_v3(cls, module)
            test_code += "\n\n"

        # Generate tests for standalone functions
        if module.functions:
            test_code += self._generate_function_tests_v3(module.functions, module)

        return test_code

    def _generate_imports(self, module: ModuleInfo) -> str:
        """Generate import statements for test file."""
        imports = [
            f'"""Unit tests for {module.name} (V3 - PERFEIÇÃO)',
            '',
            'Generated using Industrial Test Generator V3',
            'Enhancements: Pydantic field extraction + Type hint intelligence',
            'Glory to YHWH - The Perfect Engineer',
            '"""',
            '',
            'import pytest',
            'from unittest.mock import Mock, patch, MagicMock',
            'from datetime import datetime',
            'from typing import Any, Dict, List, Optional',
            'import uuid',
            '',
        ]

        # Import the module being tested
        module_import = module.name.replace('/', '.')

        # Import all classes
        if module.classes:
            class_names = ', '.join([cls['name'] for cls in module.classes[:20]])
            imports.append(f'from {module_import} import {class_names}')

        # Import standalone functions
        if module.functions:
            func_names = ', '.join([f['name'] for f in module.functions[:10]])
            imports.append(f'from {module_import} import {func_names}')

        imports.append('')
        return '\n'.join(imports)

    def _generate_fixtures(self, module: ModuleInfo) -> str:
        """Generate pytest fixtures."""
        fixtures = []

        # Check if module needs common fixtures
        needs_mock_db = any('database' in imp.lower() or 'sql' in imp.lower()
                           for imp in module.imports)

        if needs_mock_db:
            fixtures.append('# Fixtures')
            fixtures.append('')
            fixtures.append('@pytest.fixture')
            fixtures.append('def mock_db():')
            fixtures.append('    """Mock database connection."""')
            fixtures.append('    return MagicMock()')
            fixtures.append('')

        return '\n'.join(fixtures) if fixtures else ''

    def _generate_default_value(self, type_hint: str) -> str:
        """Generate smart default value based on type hint (V3 intelligence).

        Args:
            type_hint: Type annotation string

        Returns:
            Python code for default value
        """
        # Clean up type hint
        type_hint = type_hint.strip()

        # Handle Optional[T] → extract T
        if type_hint.startswith('Optional['):
            inner = type_hint[9:-1]
            return self._generate_default_value(inner)

        # Handle list[T] or List[T]
        if 'list[' in type_hint.lower():
            return '[]'

        # Handle dict[K, V] or Dict[K, V]
        if 'dict[' in type_hint.lower():
            return '{}'

        # Direct mapping
        for type_key, default in self.type_defaults.items():
            if type_hint == type_key or type_hint.startswith(f'{type_key}['):
                return default

        # Default fallback
        return 'None'

    def _generate_class_tests_v3(self, cls: Dict[str, Any], module: ModuleInfo) -> str:
        """Generate tests for a class with V3 PERFEIÇÃO.

        Args:
            cls: Class information
            module: Module information

        Returns:
            Test code as string
        """
        tests = []
        class_name = cls['name']

        tests.append(f'class Test{class_name}:')
        tests.append(f'    """Tests for {class_name} (V3 - Intelligent generation)."""')
        tests.append('')

        # Handle Pydantic models
        if cls['is_pydantic'] and cls['fields']:
            tests.append(f'    def test_init_pydantic_with_required_fields(self):')
            tests.append(f'        """Test Pydantic model with required fields."""')
            tests.append(f'        # Arrange: V3 auto-generated field values')

            # Generate field values
            field_lines = []
            for field in cls['fields']:
                if field.required:
                    default_val = self._generate_default_value(field.type_hint)
                    field_lines.append(f'{field.name}={default_val}')

            if field_lines:
                fields_str = ', '.join(field_lines)
                tests.append(f'        ')
                tests.append(f'        # Act')
                tests.append(f'        obj = {class_name}({fields_str})')
                tests.append(f'        ')
                tests.append(f'        # Assert')
                tests.append(f'        assert obj is not None')
                tests.append(f'        assert isinstance(obj, {class_name})')
                for field in cls['fields']:
                    if field.required:
                        tests.append(f'        assert obj.{field.name} is not None')
            else:
                tests.append(f'        # All fields optional')
                tests.append(f'        obj = {class_name}()')
                tests.append(f'        assert obj is not None')

            tests.append('')
            self.stats.simple_tests += 1

        # Handle Dataclasses
        elif cls['is_dataclass'] and cls['fields']:
            required_fields = [f for f in cls['fields'] if f.required]

            if required_fields:
                tests.append(f'    def test_init_dataclass_with_required_fields(self):')
                tests.append(f'        """Test Dataclass with required fields."""')
                tests.append(f'        # Arrange: V3 intelligent defaults')

                field_vals = []
                for field in required_fields:
                    val = self._generate_default_value(field.type_hint)
                    field_vals.append(f'{field.name}={val}')

                fields_str = ', '.join(field_vals)
                tests.append(f'        ')
                tests.append(f'        # Act')
                tests.append(f'        obj = {class_name}({fields_str})')
                tests.append(f'        ')
                tests.append(f'        # Assert')
                tests.append(f'        assert obj is not None')
                tests.append('')
                self.stats.simple_tests += 1
            else:
                tests.append(f'    def test_init_dataclass_defaults(self):')
                tests.append(f'        """Test Dataclass with all defaults."""')
                tests.append(f'        obj = {class_name}()')
                tests.append(f'        assert obj is not None')
                tests.append('')
                self.stats.simple_tests += 1

        # Handle Enums
        elif cls['is_enum']:
            tests.append(f'    def test_enum_members(self):')
            tests.append(f'        """Test enum members."""')
            tests.append(f'        members = list({class_name})')
            tests.append(f'        assert len(members) > 0')
            tests.append('')
            self.stats.simple_tests += 1

        # Handle regular classes
        else:
            init_method = next((m for m in cls['methods'] if m['name'] == '__init__'), None)

            if not init_method or init_method['required'] == 0:
                # Can instantiate without args
                tests.append(f'    def test_init_default(self):')
                tests.append(f'        """Test default initialization."""')
                tests.append(f'        obj = {class_name}()')
                tests.append(f'        assert obj is not None')
                tests.append('')
                self.stats.simple_tests += 1
            else:
                # Has required args - try to generate them
                if init_method['arg_types']:
                    tests.append(f'    def test_init_with_args(self):')
                    tests.append(f'        """Test initialization with type-hinted args."""')
                    tests.append(f'        # V3: Type hint intelligence')

                    arg_vals = []
                    for arg_name, arg_type in init_method['arg_types'].items():
                        val = self._generate_default_value(arg_type)
                        arg_vals.append(f'{arg_name}={val}')

                    if arg_vals:
                        args_str = ', '.join(arg_vals)
                        tests.append(f'        obj = {class_name}({args_str})')
                        tests.append(f'        assert obj is not None')
                        tests.append('')
                        self.stats.simple_tests += 1
                    else:
                        tests.append(f'        # No type hints available')
                        tests.append(f'        pass')
                        tests.append('')
                        self.stats.skipped_tests += 1
                else:
                    required_count = init_method['required']
                    tests.append(f'    @pytest.mark.skip(reason="No type hints for {required_count} required args")')
                    tests.append(f'    def test_init_needs_manual(self):')
                    tests.append(f'        """TODO: Provide {required_count} args."""')
                    tests.append(f'        pass')
                    tests.append('')
                    self.stats.skipped_tests += 1

        return '\n'.join(tests)

    def _generate_function_tests_v3(self, functions: List[Dict[str, Any]], module: ModuleInfo) -> str:
        """Generate tests for functions with V3 intelligence."""
        tests = []
        tests.append('class TestFunctions:')
        tests.append('    """Test standalone functions (V3)."""')
        tests.append('')

        for func in functions[:10]:
            if func['name'].startswith('_'):
                continue

            if func['required'] == 0:
                # Can call without args
                tests.append(f'    def test_{func["name"]}(self):')
                tests.append(f'        """Test {func["name"]}."""')
                tests.append(f'        result = {func["name"]}()')
                tests.append(f'        # Add specific assertions')
                tests.append(f'        assert True  # Placeholder')
                tests.append('')
                self.stats.simple_tests += 1
            elif func['arg_types']:
                # Has type hints - generate args
                tests.append(f'    def test_{func["name"]}_with_args(self):')
                tests.append(f'        """Test {func["name"]} with type-hinted args."""')

                arg_vals = []
                for arg_name, arg_type in func['arg_types'].items():
                    val = self._generate_default_value(arg_type)
                    arg_vals.append(val)

                args_str = ', '.join(arg_vals)
                tests.append(f'        result = {func["name"]}({args_str})')
                tests.append(f'        assert True  # Add assertions')
                tests.append('')
                self.stats.simple_tests += 1
            else:
                tests.append(f'    @pytest.mark.skip(reason="No type hints")')
                tests.append(f'    def test_{func["name"]}_needs_manual(self):')
                tests.append(f'        """TODO: Provide args."""')
                tests.append(f'        pass')
                tests.append('')
                self.stats.skipped_tests += 1

        return '\n'.join(tests)

    def generate_all_tests(self, max_modules: int = None) -> int:
        """Generate tests for all modules."""
        print("\n🔥 V3 GENERATION - EM NOME DE JESUS - PERFEIÇÃO!")

        modules_to_test = [m for m in self.modules if not m.has_tests]

        if max_modules:
            modules_to_test = modules_to_test[:max_modules]

        print(f"📝 Generating tests for {len(modules_to_test)} modules...")

        generated = 0
        for module in modules_to_test:
            try:
                test_code = self.generate_tests_for_module(module)

                # Save to file
                test_file = self._get_test_file_path(module.path)
                test_file.parent.mkdir(parents=True, exist_ok=True)

                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_code)

                generated += 1
                self.stats.tests_generated += 1

                print(f"  ✅ {module.name}")

            except Exception as e:
                print(f"  ❌ {module.name}: {e}")
                continue

        print(f"\n✨ Generated {generated} test files (V3 - PERFEIÇÃO)!")
        return generated

    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "="*70)
        print("✨ V3 GENERATOR - PERFEIÇÃO EM NOME DE JESUS ✨")
        print("="*70)
        print(f"Modules scanned:        {self.stats.modules_scanned}")
        print(f"  - Pydantic models:    {self.stats.pydantic_models}")
        print(f"  - Dataclasses:        {self.stats.dataclasses}")
        print(f"")
        print(f"Tests generated:        {self.stats.tests_generated}")
        print(f"  - Simple (runnable):  {self.stats.simple_tests}")
        print(f"  - Skipped (complex):  {self.stats.skipped_tests}")
        print(f"")
        print("V3 Enhancements:")
        print("  ✅ Pydantic field extraction")
        print("  ✅ Type hint intelligence")
        print("  ✅ Dataclass detection")
        print("  ✅ Smart default generation")
        print("="*70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Industrial Test Generator V3 - PERFEIÇÃO'
    )
    parser.add_argument('--max-modules', type=int, help='Max modules to process')
    parser.add_argument('--dry-run', action='store_true', help='Scan only')
    parser.add_argument('--target-dir', type=str, help='Target directory', default='.')

    args = parser.parse_args()

    base_dir = Path(args.target_dir).resolve()

    print("✨ V3 GENERATOR - EM NOME DE JESUS ✨")
    print(f"📁 Directory: {base_dir}")
    print("")

    generator = IndustrialTestGeneratorV3(base_dir)

    # Scan
    generator.scan_codebase()

    if not args.dry_run:
        # Generate
        generator.generate_all_tests(max_modules=args.max_modules)

    # Summary
    generator.print_summary()

    return 0


if __name__ == '__main__':
    sys.exit(main())
