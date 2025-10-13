"""
Oráculo Service - CVE Sentinel.

Responsible for:
- CVE ingestion from multiple feeds (NVD, GHSA, OSV)
- Multi-ecosystem dependency scanning (Python, JavaScript, Go, Docker)
- APV (Ameaça Potencial Verificada) generation with vulnerable code signatures
- Priority scoring and triage
- Dispatch to Eureka for confirmation

Components:
- feeds: CVE feed clients (NVD, GHSA, OSV) and orchestrator
- scanners: Dependency scanners (Python, JS, Go, Docker) and orchestrator
- apv_generator: Matches CVEs to dependencies, generates APVs
- triage_engine: Priority scoring and lifecycle management
"""

from .feeds import NVDClient, GHSAClient, OSVClient, FeedOrchestrator
from .scanners import (
    PythonScanner,
    JavaScriptScanner,
    GoScanner,
    DockerScanner,
    DependencyOrchestrator,
)
from .apv_generator import APVGenerator, VulnerableCodeSignature
from .triage_engine import TriageEngine

__all__ = [
    # Feed clients
    "NVDClient",
    "GHSAClient",
    "OSVClient",
    "FeedOrchestrator",
    # Dependency scanners
    "PythonScanner",
    "JavaScriptScanner",
    "GoScanner",
    "DockerScanner",
    "DependencyOrchestrator",
    # APV generation
    "APVGenerator",
    "VulnerableCodeSignature",
    # Triage
    "TriageEngine",
]
