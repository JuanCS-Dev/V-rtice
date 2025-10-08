"""Coordination API Models - PRODUCTION-READY

Pydantic models for coordination-related endpoints.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Request model for creating a new task"""

    task_type: str = Field(..., description="Type of task (detection, neutralization, etc.)")
    priority: int = Field(5, ge=1, le=10, description="Task priority (1-10)")
    target: Optional[str] = Field(None, description="Target identifier")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Task parameters")
    timeout: Optional[float] = Field(None, gt=0, description="Task timeout in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "detection",
                "priority": 8,
                "target": "suspicious_process_123",
                "parameters": {
                    "threshold": 0.7,
                    "scan_depth": "deep",
                },
                "timeout": 30.0,
            }
        }


class TaskResponse(BaseModel):
    """Response model for task information"""

    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of task")
    status: str = Field(..., description="Task status (pending/assigned/running/completed/failed)")
    priority: int = Field(..., description="Task priority")
    assigned_agent: Optional[str] = Field(None, description="ID of agent assigned to task")
    target: Optional[str] = Field(None, description="Target identifier")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="Creation timestamp")
    assigned_at: Optional[str] = Field(None, description="Assignment timestamp")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    duration: Optional[float] = Field(None, description="Task duration in seconds")
    retries: int = Field(0, description="Number of retries")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_detection_001",
                "task_type": "detection",
                "status": "completed",
                "priority": 8,
                "assigned_agent": "agent_neutrophil_001",
                "target": "suspicious_process_123",
                "result": {
                    "threat_detected": True,
                    "confidence": 0.92,
                },
                "error": None,
                "created_at": "2025-10-06T10:30:00",
                "assigned_at": "2025-10-06T10:30:01",
                "started_at": "2025-10-06T10:30:02",
                "completed_at": "2025-10-06T10:30:05",
                "duration": 3.0,
                "retries": 0,
            }
        }


class TaskListResponse(BaseModel):
    """Response model for list of tasks"""

    total: int = Field(..., description="Total number of tasks")
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    by_status: Dict[str, int] = Field(..., description="Task count by status")
    by_type: Dict[str, int] = Field(..., description="Task count by type")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 50,
                "tasks": [],
                "by_status": {
                    "pending": 5,
                    "assigned": 10,
                    "running": 15,
                    "completed": 18,
                    "failed": 2,
                },
                "by_type": {
                    "detection": 25,
                    "neutralization": 20,
                    "analysis": 5,
                },
            }
        }


class ElectionResponse(BaseModel):
    """Response model for leader election information"""

    has_leader: bool = Field(..., description="Whether system has a leader")
    leader_id: Optional[str] = Field(None, description="ID of current leader")
    election_term: int = Field(..., description="Current election term")
    last_election: Optional[str] = Field(None, description="Last election timestamp")
    total_elections: int = Field(..., description="Total elections performed")
    leader_changes: int = Field(..., description="Total leader changes")
    eligible_voters: int = Field(..., description="Number of eligible voters")

    class Config:
        json_schema_extra = {
            "example": {
                "has_leader": True,
                "leader_id": "agent_neutrophil_001",
                "election_term": 5,
                "last_election": "2025-10-06T10:00:00",
                "total_elections": 8,
                "leader_changes": 3,
                "eligible_voters": 10,
            }
        }


class ConsensusProposal(BaseModel):
    """Request model for consensus proposal"""

    proposal_type: str = Field(..., description="Type of proposal (agent_addition, task_assignment, etc.)")
    proposal_data: Dict[str, Any] = Field(..., description="Proposal data")
    proposer_id: str = Field(..., description="ID of agent making proposal")
    timeout: Optional[float] = Field(30.0, gt=0, description="Proposal timeout in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "proposal_type": "agent_addition",
                "proposal_data": {
                    "agent_type": "macrophage",
                    "reason": "High system load",
                },
                "proposer_id": "agent_neutrophil_001",
                "timeout": 30.0,
            }
        }


class ConsensusResponse(BaseModel):
    """Response model for consensus proposal result"""

    proposal_id: str = Field(..., description="Unique proposal identifier")
    proposal_type: str = Field(..., description="Type of proposal")
    status: str = Field(..., description="Proposal status (pending/approved/rejected/timeout)")
    votes_for: int = Field(..., description="Number of votes in favor")
    votes_against: int = Field(..., description="Number of votes against")
    votes_abstain: int = Field(..., description="Number of abstentions")
    total_voters: int = Field(..., description="Total eligible voters")
    approval_rate: float = Field(..., description="Approval rate (0.0-1.0)")
    created_at: str = Field(..., description="Proposal creation timestamp")
    decided_at: Optional[str] = Field(None, description="Decision timestamp")
    decision_duration: Optional[float] = Field(None, description="Time to decision in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "proposal_id": "proposal_001",
                "proposal_type": "agent_addition",
                "status": "approved",
                "votes_for": 8,
                "votes_against": 1,
                "votes_abstain": 1,
                "total_voters": 10,
                "approval_rate": 0.8,
                "created_at": "2025-10-06T10:30:00",
                "decided_at": "2025-10-06T10:30:15",
                "decision_duration": 15.0,
            }
        }


class CoordinationStatus(BaseModel):
    """Response model for overall coordination status"""

    has_leader: bool = Field(..., description="Whether system has a leader")
    leader_id: Optional[str] = Field(None, description="Current leader ID")
    total_agents: int = Field(..., description="Total agents in system")
    alive_agents: int = Field(..., description="Number of alive agents")
    tasks_pending: int = Field(..., description="Number of pending tasks")
    tasks_assigned: int = Field(..., description="Number of assigned tasks")
    tasks_running: int = Field(..., description="Number of running tasks")
    average_agent_health: float = Field(..., description="Average agent health score")
    average_agent_load: float = Field(..., description="Average agent load")
    system_health: str = Field(..., description="Overall system health status")

    class Config:
        json_schema_extra = {
            "example": {
                "has_leader": True,
                "leader_id": "agent_neutrophil_001",
                "total_agents": 10,
                "alive_agents": 9,
                "tasks_pending": 5,
                "tasks_assigned": 10,
                "tasks_running": 15,
                "average_agent_health": 0.88,
                "average_agent_load": 0.65,
                "system_health": "healthy",
            }
        }


# ==================== LYMPHNODE MODELS ====================


class CloneRequest(BaseModel):
    """Request model for cloning an agent"""

    agent_id: str = Field(..., description="ID of agent to clone")
    especializacao: Optional[str] = Field(None, description="Specialization for clone")
    num_clones: int = Field(1, ge=1, le=10, description="Number of clones to create (1-10)")
    mutate: bool = Field(True, description="Apply somatic hypermutation")
    mutation_rate: float = Field(0.1, ge=0.0, le=1.0, description="Mutation rate (0.0-1.0)")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "macrofago_001",
                "especializacao": "threat_192_168_1_50",
                "num_clones": 5,
                "mutate": True,
                "mutation_rate": 0.15,
            }
        }


class CloneResponse(BaseModel):
    """Response model for clone creation"""

    parent_id: str = Field(..., description="ID of parent agent")
    clone_ids: List[str] = Field(..., description="IDs of created clones")
    num_clones: int = Field(..., description="Number of clones created")
    especializacao: Optional[str] = Field(None, description="Specialization applied")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "parent_id": "macrofago_001",
                "clone_ids": [
                    "macrofago_clone_001",
                    "macrofago_clone_002",
                    "macrofago_clone_003",
                ],
                "num_clones": 3,
                "especializacao": "threat_192_168_1_50",
                "created_at": "2025-10-06T10:30:00",
            }
        }


class LymphnodeMetrics(BaseModel):
    """Response model for lymphnode metrics"""

    lymphnode_id: str = Field(..., description="Lymphnode identifier")
    nivel: str = Field(..., description="Hierarchy level (local/regional/global)")
    area_responsabilidade: str = Field(..., description="Area of responsibility")
    homeostatic_state: str = Field(..., description="Current homeostatic state")
    temperatura_regional: float = Field(..., description="Regional temperature")
    agentes_ativos: int = Field(..., description="Number of active agents")
    agentes_dormindo: int = Field(..., description="Number of sleeping agents")
    total_ameacas_detectadas: int = Field(..., description="Total threats detected")
    total_neutralizacoes: int = Field(..., description="Total neutralizations")
    total_clones_criados: int = Field(..., description="Total clones created")
    total_clones_destruidos: int = Field(..., description="Total clones destroyed")

    class Config:
        json_schema_extra = {
            "example": {
                "lymphnode_id": "lymphnode_regional_001",
                "nivel": "regional",
                "area_responsabilidade": "zone_us_east_1a",
                "homeostatic_state": "ATENÇÃO",
                "temperatura_regional": 37.8,
                "agentes_ativos": 45,
                "agentes_dormindo": 5,
                "total_ameacas_detectadas": 120,
                "total_neutralizacoes": 98,
                "total_clones_criados": 25,
                "total_clones_destruidos": 10,
            }
        }


class HomeostaticStateResponse(BaseModel):
    """Response model for homeostatic state"""

    homeostatic_state: str = Field(..., description="Current homeostatic state")
    temperatura_regional: float = Field(..., description="Regional temperature")
    description: str = Field(..., description="State description")
    recommended_action: str = Field(..., description="Recommended action")

    class Config:
        json_schema_extra = {
            "example": {
                "homeostatic_state": "ATIVAÇÃO",
                "temperatura_regional": 38.5,
                "description": "System under moderate stress, activation recommended",
                "recommended_action": "Increase agent count and activate clonal expansion",
            }
        }
