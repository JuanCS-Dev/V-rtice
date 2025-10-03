"""
MAXIMUS EUREKA - REST API
========================

FastAPI REST endpoints para análise profunda de malware.

Endpoints:
- POST /analyze → Analisa arquivo de malware
- GET /health → Health check
- GET /patterns → Lista padrões disponíveis
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from eureka import MalwareAnalyzer, AnalysisResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MAXIMUS EUREKA API",
    description="Deep Malware Analysis Orchestrator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize analyzer
analyzer = MalwareAnalyzer()


class AnalysisRequest(BaseModel):
    """Request model for analysis"""
    file_path: str = Field(..., description="Path to malware file for analysis")
    generate_playbook: bool = Field(True, description="Generate response playbook")
    export_html: bool = Field(False, description="Export HTML report")


class AnalysisResponse(BaseModel):
    """Response model for analysis"""
    status: str
    analysis_id: str
    threat_score: int
    severity: str
    malware_type: Optional[str]
    patterns_detected: int
    iocs_found: int
    report_url: Optional[str]
    playbook_url: Optional[str]
    timestamp: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "maximus-eureka",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/patterns")
async def list_patterns():
    """List available malicious patterns"""
    patterns = analyzer.pattern_detector.get_pattern_names()
    return {
        "total": len(patterns),
        "patterns": patterns
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_malware(
    file: UploadFile = File(...),
    generate_playbook: bool = True,
    export_html: bool = False
):
    """
    Analyze malware file.

    Args:
        file: Malware file to analyze
        generate_playbook: Generate YAML playbook (default: True)
        export_html: Export HTML report (default: False)

    Returns:
        Analysis results with threat score, IOCs, patterns, etc.
    """
    temp_file = None

    try:
        # Save uploaded file temporarily
        temp_dir = Path("/tmp/eureka_uploads")
        temp_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = temp_dir / f"{timestamp}_{file.filename}"

        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Analyzing file: {file.filename} ({len(content)} bytes)")

        # Run analysis
        result = analyzer.analyze_file(str(temp_file))

        # Generate playbook if requested
        playbook_url = None
        if generate_playbook:
            playbook_path = analyzer.generate_playbook(result)
            if playbook_path:
                playbook_url = f"/playbooks/{Path(playbook_path).name}"

        # Export HTML if requested
        report_url = None
        if export_html:
            html_path = analyzer.export_html(result)
            if html_path:
                report_url = f"/reports/{Path(html_path).name}"

        # Build response
        response = AnalysisResponse(
            status="success",
            analysis_id=f"eureka_{timestamp}",
            threat_score=result.threat_score,
            severity=result.severity,
            malware_type=result.malware_type or "Unknown",
            patterns_detected=len(result.patterns_detected),
            iocs_found=len(result.iocs),
            report_url=report_url,
            playbook_url=playbook_url,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Analysis complete: {file.filename} - Score: {result.threat_score}")

        return response

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Cleanup temporary file
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")


@app.post("/analyze/path")
async def analyze_file_path(request: AnalysisRequest):
    """
    Analyze malware from file path (for internal service calls).

    Args:
        request: Analysis request with file path

    Returns:
        Analysis results
    """
    try:
        file_path = Path(request.file_path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

        logger.info(f"Analyzing file: {file_path}")

        # Run analysis
        result = analyzer.analyze_file(str(file_path))

        # Generate playbook if requested
        playbook_url = None
        if request.generate_playbook:
            playbook_path = analyzer.generate_playbook(result)
            if playbook_path:
                playbook_url = f"/playbooks/{Path(playbook_path).name}"

        # Export HTML if requested
        report_url = None
        if request.export_html:
            html_path = analyzer.export_html(result)
            if html_path:
                report_url = f"/reports/{Path(html_path).name}"

        # Build response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = AnalysisResponse(
            status="success",
            analysis_id=f"eureka_{timestamp}",
            threat_score=result.threat_score,
            severity=result.severity,
            malware_type=result.malware_type or "Unknown",
            patterns_detected=len(result.patterns_detected),
            iocs_found=len(result.iocs),
            report_url=report_url,
            playbook_url=playbook_url,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Analysis complete: {file_path.name} - Score: {result.threat_score}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MAXIMUS EUREKA",
        "description": "Deep Malware Analysis Orchestrator",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze - Upload and analyze malware file",
            "analyze_path": "POST /analyze/path - Analyze file from path",
            "patterns": "GET /patterns - List detection patterns",
            "health": "GET /health - Health check",
            "docs": "GET /docs - API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
