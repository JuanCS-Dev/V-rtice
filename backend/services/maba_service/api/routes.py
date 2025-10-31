"""MABA API Routes.

FastAPI routes for MABA browser automation operations.

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from services.maba_service.models import (
    BrowserActionResponse,
    BrowserSessionRequest,
    ClickRequest,
    CognitiveMapQueryRequest,
    CognitiveMapQueryResponse,
    ExtractRequest,
    NavigationRequest,
    PageAnalysisRequest,
    PageAnalysisResponse,
    ScreenshotRequest,
    TypeRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["MABA"])


# Dependency to get MABA service instance
# This will be set by main.py after service initialization
_maba_service_instance = None


def set_maba_service(service):
    """Set the global MABA service instance."""
    global _maba_service_instance
    _maba_service_instance = service


def get_maba_service():
    """Get the MABA service instance."""
    if _maba_service_instance is None:
        raise HTTPException(status_code=503, detail="MABA service not initialized")
    return _maba_service_instance


@router.post("/sessions")
async def create_browser_session(
    request: BrowserSessionRequest, service=Depends(get_maba_service)
):
    """
    Create a new browser session.

    Args:
        request: Browser session configuration

    Returns:
        Session details including ID and status
    """
    try:
        result = await service.browser_controller.create_session(
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            user_agent=request.user_agent,
        )

        # Handle both dict response and string response
        if isinstance(result, dict):
            return result
        else:
            return {"session_id": result, "status": "created"}

    except Exception as e:
        logger.error(f"Failed to create browser session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def close_browser_session(session_id: str, service=Depends(get_maba_service)):
    """
    Close a browser session.

    Args:
        session_id: Session ID to close

    Returns:
        Success message
    """
    try:
        result = await service.browser_controller.close_session(session_id)

        # Handle both dict response and None response
        if isinstance(result, dict):
            return result
        else:
            return {"status": "closed", "message": f"Session {session_id} closed"}

    except Exception as e:
        logger.error(f"Failed to close session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/navigate", response_model=BrowserActionResponse)
async def navigate(
    request: NavigationRequest, session_id: str, service=Depends(get_maba_service)
):
    """
    Navigate to a URL.

    Args:
        request: Navigation request
        session_id: Browser session ID

    Returns:
        Navigation result
    """
    try:
        start_time = time.time()

        result = await service.browser_controller.navigate(
            session_id=session_id,
            url=request.url,
            wait_until=request.wait_until,
            timeout_ms=request.timeout_ms,
        )

        execution_time_ms = (time.time() - start_time) * 1000

        return BrowserActionResponse(
            status=result.get("status", "failed"),
            result=result,
            execution_time_ms=execution_time_ms,
        )

    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/click", response_model=BrowserActionResponse)
async def click(
    request: ClickRequest, session_id: str, service=Depends(get_maba_service)
):
    """
    Click an element.

    Args:
        request: Click request
        session_id: Browser session ID

    Returns:
        Click result
    """
    try:
        result = await service.browser_controller.click(
            session_id=session_id,
            selector=request.selector,
            timeout_ms=request.timeout_ms,
        )

        return BrowserActionResponse(
            status=result.get("status", "failed"), result=result, execution_time_ms=0.0
        )

    except Exception as e:
        logger.error(f"Click failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/type", response_model=BrowserActionResponse)
async def type_text(
    request: TypeRequest, session_id: str, service=Depends(get_maba_service)
):
    """
    Type text into an element.

    Args:
        request: Type request
        session_id: Browser session ID

    Returns:
        Type result
    """
    try:
        result = await service.browser_controller.type_text(
            session_id=session_id,
            selector=request.selector,
            text=request.text,
            delay_ms=request.delay_ms,
        )

        return BrowserActionResponse(
            status=result.get("status", "failed"), result=result, execution_time_ms=0.0
        )

    except Exception as e:
        logger.error(f"Type failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screenshot", response_model=BrowserActionResponse)
async def screenshot(
    request: ScreenshotRequest, session_id: str, service=Depends(get_maba_service)
):
    """
    Take a screenshot.

    Args:
        request: Screenshot request
        session_id: Browser session ID

    Returns:
        Screenshot result with base64 data
    """
    try:
        result = await service.browser_controller.screenshot(
            session_id=session_id,
            full_page=request.full_page,
            selector=request.selector,
        )

        return BrowserActionResponse(
            status=result.get("status", "failed"), result=result, execution_time_ms=0.0
        )

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=BrowserActionResponse)
async def extract_data(
    request: ExtractRequest, session_id: str, service=Depends(get_maba_service)
):
    """
    Extract data from current page.

    Args:
        request: Extract request
        session_id: Browser session ID

    Returns:
        Extracted data
    """
    try:
        result = await service.browser_controller.extract_data(
            session_id=session_id,
            selectors=request.selectors,
            extract_all=request.extract_all,
        )

        return BrowserActionResponse(
            status=result.get("status", "failed"), result=result, execution_time_ms=0.0
        )

    except Exception as e:
        logger.error(f"Extract failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cognitive-map/query", response_model=CognitiveMapQueryResponse)
async def query_cognitive_map(
    request: CognitiveMapQueryRequest, service=Depends(get_maba_service)
):
    """
    Query the cognitive map for learned information.

    Args:
        request: Cognitive map query request

    Returns:
        Query results
    """
    try:
        if request.query_type == "find_element":
            selector = await service.cognitive_map.find_element(
                url=request.parameters.get("url"),
                description=request.parameters.get("description"),
                min_importance=request.parameters.get("min_importance", 0.3),
            )

            if selector:
                return CognitiveMapQueryResponse(
                    found=True, result={"selector": selector}, confidence=0.8
                )
            else:
                return CognitiveMapQueryResponse(
                    found=False, result=None, confidence=0.0
                )

        elif request.query_type == "get_path":
            path = await service.cognitive_map.get_navigation_path(
                from_url=request.parameters.get("from_url"),
                to_url=request.parameters.get("to_url"),
            )

            if path:
                return CognitiveMapQueryResponse(
                    found=True, result={"path": path}, confidence=0.9
                )
            else:
                return CognitiveMapQueryResponse(
                    found=False, result=None, confidence=0.0
                )

        else:
            raise ValueError(f"Unknown query type: {request.query_type}")

    except Exception as e:
        logger.error(f"Cognitive map query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=PageAnalysisResponse)
async def analyze_page(
    request: PageAnalysisRequest, session_id: str, service=Depends(get_maba_service)
):
    """
    Analyze current page with LLM.

    This endpoint uses Claude to analyze the page content and provide
    insights, recommendations, or structured data extraction.

    NOTE: LLM-based page analysis is planned for future implementation.
    This endpoint currently returns HTTP 501 Not Implemented.

    Args:
        request: Page analysis request
        session_id: Browser session ID

    Returns:
        Analysis results

    Raises:
        HTTPException: 501 - Feature not yet implemented
    """
    raise HTTPException(
        status_code=501,
        detail={
            "error": "Not Implemented",
            "message": "LLM-based page analysis is not yet implemented",
            "planned_for": "Phase 2 (MVP expansion)",
            "alternative": "Use /extract endpoint for structured data extraction",
            "documentation": "/docs#tag/MABA/operation/extract_data_extract_post",
        },
    )


@router.get("/stats")
async def get_stats(service=Depends(get_maba_service)):
    """
    Get MABA statistics.

    Returns:
        Statistics dict
    """
    try:
        # Check if service has a get_stats method (for testing/mocking)
        if hasattr(service, "get_stats") and callable(service.get_stats):
            # If mock returns a value directly, use it
            stats = service.get_stats()
            if not asyncio.iscoroutine(stats):
                return stats
            return await stats

        # Otherwise collect stats from components
        cognitive_map_stats = (
            await service.cognitive_map.get_stats() if service.cognitive_map else {}
        )
        browser_health = (
            await service.browser_controller.health_check()
            if service.browser_controller
            else {}
        )

        return {
            "cognitive_map": cognitive_map_stats,
            "browser": browser_health,
            "uptime_seconds": (
                service.get_uptime_seconds()
                if hasattr(service, "get_uptime_seconds")
                else 0
            ),
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
