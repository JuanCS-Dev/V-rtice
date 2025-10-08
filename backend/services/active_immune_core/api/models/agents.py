"""Agent API Models - PRODUCTION-READY

Pydantic models for agent-related endpoints.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Request model for creating a new agent"""

    agent_type: str = Field(..., description="Type of agent (neutrophil, macrophage, etc.)")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "neutrophil",
                "config": {
                    "detection_threshold": 0.7,
                    "energy_cost": 0.1,
                },
            }
        }


class AgentUpdate(BaseModel):
    """Request model for updating an agent"""

    status: Optional[str] = Field(None, description="Agent status")
    health: Optional[float] = Field(None, ge=0.0, le=1.0, description="Health score (0.0-1.0)")
    load: Optional[float] = Field(None, ge=0.0, le=1.0, description="Load (0.0-1.0)")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "active",
                "health": 0.95,
                "load": 0.65,
            }
        }


class AgentResponse(BaseModel):
    """Response model for agent information"""

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent")
    status: str = Field(..., description="Current status")
    health: float = Field(..., description="Health score (0.0-1.0)")
    load: float = Field(..., description="Current load (0.0-1.0)")
    energia: float = Field(..., description="Energy level (0.0-1.0)")
    deteccoes_total: int = Field(..., description="Total detections")
    neutralizacoes_total: int = Field(..., description="Total neutralizations")
    falsos_positivos: int = Field(..., description="Total false positives")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_neutrophil_001",
                "agent_type": "neutrophil",
                "status": "active",
                "health": 0.95,
                "load": 0.65,
                "energia": 0.88,
                "deteccoes_total": 42,
                "neutralizacoes_total": 38,
                "falsos_positivos": 2,
                "created_at": "2025-10-06T10:30:00",
                "updated_at": "2025-10-06T12:45:00",
            }
        }


class AgentListResponse(BaseModel):
    """Response model for list of agents"""

    total: int = Field(..., description="Total number of agents")
    agents: List[AgentResponse] = Field(..., description="List of agents")
    by_type: Dict[str, int] = Field(..., description="Agent count by type")
    by_status: Dict[str, int] = Field(..., description="Agent count by status")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "agents": [],
                "by_type": {
                    "neutrophil": 4,
                    "macrophage": 3,
                    "nk_cell": 2,
                    "dendritic": 1,
                },
                "by_status": {
                    "active": 9,
                    "inactive": 1,
                },
            }
        }


class AgentStatsResponse(BaseModel):
    """Response model for agent statistics"""

    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    total_tasks: int = Field(..., description="Total tasks executed")
    tasks_completed: int = Field(..., description="Tasks completed successfully")
    tasks_failed: int = Field(..., description="Tasks failed")
    success_rate: float = Field(..., description="Success rate (0.0-1.0)")
    average_task_duration: float = Field(..., description="Average task duration in seconds")
    detections_total: int = Field(..., description="Total detections")
    neutralizations_total: int = Field(..., description="Total neutralizations")
    false_positives: int = Field(..., description="Total false positives")
    uptime_seconds: float = Field(..., description="Agent uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_neutrophil_001",
                "agent_type": "neutrophil",
                "total_tasks": 100,
                "tasks_completed": 95,
                "tasks_failed": 5,
                "success_rate": 0.95,
                "average_task_duration": 2.3,
                "detections_total": 42,
                "neutralizations_total": 38,
                "false_positives": 2,
                "uptime_seconds": 3600.0,
            }
        }


class AgentAction(BaseModel):
    """Request model for agent actions"""

    action: str = Field(..., description="Action to perform (start, stop, pause, resume)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "start",
                "parameters": {},
            }
        }


class AgentActionResponse(BaseModel):
    """Response model for agent actions"""

    agent_id: str = Field(..., description="Agent identifier")
    action: str = Field(..., description="Action performed")
    success: bool = Field(..., description="Whether action was successful")
    message: str = Field(..., description="Result message")
    new_status: Optional[str] = Field(None, description="New agent status")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_neutrophil_001",
                "action": "start",
                "success": True,
                "message": "Agent started successfully",
                "new_status": "active",
            }
        }
