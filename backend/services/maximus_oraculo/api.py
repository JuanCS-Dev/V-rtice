"""
MAXIMUS ORÁCULO - REST API
==========================

FastAPI REST endpoints para self-improvement engine.

Endpoints:
- POST /scan → Scans codebase
- POST /suggest → Generate improvement suggestions
- POST /implement → Auto-implement suggestion
- GET /sessions → List improvement sessions
- GET /health → Health check
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from oraculo import (
    SelfImprovementOrchestrator,
    ImprovementSession
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MAXIMUS ORÁCULO API",
    description="Self-Improvement Orchestrator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize orchestrator
# Check for GEMINI_API_KEY
if not os.getenv("GEMINI_API_KEY"):
    logger.warning("⚠️  GEMINI_API_KEY not set! Oráculo will not function properly.")
    logger.warning("Set GEMINI_API_KEY environment variable to enable AI suggestions.")

orchestrator = SelfImprovementOrchestrator()


class ScanRequest(BaseModel):
    """Request model for code scanning"""
    target_path: Optional[str] = Field(None, description="Path to scan (default: MAXIMUS root)")
    extensions: List[str] = Field(["py", "js", "md"], description="File extensions to scan")


class ScanResponse(BaseModel):
    """Response model for scan"""
    status: str
    files_scanned: int
    total_lines: int
    timestamp: str


class SuggestRequest(BaseModel):
    """Request model for suggestions"""
    focus_areas: List[str] = Field(
        ["security", "performance", "features"],
        description="Areas to focus on"
    )
    max_suggestions: int = Field(10, description="Maximum suggestions to generate")


class SuggestResponse(BaseModel):
    """Response model for suggestions"""
    status: str
    suggestions_count: int
    suggestions: List[Dict[str, Any]]
    timestamp: str


class ImplementRequest(BaseModel):
    """Request model for implementation"""
    suggestion_id: int = Field(..., description="Suggestion ID to implement")
    auto_approve: bool = Field(False, description="Auto-approve without human review")


class ImplementResponse(BaseModel):
    """Response model for implementation"""
    status: str
    implemented: bool
    tests_passed: bool
    commit_hash: Optional[str]
    message: str
    timestamp: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "status": "healthy" if gemini_configured else "degraded",
        "service": "maximus-oraculo",
        "version": "1.0.0",
        "gemini_api_key_configured": gemini_configured,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scan", response_model=ScanResponse)
async def scan_codebase(request: ScanRequest):
    """
    Scan codebase for analysis.

    Args:
        request: Scan configuration

    Returns:
        Scan results with file count and line count
    """
    try:
        logger.info(f"Starting codebase scan: {request.target_path or 'default path'}")

        # Run scan
        target = request.target_path or orchestrator.scanner.maximus_root
        files = orchestrator.scanner.scan_directory(
            target,
            extensions=request.extensions
        )

        total_lines = sum(f.line_count for f in files)

        logger.info(f"Scan complete: {len(files)} files, {total_lines} lines")

        return ScanResponse(
            status="success",
            files_scanned=len(files),
            total_lines=total_lines,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Scan failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.post("/suggest", response_model=SuggestResponse)
async def generate_suggestions(request: SuggestRequest):
    """
    Generate improvement suggestions via AI.

    Args:
        request: Suggestion configuration

    Returns:
        List of AI-generated suggestions
    """
    try:
        # Check API key
        if not os.getenv("GEMINI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="GEMINI_API_KEY not configured. Cannot generate suggestions."
            )

        logger.info(f"Generating suggestions: {request.focus_areas}")

        # Generate suggestions
        suggestions = orchestrator.suggestion_gen.generate_suggestions(
            orchestrator.scanner.code_files,
            focus_areas=request.focus_areas,
            max_suggestions=request.max_suggestions
        )

        # Convert to dict
        suggestions_data = [
            {
                "id": i,
                "category": s.category,
                "priority": s.priority,
                "title": s.title,
                "description": s.description,
                "file_path": s.file_path,
                "implementation_notes": s.implementation_notes
            }
            for i, s in enumerate(suggestions, 1)
        ]

        logger.info(f"Generated {len(suggestions)} suggestions")

        return SuggestResponse(
            status="success",
            suggestions_count=len(suggestions),
            suggestions=suggestions_data,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suggestion generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@app.post("/implement", response_model=ImplementResponse)
async def implement_suggestion(request: ImplementRequest, background_tasks: BackgroundTasks):
    """
    Implement a suggestion with safety checks.

    Args:
        request: Implementation request

    Returns:
        Implementation result with test status
    """
    try:
        logger.info(f"Implementing suggestion #{request.suggestion_id}")

        # Get suggestion from last session
        if not orchestrator.sessions:
            raise HTTPException(
                status_code=400,
                detail="No suggestions available. Run /suggest first."
            )

        last_session = orchestrator.sessions[-1]
        suggestions = last_session.suggestions

        if request.suggestion_id < 1 or request.suggestion_id > len(suggestions):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid suggestion_id. Must be 1-{len(suggestions)}"
            )

        suggestion = suggestions[request.suggestion_id - 1]

        # Implement with safety checks
        success = orchestrator.implementer.implement_suggestion(
            suggestion,
            auto_approve=request.auto_approve
        )

        # Get commit hash if successful
        commit_hash = None
        if success:
            # TODO: Get actual commit hash from git
            commit_hash = "pending"

        message = "Implementation successful" if success else "Implementation failed or requires approval"

        logger.info(f"Implementation result: {message}")

        return ImplementResponse(
            status="success" if success else "requires_approval",
            implemented=success,
            tests_passed=success,  # TODO: Get actual test results
            commit_hash=commit_hash,
            message=message,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Implementation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Implementation failed: {str(e)}")


@app.get("/sessions")
async def list_sessions():
    """
    List all improvement sessions.

    Returns:
        List of sessions with statistics
    """
    try:
        sessions_data = []

        for session in orchestrator.sessions:
            sessions_data.append({
                "session_id": session.session_id,
                "timestamp": session.timestamp,
                "suggestions_count": len(session.suggestions),
                "implemented_count": len(session.implemented_suggestions)
            })

        return {
            "status": "success",
            "total_sessions": len(sessions_data),
            "sessions": sessions_data
        }

    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.post("/improve")
async def run_full_improvement_cycle(background_tasks: BackgroundTasks):
    """
    Run full improvement cycle (scan + suggest + implement safe changes).

    Returns:
        Cycle results
    """
    try:
        if not os.getenv("GEMINI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="GEMINI_API_KEY not configured. Cannot run improvement cycle."
            )

        logger.info("Starting full improvement cycle")

        # Run cycle in background
        background_tasks.add_task(orchestrator.run_improvement_cycle)

        return {
            "status": "started",
            "message": "Improvement cycle started in background",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start cycle: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start cycle: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MAXIMUS ORÁCULO",
        "description": "Self-Improvement Orchestrator",
        "version": "1.0.0",
        "endpoints": {
            "scan": "POST /scan - Scan codebase",
            "suggest": "POST /suggest - Generate AI suggestions",
            "implement": "POST /implement - Implement suggestion",
            "improve": "POST /improve - Run full cycle",
            "sessions": "GET /sessions - List sessions",
            "health": "GET /health - Health check",
            "docs": "GET /docs - API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8201)
