"""Maximus Eureka Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Eureka
Service. It exposes functionalities for identifying novel insights, making
unexpected connections, and generating breakthrough discoveries from vast
amounts of data.

Endpoints are provided for:
- Submitting data for insight generation.
- Querying for novel patterns or anomalies.
- Retrieving generated hypotheses or discoveries.

This API allows other Maximus AI services or human analysts to leverage the
Eureka Service's advanced analytical capabilities, facilitating scientific
discovery, strategic planning, and complex problem-solving within the Maximus
AI system.
"""

from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from eureka import EurekaEngine
from ioc_extractor import IoCExtractor
from pattern_detector import PatternDetector
from playbook_generator import PlaybookGenerator

app = FastAPI(title="Maximus Eureka Service", version="1.0.0")

# Initialize Eureka components
eureka_engine = EurekaEngine()
pattern_detector = PatternDetector()
ioc_extractor = IoCExtractor()
playbook_generator = PlaybookGenerator()


class InsightRequest(BaseModel):
    """Request model for submitting data for insight generation.

    Attributes:
        data (Dict[str, Any]): The data to analyze for insights.
        data_type (str): The type of data (e.g., 'logs', 'network_traffic', 'threat_intel').
        context (Optional[Dict[str, Any]]): Additional context for the analysis.
    """

    data: dict[str, Any]
    data_type: str
    context: dict[str, Any] | None = None


class PatternDetectionRequest(BaseModel):
    """Request model for detecting specific patterns.

    Attributes:
        data (Dict[str, Any]): The data to analyze for patterns.
        pattern_definition (Dict[str, Any]): The definition of the pattern to detect.
    """

    data: dict[str, Any]
    pattern_definition: dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Eureka Service."""
    print("💡 Starting Maximus Eureka Service...")
    print("✅ Maximus Eureka Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Eureka Service."""
    print("👋 Shutting down Maximus Eureka Service...")
    print("🛑 Maximus Eureka Service shut down.")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Performs a health check of the Eureka Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Eureka Service is operational."}


@app.post("/generate_insight")
async def generate_insight_endpoint(request: InsightRequest) -> dict[str, Any]:
    """Submits data for insight generation and returns novel discoveries.

    Args:
        request (InsightRequest): The request body containing data for analysis.

    Returns:
        Dict[str, Any]: A dictionary containing the generated insights and discoveries.
    """
    print(f"[API] Generating insight for {request.data_type} data.")

    # Simulate various Eureka engine operations
    insights = await eureka_engine.analyze_data(request.data, request.data_type, request.context)

    # Extract IoCs if applicable
    extracted_iocs = ioc_extractor.extract_iocs(request.data)
    if extracted_iocs:
        insights["extracted_iocs"] = extracted_iocs

    # Detect patterns
    detected_patterns = pattern_detector.detect_patterns(request.data, {"type": "anomaly"})  # Generic pattern
    if detected_patterns:
        insights["detected_patterns"] = detected_patterns

    # Generate playbook if a critical insight is found
    if insights.get("novel_discovery") and insights["novel_discovery"].get("severity", "low") == "critical":
        playbook = playbook_generator.generate_playbook(insights["novel_discovery"])
        insights["suggested_playbook"] = playbook

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "insights": insights,
    }


@app.post("/detect_pattern")
async def detect_pattern_endpoint(request: PatternDetectionRequest) -> dict[str, Any]:
    """Detects specific patterns within provided data.

    Args:
        request (PatternDetectionRequest): The request body containing data and pattern definition.

    Returns:
        Dict[str, Any]: A dictionary containing the pattern detection results.
    """
    print("[API] Detecting patterns in data.")
    detected_patterns = pattern_detector.detect_patterns(request.data, request.pattern_definition)
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "detected_patterns": detected_patterns,
    }


@app.post("/extract_iocs")
async def extract_iocs_endpoint(data: dict[str, Any]) -> dict[str, Any]:
    """Extracts Indicators of Compromise (IoCs) from provided data.

    Args:
        data (Dict[str, Any]): The data from which to extract IoCs.

    Returns:
        Dict[str, Any]: A dictionary containing the extracted IoCs.
    """
    print("[API] Extracting IoCs from data.")
    extracted_iocs = ioc_extractor.extract_iocs(data)
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "extracted_iocs": extracted_iocs,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8024)
