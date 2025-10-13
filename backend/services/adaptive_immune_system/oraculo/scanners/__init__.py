"""
Dependency Scanners.

Multi-ecosystem dependency scanning for:
- Python (pip, poetry)
- JavaScript/Node.js (npm, yarn)
- Go (go modules)
- Docker images (trivy, runtime inspection)
"""

from .python_scanner import PythonScanner, PythonPackage
from .javascript_scanner import JavaScriptScanner, JavaScriptPackage
from .go_scanner import GoScanner, GoPackage
from .docker_scanner import DockerScanner, DockerPackage, DockerImageInfo
from .orchestrator import DependencyOrchestrator

__all__ = [
    "PythonScanner",
    "PythonPackage",
    "JavaScriptScanner",
    "JavaScriptPackage",
    "GoScanner",
    "GoPackage",
    "DockerScanner",
    "DockerPackage",
    "DockerImageInfo",
    "DependencyOrchestrator",
]
