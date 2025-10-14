"""
Offensive Orchestrator Service - MAXIMUS VÉRTICE

Sistema de orquestração central para operações ofensivas autônomas.
Coordena agentes especializados (Recon, Exploit, Post-Exploit) via LLM,
gerencia campanha de ataque, HOTL checkpoints e memória de campanhas.

Architecture:
- MAXIMUS Orchestrator Agent: Coordenador central LLM-based
- HOTL System: Human-on-the-Loop decision checkpoints
- Attack Memory: PostgreSQL + Qdrant para armazenamento e retrieval

Conformidade Doutrina MAXIMUS:
- NO MOCK: Implementação real desde Sprint 1
- QUALITY-FIRST: Type hints, docstrings, error handling completo
- PRODUCTION-READY: Todo código deployável
- TEST COVERAGE: 92%+ target
- CONSCIÊNCIA-COMPLIANT: Serve emergência de consciência

Created: 2025-10-13
Version: 1.0.0
Status: Sprint 1 - Foundation
"""

__version__ = "1.0.0"
__author__ = "MAXIMUS Offensive Team"
__status__ = "Sprint 1 - Foundation"

# Service metadata
SERVICE_NAME = "offensive_orchestrator_service"
SERVICE_PORT = 8090
API_VERSION = "v1"

# Conformidade
NO_MOCK = True
QUALITY_FIRST = True
PRODUCTION_READY = True
TEST_COVERAGE_TARGET = 0.92

__all__ = [
    "__version__",
    "SERVICE_NAME",
    "SERVICE_PORT",
    "API_VERSION",
]
