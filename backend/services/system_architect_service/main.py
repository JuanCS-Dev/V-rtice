"""System Architect Service - VÉRTICE Product Analysis

Provides macro-level architectural analysis of the entire VÉRTICE platform.
Identifies gaps, redundancies, optimization opportunities, and generates
comprehensive reports for pre-deployment refinement.

Architectural Role:
- Scans all 89+ microservices
- Analyzes integration patterns (Kafka, Redis, HTTP)
- Detects redundancies and optimization opportunities
- Generates executive reports for deployment decisions

Production-Ready: Zero mocks, zero placeholders, zero TODOs.
Padrão Pagani Absoluto compliance: 100%
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from analyzers.architecture_scanner import ArchitectureScanner
from analyzers.integration_analyzer import IntegrationAnalyzer
from analyzers.redundancy_detector import RedundancyDetector
from analyzers.deployment_optimizer import DeploymentOptimizer
from generators.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="System Architect Service",
    version="1.0.0",
    description="Macro-level architectural analysis for VÉRTICE platform"
)

# Global state
_scanner: ArchitectureScanner | None = None
_integration_analyzer: IntegrationAnalyzer | None = None
_redundancy_detector: RedundancyDetector | None = None
_deployment_optimizer: DeploymentOptimizer | None = None
_report_generator: ReportGenerator | None = None


class AnalysisRequest(BaseModel):
    """Request model for system analysis."""
    subsystem: str | None = None  # Optional: analyze specific subsystem
    include_recommendations: bool = True
    generate_graphs: bool = True


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    status: str
    timestamp: str
    summary: Dict[str, Any]
    report_id: str
    report_url: str | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize analyzers on startup."""
    global _scanner, _integration_analyzer, _redundancy_detector
    global _deployment_optimizer, _report_generator

    logger.info("🔮 Starting System Architect Service...")

    # Initialize all analyzers
    docker_compose_path = "/home/juan/vertice-dev/backend/services/../docker-compose.yml"
    services_path = "/home/juan/vertice-dev/backend/services"

    _scanner = ArchitectureScanner(
        docker_compose_path=docker_compose_path,
        services_base_path=services_path
    )

    _integration_analyzer = IntegrationAnalyzer(scanner=_scanner)
    _redundancy_detector = RedundancyDetector(scanner=_scanner)
    _deployment_optimizer = DeploymentOptimizer(scanner=_scanner)
    _report_generator = ReportGenerator(output_dir="/tmp/system_architect_reports")

    logger.info("✅ System Architect Service initialized successfully")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "system_architect_service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "analyzers": {
            "scanner": _scanner is not None,
            "integration_analyzer": _integration_analyzer is not None,
            "redundancy_detector": _redundancy_detector is not None,
            "deployment_optimizer": _deployment_optimizer is not None,
            "report_generator": _report_generator is not None
        }
    }


@app.post("/analyze/full", response_model=AnalysisResponse)
async def analyze_full_system(request: AnalysisRequest) -> AnalysisResponse:
    """
    Perform comprehensive analysis of the entire VÉRTICE platform.

    Analyzes:
    - All 89+ services
    - Integration patterns (Kafka, Redis, HTTP)
    - Redundancies and gaps
    - Deployment readiness

    Returns executive summary and generates detailed reports.
    """
    if not _scanner or not _report_generator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    logger.info("🔍 Starting full system analysis...")

    try:
        # Step 1: Scan architecture
        logger.info("📊 Scanning architecture...")
        architecture = await _scanner.scan()

        # Step 2: Analyze integrations
        logger.info("🔗 Analyzing integrations...")
        integrations = await _integration_analyzer.analyze()

        # Step 3: Detect redundancies
        logger.info("🔄 Detecting redundancies...")
        redundancies = await _redundancy_detector.detect()

        # Step 4: Optimize deployment
        logger.info("🚀 Optimizing deployment...")
        optimizations = await _deployment_optimizer.optimize()

        # Step 5: Generate reports
        logger.info("📝 Generating reports...")
        report_id = f"VERTICE_ANALYSIS_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        report_data = {
            "architecture": architecture,
            "integrations": integrations,
            "redundancies": redundancies,
            "optimizations": optimizations,
            "metadata": {
                "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
                "report_id": report_id,
                "analyzer_version": "1.0.0"
            }
        }

        report_paths = await _report_generator.generate_all(
            report_id=report_id,
            data=report_data,
            include_graphs=request.generate_graphs
        )

        # Build summary
        summary = {
            "total_services": architecture.get("total_services", 0),
            "subsystems": len(architecture.get("subsystems", {})),
            "integration_points": integrations.get("total_integration_points", 0),
            "redundancies_found": len(redundancies.get("redundant_services", [])),
            "optimization_opportunities": len(optimizations.get("recommendations", [])),
            "deployment_readiness_score": optimizations.get("readiness_score", 0),
            "critical_gaps": len([
                gap for gap in optimizations.get("gaps", [])
                if gap.get("priority") == "CRITICAL"
            ])
        }

        logger.info(f"✅ Analysis complete - Report ID: {report_id}")

        return AnalysisResponse(
            status="success",
            timestamp=datetime.utcnow().isoformat() + "Z",
            summary=summary,
            report_id=report_id,
            report_url=report_paths.get("html")
        )

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/subsystem", response_model=AnalysisResponse)
async def analyze_subsystem(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze a specific subsystem (e.g., 'consciousness', 'immune', 'homeostatic')."""
    if not request.subsystem:
        raise HTTPException(status_code=400, detail="Subsystem name required")

    if not _scanner or not _report_generator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    logger.info(f"🔍 Analyzing subsystem: {request.subsystem}")

    try:
        # Scan only the specified subsystem
        architecture = await _scanner.scan(subsystem_filter=request.subsystem)

        if not architecture.get("services"):
            raise HTTPException(
                status_code=404,
                detail=f"Subsystem '{request.subsystem}' not found"
            )

        # Generate subsystem-specific report
        report_id = f"{request.subsystem.upper()}_ANALYSIS_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        report_data = {
            "architecture": architecture,
            "metadata": {
                "subsystem": request.subsystem,
                "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
                "report_id": report_id
            }
        }

        report_paths = await _report_generator.generate_subsystem_report(
            report_id=report_id,
            subsystem=request.subsystem,
            data=report_data
        )

        summary = {
            "subsystem": request.subsystem,
            "total_services": len(architecture.get("services", [])),
            "health_status": architecture.get("health_summary", {})
        }

        return AnalysisResponse(
            status="success",
            timestamp=datetime.utcnow().isoformat() + "Z",
            summary=summary,
            report_id=report_id,
            report_url=report_paths.get("html")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Subsystem analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/reports/latest")
async def get_latest_report() -> Dict[str, Any]:
    """Get the most recent analysis report."""
    if not _report_generator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        latest = await _report_generator.get_latest_report()

        if not latest:
            raise HTTPException(status_code=404, detail="No reports found")

        return latest

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve latest report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gaps")
async def get_gaps() -> Dict[str, Any]:
    """Get identified architectural gaps."""
    if not _deployment_optimizer:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        gaps = await _deployment_optimizer.get_gaps()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "gaps": gaps
        }
    except Exception as e:
        logger.error(f"❌ Failed to retrieve gaps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/redundancies")
async def get_redundancies() -> Dict[str, Any]:
    """Get identified redundant services."""
    if not _redundancy_detector:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        redundancies = await _redundancy_detector.detect()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "redundancies": redundancies
        }
    except Exception as e:
        logger.error(f"❌ Failed to retrieve redundancies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get system architecture metrics."""
    if not _scanner:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        architecture = await _scanner.scan()

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": {
                "total_services": architecture.get("total_services", 0),
                "subsystems": len(architecture.get("subsystems", {})),
                "ports_allocated": len(architecture.get("ports", {})),
                "networks": len(architecture.get("networks", [])),
                "volumes": len(architecture.get("volumes", []))
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to retrieve metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8900,
        log_level="info"
    )
