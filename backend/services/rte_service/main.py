"""Maximus RTE Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Real-Time Execution
(RTE) Service. It initializes and configures the FastAPI application, sets up
event handlers for startup and shutdown, and defines the API endpoints for
executing critical, time-sensitive operations and commands.

It orchestrates the integration of various real-time components, such as the
Fusion Engine for data correlation, Fast ML for rapid predictions, and Hyperscan
Matcher for high-speed pattern detection. This service is crucial for providing
a robust and responsive execution environment for Maximus AI's most demanding
operational requirements, enabling immediate reactions to dynamic environmental
changes or emerging threats.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import asyncio
from datetime import datetime

from fusion_engine import FusionEngine
from fast_ml import FastML
from hyperscan_matcher import HyperscanMatcher
from playbooks import RealTimePlaybookExecutor

app = FastAPI(title="Maximus RTE Service", version="1.0.0")

# Initialize RTE components
fusion_engine = FusionEngine()
fast_ml = FastML()
hyperscan_matcher = HyperscanMatcher()
real_time_playbook_executor = RealTimePlaybookExecutor(fast_ml, hyperscan_matcher)


class RealTimeCommand(BaseModel):
    """Request model for executing a real-time command.

    Attributes:
        command_name (str): The name of the command to execute (e.g., 'block_ip', 'isolate_process').
        parameters (Dict[str, Any]): Parameters for the command.
        priority (int): The priority of the command (1-10, 10 being highest).
    """
    command_name: str
    parameters: Dict[str, Any]
    priority: int = 5


class DataStreamIngest(BaseModel):
    """Request model for ingesting real-time data streams.

    Attributes:
        stream_id (str): Identifier for the data stream.
        data (Dict[str, Any]): The data payload from the stream.
        data_type (str): The type of data (e.g., 'network_packet', 'log_entry', 'sensor_reading').
    """
    stream_id: str
    data: Dict[str, Any]
    data_type: str


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the RTE Service."""
    print("⚡ Starting Maximus RTE Service...")
    # Compile Hyperscan patterns on startup
    await hyperscan_matcher.compile_patterns(["malicious_pattern_1", "exploit_signature_A"])
    print("✅ Maximus RTE Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the RTE Service."""
    print("👋 Shutting down Maximus RTE Service...")
    print("🛑 Maximus RTE Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the RTE Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "RTE Service is operational."}


@app.post("/execute_realtime_command")
async def execute_realtime_command_endpoint(request: RealTimeCommand) -> Dict[str, Any]:
    """Executes a critical, time-sensitive command.

    Args:
        request (RealTimeCommand): The request body containing the command details.

    Returns:
        Dict[str, Any]: A dictionary containing the execution results.
    """
    print(f"[API] Executing real-time command: {request.command_name} (priority: {request.priority})")
    
    # Simulate execution via playbook executor
    execution_result = await real_time_playbook_executor.execute_command(request.command_name, request.parameters)

    return {"status": "success", "timestamp": datetime.now().isoformat(), "execution_result": execution_result}


@app.post("/ingest_data_stream")
async def ingest_data_stream_endpoint(request: DataStreamIngest) -> Dict[str, Any]:
    """Ingests real-time data from a stream, processes it, and performs rapid analysis.

    Args:
        request (DataStreamIngest): The request body containing stream data.

    Returns:
        Dict[str, Any]: A dictionary containing the processing and analysis results.
    """
    print(f"[API] Ingesting {request.data_type} data from stream {request.stream_id}.")
    
    # 1. Fuse data (if multiple sources were involved, here just one)
    fused_data = await fusion_engine.fuse_data([request.data])

    # 2. Perform rapid ML prediction
    ml_prediction = await fast_ml.predict(fused_data, "threat_score")

    # 3. Perform Hyperscan pattern matching
    hyperscan_matches = await hyperscan_matcher.scan_data(str(request.data).encode('utf-8'))

    # 4. Trigger playbook if critical conditions met
    if ml_prediction.get("prediction_value", 0) > 0.7 or hyperscan_matches:
        print("[API] Critical condition detected, triggering real-time playbook.")
        playbook_result = await real_time_playbook_executor.execute_command("critical_threat_response", {"threat_data": request.data, "ml_prediction": ml_prediction})
    else:
        playbook_result = {"status": "no_action_needed"}

    return {
        "status": "processed",
        "timestamp": datetime.now().isoformat(),
        "fused_data_summary": fused_data,
        "ml_prediction": ml_prediction,
        "hyperscan_matches": hyperscan_matches,
        "playbook_action": playbook_result
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8038)