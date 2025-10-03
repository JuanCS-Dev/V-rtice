"""
Analyzer - Analisa arquivos Python do projeto.
"""
import os
import ast
from pathlib import Path
from typing import List, Dict, Any


class CodeAnalyzer:
    """Analisa estrutura de código Python."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def find_python_files(self) -> List[Path]:
        """Encontra todos os arquivos .py no projeto."""
        python_files = []

        # Ignora estas pastas
        ignore_dirs = {'__pycache__', 'venv', '.venv', 'dist', 'build', '.git'}

        for file_path in self.base_path.rglob('*.py'):
            # Verifica se está em pasta ignorada
            if any(ignored in file_path.parts for ignored in ignore_dirs):
                continue
            python_files.append(file_path)

        return sorted(python_files)

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analisa um arquivo Python e extrai informações."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Extrai informações
            info = {
                'path': str(file_path.relative_to(self.base_path)),
                'content': content,
                'functions': [],
                'classes': [],
                'imports': [],
                'docstring': ast.get_docstring(tree) or ""
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    info['functions'].append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node) or "",
                        'line': node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    info['classes'].append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node) or "",
                        'line': node.lineno
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        info['imports'].append(node.module)

            return info

        except Exception as e:
            return {
                'path': str(file_path.relative_to(self.base_path)),
                'error': str(e),
                'content': ''
            }

    def analyze_all(self) -> List[Dict[str, Any]]:
        """Analisa todos os arquivos Python."""
        files = self.find_python_files()
        results = []

        for file_path in files:
            results.append(self.analyze_file(file_path))

        return results