# IMPLEMENTATION PLAN 01: OFFENSIVE SECURITY TOOLKIT
## Plano Detalhado de Execução - Fase por Fase

**Blueprint**: OFFENSIVE-TOOLKIT | **Roadmap**: 01  
**Version**: 1.0 | **Date**: 2025-10-11  
**Methodology**: AGILE + TDD + Quality-First

---

## 🎯 OBJETIVO GERAL

Implementar sistema multiagente de pentest autônomo supervisionado, world-class, em conformidade com Doutrina MAXIMUS, em 9 semanas.

---

## 📋 PHASE 0: PREPARATION & ARCHITECTURE (Days 1-3)

### Day 1: Agent Communication Protocol (ACP)

#### Task 0.1: Design ACP Specification
**Owner**: Tech Lead  
**Duration**: 4h

**Steps**:
1. Definir schema de mensagens (JSON)
2. Estabelecer message types (TASK_ASSIGN, TASK_RESULT, STATUS_UPDATE, ERROR)
3. Definir routing rules entre agents
4. Especificar formato de error handling
5. Documentar protocol versioning

**Deliverables**:
```bash
# Criar documento
touch docs/architecture/security/ACP-SPECIFICATION.md

# Estrutura do doc
## 1. Overview
## 2. Message Schema
## 3. Message Types
## 4. Routing Rules
## 5. Error Handling
## 6. Versioning
## 7. Examples
```

**Validation**:
```bash
# Schema validation
python -c "import json; json.load(open('schemas/acp-message.json'))"
```

#### Task 0.2: Setup Message Broker Infrastructure
**Owner**: Backend Engineer  
**Duration**: 4h

**Commands**:
```bash
# 1. Criar serviço de message broker
mkdir -p backend/services/agent_communication
cd backend/services/agent_communication

# 2. Estrutura de arquivos
cat > __init__.py << 'EOF'
"""Agent Communication Protocol (ACP) implementation."""
from .broker import MessageBroker
from .message import ACPMessage
from .router import MessageRouter

__all__ = ["MessageBroker", "ACPMessage", "MessageRouter"]
EOF

# 3. Criar requirements
cat > requirements.txt << 'EOF'
redis==5.0.1
aio-pika==9.3.1  # RabbitMQ async client
pydantic==2.5.0
fastapi==0.104.1
EOF

# 4. Install dependencies
pip install -r requirements.txt
```

**Implementation**: `broker.py`
```python
"""Message broker wrapper for agent communication."""
import asyncio
from typing import Optional, Callable, Dict
import aio_pika
from redis import asyncio as aioredis

class MessageBroker:
    """Abstraction over RabbitMQ for agent messaging."""
    
    def __init__(self, connection_url: str = "amqp://guest:guest@localhost/"):
        self.connection_url = connection_url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queues: Dict[str, aio_pika.Queue] = {}
    
    async def connect(self) -> None:
        """Establish connection to message broker."""
        self.connection = await aio_pika.connect_robust(self.connection_url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)
    
    async def declare_queue(self, queue_name: str) -> aio_pika.Queue:
        """Declare a queue for an agent."""
        if queue_name in self.queues:
            return self.queues[queue_name]
        
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={"x-message-ttl": 300000}  # 5 min TTL
        )
        self.queues[queue_name] = queue
        return queue
    
    async def publish(
        self,
        queue_name: str,
        message: dict,
        priority: int = 0
    ) -> None:
        """Publish message to agent queue."""
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                priority=priority
            ),
            routing_key=queue_name
        )
    
    async def consume(
        self,
        queue_name: str,
        callback: Callable
    ) -> None:
        """Consume messages from queue."""
        queue = await self.declare_queue(queue_name)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body.decode())
                    await callback(data)
    
    async def close(self) -> None:
        """Close connection."""
        if self.connection:
            await self.connection.close()
```

**Validation**:
```bash
# Test connection
pytest backend/services/agent_communication/tests/test_broker.py -v
```

---

### Day 2: Agent Base Classes & Directory Structure

#### Task 0.3: Create Agent Base Class
**Owner**: Tech Lead  
**Duration**: 4h

**Commands**:
```bash
# Create shared agent library
mkdir -p backend/lib/agents
cd backend/lib/agents

cat > base_agent.py << 'EOF'
"""Base class for all MAXIMUS agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
from uuid import uuid4
from datetime import datetime

from backend.services.agent_communication import MessageBroker, ACPMessage

class BaseAgent(ABC):
    """Base class for autonomous agents in MAXIMUS."""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        broker: MessageBroker
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.broker = broker
        self.queue_name = f"{agent_type}_{agent_id}"
        self.running = False
    
    async def start(self) -> None:
        """Start agent and begin consuming messages."""
        await self.broker.declare_queue(self.queue_name)
        self.running = True
        
        # Start message consumption
        asyncio.create_task(
            self.broker.consume(self.queue_name, self.handle_message)
        )
        
        await self.on_start()
    
    async def stop(self) -> None:
        """Stop agent gracefully."""
        self.running = False
        await self.on_stop()
    
    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message. Must be implemented by subclass."""
        pass
    
    @abstractmethod
    async def on_start(self) -> None:
        """Called when agent starts. Override for initialization."""
        pass
    
    async def on_stop(self) -> None:
        """Called when agent stops. Override for cleanup."""
        pass
    
    async def send_message(
        self,
        to_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> None:
        """Send message to another agent."""
        message = {
            "message_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "from_agent": self.agent_id,
            "to_agent": to_agent,
            "message_type": message_type,
            "priority": priority,
            "payload": payload
        }
        
        await self.broker.publish(
            queue_name=f"{to_agent}",
            message=message,
            priority=priority
        )
    
    async def log(self, level: str, message: str, **kwargs) -> None:
        """Log message with context."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "level": level,
            "message": message,
            **kwargs
        }
        # TODO: Send to logging service
        print(f"[{level}] {self.agent_id}: {message}")
EOF
```

#### Task 0.4: Create Agent Directory Structure
**Owner**: Backend Engineer  
**Duration**: 2h

**Commands**:
```bash
# Create directory structure for all agents
cd /home/juan/vertice-dev/backend/services

# Agent directories
for agent in offensive_orchestrator reconnaissance_agent exploitation_agent postexploit_agent analysis_agent; do
    mkdir -p $agent/{tests,models}
    
    # Create __init__.py
    touch $agent/__init__.py
    
    # Create placeholder main files
    touch $agent/agent.py
    touch $agent/models.py
    touch $agent/config.py
    
    # Create tests
    touch $agent/tests/__init__.py
    touch $agent/tests/test_agent.py
    touch $agent/tests/test_integration.py
    
    # Create requirements.txt
    cat > $agent/requirements.txt << 'DEPS'
fastapi==0.104.1
pydantic==2.5.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
DEPS
done

echo "✅ Agent structure created"
```

---

### Day 3: CI/CD Setup & Integration Tests

#### Task 0.5: Configure CI/CD Pipeline
**Owner**: Tech Lead  
**Duration**: 4h

**Commands**:
```bash
# Create GitHub Actions workflow for agents
mkdir -p .github/workflows

cat > .github/workflows/offensive-toolkit-ci.yml << 'EOF'
name: Offensive Toolkit CI

on:
  push:
    branches: [ main, feature/offensive-* ]
    paths:
      - 'backend/services/offensive_orchestrator/**'
      - 'backend/services/reconnaissance_agent/**'
      - 'backend/services/exploitation_agent/**'
      - 'backend/services/postexploit_agent/**'
      - 'backend/services/analysis_agent/**'
      - 'backend/services/agent_communication/**'
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      rabbitmq:
        image: rabbitmq:3.12-management
        ports:
          - 5672:5672
          - 15672:15672
        env:
          RABBITMQ_DEFAULT_USER: guest
          RABBITMQ_DEFAULT_PASS: guest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/services/agent_communication/requirements.txt
        pip install pytest pytest-cov mypy black pylint
    
    - name: Lint with black
      run: black --check backend/services/
    
    - name: Type check with mypy
      run: mypy backend/services/agent_communication --strict
    
    - name: Run tests
      run: |
        pytest backend/services/agent_communication/tests/ \
          --cov=backend/services/agent_communication \
          --cov-report=xml \
          --cov-report=term \
          -v
    
    - name: Check coverage
      run: |
        coverage report --fail-under=90
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
EOF

echo "✅ CI/CD pipeline configured"
```

#### Task 0.6: End-to-End Ping-Pong Test
**Owner**: Backend Engineer  
**Duration**: 2h

**Implementation**: Create integration test
```bash
cat > backend/services/agent_communication/tests/test_e2e.py << 'EOF'
"""End-to-end integration tests for agent communication."""
import pytest
import asyncio
from backend.services.agent_communication import MessageBroker
from backend.lib.agents import BaseAgent

class PingAgent(BaseAgent):
    """Test agent that sends ping."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pong_received = False
    
    async def handle_message(self, message: dict) -> None:
        if message["message_type"] == "PONG":
            self.pong_received = True
            await self.log("INFO", f"Received PONG: {message}")
    
    async def on_start(self) -> None:
        await self.log("INFO", "PingAgent started")
    
    async def send_ping(self, to_agent: str) -> None:
        await self.send_message(
            to_agent=to_agent,
            message_type="PING",
            payload={"message": "ping"}
        )

class PongAgent(BaseAgent):
    """Test agent that responds with pong."""
    
    async def handle_message(self, message: dict) -> None:
        if message["message_type"] == "PING":
            await self.log("INFO", f"Received PING from {message['from_agent']}")
            await self.send_message(
                to_agent=message["from_agent"],
                message_type="PONG",
                payload={"message": "pong"}
            )
    
    async def on_start(self) -> None:
        await self.log("INFO", "PongAgent started")

@pytest.mark.asyncio
async def test_ping_pong_communication():
    """Test basic agent-to-agent communication."""
    broker = MessageBroker("amqp://guest:guest@localhost/")
    await broker.connect()
    
    # Create agents
    ping_agent = PingAgent("ping1", "ping", broker)
    pong_agent = PongAgent("pong1", "pong", broker)
    
    # Start agents
    await ping_agent.start()
    await pong_agent.start()
    
    # Send ping
    await ping_agent.send_ping("pong1")
    
    # Wait for pong response
    await asyncio.sleep(0.5)
    
    # Assert pong received
    assert ping_agent.pong_received, "Pong not received"
    
    # Cleanup
    await ping_agent.stop()
    await pong_agent.stop()
    await broker.close()
EOF
```

**Validation**:
```bash
# Run integration test
docker-compose up -d rabbitmq  # Start RabbitMQ
pytest backend/services/agent_communication/tests/test_e2e.py -v

# Expected output: PASSED
```

---

## 📋 PHASE 1: ORCHESTRATOR AGENT (Days 4-8)

### Day 4-5: Orchestrator Core Implementation

#### Task 1.1: LLM Integration Module
**Owner**: Backend Engineer  
**Duration**: 8h

**Commands**:
```bash
cd backend/services/offensive_orchestrator

# Install LLM dependencies
cat >> requirements.txt << 'EOF'
litellm==1.17.0  # Unified LLM API
langchain==0.1.0
langchain-openai==0.0.2
pydantic==2.5.0
networkx==3.2.1  # For DAG
EOF

pip install -r requirements.txt
```

**Implementation**: `llm_integration.py`
```python
"""LLM integration for orchestrator agent."""
from typing import List, Dict, Any, Optional
from litellm import acompletion
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class TaskNode(BaseModel):
    """Represents a single task in the task graph."""
    task_id: str = Field(description="Unique task identifier")
    agent_type: str = Field(description="Agent responsible for task")
    action: str = Field(description="Action to perform")
    parameters: Dict[str, Any] = Field(description="Action parameters")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")
    priority: int = Field(default=0, description="Priority (0-10)")

class TaskGraph(BaseModel):
    """Complete task decomposition."""
    objective: str = Field(description="Original objective")
    tasks: List[TaskNode] = Field(description="List of tasks")

class LLMOrchestrator:
    """LLM-powered task decomposition and planning."""
    
    DECOMPOSITION_PROMPT = """You are MAXIMUS Offensive Orchestrator, an AI agent coordinating penetration testing operations.

Given a high-level objective, decompose it into a directed acyclic graph (DAG) of concrete tasks.

Available agents and their capabilities:
- reconnaissance: OSINT collection, network scanning, service enumeration, vulnerability mapping
- exploitation: Exploit generation, payload delivery, vulnerability exploitation
- postexploit: Lateral movement, privilege escalation, credential harvesting
- analysis: Result processing, report generation, knowledge base updates

Constraints:
- Each task must be assigned to exactly one agent
- Tasks can depend on completion of other tasks
- Use realistic pentest methodology (PTES: Recon → Exploit → Post-Exploit)

Objective: {objective}

{format_instructions}

Generate the task graph:"""
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key
        self.parser = PydanticOutputParser(pydantic_object=TaskGraph)
    
    async def decompose_objective(self, objective: str) -> TaskGraph:
        """Decompose high-level objective into task graph."""
        prompt = self.DECOMPOSITION_PROMPT.format(
            objective=objective,
            format_instructions=self.parser.get_format_instructions()
        )
        
        response = await acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_key=self.api_key,
            temperature=0.3  # Lower temp for more structured output
        )
        
        result_text = response.choices[0].message.content
        task_graph = self.parser.parse(result_text)
        
        return task_graph
    
    async def assess_risk(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risk level of proposed action."""
        prompt = f"""Assess the risk of this penetration testing action:

Action: {action}
Context: {context}

Evaluate on these dimensions:
1. Destructiveness (0-10): Potential for data loss or service disruption
2. Detectability (0-10): Likelihood of detection by defenders
3. Scope compliance (0-10): Risk of exceeding authorized scope
4. Reversibility (0-10): Ability to undo changes (10 = fully reversible)

Provide risk score (0-100) and recommendation (APPROVE, REVIEW, REJECT).

Output JSON:
{{
    "risk_score": <0-100>,
    "destructiveness": <0-10>,
    "detectability": <0-10>,
    "scope_risk": <0-10>,
    "reversibility": <0-10>,
    "recommendation": "<APPROVE|REVIEW|REJECT>",
    "reasoning": "<explanation>"
}}
"""
        
        response = await acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_key=self.api_key,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
```

**Tests**: `tests/test_llm_integration.py`
```python
"""Tests for LLM integration."""
import pytest
from backend.services.offensive_orchestrator.llm_integration import (
    LLMOrchestrator, TaskGraph
)

@pytest.mark.asyncio
async def test_decompose_simple_objective():
    """Test decomposition of simple objective."""
    orchestrator = LLMOrchestrator(model="gpt-3.5-turbo")
    
    objective = "Scan network 10.1.1.0/24 and identify vulnerable services"
    
    task_graph = await orchestrator.decompose_objective(objective)
    
    assert isinstance(task_graph, TaskGraph)
    assert task_graph.objective == objective
    assert len(task_graph.tasks) >= 2  # At least recon + analysis
    
    # Check first task is reconnaissance
    assert task_graph.tasks[0].agent_type == "reconnaissance"

@pytest.mark.asyncio
async def test_risk_assessment_safe_action():
    """Test risk assessment for safe action."""
    orchestrator = LLMOrchestrator()
    
    risk = await orchestrator.assess_risk(
        action="nmap_scan",
        context={"target": "10.1.1.50", "ports": "80,443"}
    )
    
    assert risk["risk_score"] < 30  # Low risk
    assert risk["recommendation"] == "APPROVE"

@pytest.mark.asyncio
async def test_risk_assessment_dangerous_action():
    """Test risk assessment for dangerous action."""
    orchestrator = LLMOrchestrator()
    
    risk = await orchestrator.assess_risk(
        action="ransomware_deploy",
        context={"target": "production_server"}
    )
    
    assert risk["risk_score"] > 80  # High risk
    assert risk["recommendation"] == "REJECT"
```

**Validation**:
```bash
pytest backend/services/offensive_orchestrator/tests/test_llm_integration.py -v
```

---

### Day 6: Task Graph Implementation

#### Task 1.2: DAG Task Graph
**Owner**: Backend Engineer  
**Duration**: 6h

**Implementation**: `task_graph.py`
```python
"""Task graph implementation using DAG."""
from typing import List, Dict, Set, Optional
from enum import Enum
import networkx as nx
from dataclasses import dataclass, field
from datetime import datetime

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"  # Dependencies satisfied
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class Task:
    """Individual task in the graph."""
    task_id: str
    agent_type: str
    action: str
    parameters: Dict
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class TaskGraph:
    """Directed Acyclic Graph of tasks."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.tasks: Dict[str, Task] = {}
    
    def add_task(self, task: Task) -> None:
        """Add task to graph."""
        self.tasks[task.task_id] = task
        self.graph.add_node(task.task_id, task=task)
        
        # Add dependency edges
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                raise ValueError(f"Dependency {dep_id} not found")
            self.graph.add_edge(dep_id, task.task_id)
        
        # Validate DAG
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Graph contains cycles")
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks whose dependencies are satisfied."""
        ready = []
        
        for task_id, task in self.tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_completed = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_completed:
                task.status = TaskStatus.READY
                ready.append(task)
        
        return ready
    
    def mark_completed(self, task_id: str, result: Dict) -> None:
        """Mark task as completed with result."""
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.utcnow()
    
    def mark_failed(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.utcnow()
        
        # Block dependent tasks
        for dependent_id in nx.descendants(self.graph, task_id):
            self.tasks[dependent_id].status = TaskStatus.BLOCKED
    
    def get_execution_order(self) -> List[str]:
        """Get topological order of task execution."""
        return list(nx.topological_sort(self.graph))
    
    def visualize(self) -> str:
        """Generate mermaid diagram of task graph."""
        lines = ["graph TD"]
        
        for task_id, task in self.tasks.items():
            label = f"{task.agent_type}: {task.action}"
            style = {
                TaskStatus.COMPLETED: ":::completed",
                TaskStatus.RUNNING: ":::running",
                TaskStatus.FAILED: ":::failed",
            }.get(task.status, "")
            
            lines.append(f"    {task_id}[{label}]{style}")
        
        for edge in self.graph.edges():
            lines.append(f"    {edge[0]} --> {edge[1]}")
        
        lines.extend([
            "    classDef completed fill:#90EE90",
            "    classDef running fill:#FFD700",
            "    classDef failed fill:#FF6B6B"
        ])
        
        return "\n".join(lines)
```

**Tests**: `tests/test_task_graph.py`
```python
"""Tests for task graph."""
import pytest
from backend.services.offensive_orchestrator.task_graph import (
    Task, TaskGraph, TaskStatus
)

def test_add_task_no_dependencies():
    """Test adding task without dependencies."""
    graph = TaskGraph()
    task = Task(
        task_id="recon1",
        agent_type="reconnaissance",
        action="nmap_scan",
        parameters={"target": "10.1.1.0/24"}
    )
    
    graph.add_task(task)
    
    assert "recon1" in graph.tasks
    assert len(graph.get_ready_tasks()) == 1

def test_add_task_with_dependencies():
    """Test adding task with dependencies."""
    graph = TaskGraph()
    
    task1 = Task(task_id="recon1", agent_type="reconnaissance", action="scan", parameters={})
    task2 = Task(
        task_id="exploit1",
        agent_type="exploitation",
        action="exploit_ssh",
        parameters={},
        dependencies=["recon1"]
    )
    
    graph.add_task(task1)
    graph.add_task(task2)
    
    ready = graph.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].task_id == "recon1"

def test_mark_completed_enables_dependents():
    """Test that completing task enables dependent tasks."""
    graph = TaskGraph()
    
    task1 = Task(task_id="t1", agent_type="recon", action="scan", parameters={})
    task2 = Task(task_id="t2", agent_type="exploit", action="exploit", parameters={}, dependencies=["t1"])
    
    graph.add_task(task1)
    graph.add_task(task2)
    
    # Initially only t1 is ready
    assert len(graph.get_ready_tasks()) == 1
    
    # Complete t1
    graph.mark_completed("t1", {"hosts": ["10.1.1.50"]})
    
    # Now t2 should be ready
    ready = graph.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].task_id == "t2"

def test_cycle_detection():
    """Test that cycles are detected."""
    graph = TaskGraph()
    
    task1 = Task(task_id="t1", agent_type="a", action="act", parameters={}, dependencies=["t2"])
    task2 = Task(task_id="t2", agent_type="b", action="act", parameters={}, dependencies=["t1"])
    
    graph.add_task(Task(task_id="t1", agent_type="a", action="act", parameters={}))
    
    with pytest.raises(ValueError, match="cycles"):
        # This should fail because it creates a cycle
        graph.graph.add_edge("t1", "t2")
        graph.graph.add_edge("t2", "t1")
        nx.is_directed_acyclic_graph(graph.graph)  # Will return False
```

---

### Day 7: HOTL Interface

#### Task 1.3: Human-on-the-Loop Interface
**Owner**: Backend Engineer  
**Duration**: 6h

**Implementation**: `hotl_interface.py`
```python
"""Human-on-the-Loop interface for orchestrator."""
from typing import Optional, Dict, Any, Callable
from enum import Enum
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
from datetime import datetime

class ApprovalDecision(str, Enum):
    """Human approval decision."""
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"

class ApprovalRequest(BaseModel):
    """Request for human approval."""
    request_id: str
    timestamp: datetime
    action_type: str
    action_details: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommended_decision: str

class ApprovalResponse(BaseModel):
    """Human response to approval request."""
    request_id: str
    decision: ApprovalDecision
    modifications: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None

class HOTLInterface:
    """Human-on-the-Loop interface for critical decisions."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.pending_approvals: Dict[str, asyncio.Future] = {}
        self.websocket: Optional[WebSocket] = None
        
        # Register WebSocket endpoint
        @app.websocket("/hotl/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket(websocket)
    
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection from operator."""
        await websocket.accept()
        self.websocket = websocket
        
        try:
            while True:
                # Receive approval responses
                data = await websocket.receive_json()
                response = ApprovalResponse(**data)
                
                # Resolve pending approval
                if response.request_id in self.pending_approvals:
                    future = self.pending_approvals[response.request_id]
                    future.set_result(response)
                    del self.pending_approvals[response.request_id]
        
        except WebSocketDisconnect:
            self.websocket = None
    
    async def request_approval(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        timeout: int = 300  # 5 minutes
    ) -> ApprovalResponse:
        """Request approval from human operator."""
        if not self.websocket:
            raise RuntimeError("No operator connected via WebSocket")
        
        request_id = f"approval_{datetime.utcnow().timestamp()}"
        
        request = ApprovalRequest(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            action_type=action_type,
            action_details=action_details,
            risk_assessment=risk_assessment,
            recommended_decision=self._get_recommendation(risk_assessment)
        )
        
        # Send to operator
        await self.websocket.send_json(request.dict())
        
        # Wait for response
        future = asyncio.Future()
        self.pending_approvals[request_id] = future
        
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            del self.pending_approvals[request_id]
            raise TimeoutError(f"Approval request {request_id} timed out")
    
    def _get_recommendation(self, risk_assessment: Dict[str, Any]) -> str:
        """Get recommended decision based on risk."""
        risk_score = risk_assessment.get("risk_score", 50)
        
        if risk_score < 30:
            return "APPROVE"
        elif risk_score < 70:
            return "REVIEW"
        else:
            return "REJECT"
```

**Frontend Component**: `frontend/src/components/HOTLDashboard.tsx`
```typescript
/**
 * HOTL Dashboard for operator interface.
 */
import { useState, useEffect } from 'react';
import { Card, Button, Badge } from '@/components/ui';

interface ApprovalRequest {
  request_id: string;
  timestamp: string;
  action_type: string;
  action_details: Record<string, any>;
  risk_assessment: {
    risk_score: number;
    recommendation: string;
    reasoning: string;
  };
}

export function HOTLDashboard() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [pendingRequests, setPendingRequests] = useState<ApprovalRequest[]>([]);
  
  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8000/hotl/ws');
    
    websocket.onmessage = (event) => {
      const request: ApprovalRequest = JSON.parse(event.data);
      setPendingRequests(prev => [...prev, request]);
    };
    
    setWs(websocket);
    
    return () => websocket.close();
  }, []);
  
  const handleDecision = (requestId: string, decision: string, modifications?: any) => {
    if (!ws) return;
    
    ws.send(JSON.stringify({
      request_id: requestId,
      decision,
      modifications,
      reasoning: "Operator decision"
    }));
    
    setPendingRequests(prev => prev.filter(r => r.request_id !== requestId));
  };
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">HOTL Approval Dashboard</h1>
      
      {pendingRequests.length === 0 ? (
        <p className="text-gray-500">No pending approval requests</p>
      ) : (
        pendingRequests.map(request => (
          <Card key={request.request_id} className="mb-4 p-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{request.action_type}</h3>
                <Badge variant={request.risk_assessment.risk_score > 70 ? 'destructive' : 'default'}>
                  Risk: {request.risk_assessment.risk_score}/100
                </Badge>
                
                <pre className="mt-2 bg-gray-100 p-2 rounded">
                  {JSON.stringify(request.action_details, null, 2)}
                </pre>
                
                <p className="mt-2 text-sm text-gray-600">
                  {request.risk_assessment.reasoning}
                </p>
              </div>
              
              <div className="flex gap-2">
                <Button
                  variant="default"
                  onClick={() => handleDecision(request.request_id, 'approved')}
                >
                  ✓ Approve
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleDecision(request.request_id, 'rejected')}
                >
                  ✗ Reject
                </Button>
              </div>
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
```

---

### Day 8: Orchestrator Integration & Testing

#### Task 1.4: Complete Orchestrator Agent
**Owner**: Tech Lead  
**Duration**: 8h

**Implementation**: `agent.py`
```python
"""Main orchestrator agent implementation."""
from typing import Dict, Any, List
import asyncio
from backend.lib.agents import BaseAgent
from backend.services.agent_communication import MessageBroker
from .llm_integration import LLMOrchestrator, TaskGraph as LLMTaskGraph
from .task_graph import TaskGraph, Task, TaskStatus
from .hotl_interface import HOTLInterface, ApprovalDecision
from .risk_assessor import RiskAssessor

class OrchestratorAgent(BaseAgent):
    """Central orchestrator for offensive operations."""
    
    def __init__(self, broker: MessageBroker, hotl: HOTLInterface):
        super().__init__(
            agent_id="orchestrator_main",
            agent_type="orchestrator",
            broker=broker
        )
        
        self.llm = LLMOrchestrator()
        self.task_graph: Optional[TaskGraph] = None
        self.hotl = hotl
        self.risk_assessor = RiskAssessor()
        
        # Track active operations
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def on_start(self) -> None:
        """Initialize orchestrator."""
        await self.log("INFO", "Orchestrator agent started")
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming messages."""
        msg_type = message["message_type"]
        
        handlers = {
            "NEW_OBJECTIVE": self.handle_new_objective,
            "TASK_RESULT": self.handle_task_result,
            "TASK_ERROR": self.handle_task_error,
        }
        
        handler = handlers.get(msg_type)
        if handler:
            await handler(message)
        else:
            await self.log("WARNING", f"Unknown message type: {msg_type}")
    
    async def handle_new_objective(self, message: Dict[str, Any]) -> None:
        """Handle new pentest objective."""
        objective = message["payload"]["objective"]
        
        await self.log("INFO", f"Received objective: {objective}")
        
        # 1. Decompose into tasks
        llm_graph = await self.llm.decompose_objective(objective)
        
        # 2. Build task graph
        self.task_graph = self._build_task_graph(llm_graph)
        
        # 3. Start execution
        await self._execute_task_graph()
    
    def _build_task_graph(self, llm_graph: LLMTaskGraph) -> TaskGraph:
        """Convert LLM output to executable task graph."""
        graph = TaskGraph()
        
        for llm_task in llm_graph.tasks:
            task = Task(
                task_id=llm_task.task_id,
                agent_type=llm_task.agent_type,
                action=llm_task.action,
                parameters=llm_task.parameters,
                dependencies=llm_task.dependencies
            )
            graph.add_task(task)
        
        return graph
    
    async def _execute_task_graph(self) -> None:
        """Execute tasks in topological order."""
        await self.log("INFO", "Starting task graph execution")
        
        while True:
            # Get tasks that are ready to run
            ready_tasks = self.task_graph.get_ready_tasks()
            
            if not ready_tasks:
                # Check if all tasks completed
                all_done = all(
                    t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED]
                    for t in self.task_graph.tasks.values()
                )
                
                if all_done:
                    await self.log("INFO", "Task graph execution completed")
                    break
                else:
                    # Wait for running tasks
                    await asyncio.sleep(1)
                    continue
            
            # Execute ready tasks
            for task in ready_tasks:
                await self._execute_task(task)
            
            await asyncio.sleep(0.5)
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        
        await self.log("INFO", f"Executing task {task.task_id}: {task.action}")
        
        # Check if HOTL approval required
        requires_approval = self._requires_hotl_approval(task)
        
        if requires_approval:
            await self.log("INFO", f"Task {task.task_id} requires HOTL approval")
            
            # Assess risk
            risk = await self.llm.assess_risk(task.action, task.parameters)
            
            # Request approval
            try:
                approval = await self.hotl.request_approval(
                    action_type=task.action,
                    action_details=task.parameters,
                    risk_assessment=risk
                )
                
                if approval.decision == ApprovalDecision.REJECTED:
                    await self.log("WARNING", f"Task {task.task_id} rejected by operator")
                    self.task_graph.mark_failed(task.task_id, "Rejected by operator")
                    return
                
                elif approval.decision == ApprovalDecision.MODIFIED:
                    # Apply modifications
                    task.parameters.update(approval.modifications or {})
            
            except TimeoutError:
                await self.log("ERROR", f"HOTL approval timeout for task {task.task_id}")
                self.task_graph.mark_failed(task.task_id, "Approval timeout")
                return
        
        # Delegate to agent
        await self.send_message(
            to_agent=task.agent_type,
            message_type="TASK_ASSIGN",
            payload={
                "task_id": task.task_id,
                "action": task.action,
                "parameters": task.parameters
            },
            priority=5
        )
    
    def _requires_hotl_approval(self, task: Task) -> bool:
        """Determine if task requires human approval."""
        # Critical actions always require approval
        critical_actions = {
            "exploit", "exploit_vulnerability", "deploy_payload",
            "lateral_move", "privilege_escalate", "exfiltrate_data"
        }
        
        return any(keyword in task.action.lower() for keyword in critical_actions)
    
    async def handle_task_result(self, message: Dict[str, Any]) -> None:
        """Handle task completion from agent."""
        task_id = message["payload"]["task_id"]
        result = message["payload"]["result"]
        
        await self.log("INFO", f"Task {task_id} completed")
        
        self.task_graph.mark_completed(task_id, result)
    
    async def handle_task_error(self, message: Dict[str, Any]) -> None:
        """Handle task failure from agent."""
        task_id = message["payload"]["task_id"]
        error = message["payload"]["error"]
        
        await self.log("ERROR", f"Task {task_id} failed: {error}")
        
        self.task_graph.mark_failed(task_id, error)
```

**End-to-End Test**: `tests/test_orchestrator_e2e.py`
```python
"""End-to-end tests for orchestrator."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from backend.services.offensive_orchestrator.agent import OrchestratorAgent
from backend.services.agent_communication import MessageBroker
from backend.services.offensive_orchestrator.hotl_interface import HOTLInterface

@pytest.mark.asyncio
async def test_orchestrator_simple_workflow(mock_broker, mock_hotl):
    """Test orchestrator handling simple workflow."""
    orchestrator = OrchestratorAgent(mock_broker, mock_hotl)
    
    await orchestrator.start()
    
    # Send objective
    await orchestrator.handle_message({
        "message_type": "NEW_OBJECTIVE",
        "payload": {
            "objective": "Scan network 10.1.1.0/24"
        }
    })
    
    # Wait for task graph creation
    await asyncio.sleep(2)
    
    assert orchestrator.task_graph is not None
    assert len(orchestrator.task_graph.tasks) > 0
    
    # Simulate task completion
    task_id = list(orchestrator.task_graph.tasks.keys())[0]
    await orchestrator.handle_message({
        "message_type": "TASK_RESULT",
        "payload": {
            "task_id": task_id,
            "result": {"hosts": ["10.1.1.50"]}
        }
    })
    
    assert orchestrator.task_graph.tasks[task_id].status == "completed"

@pytest.mark.asyncio
async def test_orchestrator_hotl_approval(mock_broker, mock_hotl):
    """Test HOTL approval flow."""
    mock_hotl.request_approval = AsyncMock(return_value=Mock(
        decision="approved",
        modifications=None
    ))
    
    orchestrator = OrchestratorAgent(mock_broker, mock_hotl)
    await orchestrator.start()
    
    # Create task requiring approval
    task = Task(
        task_id="exploit1",
        agent_type="exploitation",
        action="exploit_vulnerability",
        parameters={"target": "10.1.1.50", "cve": "CVE-2021-44228"}
    )
    
    # Execute task
    await orchestrator._execute_task(task)
    
    # Verify approval was requested
    mock_hotl.request_approval.assert_called_once()
```

**Validation Commands**:
```bash
# Run all orchestrator tests
pytest backend/services/offensive_orchestrator/tests/ -v --cov

# Expected: All tests pass, coverage >90%

# Run integration test
pytest backend/services/offensive_orchestrator/tests/test_orchestrator_e2e.py -v

# Start orchestrator service
cd backend/services/offensive_orchestrator
uvicorn main:app --reload

# Test HOTL interface
curl -X POST http://localhost:8000/api/v1/objective \
  -H "Content-Type: application/json" \
  -d '{"objective": "Scan 10.1.1.0/24 and identify SSH servers"}'
```

---

## 📊 PHASE 1 COMPLETION CHECKLIST

- [ ] LLM integration functional (task decomposition working)
- [ ] Task Graph implementation complete (DAG valid)
- [ ] HOTL interface operational (WebSocket connection)
- [ ] Orchestrator agent running and delegating tasks
- [ ] All tests passing (≥90% coverage)
- [ ] Documentation updated (`docs/guides/orchestrator-usage.md`)
- [ ] Demo prepared: "Objective → Task Graph → HOTL Approval"

**Demo Script**:
```bash
# Terminal 1: Start services
docker-compose up -d rabbitmq postgres
cd backend/services/offensive_orchestrator
uvicorn main:app --reload

# Terminal 2: Connect HOTL interface
cd frontend
npm run dev
# Open http://localhost:3000/hotl

# Terminal 3: Submit objective
curl -X POST http://localhost:8000/api/v1/objective \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Perform reconnaissance on network 192.168.1.0/24 and identify all web servers with outdated software"
  }'

# Observe:
# 1. Task graph generated by LLM
# 2. Tasks appear in HOTL dashboard
# 3. Approval/rejection workflow
# 4. Task delegation to agents
```

---

## 📝 NEXT STEPS

After Phase 1 completion:
1. **Code Review**: Tech Lead reviews all Phase 1 code
2. **Merge**: Create PR and merge to `main`
3. **Documentation**: Update architecture docs
4. **Demo**: Present to stakeholders
5. **Start Phase 2**: Begin Reconnaissance Agent implementation

---

**Document Status**: IN PROGRESS - Phase 1  
**Last Updated**: 2025-10-11  
**Next Review**: End of Week 1

---

*[Continua na próxima parte do documento...]*

