"""Maximus Oraculo Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Oraculo
Service. It exposes functionalities for providing predictive insights,
probabilistic forecasts, and strategic guidance based on complex data analysis
and advanced modeling.

Endpoints are provided for:
- Submitting data for predictive analysis.
- Querying for forecasts of future events or trends.
- Retrieving strategic recommendations and risk assessments.

This API allows other Maximus AI services or human operators to leverage the
Oraculo Service's advanced foresight capabilities, supporting high-level
decision-making and long-term planning for the Maximus AI system.
"""

from datetime import datetime
import os
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from auto_implementer import AutoImplementer
from code_scanner import CodeScanner
from oraculo import OraculoEngine
from suggestion_generator import SuggestionGenerator
from config import config

# WebSocket support for Adaptive Immunity (conditionally imported)
try:
    from api_endpoints import websocket_router, initialize_stream_manager
    from websocket import APVStreamManager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("[API] WebSocket support not available")

app = FastAPI(title="Maximus Oraculo Service", version="2.0.0")

# Include WebSocket router only if enabled and available
if config.enable_websocket and WEBSOCKET_AVAILABLE:
    app.include_router(websocket_router)
    print("[API] WebSocket router enabled")

# Initialize Oraculo components
oraculo_engine = OraculoEngine()
suggestion_generator = SuggestionGenerator()
code_scanner = CodeScanner()
auto_implementer = AutoImplementer()

# WebSocket stream manager (initialized on startup)
stream_manager: Optional[APVStreamManager] = None


class PredictionRequest(BaseModel):
    """Request model for submitting data for predictive analysis.

    Attributes:
        data (Dict[str, Any]): The data to analyze for predictions.
        prediction_type (str): The type of prediction requested (e.g., 'threat_level', 'resource_demand').
        time_horizon (str): The time horizon for the prediction (e.g., '24h', '7d').
    """

    data: Dict[str, Any]
    prediction_type: str
    time_horizon: str


class CodeAnalysisRequest(BaseModel):
    """Request model for submitting code for analysis.

    Attributes:
        code (str): The code snippet to analyze.
        language (str): The programming language of the code.
        analysis_type (str): The type of analysis (e.g., 'vulnerability', 'performance', 'refactoring').
    """

    code: str
    language: str
    analysis_type: str


class ImplementationRequest(BaseModel):
    """Request model for requesting automated code implementation.

    Attributes:
        task_description (str): A description of the coding task.
        context (Optional[Dict[str, Any]]): Additional context or existing code.
        target_language (str): The target programming language.
    """

    task_description: str
    context: Optional[Dict[str, Any]] = None
    target_language: str


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Oraculo Service."""
    global stream_manager

    print(f"🔮 Starting Maximus Oraculo Service v{config.service_version}...")

    # Initialize WebSocket APV Stream Manager (optional)
    if config.enable_kafka and WEBSOCKET_AVAILABLE:
        try:
            print("[Startup] Initializing Kafka/WebSocket integration...")
            stream_manager = APVStreamManager(
                kafka_bootstrap_servers=config.kafka_brokers,
                kafka_topic=config.kafka_topic,
            )
            await stream_manager.start()
            initialize_stream_manager(stream_manager)
            print(f"✅ WebSocket endpoint available (Kafka: {config.kafka_brokers})")
        except Exception as e:
            print(f"⚠️  Kafka/WebSocket initialization failed: {e}")
            print("⚠️  Service will continue without WebSocket features")
            config.add_degradation("kafka_unavailable")
            stream_manager = None
    else:
        print("[Startup] Kafka/WebSocket disabled (ENABLE_KAFKA=false or not available)")
        stream_manager = None

    # Display capabilities
    capabilities = config.get_capabilities()
    print(f"✅ Maximus Oraculo Service started successfully")
    print(f"📋 Capabilities: {capabilities}")
    if config.degradations:
        print(f"⚠️  Degradations: {config.degradations}")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Oraculo Service."""
    global stream_manager
    
    print("👋 Shutting down Maximus Oraculo Service...")
    
    # Stop stream manager
    if stream_manager:
        await stream_manager.stop()
    
    print("🛑 Maximus Oraculo Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Performs a health check of the Oraculo Service.

    Includes APVStreamManager status for degraded mode visibility.
    AG-RUNTIME-001: Exposes Kafka connection status.

    Returns:
        Dict[str, Any]: A dictionary indicating the service status and capabilities.
    """
    health_status = config.get_health_status()

    # Add APV Stream Manager status if available
    if stream_manager:
        health_status["apv_stream_manager"] = stream_manager.get_metrics()

    return health_status


@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get service capabilities and feature flags.

    Returns:
        Dict[str, Any]: Current capabilities and configuration.
    """
    return {
        "capabilities": config.get_capabilities(),
        "configuration": {
            "llm_model": config.openai_model if config.check_llm_availability() else None,
            "kafka_enabled": config.enable_kafka,
            "websocket_enabled": config.enable_websocket,
        },
    }


@app.post("/predict")
async def get_prediction(request: PredictionRequest) -> Dict[str, Any]:
    """Generates a predictive insight based on the provided data.

    Args:
        request (PredictionRequest): The request body containing data and prediction parameters.

    Returns:
        Dict[str, Any]: A dictionary containing the prediction results and confidence.
    """
    print(f"[API] Generating {request.prediction_type} prediction for {request.time_horizon}.")
    prediction_result = await oraculo_engine.generate_prediction(
        request.data, request.prediction_type, request.time_horizon
    )
    suggestions = await suggestion_generator.generate_suggestions(prediction_result)
    prediction_result["suggestions"] = suggestions
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction_result,
    }


@app.post("/analyze_code")
async def analyze_code_endpoint(request: CodeAnalysisRequest) -> Dict[str, Any]:
    """Analyzes code for vulnerabilities, performance issues, or refactoring opportunities.

    Args:
        request (CodeAnalysisRequest): The request body containing the code and analysis parameters.

    Returns:
        Dict[str, Any]: A dictionary containing the code analysis results.
    """
    print(f"[API] Analyzing {request.language} code for {request.analysis_type}.")
    analysis_result = await code_scanner.scan_code(request.code, request.language, request.analysis_type)
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "analysis_result": analysis_result,
    }


@app.post("/auto_implement")
async def auto_implement_code_endpoint(
    request: ImplementationRequest,
) -> Dict[str, Any]:
    """Requests automated code implementation based on a task description.

    Args:
        request (ImplementationRequest): The request body containing the task description and context.

    Returns:
        Dict[str, Any]: A dictionary containing the generated code and implementation details.
    """
    print(f"[API] Requesting auto-implementation for task: {request.task_description}")
    implementation_result = await auto_implementer.implement_code(
        request.task_description, request.context, request.target_language
    )
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "implementation_result": implementation_result,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8026)
