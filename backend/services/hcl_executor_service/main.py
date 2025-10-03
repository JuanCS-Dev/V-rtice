"""
HCL Executor Service - Main Application
=========================================
Executes HCL decisions on Kubernetes cluster.

Architecture:
1. Consumes actions from Planner (Kafka: system.actions)
2. Validates and executes actions via Kubernetes API
3. Records execution results to Knowledge Base
4. Provides manual override endpoints

Port: 8004
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import httpx
from aiokafka import AIOKafkaConsumer

from k8s_controller import KubernetesController
from action_executor import ActionExecutor, ActionType, ExecutionStatus

# Configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "hcl_executor")
KB_API_URL = os.getenv("KB_API_URL", "http://localhost:8000")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
IN_CLUSTER = os.getenv("IN_CLUSTER", "true").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
ENABLE_ROLLBACK = os.getenv("ENABLE_ROLLBACK", "true").lower() == "true"

# Kafka topics
TOPIC_ACTIONS = "system.actions"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class ActionPlan(BaseModel):
    """Action plan from Planner"""
    decision_id: str
    timestamp: str
    operational_mode: str
    confidence: float = Field(..., ge=0, le=1)
    actions: List[Dict]
    reasoning: str
    expected_impact: Dict


class ScaleRequest(BaseModel):
    """Manual scale request"""
    service: str
    target_replicas: int = Field(..., ge=1, le=20)


class ResourceUpdateRequest(BaseModel):
    """Manual resource update request"""
    service: str
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    cpu_request: Optional[str] = None
    memory_request: Optional[str] = None


class HPARequest(BaseModel):
    """HPA configuration request"""
    service: str
    min_replicas: int = Field(..., ge=1)
    max_replicas: int = Field(..., ge=1)
    target_cpu_utilization: int = Field(70, ge=1, le=100)
    target_memory_utilization: Optional[int] = Field(None, ge=1, le=100)


class ExecutionResponse(BaseModel):
    """Execution response"""
    execution_id: str
    decision_id: str
    status: str
    actions_executed: int
    actions_failed: int
    rollback_performed: bool
    details: Dict


# ============================================================================
# Kafka Integration
# ============================================================================

class KafkaHandler:
    """Handle Kafka consumer for action plans"""

    def __init__(self, action_executor: ActionExecutor):
        self.action_executor = action_executor
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False

    async def start(self):
        """Start Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                TOPIC_ACTIONS,
                bootstrap_servers=KAFKA_BROKERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id=f"{SERVICE_NAME}_group",
                auto_offset_reset='latest'
            )

            await self.consumer.start()

            logger.info(f"Kafka connected: {KAFKA_BROKERS}")
            logger.info(f"Consuming from: {TOPIC_ACTIONS}")

            self.running = True
            asyncio.create_task(self._consume_loop())

        except Exception as e:
            logger.error(f"Failed to start Kafka: {e}")
            raise

    async def stop(self):
        """Stop Kafka consumer"""
        self.running = False

        if self.consumer:
            await self.consumer.stop()

        logger.info("Kafka disconnected")

    async def _consume_loop(self):
        """Main consumption loop"""
        logger.info("Starting action consumption loop")

        try:
            async for msg in self.consumer:
                try:
                    action_plan = msg.value
                    await self._handle_action_plan(action_plan)
                except Exception as e:
                    logger.error(f"Error handling action plan: {e}")
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")

    async def _handle_action_plan(self, action_plan: Dict):
        """Handle incoming action plan"""
        decision_id = action_plan.get("decision_id", "unknown")
        logger.info(f"Received action plan: {decision_id}")

        try:
            # Execute action plan
            result = await self.action_executor.execute_action_plan(
                decision_id=action_plan.get("decision_id"),
                actions=action_plan.get("actions", []),
                operational_mode=action_plan.get("operational_mode", "BALANCED"),
                confidence=action_plan.get("confidence", 0.5)
            )

            # Record to Knowledge Base
            await self._record_execution(result)

            logger.info(
                f"Action plan {decision_id} executed: {result['status']} "
                f"(success={len(result['results'])}, errors={len(result['errors'])})"
            )

        except Exception as e:
            logger.error(f"Error executing action plan {decision_id}: {e}")

    async def _record_execution(self, execution_result: Dict):
        """Record execution result to Knowledge Base"""
        try:
            async with httpx.AsyncClient() as client:
                # Update decision with execution result
                decision_id = execution_result.get("decision_id")

                payload = {
                    "execution_status": execution_result["status"],
                    "execution_timestamp": execution_result["end_time"],
                    "actions_executed": execution_result["results"],
                    "errors": execution_result["errors"],
                    "rollback_performed": execution_result.get("rollback_performed", False)
                }

                response = await client.patch(
                    f"{KB_API_URL}/decisions/{decision_id}",
                    json=payload,
                    timeout=5.0
                )

                if response.status_code == 200:
                    logger.info(f"Recorded execution to KB: {decision_id}")
                else:
                    logger.warning(f"Failed to record execution: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to record execution to KB: {e}")


# ============================================================================
# FastAPI Application
# ============================================================================

# Initialize components
k8s_controller = None
action_executor = None
kafka_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    global k8s_controller, action_executor, kafka_handler

    logger.info("Starting HCL Executor Service")

    try:
        # Initialize Kubernetes controller
        k8s_controller = KubernetesController(
            namespace=K8S_NAMESPACE,
            in_cluster=IN_CLUSTER
        )

        # Initialize action executor
        action_executor = ActionExecutor(
            k8s_controller=k8s_controller,
            dry_run=DRY_RUN,
            enable_rollback=ENABLE_ROLLBACK
        )

        # Initialize Kafka handler
        kafka_handler = KafkaHandler(action_executor)

        # Start Kafka consumer
        try:
            await kafka_handler.start()
        except Exception as e:
            logger.warning(f"Kafka not available: {e}")

        logger.info(
            f"HCL Executor ready (namespace={K8S_NAMESPACE}, dry_run={DRY_RUN})"
        )

    except Exception as e:
        logger.error(f"Failed to initialize executor: {e}")
        raise

    yield

    # Cleanup
    if kafka_handler:
        await kafka_handler.stop()

    logger.info("HCL Executor Service stopped")


app = FastAPI(
    title="HCL Executor Service",
    description="Executes HCL decisions on Kubernetes cluster",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "kubernetes": {
            "namespace": K8S_NAMESPACE,
            "in_cluster": IN_CLUSTER
        },
        "dry_run": DRY_RUN,
        "rollback_enabled": ENABLE_ROLLBACK,
        "kafka_connected": kafka_handler.running if kafka_handler else False,
        "executions_count": len(action_executor.execution_history) if action_executor else 0
    }


@app.post("/execute", response_model=ExecutionResponse)
async def execute_action_plan(action_plan: ActionPlan):
    """
    Manually execute action plan.

    Useful for testing or emergency override.
    """
    if not action_executor:
        raise HTTPException(status_code=503, detail="Executor not initialized")

    try:
        result = await action_executor.execute_action_plan(
            decision_id=action_plan.decision_id,
            actions=action_plan.actions,
            operational_mode=action_plan.operational_mode,
            confidence=action_plan.confidence
        )

        return ExecutionResponse(
            execution_id=result["execution_id"],
            decision_id=result["decision_id"],
            status=result["status"],
            actions_executed=len(result["results"]),
            actions_failed=len(result["errors"]),
            rollback_performed=result.get("rollback_performed", False),
            details=result
        )

    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scale")
async def scale_service(request: ScaleRequest):
    """
    Manually scale service.

    Direct Kubernetes operation without action plan.
    """
    if not k8s_controller:
        raise HTTPException(status_code=503, detail="Kubernetes controller not initialized")

    try:
        deployment_name = action_executor.SERVICE_DEPLOYMENTS.get(request.service)

        if not deployment_name:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {request.service}"
            )

        result = await k8s_controller.scale_deployment(
            deployment_name=deployment_name,
            target_replicas=request.target_replicas
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scale error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resources")
async def update_resources(request: ResourceUpdateRequest):
    """
    Manually update resource limits.

    Direct Kubernetes operation without action plan.
    """
    if not k8s_controller:
        raise HTTPException(status_code=503, detail="Kubernetes controller not initialized")

    try:
        deployment_name = action_executor.SERVICE_DEPLOYMENTS.get(request.service)

        if not deployment_name:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {request.service}"
            )

        result = await k8s_controller.update_resource_limits(
            deployment_name=deployment_name,
            cpu_limit=request.cpu_limit,
            memory_limit=request.memory_limit,
            cpu_request=request.cpu_request,
            memory_request=request.memory_request
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resource update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/hpa")
async def create_hpa(request: HPARequest):
    """
    Create or update HorizontalPodAutoscaler.

    Enables automatic scaling based on CPU/Memory metrics.
    """
    if not k8s_controller:
        raise HTTPException(status_code=503, detail="Kubernetes controller not initialized")

    try:
        deployment_name = action_executor.SERVICE_DEPLOYMENTS.get(request.service)

        if not deployment_name:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {request.service}"
            )

        result = await k8s_controller.create_or_update_hpa(
            deployment_name=deployment_name,
            min_replicas=request.min_replicas,
            max_replicas=request.max_replicas,
            target_cpu_utilization=request.target_cpu_utilization,
            target_memory_utilization=request.target_memory_utilization
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HPA error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/hpa/{service}")
async def delete_hpa(service: str):
    """
    Delete HorizontalPodAutoscaler.

    Disables automatic scaling.
    """
    if not k8s_controller:
        raise HTTPException(status_code=503, detail="Kubernetes controller not initialized")

    try:
        deployment_name = action_executor.SERVICE_DEPLOYMENTS.get(service)

        if not deployment_name:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {service}"
            )

        result = await k8s_controller.delete_hpa(deployment_name)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HPA deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deployments")
async def list_deployments():
    """
    List all deployments in namespace.

    Shows current status of all managed services.
    """
    if not k8s_controller:
        raise HTTPException(status_code=503, detail="Kubernetes controller not initialized")

    try:
        deployments = await k8s_controller.list_deployments()
        return {"deployments": deployments, "count": len(deployments)}

    except Exception as e:
        logger.error(f"List deployments error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deployments/{deployment_name}/status")
async def get_deployment_status(deployment_name: str):
    """
    Get detailed status of specific deployment.

    Includes replicas, conditions, resources.
    """
    if not k8s_controller:
        raise HTTPException(status_code=503, detail="Kubernetes controller not initialized")

    try:
        status = await k8s_controller.get_deployment_status(deployment_name)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_execution_history(limit: int = 100):
    """Get recent execution history"""
    if not action_executor:
        raise HTTPException(status_code=503, detail="Executor not initialized")

    history = action_executor.get_execution_history(limit)

    return {
        "count": len(history),
        "executions": history
    }


@app.post("/rollback/{service}")
async def rollback_deployment(service: str, revision: Optional[int] = None):
    """
    Rollback deployment to previous revision.

    Emergency rollback for failed deployments.
    """
    if not k8s_controller:
        raise HTTPException(status_code=503, detail="Kubernetes controller not initialized")

    try:
        deployment_name = action_executor.SERVICE_DEPLOYMENTS.get(service)

        if not deployment_name:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {service}"
            )

        result = await k8s_controller.rollback_deployment(
            deployment_name=deployment_name,
            revision=revision
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get detailed service status"""
    status = {
        "service": SERVICE_NAME,
        "kubernetes": {
            "namespace": K8S_NAMESPACE,
            "in_cluster": IN_CLUSTER,
            "controller_ready": k8s_controller is not None
        },
        "executor": {
            "dry_run": DRY_RUN,
            "rollback_enabled": ENABLE_ROLLBACK,
            "ready": action_executor is not None
        },
        "kafka": {
            "connected": kafka_handler.running if kafka_handler else False,
            "consuming_from": TOPIC_ACTIONS
        }
    }

    if action_executor:
        status["execution_stats"] = {
            "total_executions": len(action_executor.execution_history),
            "recent_executions": action_executor.execution_history[-5:] if action_executor.execution_history else []
        }

    return status


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )
