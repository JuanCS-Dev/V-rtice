# 📅 Scheduler Dashboard - Blueprint Técnico

> **Status:** Blueprint - Pronto para implementação
> **Prioridade:** CRITICAL - Epic 0
> **Timeline:** 2025-10-06 (Amanhã) - 10-12h full focus
> **Issue:** https://github.com/JuanCS-Dev/V-rtice/issues/2

---

## 1. VISÃO GERAL

### Objetivo
Dashboard tipo calendário para automação e agendamento de tasks, varreduras OSINT, análises de malware, manutenções preventivas e workflows Maximus AI.

### Casos de Uso Principais
1. **Agendamento de Varreduras:** OSINT domains, IP intel, malware analysis
2. **Manutenções Automáticas:** Container cleanup, DB optimization, cache purge
3. **Workflows Maximus:** Autonomous mode scheduling, periodic analysis
4. **Immunis Scans:** Periodic threat detection and response
5. **Reports Automáticos:** Daily/weekly security reports

---

## 2. DECISÕES ARQUITETURAIS

### Stack Tecnológico

#### Backend
- **Framework:** FastAPI (consistente com outros serviços)
- **Scheduler Engine:** **APScheduler** ✅
  - Razão: Python-native, persistent JobStore, cron support
  - Alternativas descartadas:
    - Celery Beat (overhead para caso de uso)
    - RQ (sem cron nativo)
    - Dramatiq (menos maduro)
- **Storage:** PostgreSQL + SQLAlchemy (jobs persistentes)
- **Job Queue:** Redis (para execução assíncrona)

#### Frontend
- **Calendar Library:** **react-big-calendar** ✅
  - Razão: Popular, customizável, views month/week/day
  - Alternativas: FullCalendar (pago para features avançadas)
- **Date Utils:** date-fns (leve, tree-shakeable)
- **State:** React Query (cache + sync)
- **Forms:** React Hook Form + Zod validation

#### vCLI
- **Command:** `vcli schedule` (principal)
- **Subcommands:** list, create, run, enable, disable, history
- **Interactive:** Questionary para task creation wizard

---

## 3. DATA MODELS

### Database Schema (SQLAlchemy)

```python
# backend/services/scheduler_service/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class ScheduleType(str, enum.Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))

    # Scheduling
    schedule_type = Column(Enum(ScheduleType), nullable=False)
    cron_expression = Column(String(100))  # "0 2 * * *" for recurring
    run_at = Column(DateTime)  # For one_time tasks

    # Task configuration
    task_type = Column(String(100), nullable=False)  # osint_scan, malware_check, etc
    task_config = Column(JSON, nullable=False)  # Task-specific parameters

    # State
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)

    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # APScheduler job ID (for job management)
    job_id = Column(String(100), unique=True)

class TaskExecution(Base):
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False)  # FK to scheduled_tasks

    # Execution state
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Results
    result = Column(JSON)  # Success response
    error_message = Column(String(2000))  # Failure details

    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
```

---

## 4. API SPECIFICATION

### REST Endpoints

```python
# backend/services/scheduler_service/main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Scheduler Service", version="1.0.0")

# === DTOs ===

class TaskConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    schedule_type: ScheduleType
    cron_expression: Optional[str] = None  # Required if recurring
    run_at: Optional[datetime] = None  # Required if one_time
    task_type: str
    task_config: dict
    enabled: bool = True

class TaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schedule_type: ScheduleType
    cron_expression: Optional[str]
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    enabled: bool
    task_type: str
    created_at: datetime

class ExecutionResponse(BaseModel):
    id: int
    task_id: int
    status: TaskStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[dict]
    error_message: Optional[str]

# === Routes ===

@app.post("/api/scheduler/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskConfigBase):
    """Create a new scheduled task."""
    pass

@app.get("/api/scheduler/tasks", response_model=List[TaskResponse])
async def list_tasks(
    enabled: Optional[bool] = None,
    task_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List all scheduled tasks with optional filters."""
    pass

@app.get("/api/scheduler/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Get task details by ID."""
    pass

@app.put("/api/scheduler/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskConfigBase):
    """Update an existing task (recreates APScheduler job)."""
    pass

@app.delete("/api/scheduler/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    """Delete a task and its APScheduler job."""
    pass

@app.post("/api/scheduler/tasks/{task_id}/run", response_model=ExecutionResponse)
async def trigger_task(task_id: int):
    """Manually trigger a task execution (bypass schedule)."""
    pass

@app.post("/api/scheduler/tasks/{task_id}/enable", status_code=200)
async def enable_task(task_id: int):
    """Enable a disabled task."""
    pass

@app.post("/api/scheduler/tasks/{task_id}/disable", status_code=200)
async def disable_task(task_id: int):
    """Disable a task (removes from APScheduler queue)."""
    pass

@app.get("/api/scheduler/executions", response_model=List[ExecutionResponse])
async def list_executions(
    task_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 100,
    offset: int = 0
):
    """List task execution history."""
    pass

@app.get("/api/scheduler/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: int):
    """Get execution details by ID."""
    pass
```

---

## 5. TASK REGISTRY

### Tipos de Tasks Suportados (Inicial)

```python
# backend/services/scheduler_service/task_registry.py

from typing import Dict, Callable, Any
import httpx

class TaskRegistry:
    """Registry of available task types and their executors."""

    def __init__(self):
        self.tasks: Dict[str, Callable] = {
            'osint_domain_scan': self.execute_osint_scan,
            'malware_hash_check': self.execute_malware_check,
            'ip_threat_intel': self.execute_ip_intel,
            'container_cleanup': self.execute_container_cleanup,
            'maximus_autopilot': self.execute_maximus_workflow,
        }

    async def execute_task(self, task_type: str, config: dict) -> dict:
        """Execute a task based on its type."""
        if task_type not in self.tasks:
            raise ValueError(f"Unknown task type: {task_type}")

        executor = self.tasks[task_type]
        return await executor(config)

    # === Task Executors ===

    async def execute_osint_scan(self, config: dict) -> dict:
        """Execute OSINT domain scan via osint_service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://osint-service:8080/api/scan/domain",
                json={
                    "domain": config["domain"],
                    "depth": config.get("depth", 2)
                },
                timeout=300.0
            )
            response.raise_for_status()
            return response.json()

    async def execute_malware_check(self, config: dict) -> dict:
        """Execute malware hash check via malware_analysis_service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://malware-analysis:8003/api/analyze/hash",
                json={"hash": config["hash"]},
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()

    async def execute_ip_intel(self, config: dict) -> dict:
        """Execute IP threat intelligence check."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://ip-intelligence:8002/api/check",
                json={
                    "ip": config["ip"],
                    "check_blacklists": config.get("check_blacklists", True)
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def execute_container_cleanup(self, config: dict) -> dict:
        """Execute Docker container cleanup (maintenance)."""
        import docker
        client = docker.from_env()

        # Remove stopped containers older than max_age_days
        max_age = config.get("max_age_days", 7)
        removed = []

        for container in client.containers.list(all=True):
            if container.status == "exited":
                # Check age logic here
                container.remove()
                removed.append(container.name)

        return {"removed_containers": removed, "count": len(removed)}

    async def execute_maximus_workflow(self, config: dict) -> dict:
        """Execute Maximus AI autonomous workflow."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://maximus-core:8001/api/workflow/execute",
                json={
                    "workflow_id": config["workflow_id"],
                    "parameters": config.get("parameters", {})
                },
                timeout=600.0
            )
            response.raise_for_status()
            return response.json()
```

---

## 6. SCHEDULER ENGINE

### APScheduler Configuration

```python
# backend/services/scheduler_service/scheduler_engine.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SchedulerEngine:
    """Manages APScheduler for task execution."""

    def __init__(self, database_url: str):
        jobstores = {
            'default': SQLAlchemyJobStore(url=database_url)
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=10)
        }
        job_defaults = {
            'coalesce': False,  # Run all missed jobs
            'max_instances': 3,  # Max concurrent instances per job
            'misfire_grace_time': 300  # 5 min grace period
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )

    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown")

    async def add_task(self, task_id: int, schedule_type: str,
                       cron_expr: str = None, run_at: datetime = None,
                       task_executor: callable = None) -> str:
        """Add a task to the scheduler."""

        if schedule_type == "recurring":
            trigger = CronTrigger.from_crontab(cron_expr)
        elif schedule_type == "one_time":
            trigger = DateTrigger(run_date=run_at)
        else:
            raise ValueError(f"Invalid schedule_type: {schedule_type}")

        job = self.scheduler.add_job(
            func=task_executor,
            trigger=trigger,
            id=f"task_{task_id}",
            name=f"Task {task_id}",
            replace_existing=True
        )

        logger.info(f"Added job {job.id} with trigger {trigger}")
        return job.id

    def remove_task(self, job_id: str):
        """Remove a task from the scheduler."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")

    def pause_task(self, job_id: str):
        """Pause a task temporarily."""
        self.scheduler.pause_job(job_id)
        logger.info(f"Paused job {job_id}")

    def resume_task(self, job_id: str):
        """Resume a paused task."""
        self.scheduler.resume_job(job_id)
        logger.info(f"Resumed job {job_id}")

    def get_next_run_time(self, job_id: str) -> datetime:
        """Get the next scheduled run time for a job."""
        job = self.scheduler.get_job(job_id)
        return job.next_run_time if job else None
```

---

## 7. FRONTEND COMPONENTS

### React Component Structure

```
frontend/src/components/scheduler/
├── SchedulerDashboard.jsx       # Main container
├── CalendarView.jsx              # Calendar display
├── TaskCreationModal.jsx         # Create/edit task modal
├── TaskTypeSelector.jsx          # Task type picker
├── CronBuilder.jsx               # Visual cron expression builder
├── TaskConfigForm.jsx            # Dynamic form based on task type
├── ExecutionHistoryPanel.jsx    # Sidebar with execution history
├── ExecutionCard.jsx             # Individual execution display
└── QuickActionsToolbar.jsx      # Bulk actions, filters, etc
```

### CalendarView Component

```jsx
// frontend/src/components/scheduler/CalendarView.jsx

import React, { useState, useCallback } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { useQuery } from '@tanstack/react-query';
import { fetchScheduledTasks } from '../../api/scheduler';

const localizer = momentLocalizer(moment);

export default function CalendarView({ onSelectEvent, onSelectSlot }) {
  const [view, setView] = useState('month'); // month, week, day

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['scheduled-tasks'],
    queryFn: fetchScheduledTasks,
    refetchInterval: 30000 // Refresh every 30s
  });

  // Transform tasks to calendar events
  const events = tasks?.map(task => ({
    id: task.id,
    title: task.name,
    start: new Date(task.next_run),
    end: new Date(task.next_run),
    resource: task,
    backgroundColor: getTaskColor(task.task_type)
  })) || [];

  const handleSelectEvent = useCallback((event) => {
    onSelectEvent(event.resource);
  }, [onSelectEvent]);

  const handleSelectSlot = useCallback((slotInfo) => {
    onSelectSlot(slotInfo.start);
  }, [onSelectSlot]);

  return (
    <div className="calendar-container" style={{ height: '700px' }}>
      <Calendar
        localizer={localizer}
        events={events}
        view={view}
        onView={setView}
        onSelectEvent={handleSelectEvent}
        onSelectSlot={handleSelectSlot}
        selectable
        eventPropGetter={(event) => ({
          style: {
            backgroundColor: event.backgroundColor,
            borderRadius: '5px',
            opacity: 0.8,
            color: 'white',
            border: '0px',
            display: 'block'
          }
        })}
      />
    </div>
  );
}

function getTaskColor(taskType) {
  const colors = {
    osint_domain_scan: '#3498db',    // Blue
    malware_hash_check: '#e74c3c',   // Red
    ip_threat_intel: '#9b59b6',      // Purple
    container_cleanup: '#95a5a6',    // Gray
    maximus_autopilot: '#2ecc71',    // Green
  };
  return colors[taskType] || '#34495e';
}
```

### CronBuilder Component

```jsx
// frontend/src/components/scheduler/CronBuilder.jsx

import React, { useState, useEffect } from 'react';
import cronstrue from 'cronstrue';

export default function CronBuilder({ value, onChange }) {
  const [preset, setPreset] = useState('custom');
  const [cronParts, setCronParts] = useState({
    minute: '*',
    hour: '*',
    dayOfMonth: '*',
    month: '*',
    dayOfWeek: '*'
  });

  const presets = {
    daily: '0 2 * * *',         // Every day at 2 AM
    hourly: '0 * * * *',         // Every hour
    weekly: '0 2 * * 0',         // Every Sunday at 2 AM
    monthly: '0 2 1 * *',        // First day of month at 2 AM
    custom: value || '* * * * *'
  };

  useEffect(() => {
    const cronExpr = preset === 'custom'
      ? Object.values(cronParts).join(' ')
      : presets[preset];
    onChange(cronExpr);
  }, [preset, cronParts]);

  const cronExpression = preset === 'custom'
    ? Object.values(cronParts).join(' ')
    : presets[preset];

  const humanReadable = cronstrue.toString(cronExpression, { use24HourTimeFormat: true });

  return (
    <div className="cron-builder">
      <div className="preset-selector">
        <label>Preset:</label>
        <select value={preset} onChange={(e) => setPreset(e.target.value)}>
          <option value="daily">Daily (2 AM)</option>
          <option value="hourly">Hourly</option>
          <option value="weekly">Weekly (Sunday 2 AM)</option>
          <option value="monthly">Monthly (1st day, 2 AM)</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      {preset === 'custom' && (
        <div className="cron-fields">
          <input placeholder="Minute" value={cronParts.minute}
                 onChange={(e) => setCronParts({...cronParts, minute: e.target.value})} />
          <input placeholder="Hour" value={cronParts.hour}
                 onChange={(e) => setCronParts({...cronParts, hour: e.target.value})} />
          <input placeholder="Day" value={cronParts.dayOfMonth}
                 onChange={(e) => setCronParts({...cronParts, dayOfMonth: e.target.value})} />
          <input placeholder="Month" value={cronParts.month}
                 onChange={(e) => setCronParts({...cronParts, month: e.target.value})} />
          <input placeholder="Weekday" value={cronParts.dayOfWeek}
                 onChange={(e) => setCronParts({...cronParts, dayOfWeek: e.target.value})} />
        </div>
      )}

      <div className="cron-preview">
        <strong>Expression:</strong> <code>{cronExpression}</code>
        <br />
        <strong>Meaning:</strong> {humanReadable}
      </div>
    </div>
  );
}
```

---

## 8. vCLI INTEGRATION

### Command Structure

```python
# vertice-terminal/vertice/commands/schedule.py

import click
from rich.console import Console
from rich.table import Table
from vertice.connectors.scheduler import SchedulerConnector
import questionary

console = Console()
scheduler = SchedulerConnector()

@click.group()
def schedule():
    """Manage scheduled tasks and automation."""
    pass

@schedule.command()
@click.option('--enabled/--disabled', default=None, help='Filter by enabled status')
@click.option('--type', help='Filter by task type')
def list(enabled, type):
    """List all scheduled tasks."""
    tasks = scheduler.list_tasks(enabled=enabled, task_type=type)

    table = Table(title="Scheduled Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("Schedule", style="magenta")
    table.add_column("Next Run", style="green")
    table.add_column("Status", style="bold")

    for task in tasks:
        status_color = "green" if task['enabled'] else "red"
        status_text = "✓ Enabled" if task['enabled'] else "✗ Disabled"

        table.add_row(
            str(task['id']),
            task['name'],
            task['task_type'],
            task['cron_expression'] or 'One-time',
            task['next_run'] or 'N/A',
            f"[{status_color}]{status_text}[/{status_color}]"
        )

    console.print(table)

@schedule.command()
def create():
    """Interactive task creation wizard."""

    # Task type selection
    task_type = questionary.select(
        "Select task type:",
        choices=[
            "osint_domain_scan",
            "malware_hash_check",
            "ip_threat_intel",
            "container_cleanup",
            "maximus_autopilot"
        ]
    ).ask()

    # Basic info
    name = questionary.text("Task name:").ask()
    description = questionary.text("Description (optional):", default="").ask()

    # Schedule type
    schedule_type = questionary.select(
        "Schedule type:",
        choices=["Recurring (cron)", "One-time"]
    ).ask()

    if schedule_type == "Recurring (cron)":
        cron_expr = questionary.text("Cron expression (e.g., '0 2 * * *'):").ask()
        schedule_data = {"cron_expression": cron_expr}
    else:
        run_at = questionary.text("Run at (YYYY-MM-DD HH:MM):").ask()
        schedule_data = {"run_at": run_at}

    # Task-specific config (dynamic based on task_type)
    task_config = get_task_config_interactive(task_type)

    # Create task
    result = scheduler.create_task(
        name=name,
        description=description,
        task_type=task_type,
        schedule_type="recurring" if "cron" in schedule_data else "one_time",
        **schedule_data,
        task_config=task_config
    )

    console.print(f"[green]✓ Task created: {result['id']}[/green]")

@schedule.command()
@click.argument('task_id', type=int)
def run(task_id):
    """Manually trigger a task execution."""
    execution = scheduler.trigger_task(task_id)
    console.print(f"[green]✓ Task triggered. Execution ID: {execution['id']}[/green]")

@schedule.command()
@click.argument('task_id', type=int)
@click.option('--limit', default=10, help='Number of executions to show')
def history(task_id, limit):
    """Show execution history for a task."""
    executions = scheduler.get_executions(task_id=task_id, limit=limit)

    table = Table(title=f"Execution History - Task {task_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Started", style="white")
    table.add_column("Duration", style="yellow")
    table.add_column("Result", style="green")

    for exec in executions:
        status_color = {
            "success": "green",
            "failed": "red",
            "running": "yellow",
            "pending": "gray"
        }.get(exec['status'], "white")

        duration = calculate_duration(exec['started_at'], exec['completed_at'])
        result_summary = exec['error_message'] if exec['status'] == 'failed' else 'OK'

        table.add_row(
            str(exec['id']),
            f"[{status_color}]{exec['status'].upper()}[/{status_color}]",
            exec['started_at'] or 'N/A',
            duration,
            result_summary[:50]
        )

    console.print(table)
```

---

## 9. TESTING STRATEGY

### Unit Tests

```python
# backend/services/scheduler_service/tests/test_scheduler.py

import pytest
from scheduler_engine import SchedulerEngine
from task_registry import TaskRegistry
from datetime import datetime, timedelta

@pytest.fixture
def scheduler_engine():
    return SchedulerEngine("sqlite:///:memory:")

@pytest.fixture
def task_registry():
    return TaskRegistry()

def test_add_recurring_task(scheduler_engine):
    """Test adding a recurring task with cron expression."""
    job_id = await scheduler_engine.add_task(
        task_id=1,
        schedule_type="recurring",
        cron_expr="0 2 * * *",
        task_executor=lambda: print("Test")
    )
    assert job_id == "task_1"

def test_add_one_time_task(scheduler_engine):
    """Test adding a one-time task."""
    run_at = datetime.now() + timedelta(hours=1)
    job_id = await scheduler_engine.add_task(
        task_id=2,
        schedule_type="one_time",
        run_at=run_at,
        task_executor=lambda: print("Test")
    )
    assert job_id == "task_2"

def test_task_execution_osint(task_registry):
    """Test OSINT scan task execution."""
    config = {"domain": "example.com", "depth": 2}
    result = await task_registry.execute_task("osint_domain_scan", config)
    assert "domain" in result
```

### Integration Tests

```python
# backend/services/scheduler_service/tests/test_integration.py

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task_api():
    """Test task creation via API."""
    response = client.post("/api/scheduler/tasks", json={
        "name": "Test OSINT Scan",
        "schedule_type": "recurring",
        "cron_expression": "0 2 * * *",
        "task_type": "osint_domain_scan",
        "task_config": {"domain": "example.com", "depth": 2}
    })
    assert response.status_code == 201
    assert response.json()["id"] > 0

def test_list_tasks_api():
    """Test listing tasks via API."""
    response = client.get("/api/scheduler/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_trigger_task_api():
    """Test manual task trigger."""
    # Create task first
    create_response = client.post("/api/scheduler/tasks", json={...})
    task_id = create_response.json()["id"]

    # Trigger it
    trigger_response = client.post(f"/api/scheduler/tasks/{task_id}/run")
    assert trigger_response.status_code == 200
    assert trigger_response.json()["status"] == "pending"
```

---

## 10. DEPLOYMENT

### Docker Configuration

```dockerfile
# backend/services/scheduler_service/Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8050"]
```

### docker-compose.yml Entry

```yaml
scheduler-service:
  build: ./backend/services/scheduler_service
  container_name: scheduler-service
  ports:
    - "8050:8050"
  environment:
    - DATABASE_URL=postgresql://user:pass@postgres:5432/scheduler
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    - postgres
    - redis
  restart: unless-stopped
```

---

## 11. NEXT STEPS (Implementação Amanhã)

### Fase 1: Brainstorm ✅ DONE
- [x] Stack tecnológico definido
- [x] Casos de uso mapeados
- [x] Benchmarking completo

### Fase 2: Deep Search (2-3h)
- [ ] Estudar APScheduler docs em profundidade
- [ ] Explorar react-big-calendar customization
- [ ] Revisar padrões de retry e error handling
- [ ] Security considerations (RBAC, audit log)

### Fase 3: Paper + Blueprint ✅ DONE
- [x] Data models documentados
- [x] API specs completas
- [x] Component architecture
- [x] vCLI commands

### Fase 4: Implementação (8-12h)
1. **Backend (4-5h)**
   - [ ] Setup FastAPI + SQLAlchemy models
   - [ ] Implement TaskRegistry executors
   - [ ] Configure APScheduler engine
   - [ ] Create REST API endpoints
   - [ ] Add error handling + logging

2. **Frontend (3-4h)**
   - [ ] Install dependencies (react-big-calendar, date-fns, cronstrue)
   - [ ] Create CalendarView component
   - [ ] Build TaskCreationModal + CronBuilder
   - [ ] Implement ExecutionHistoryPanel
   - [ ] API integration with React Query

3. **vCLI (1-2h)**
   - [ ] Create `schedule.py` command file
   - [ ] Implement SchedulerConnector
   - [ ] Build interactive wizards
   - [ ] Pretty-print tables

### Fase 5: Validação (2-3h)
- [ ] Unit tests (scheduler engine, task registry)
- [ ] API endpoint tests
- [ ] Frontend component tests
- [ ] vCLI integration tests

### Fase 6: Testes (1-2h)
- [ ] Manual QA (create, update, delete tasks)
- [ ] End-to-end workflow tests
- [ ] Edge cases (invalid cron, failed execution, etc)
- [ ] Performance tests (100 concurrent tasks)

---

## 12. MÉTRICAS DE SUCESSO

- [ ] Calendar dashboard funcional (month/week/day views)
- [ ] 5 task types implementados e testados
- [ ] `vcli schedule` commands operacionais
- [ ] Execuções aparecem no histórico com logs
- [ ] Tasks recorrentes executam conforme cron
- [ ] One-time tasks executam no horário especificado
- [ ] Retry logic funcionando em caso de falhas
- [ ] API response time <200ms
- [ ] Calendar view load time <2s
- [ ] Zero crashes em 24h de operação contínua

---

**Criado em:** 2025-10-05
**Autor:** Claude Code + JuanCS-Dev
**Próxima Revisão:** 2025-10-06 (início da implementação)
