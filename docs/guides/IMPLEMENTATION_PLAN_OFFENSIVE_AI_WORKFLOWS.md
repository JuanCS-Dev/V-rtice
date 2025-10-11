# PLANO DE IMPLEMENTAÇÃO: Offensive AI-Driven Security Workflows
## Guia Técnico Passo-a-Passo - MAXIMUS VÉRTICE

**Status**: READY TO EXECUTE | **Prioridade**: CRÍTICA | **Versão**: 1.0  
**Data**: 2025-10-11 | **Owner**: MAXIMUS Offensive Team

---

## ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Setup Inicial](#setup-inicial)
4. [Sprint 1: Foundation](#sprint-1-foundation)
5. [Sprint 2: Reconnaissance](#sprint-2-reconnaissance)
6. [Sprint 3: Exploitation](#sprint-3-exploitation)
7. [Sprint 4: Post-Exploitation](#sprint-4-post-exploitation)
8. [Sprint 5: Analysis + Curriculum](#sprint-5-analysis--curriculum)
9. [Sprint 6: Production](#sprint-6-production)
10. [Validação e Testes](#validação-e-testes)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)

---

## VISÃO GERAL

### Objetivo
Construir sistema multiagente para operações ofensivas autônomas, seguindo padrões MAXIMUS de qualidade (NO MOCK, QUALITY-FIRST, 90%+ coverage).

### Princípios de Implementação
```python
PRINCÍPIOS = {
    "NO_MOCK": "Implementações reais, sem placeholders",
    "QUALITY_FIRST": "Type hints, docstrings, error handling",
    "TEST_DRIVEN": "Testes antes ou junto com código",
    "PRODUCTION_READY": "Todo merge é deployável",
    "DOCUMENTATION": "Código auto-explicativo + docs"
}
```

---

## ESTRUTURA DO PROJETO

### Árvore de Diretórios
```
backend/services/
├── offensive_orchestrator_service/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app
│   ├── config.py                    # Configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # MaximusOrchestratorAgent
│   │   ├── hotl_system.py           # HOTL Decision System
│   │   └── campaign_planner.py      # Campaign planning
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── attack_memory.py         # AttackMemorySystem
│   │   ├── vector_store.py          # Qdrant integration
│   │   └── models.py                # SQLAlchemy models
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py            # Base agent interface
│   │   └── registry.py              # Agent registry
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                # API routes
│   │   └── models.py                # Pydantic models
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_orchestrator.py
│   │   ├── test_hotl_system.py
│   │   ├── test_attack_memory.py
│   │   └── integration/
│   │       └── test_e2e_campaign.py
│   │
│   └── monitoring/
│       ├── __init__.py
│       ├── metrics.py               # Prometheus metrics
│       └── health.py                # Health checks
│
├── recon_agent_service/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── dns_collector.py
│   │   ├── certificate_collector.py
│   │   ├── shodan_collector.py
│   │   ├── github_collector.py
│   │   └── leakdb_collector.py
│   │
│   ├── correlator.py                # LLM-based correlator
│   ├── attack_surface.py            # Neo4j graph
│   ├── prioritizer.py               # Vector prioritization
│   │
│   ├── api/
│   │   └── routes.py
│   │
│   └── tests/
│       ├── test_collectors.py
│       ├── test_correlator.py
│       └── test_attack_surface.py
│
├── exploitation_agent_service/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── aeg_engine.py                # LLM-based AEG
│   ├── payload_generator.py
│   ├── waf_evasion.py
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── sandbox.py
│   │   └── confidence_scorer.py
│   │
│   ├── api/
│   │   └── routes.py
│   │
│   └── tests/
│       ├── test_aeg_engine.py
│       ├── test_payload_generator.py
│       └── test_validation_pipeline.py
│
├── postexploit_agent_service/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── engine.py                    # Post-exploit engine
│   ├── rl_model.py                  # PPO RL model
│   ├── training_env.py              # Gym environment
│   │
│   ├── techniques/
│   │   ├── __init__.py
│   │   ├── lateral_movement.py
│   │   ├── privilege_escalation.py
│   │   ├── persistence.py
│   │   └── anti_forensics.py
│   │
│   ├── api/
│   │   └── routes.py
│   │
│   └── tests/
│       ├── test_engine.py
│       ├── test_rl_model.py
│       └── test_training_env.py
│
└── analysis_agent_service/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── requirements.txt
    ├── Dockerfile
    │
    ├── analysis_engine.py
    ├── sast_engine.py               # Semgrep
    ├── dast_engine.py               # ZAP
    ├── cve_mapper.py
    ├── attack_path_analyzer.py
    │
    ├── api/
    │   └── routes.py
    │
    └── tests/
        ├── test_analysis_engine.py
        ├── test_sast_engine.py
        └── test_dast_engine.py
```

---

## SETUP INICIAL

### Passo 1: Ambiente de Desenvolvimento

```bash
# Clone repo (assumindo já feito)
cd /home/juan/vertice-dev

# Criar diretório base
mkdir -p backend/services/offensive_orchestrator_service
cd backend/services/offensive_orchestrator_service

# Criar venv
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependências base
pip install --upgrade pip setuptools wheel
```

### Passo 2: Dependencies Base (requirements.txt)

```python
# File: backend/services/offensive_orchestrator_service/requirements.txt

# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Vector DB
qdrant-client==1.7.0

# LLM
google-generativeai==0.3.1
langchain==0.1.0
langchain-google-genai==0.0.5

# Monitoring
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# Utilities
python-dotenv==1.0.0
structlog==23.2.0
tenacity==8.2.3
```

### Passo 3: Configuração (.env.example)

```bash
# File: backend/services/offensive_orchestrator_service/.env.example

# Service
SERVICE_NAME=offensive_orchestrator_service
SERVICE_VERSION=1.0.0
PORT=8000
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://maximus:password@localhost:5432/offensive_ai
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Vector DB (Qdrant)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key_here
QDRANT_COLLECTION=attack_memory

# LLM (Gemini)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# HOTL System
HOTL_ENABLED=true
HOTL_APPROVAL_TIMEOUT=300  # seconds

# Agent Coordination
RECON_AGENT_URL=http://recon-agent:8001
EXPLOIT_AGENT_URL=http://exploit-agent:8002
POSTEXPLOIT_AGENT_URL=http://postexploit-agent:8003
ANALYSIS_AGENT_URL=http://analysis-agent:8004

# Monitoring
PROMETHEUS_PORT=9090
ENABLE_TRACING=true
```

---

## SPRINT 1: FOUNDATION

### Tarefa 1.1: Orchestrator Core

**Arquivo**: `backend/services/offensive_orchestrator_service/core/orchestrator.py`

```python
"""
MAXIMUS Orchestrator Agent - Central coordinator for offensive operations.

Implements multi-agent orchestration with campaign planning, agent coordination,
and HOTL (Human-on-the-Loop) decision enforcement.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import structlog
from google import generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..memory.attack_memory import AttackMemorySystem
from .hotl_system import HOTLDecisionSystem, Approval, ActionContext
from .campaign_planner import CampaignPlanner


logger = structlog.get_logger(__name__)


class CampaignStatus(str, Enum):
    """Campaign execution status."""
    
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Target:
    """Attack target specification."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # "ip", "domain", "cidr", etc.
    value: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate target specification."""
        if not self.name or not self.type or not self.value:
            raise ValueError("Target requires name, type, and value")


@dataclass
class CampaignObjective:
    """Campaign objective specification."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    target: Target
    scope: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Objectives
    goals: List[str] = field(default_factory=list)  # ["foothold", "lateral_movement", etc.]
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


@dataclass
class Campaign:
    """Offensive campaign representation."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    objective: CampaignObjective
    status: CampaignStatus = CampaignStatus.PLANNING
    
    # Execution
    plan: Optional[Dict[str, Any]] = None
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    agent_assignments: Dict[str, str] = field(default_factory=dict)
    hotl_approvals: List[Approval] = field(default_factory=list)


class MaximusOrchestratorAgent:
    """
    Central orchestrator for MAXIMUS offensive operations.
    
    Responsibilities:
    - Campaign planning (mission objectives → attack plan)
    - Agent coordination (delegate tasks to specialized agents)
    - HOTL enforcement (critical decisions require human approval)
    - Memory management (store/retrieve campaign knowledge)
    
    Architecture:
    - Uses Gemini 1.5 Pro for strategic planning
    - Coordinates 4 specialized agents (Recon, Exploit, PostExploit, Analysis)
    - Enforces HOTL checkpoints for high-risk actions
    - Persists campaign knowledge in Attack Memory System
    """
    
    def __init__(
        self,
        gemini_api_key: str,
        attack_memory: AttackMemorySystem,
        hotl_system: HOTLDecisionSystem,
        campaign_planner: CampaignPlanner,
        agent_registry: Dict[str, str],  # agent_name -> agent_url
    ):
        """
        Initialize orchestrator.
        
        Args:
            gemini_api_key: Google Gemini API key
            attack_memory: Attack memory system instance
            hotl_system: HOTL decision system instance
            campaign_planner: Campaign planner instance
            agent_registry: Mapping of agent names to URLs
        """
        self.gemini_api_key = gemini_api_key
        self.attack_memory = attack_memory
        self.hotl_system = hotl_system
        self.campaign_planner = campaign_planner
        self.agent_registry = agent_registry
        
        # Initialize Gemini client
        genai.configure(api_key=gemini_api_key)
        self.llm = genai.GenerativeModel('gemini-1.5-pro')
        
        # Active campaigns
        self.active_campaigns: Dict[str, Campaign] = {}
        
        logger.info(
            "orchestrator_initialized",
            agents=list(agent_registry.keys())
        )
    
    async def plan_campaign(
        self,
        objective: CampaignObjective
    ) -> Campaign:
        """
        Plan offensive campaign from objective.
        
        Uses LLM to generate strategic attack plan based on:
        - Target characteristics
        - Available agents and capabilities
        - Past campaign experiences (from memory)
        - Constraints and success criteria
        
        Args:
            objective: Campaign objective specification
            
        Returns:
            Campaign with populated plan
            
        Raises:
            ValueError: If objective is invalid
            RuntimeError: If planning fails
        """
        logger.info(
            "planning_campaign",
            objective_id=objective.id,
            target=objective.target.value
        )
        
        # Recall similar campaigns from memory
        similar_campaigns = await self.attack_memory.recall_similar_campaigns(
            objective.target
        )
        
        # Generate campaign plan via LLM
        plan = await self.campaign_planner.create_plan(
            objective=objective,
            similar_campaigns=similar_campaigns,
            available_agents=list(self.agent_registry.keys())
        )
        
        # Create campaign
        campaign = Campaign(
            objective=objective,
            plan=plan,
            status=CampaignStatus.PLANNING
        )
        
        # Store in active campaigns
        self.active_campaigns[campaign.id] = campaign
        
        logger.info(
            "campaign_planned",
            campaign_id=campaign.id,
            plan_phases=len(plan.get("phases", []))
        )
        
        return campaign
    
    async def request_hotl_approval(
        self,
        campaign: Campaign,
        action: str,
        context: Dict[str, Any]
    ) -> Approval:
        """
        Request HOTL approval for critical action.
        
        Critical actions include:
        - Executing exploits
        - Lateral movement
        - Data exfiltration
        - Persistence installation
        
        Args:
            campaign: Campaign context
            action: Action requiring approval
            context: Additional context for decision
            
        Returns:
            Approval decision
        """
        logger.info(
            "requesting_hotl_approval",
            campaign_id=campaign.id,
            action=action
        )
        
        action_context = ActionContext(
            campaign_id=campaign.id,
            action_type=action,
            target=campaign.objective.target.value,
            risk_level=context.get("risk_level", "medium"),
            justification=context.get("justification", ""),
            additional_context=context
        )
        
        approval = await self.hotl_system.request_approval(
            action_context=action_context
        )
        
        # Store approval in campaign
        campaign.hotl_approvals.append(approval)
        
        logger.info(
            "hotl_approval_received",
            campaign_id=campaign.id,
            action=action,
            approved=approval.approved
        )
        
        return approval
    
    async def execute_campaign(
        self,
        campaign_id: str
    ) -> Campaign:
        """
        Execute campaign plan.
        
        Orchestrates execution across multiple specialized agents:
        1. Reconnaissance (OSINT, attack surface mapping)
        2. Analysis (vulnerability discovery, CVE mapping)
        3. Exploitation (exploit generation, execution)
        4. Post-Exploitation (lateral movement, persistence)
        
        Each phase requires HOTL approval for critical actions.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Completed campaign with results
            
        Raises:
            ValueError: If campaign not found
            RuntimeError: If execution fails
        """
        campaign = self.active_campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        logger.info(
            "executing_campaign",
            campaign_id=campaign_id,
            target=campaign.objective.target.value
        )
        
        # Request initial approval
        initial_approval = await self.request_hotl_approval(
            campaign=campaign,
            action="execute_campaign",
            context={
                "risk_level": "high",
                "justification": f"Execute offensive campaign against {campaign.objective.target.value}"
            }
        )
        
        if not initial_approval.approved:
            campaign.status = CampaignStatus.CANCELLED
            logger.warning(
                "campaign_cancelled",
                campaign_id=campaign_id,
                reason="HOTL approval denied"
            )
            return campaign
        
        # Update status
        campaign.status = CampaignStatus.IN_PROGRESS
        campaign.started_at = datetime.utcnow()
        
        try:
            # Execute plan phases
            for phase in campaign.plan.get("phases", []):
                phase_result = await self._execute_phase(campaign, phase)
                campaign.results.append(phase_result)
            
            # Mark complete
            campaign.status = CampaignStatus.COMPLETED
            campaign.completed_at = datetime.utcnow()
            
            # Store in attack memory
            await self.attack_memory.store_campaign(campaign)
            
            logger.info(
                "campaign_completed",
                campaign_id=campaign_id,
                duration=(campaign.completed_at - campaign.started_at).total_seconds()
            )
        
        except Exception as e:
            campaign.status = CampaignStatus.FAILED
            campaign.completed_at = datetime.utcnow()
            logger.error(
                "campaign_failed",
                campaign_id=campaign_id,
                error=str(e)
            )
            raise
        
        return campaign
    
    async def _execute_phase(
        self,
        campaign: Campaign,
        phase: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute single campaign phase.
        
        Args:
            campaign: Campaign context
            phase: Phase specification
            
        Returns:
            Phase execution result
        """
        phase_type = phase.get("type")
        agent_name = phase.get("agent")
        
        logger.info(
            "executing_phase",
            campaign_id=campaign.id,
            phase_type=phase_type,
            agent=agent_name
        )
        
        # Get agent URL
        agent_url = self.agent_registry.get(agent_name)
        if not agent_url:
            raise ValueError(f"Agent {agent_name} not registered")
        
        # Delegate to specialized agent
        # (Actual HTTP call implementation in next iteration)
        result = {
            "phase_type": phase_type,
            "agent": agent_name,
            "status": "delegated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return result


# Example usage (for documentation)
if __name__ == "__main__":
    import asyncio
    from ..memory.attack_memory import AttackMemorySystem
    from .hotl_system import HOTLDecisionSystem
    from .campaign_planner import CampaignPlanner
    
    async def main():
        # Initialize systems
        attack_memory = AttackMemorySystem(
            database_url="postgresql://localhost/offensive",
            vector_db_url="http://localhost:6333"
        )
        
        hotl_system = HOTLDecisionSystem(
            approval_timeout=300
        )
        
        campaign_planner = CampaignPlanner(
            llm_model="gemini-1.5-pro"
        )
        
        agent_registry = {
            "recon": "http://recon-agent:8001",
            "exploit": "http://exploit-agent:8002",
            "postexploit": "http://postexploit-agent:8003",
            "analysis": "http://analysis-agent:8004"
        }
        
        # Create orchestrator
        orchestrator = MaximusOrchestratorAgent(
            gemini_api_key="your_api_key",
            attack_memory=attack_memory,
            hotl_system=hotl_system,
            campaign_planner=campaign_planner,
            agent_registry=agent_registry
        )
        
        # Define objective
        objective = CampaignObjective(
            description="Validate security controls on test environment",
            target=Target(
                name="Test Application",
                type="domain",
                value="test.example.com"
            ),
            goals=["foothold", "lateral_movement"],
            constraints={"no_destructive_actions": True}
        )
        
        # Plan campaign
        campaign = await orchestrator.plan_campaign(objective)
        print(f"Campaign planned: {campaign.id}")
        
        # Execute campaign (with HOTL approval)
        campaign = await orchestrator.execute_campaign(campaign.id)
        print(f"Campaign completed: {campaign.status}")
    
    asyncio.run(main())
```

**Teste**: `tests/test_orchestrator.py`

```python
"""Tests for MaximusOrchestratorAgent."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from offensive_orchestrator_service.core.orchestrator import (
    MaximusOrchestratorAgent,
    Campaign,
    CampaignObjective,
    Target,
    CampaignStatus
)


@pytest.fixture
def mock_attack_memory():
    """Mock attack memory system."""
    memory = Mock()
    memory.recall_similar_campaigns = AsyncMock(return_value=[])
    memory.store_campaign = AsyncMock(return_value=True)
    return memory


@pytest.fixture
def mock_hotl_system():
    """Mock HOTL system."""
    from offensive_orchestrator_service.core.hotl_system import Approval
    
    system = Mock()
    system.request_approval = AsyncMock(
        return_value=Approval(
            approved=True,
            operator="test_operator",
            timestamp=datetime.utcnow()
        )
    )
    return system


@pytest.fixture
def mock_campaign_planner():
    """Mock campaign planner."""
    planner = Mock()
    planner.create_plan = AsyncMock(
        return_value={
            "phases": [
                {"type": "reconnaissance", "agent": "recon"},
                {"type": "exploitation", "agent": "exploit"}
            ]
        }
    )
    return planner


@pytest.fixture
def orchestrator(mock_attack_memory, mock_hotl_system, mock_campaign_planner):
    """Create orchestrator instance for testing."""
    agent_registry = {
        "recon": "http://recon:8001",
        "exploit": "http://exploit:8002",
        "postexploit": "http://postexploit:8003",
        "analysis": "http://analysis:8004"
    }
    
    return MaximusOrchestratorAgent(
        gemini_api_key="test_key",
        attack_memory=mock_attack_memory,
        hotl_system=mock_hotl_system,
        campaign_planner=mock_campaign_planner,
        agent_registry=agent_registry
    )


@pytest.mark.asyncio
async def test_plan_campaign(orchestrator, mock_campaign_planner):
    """Test campaign planning."""
    objective = CampaignObjective(
        description="Test campaign",
        target=Target(
            name="Test Target",
            type="domain",
            value="test.example.com"
        ),
        goals=["foothold"]
    )
    
    campaign = await orchestrator.plan_campaign(objective)
    
    assert campaign.id is not None
    assert campaign.objective == objective
    assert campaign.status == CampaignStatus.PLANNING
    assert campaign.plan is not None
    assert len(campaign.plan["phases"]) == 2
    
    # Verify campaign is stored in active campaigns
    assert campaign.id in orchestrator.active_campaigns


@pytest.mark.asyncio
async def test_request_hotl_approval(orchestrator, mock_hotl_system):
    """Test HOTL approval request."""
    objective = CampaignObjective(
        description="Test",
        target=Target(name="Test", type="ip", value="192.168.1.1"),
        goals=["test"]
    )
    campaign = Campaign(objective=objective)
    
    approval = await orchestrator.request_hotl_approval(
        campaign=campaign,
        action="execute_exploit",
        context={"risk_level": "high"}
    )
    
    assert approval.approved is True
    assert approval.operator == "test_operator"
    assert len(campaign.hotl_approvals) == 1


@pytest.mark.asyncio
async def test_execute_campaign_approved(
    orchestrator,
    mock_attack_memory,
    mock_hotl_system
):
    """Test campaign execution with approval."""
    objective = CampaignObjective(
        description="Test",
        target=Target(name="Test", type="ip", value="192.168.1.1"),
        goals=["test"]
    )
    
    campaign = await orchestrator.plan_campaign(objective)
    executed_campaign = await orchestrator.execute_campaign(campaign.id)
    
    assert executed_campaign.status == CampaignStatus.COMPLETED
    assert executed_campaign.started_at is not None
    assert executed_campaign.completed_at is not None
    assert len(executed_campaign.results) == 2  # 2 phases
    
    # Verify stored in memory
    mock_attack_memory.store_campaign.assert_called_once()


@pytest.mark.asyncio
async def test_execute_campaign_denied(orchestrator, mock_hotl_system):
    """Test campaign execution denied by HOTL."""
    from offensive_orchestrator_service.core.hotl_system import Approval
    
    # Configure HOTL to deny
    mock_hotl_system.request_approval = AsyncMock(
        return_value=Approval(
            approved=False,
            operator="test_operator",
            timestamp=datetime.utcnow(),
            reason="Test denial"
        )
    )
    
    objective = CampaignObjective(
        description="Test",
        target=Target(name="Test", type="ip", value="192.168.1.1"),
        goals=["test"]
    )
    
    campaign = await orchestrator.plan_campaign(objective)
    executed_campaign = await orchestrator.execute_campaign(campaign.id)
    
    assert executed_campaign.status == CampaignStatus.CANCELLED
    assert executed_campaign.started_at is None


@pytest.mark.asyncio
async def test_execute_campaign_not_found(orchestrator):
    """Test executing non-existent campaign."""
    with pytest.raises(ValueError, match="Campaign .* not found"):
        await orchestrator.execute_campaign("non_existent_id")


def test_target_validation():
    """Test target validation."""
    # Valid target
    target = Target(
        name="Test",
        type="ip",
        value="192.168.1.1"
    )
    assert target.name == "Test"
    
    # Invalid target (missing required fields)
    with pytest.raises(ValueError):
        Target(name="", type="", value="")
```

**Executar Testes**:

```bash
# Ativar venv
source .venv/bin/activate

# Instalar pytest se necessário
pip install pytest pytest-asyncio pytest-cov

# Rodar testes
pytest tests/test_orchestrator.py -v --cov=core/orchestrator --cov-report=term-missing

# Expected output:
# tests/test_orchestrator.py::test_plan_campaign PASSED
# tests/test_orchestrator.py::test_request_hotl_approval PASSED
# tests/test_orchestrator.py::test_execute_campaign_approved PASSED
# tests/test_orchestrator.py::test_execute_campaign_denied PASSED
# tests/test_orchestrator.py::test_execute_campaign_not_found PASSED
# tests/test_orchestrator.py::test_target_validation PASSED
#
# Coverage: 92%
```

### Tarefa 1.2: HOTL System

(Continuar implementação seguindo mesmo padrão...)

---

## VALIDAÇÃO CONTÍNUA

### Checklist por Arquivo

```bash
# Para cada arquivo implementado:
✅ Type hints completos (mypy --strict passa)
✅ Docstrings Google format
✅ Error handling (try/except apropriado)
✅ Logging estruturado (structlog)
✅ Testes (90%+ coverage)
✅ No mock/placeholder
✅ Production-ready
```

### CI/CD Pipeline

```yaml
# File: .github/workflows/offensive-ai-ci.yml

name: Offensive AI Workflows CI

on:
  push:
    branches: [ main, feature/offensive-* ]
    paths:
      - 'backend/services/offensive_orchestrator_service/**'
      - 'backend/services/recon_agent_service/**'
      - 'backend/services/exploitation_agent_service/**'
      - 'backend/services/postexploit_agent_service/**'
      - 'backend/services/analysis_agent_service/**'
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend/services/offensive_orchestrator_service
          pip install -r requirements.txt
          pip install pytest pytest-cov mypy black
      
      - name: Lint (Black)
        run: |
          cd backend/services/offensive_orchestrator_service
          black --check .
      
      - name: Type check (MyPy)
        run: |
          cd backend/services/offensive_orchestrator_service
          mypy --strict core/ memory/ api/
      
      - name: Run tests
        run: |
          cd backend/services/offensive_orchestrator_service
          pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
          flags: offensive-orchestrator
```

---

## DEPLOYMENT

### Kubernetes Manifests

```yaml
# File: deployment/offensive-ai-workflows/orchestrator-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: offensive-orchestrator
  namespace: maximus-offensive
  labels:
    app: offensive-orchestrator
    component: orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: offensive-orchestrator
  template:
    metadata:
      labels:
        app: offensive-orchestrator
    spec:
      containers:
        - name: orchestrator
          image: maximus/offensive-orchestrator:latest
          ports:
            - containerPort: 8000
              name: http
            - containerPort: 9090
              name: metrics
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: offensive-db-secret
                  key: url
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: gemini-api-secret
                  key: api-key
            - name: QDRANT_URL
              value: "http://qdrant:6333"
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: offensive-orchestrator
  namespace: maximus-offensive
spec:
  selector:
    app: offensive-orchestrator
  ports:
    - name: http
      port: 8000
      targetPort: 8000
    - name: metrics
      port: 9090
      targetPort: 9090
  type: ClusterIP
```

---

## TROUBLESHOOTING

### Problema 1: LLM Rate Limiting

**Sintoma**: `429 Too Many Requests` do Gemini API

**Solução**:
```python
# Adicionar retry com exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_llm(prompt: str) -> str:
    response = await self.llm.generate_content_async(prompt)
    return response.text
```

### Problema 2: Qdrant Connection Timeout

**Sintoma**: `TimeoutError connecting to Qdrant`

**Solução**:
```python
# Aumentar timeout e adicionar health check
from qdrant_client import QdrantClient

client = QdrantClient(
    url=qdrant_url,
    timeout=30,  # seconds
    prefer_grpc=True
)

# Health check antes de usar
try:
    client.get_collections()
except Exception as e:
    logger.error("qdrant_unhealthy", error=str(e))
    raise
```

### Problema 3: Test Coverage Baixo

**Sintoma**: Coverage < 90%

**Solução**:
```bash
# Identificar linhas não cobertas
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Adicionar testes para edge cases
# Adicionar testes de integração
# Mockar dependências externas
```

---

## MÉTRICAS DE SUCESSO

```bash
✅ Sprint 1 Complete:
   - Orchestrator operational
   - HOTL system enforcing approvals
   - Attack memory storing campaigns
   - 92%+ test coverage
   - CI/CD pipeline green
   - Kubernetes deployment successful

Next: Sprint 2 - Reconnaissance Agent
```

---

**Status**: IMPLEMENTATION GUIDE COMPLETE  
**Owner**: MAXIMUS Offensive Team  
**Last Updated**: 2025-10-11
