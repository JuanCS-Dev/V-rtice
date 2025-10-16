# TRACK 3: SERVICE TEMPLATE & MIGRAÇÕES

**Executor:** Dev Sênior C  
**Especialidade:** Clean Architecture, DDD, FastAPI, Refactoring  
**Duração:** 20 dias (Dias 11-30)  
**Branch:** `backend-transformation/track3-services`

---

## MISSÃO

Criar service template e migrar serviços críticos:
1. Service template Clean Architecture (Dias 11-14)
2. Documentação e testing do template (Dia 15-16)
3. Migração de 10 serviços críticos (Dias 17-30)

---

## PRÉ-REQUISITOS (GATE 2)

### Dependências de Outros Tracks

**❌ NÃO INICIAR ATÉ:**
- [ ] Track 1: vertice_core v1.0.0 disponível
- [ ] Track 1: vertice_api v1.0.0 disponível
- [ ] Track 1: vertice_db v1.0.0 disponível
- [ ] Track 2: Port registry completo
- [ ] Track 2: CI/CD pipeline funcional
- [ ] Aprovação do Arquiteto-Chefe (GATE 2)

**Validar dependências:**
```bash
# Check libs disponíveis
cd /home/juan/vertice-dev/backend/libs
ls -d vertice_core vertice_api vertice_db
# EXPECTED: All 3 directories exist

# Check port registry
cd /home/juan/vertice-dev/backend
python scripts/validate_ports.py
# EXPECTED: ✅ PORT REGISTRY VALID

# Check CI
gh workflow list | grep "validate-backend"
# EXPECTED: Workflow exists
```

---

## ÁREA DE TRABALHO (Sem Conflitos)

```
backend/
├── service_template/           # Você cria
├── services/
│   ├── api_gateway/           # Você migra
│   ├── osint_service/         # Você migra
│   └── (outros 8 serviços)    # Você migra
docs/migration/                 # Você cria
└── service-template-guide.md  # Você cria
```

**Track 1 (libs):** SOMENTE LEITURA (importar)  
**Track 2 (infra):** SOMENTE LEITURA (usar port registry)

---

## DIAS 11-12: Service Template - Domain Layer

### 11.1 Criar Estrutura Base (Manhã)

```bash
cd /home/juan/vertice-dev/backend
mkdir -p service_template/{src/service_template,tests,alembic/versions}
cd service_template
```

**Criar `pyproject.toml`:**
```toml
[project]
name = "service-template"
version = "1.0.0"
description = "Clean Architecture template for Vértice services"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "httpx>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "redis[hiredis]>=5.0.0",
    "python-dotenv>=1.0.0",
    # Vértice libs (ajustar path conforme instalação)
    "vertice-core>=1.0.0",
    "vertice-api>=1.0.0",
    "vertice-db>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "httpx>=0.27.0",
    "testcontainers[postgres]>=4.0.0",
    "testcontainers[redis]>=4.0.0",
    "ruff>=0.13.0",
    "mypy>=1.8.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = ["--cov=src", "--cov-fail-under=90", "-v"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "ANN", "S", "B"]
ignore = ["ANN101", "S101"]

[tool.mypy]
python_version = "3.11"
strict = true
```

**Criar estrutura de diretórios:**
```bash
mkdir -p src/service_template/{domain,application,infrastructure,presentation}
mkdir -p src/service_template/domain
mkdir -p src/service_template/application
mkdir -p src/service_template/infrastructure/{database,http,messaging}
mkdir -p src/service_template/presentation/api/v1
mkdir -p tests/{unit,integration,e2e}

touch src/service_template/__init__.py
touch src/service_template/domain/{__init__.py,models.py,services.py,exceptions.py,events.py}
touch src/service_template/application/{__init__.py,queries.py,commands.py}
touch src/service_template/infrastructure/__init__.py
touch src/service_template/infrastructure/database/{__init__.py,models.py,repositories.py,session.py}
touch src/service_template/infrastructure/http/{__init__.py,client.py}
touch src/service_template/infrastructure/messaging/{__init__.py,publisher.py}
touch src/service_template/presentation/__init__.py
touch src/service_template/presentation/api/{__init__.py,dependencies.py}
touch src/service_template/presentation/api/v1/{__init__.py,endpoints.py,schemas.py}
touch src/service_template/{main.py,config.py}
```

**Tree esperada:**
```
service_template/
├── pyproject.toml
├── src/service_template/
│   ├── domain/          (Pure Python, zero deps externas)
│   ├── application/     (Use cases)
│   ├── infrastructure/  (External systems)
│   ├── presentation/    (API layer)
│   ├── main.py
│   └── config.py
└── tests/
```

**Instalar:**
```bash
uv sync --group dev
```

---

### 11.2 Implementar Domain Layer (Tarde Dia 11)

**REGRA CRÍTICA:** Domain = Pure Python, ZERO dependencies externas.

**`src/service_template/domain/exceptions.py`:**
```python
"""Domain-specific exceptions.

These exceptions represent business rule violations and domain errors.
They should NOT depend on any framework or infrastructure concerns.
"""


class DomainError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ValidationError(DomainError):
    """Business validation failed."""
    
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class InvalidStateTransition(DomainError):
    """Attempted invalid state transition."""


class BusinessRuleViolation(DomainError):
    """Business rule violated."""


class EntityNotFound(DomainError):
    """Domain entity not found."""
    
    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(f"{entity_type} not found: {identifier}")
        self.entity_type = entity_type
        self.identifier = identifier
```

**`src/service_template/domain/events.py`:**
```python
"""Domain events.

Events represent things that happened in the domain.
They are immutable and contain all data needed to handle them.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    """Base domain event."""
    
    occurred_at: datetime
    event_version: int = 1
    
    @property
    def event_type(self) -> str:
        """Get event type from class name."""
        return self.__class__.__name__


@dataclass(frozen=True)
class EntityCreated(DomainEvent):
    """Entity was created."""
    
    entity_id: UUID
    entity_type: str
    occurred_at: datetime = datetime.utcnow()


@dataclass(frozen=True)
class EntityUpdated(DomainEvent):
    """Entity was updated."""
    
    entity_id: UUID
    entity_type: str
    changes: dict[str, Any]
    occurred_at: datetime = datetime.utcnow()


@dataclass(frozen=True)
class EntityDeleted(DomainEvent):
    """Entity was deleted."""
    
    entity_id: UUID
    entity_type: str
    occurred_at: datetime = datetime.utcnow()
```

**`src/service_template/domain/models.py`:**
```python
"""Domain models - Core business entities.

These are pure Python classes with business logic and invariants.
NO framework dependencies allowed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from .events import DomainEvent, EntityCreated, EntityUpdated
from .exceptions import InvalidStateTransition, ValidationError


@dataclass
class Entity:
    """Base domain entity with identity and event tracking."""
    
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 0
    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)
    
    def _record_event(self, event: DomainEvent) -> None:
        """Record a domain event."""
        self._events.append(event)
    
    @property
    def events(self) -> list[DomainEvent]:
        """Get recorded events (read-only)."""
        return self._events.copy()
    
    def clear_events(self) -> list[DomainEvent]:
        """Clear and return recorded events."""
        events = self._events.copy()
        self._events.clear()
        return events


@dataclass
class Task(Entity):
    """Task entity - Example domain model.
    
    Business Rules:
    - Title: 3-100 characters
    - Description: max 1000 characters
    - Status: pending → in_progress → completed|cancelled
    - Cannot complete cancelled task
    - Cannot cancel completed task
    """
    
    title: str
    description: str = ""
    status: str = "pending"
    
    def __post_init__(self) -> None:
        """Validate business rules after creation."""
        self._validate()
        self._record_event(EntityCreated(
            entity_id=self.id,
            entity_type="Task",
            occurred_at=self.created_at,
        ))
    
    def _validate(self) -> None:
        """Enforce business invariants."""
        if not (3 <= len(self.title) <= 100):
            raise ValidationError(
                f"Title must be 3-100 characters, got {len(self.title)}",
                field="title",
            )
        
        if len(self.description) > 1000:
            raise ValidationError(
                f"Description max 1000 characters, got {len(self.description)}",
                field="description",
            )
        
        valid_statuses = {"pending", "in_progress", "completed", "cancelled"}
        if self.status not in valid_statuses:
            raise ValidationError(
                f"Invalid status: {self.status}",
                field="status",
            )
    
    def start(self) -> None:
        """Transition to in_progress state."""
        if self.status != "pending":
            raise InvalidStateTransition(
                f"Cannot start task in status '{self.status}'"
            )
        
        self.status = "in_progress"
        self.updated_at = datetime.utcnow()
        self.version += 1
        
        self._record_event(EntityUpdated(
            entity_id=self.id,
            entity_type="Task",
            changes={"status": "in_progress"},
            occurred_at=self.updated_at,
        ))
    
    def complete(self) -> None:
        """Mark task as completed."""
        if self.status not in ("pending", "in_progress"):
            raise InvalidStateTransition(
                f"Cannot complete task in status '{self.status}'"
            )
        
        self.status = "completed"
        self.updated_at = datetime.utcnow()
        self.version += 1
        
        self._record_event(EntityUpdated(
            entity_id=self.id,
            entity_type="Task",
            changes={"status": "completed"},
            occurred_at=self.updated_at,
        ))
    
    def cancel(self) -> None:
        """Cancel the task."""
        if self.status == "completed":
            raise InvalidStateTransition("Cannot cancel completed task")
        
        self.status = "cancelled"
        self.updated_at = datetime.utcnow()
        self.version += 1
        
        self._record_event(EntityUpdated(
            entity_id=self.id,
            entity_type="Task",
            changes={"status": "cancelled"},
            occurred_at=self.updated_at,
        ))
```

**Testes Domain (COMPLETOS, 100% coverage):**

`tests/unit/test_domain_models.py`:
```python
"""Unit tests for domain models - Pure Python, no dependencies."""

import pytest
from datetime import datetime
from uuid import UUID

from service_template.domain.models import Task
from service_template.domain.exceptions import InvalidStateTransition, ValidationError


class TestTaskCreation:
    """Tests for Task entity creation."""
    
    def test_creates_task_with_valid_data(self) -> None:
        """Test creating a task with valid data."""
        task = Task(title="Test Task", description="Test description")
        
        assert isinstance(task.id, UUID)
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.status == "pending"
        assert isinstance(task.created_at, datetime)
        assert task.version == 0
    
    def test_generates_unique_ids(self) -> None:
        """Test that each task gets a unique ID."""
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        
        assert task1.id != task2.id
    
    def test_records_creation_event(self) -> None:
        """Test that creation event is recorded."""
        task = Task(title="Test Task")
        
        events = task.events
        assert len(events) == 1
        assert events[0].event_type == "EntityCreated"
        assert events[0].entity_id == task.id
        assert events[0].entity_type == "Task"


class TestTaskValidation:
    """Tests for Task validation rules."""
    
    def test_rejects_title_too_short(self) -> None:
        """Test that titles < 3 chars are rejected."""
        with pytest.raises(ValidationError, match="Title must be 3-100 characters"):
            Task(title="AB")
    
    def test_rejects_title_too_long(self) -> None:
        """Test that titles > 100 chars are rejected."""
        long_title = "A" * 101
        with pytest.raises(ValidationError, match="Title must be 3-100 characters"):
            Task(title=long_title)
    
    def test_accepts_title_boundary_values(self) -> None:
        """Test that boundary values are accepted."""
        # Min length
        task_min = Task(title="ABC")
        assert task_min.title == "ABC"
        
        # Max length
        task_max = Task(title="A" * 100)
        assert len(task_max.title) == 100
    
    def test_rejects_description_too_long(self) -> None:
        """Test that descriptions > 1000 chars are rejected."""
        long_desc = "A" * 1001
        with pytest.raises(ValidationError, match="Description max 1000 characters"):
            Task(title="Valid", description=long_desc)
    
    def test_accepts_empty_description(self) -> None:
        """Test that empty description is allowed."""
        task = Task(title="Valid Title")
        assert task.description == ""


class TestTaskStateTransitions:
    """Tests for Task state machine."""
    
    def test_start_transitions_to_in_progress(self) -> None:
        """Test starting a pending task."""
        task = Task(title="Test Task")
        
        task.start()
        
        assert task.status == "in_progress"
        assert task.version == 1
    
    def test_start_records_event(self) -> None:
        """Test that start() records an event."""
        task = Task(title="Test Task")
        task.clear_events()  # Clear creation event
        
        task.start()
        
        events = task.events
        assert len(events) == 1
        assert events[0].event_type == "EntityUpdated"
        assert events[0].changes == {"status": "in_progress"}
    
    def test_cannot_start_in_progress_task(self) -> None:
        """Test that starting an in-progress task fails."""
        task = Task(title="Test Task")
        task.start()
        
        with pytest.raises(InvalidStateTransition):
            task.start()
    
    def test_complete_from_pending(self) -> None:
        """Test completing a pending task."""
        task = Task(title="Test Task")
        
        task.complete()
        
        assert task.status == "completed"
    
    def test_complete_from_in_progress(self) -> None:
        """Test completing an in-progress task."""
        task = Task(title="Test Task")
        task.start()
        
        task.complete()
        
        assert task.status == "completed"
        assert task.version == 2  # start + complete
    
    def test_cannot_complete_cancelled_task(self) -> None:
        """Test that completed tasks cannot be completed again."""
        task = Task(title="Test Task")
        task.cancel()
        
        with pytest.raises(InvalidStateTransition):
            task.complete()
    
    def test_cancel_pending_task(self) -> None:
        """Test cancelling a pending task."""
        task = Task(title="Test Task")
        
        task.cancel()
        
        assert task.status == "cancelled"
    
    def test_cancel_in_progress_task(self) -> None:
        """Test cancelling an in-progress task."""
        task = Task(title="Test Task")
        task.start()
        
        task.cancel()
        
        assert task.status == "cancelled"
    
    def test_cannot_cancel_completed_task(self) -> None:
        """Test that completed tasks cannot be cancelled."""
        task = Task(title="Test Task")
        task.complete()
        
        with pytest.raises(InvalidStateTransition, match="Cannot cancel completed task"):
            task.cancel()


class TestEventManagement:
    """Tests for domain event management."""
    
    def test_clear_events_returns_and_removes(self) -> None:
        """Test that clear_events() returns events and clears list."""
        task = Task(title="Test Task")
        task.start()
        
        # Should have 2 events (creation + start)
        assert len(task.events) == 2
        
        # Clear and get
        events = task.clear_events()
        assert len(events) == 2
        assert len(task.events) == 0
    
    def test_events_property_is_copy(self) -> None:
        """Test that events property returns a copy."""
        task = Task(title="Test Task")
        
        events1 = task.events
        events2 = task.events
        
        # Should be equal but not same object
        assert events1 == events2
        assert events1 is not events2
```

**Validar Domain Layer:**
```bash
cd /home/juan/vertice-dev/backend/service_template

# Run tests
uv run pytest tests/unit/test_domain_models.py -v --cov=src/service_template/domain/models.py

# EXPECTED: 100% coverage, all tests pass

# Type check
uv run mypy src/service_template/domain/

# Lint
uv run ruff check src/service_template/domain/
```

**Checkpoint Dia 11:**
```bash
git add service_template/src/service_template/domain/
git add service_template/tests/unit/test_domain_models.py
git commit -m "feat(template): implement domain layer with Task entity"
```

---

## DIA 12-13: Application + Infrastructure Layers

(Implementar use cases, repositories, database models, HTTP clients...)

---

## DIA 14: Presentation Layer + Main

(Implementar FastAPI endpoints, schemas, dependencies, main.py)

---

## DIAS 15-16: Documentação e Testing

**Deliverables:**
- README completo com examples
- Guia de uso do template
- E2E tests
- Docker build validado

---

## DIAS 17-30: Migração de Serviços

**Prioridade de Migração:**

1. **api_gateway** (Dias 17-18)
2. **osint_service** (Dias 19-20)
3. **maximus_core** → decomposição (Dias 21-26)
4. **active_immune_core** (Dias 27-28)
5. **consciousness_api** (Dias 29-30)

**Processo por Serviço:**

### Dia N: Análise
1. Documentar dependências atuais
2. Identificar bounded contexts
3. Criar ADR
4. Definir API (OpenAPI)

### Dia N+1: Migração
1. Copiar template
2. Implementar domain
3. Implementar application
4. Implementar infrastructure
5. Implementar presentation
6. Testes (unit + integration + e2e)
7. Validação tripla
8. Deploy staging

**Critérios de Validação por Serviço:**
- [ ] Coverage ≥90%
- [ ] Linting pass
- [ ] Type check pass
- [ ] Zero TODO/FIXME
- [ ] Performance: p95 ≤ antigo +10%
- [ ] Load test: 1000 req/s

---

## VALIDAÇÃO FINAL TRACK 3

```bash
# Template funcional
cd backend/service_template
uv run pytest --cov --cov-fail-under=90
docker build -t template-test .

# 10 serviços migrados
for svc in api_gateway osint_service ...; do
    cd backend/services/$svc
    uv run pytest --cov --cov-fail-under=90 || exit 1
done

echo "✅ TRACK 3 COMPLETO"
```

**Entregáveis:**
- [ ] Service template production-ready
- [ ] 10 serviços migrados
- [ ] Documentação completa
- [ ] E2E tests passando
- [ ] PR aberto

---

**FIM DO TRACK 3 = FIM DA TRANSFORMAÇÃO BACKEND**
