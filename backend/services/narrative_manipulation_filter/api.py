"""
Cognitive Defense System - FastAPI Application.

Refactored API with dependency injection, lifespan management,
and comprehensive health checks for all infrastructure components.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from cache_manager import cache_manager
from config import get_settings
from database import db_manager, get_db_session
from kafka_client import kafka_client
from models import (
    AnalysisRequest,
    AnalysisResponse,
    HealthCheckResponse,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown of all infrastructure components:
    - PostgreSQL database
    - Redis cache
    - Kafka producer/consumers
    - ML models (to be added in Phase 2+)
    """
    # ========== STARTUP ==========
    logger.info("🚀 Starting Cognitive Defense System...")

    startup_errors = []

    # 1. Initialize Database
    try:
        await db_manager.initialize()
        if settings.POSTGRES_AUTO_CREATE_TABLES:
            await db_manager.create_tables()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        startup_errors.append(f"Database: {e}")

    # 2. Initialize Cache
    try:
        await cache_manager.initialize()
        logger.info("✅ Redis cache initialized")
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
        startup_errors.append(f"Redis: {e}")

    # 3. Initialize Kafka
    try:
        await kafka_client.initialize_producer()
        logger.info("✅ Kafka producer initialized")
    except Exception as e:
        logger.error(f"❌ Kafka initialization failed: {e}")
        startup_errors.append(f"Kafka: {e}")

    # Phase 2+ ML Models (tracked in GitHub Issue #NARRATIVE_ML_MODELS):
    # - BERTimbau emotion classifier
    # - RoBERTa propaganda detector
    # - BiLSTM-CNN-CRF argument miner
    # - Sentence transformers
    # Currently using rule-based pipeline (Phase 1)

    if startup_errors:
        logger.warning(f"⚠️  Service started with errors: {startup_errors}")
    else:
        logger.info("✅ All systems initialized successfully")

    logger.info(f"🎯 Cognitive Defense System v{settings.SERVICE_VERSION} ready on port {settings.SERVICE_PORT}")

    yield

    # ========== SHUTDOWN ==========
    logger.info("🛑 Shutting down Cognitive Defense System...")

    # Close connections in reverse order
    try:
        await kafka_client.close_all_consumers()
        await kafka_client.close_producer()
        logger.info("✅ Kafka connections closed")
    except Exception as e:
        logger.error(f"Error closing Kafka: {e}")

    try:
        await cache_manager.close()
        logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    try:
        await db_manager.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

    logger.info("👋 Shutdown complete")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Cognitive Defense System",
    description="Advanced narrative manipulation detection inspired by prefrontal cortex architecture",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for all system components.

    Returns:
        HealthCheckResponse with status and component health
    """
    services = {}

    # Check database
    try:
        services["postgres"] = await db_manager.health_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        services["postgres"] = False

    # Check Redis
    try:
        services["redis"] = await cache_manager.health_check()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services["redis"] = False

    # Check Kafka
    try:
        services["kafka"] = await kafka_client.health_check()
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        services["kafka"] = False

    # Phase 2+ ML model health checks (GitHub Issue #NARRATIVE_ML_MODELS):
    # services["bertimbau"] = model_manager.is_loaded("bertimbau")
    # services["roberta"] = model_manager.is_loaded("roberta")
    # etc.

    # Determine overall status
    all_healthy = all(services.values())
    any_healthy = any(services.values())

    if all_healthy:
        overall_status = "healthy"
    elif any_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthCheckResponse(
        status=overall_status,
        version=settings.SERVICE_VERSION,
        timestamp=datetime.utcnow(),
        services=services,
        models_loaded=[],  # Phase 2+: GitHub Issue #NARRATIVE_ML_MODELS
    )


@app.get("/health/simple")
async def simple_health_check() -> Dict[str, str]:
    """Lightweight health check for load balancers."""
    return {"status": "ok"}


# ============================================================================
# ANALYSIS ENDPOINT (STUB - FULL IMPLEMENTATION IN PHASE 2+)
# ============================================================================


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest, db: AsyncSession = Depends(get_db_session)) -> AnalysisResponse:
    """
    Analyze content for narrative manipulation.

    This is a STUB endpoint. Full implementation will be added in Phase 2-6
    with all 4 modules integrated.

    Args:
        request: Analysis request with text and options
        db: Database session (injected)

    Returns:
        Analysis response with threat assessment
    """
    start_time = time.time()

    try:
        # Phase 2-6 Full Pipeline (tracked in GitHub Issues):
        # 1. Text preprocessing (utils.clean_text) - Phase 1 ✓
        # 2. Entity linking (DBpedia Spotlight) - Issue #NARRATIVE_ENTITY_LINKING
        # 3. Argument mining (BiLSTM-CNN-CRF) - Issue #NARRATIVE_ARGUMENT_MINING
        # 4. Module 1: Source Credibility (NewsGuard + Bayesian) - Issue #NARRATIVE_SOURCE_CRED
        # 5. Module 2: Emotional Manipulation (BERTimbau + RoBERTa) - Issue #NARRATIVE_ML_MODELS
        # 6. Module 3: Logical Fallacy (classifiers + Dung's AF) - Phase 1 ✓
        # 7. Module 4: Reality Distortion (ClaimBuster + SPARQL KG) - Issue #NARRATIVE_FACT_CHECK
        # 8. Executive Controller: Threat aggregation - Phase 1 ✓
        # 9. Store results in PostgreSQL - Phase 1 ✓
        # 10. Send events to Kafka - Phase 1 ✓

        # STUB RESPONSE (Phase 1)
        logger.warning("⚠️  Using stub analysis - full implementation in Phase 2+")

        from uuid import uuid4

        from models import (
            CognitiveDefenseAction,
            CognitiveDefenseReport,
            CredibilityRating,
            EmotionalManipulationResult,
            EmotionCategory,
            EmotionProfile,
            LogicalFallacyResult,
            ManipulationSeverity,
            RealityDistortionResult,
            SourceCredibilityResult,
        )

        # Stub module results
        credibility_result = SourceCredibilityResult(
            domain="example.com",
            credibility_score=50.0,
            rating=CredibilityRating.PROCEED_WITH_CAUTION,
            does_not_repeatedly_publish_false_content=0.5,
            gathers_and_presents_info_responsibly=0.5,
            regularly_corrects_errors=0.5,
            handles_difference_between_news_opinion=0.5,
            avoids_deceptive_headlines=0.5,
            website_discloses_ownership=0.5,
            clearly_labels_advertising=0.5,
            reveals_whos_in_charge=0.5,
            provides_names_of_content_creators=0.5,
            historical_reliability=0.5,
            tier_used=1,
        )

        emotional_result = EmotionalManipulationResult(
            manipulation_score=0.3,
            emotion_profile=EmotionProfile(
                primary_emotion=EmotionCategory.NEUTRAL,
                emotion_scores={EmotionCategory.NEUTRAL: 1.0},
                arousal=0.3,
                valence=0.0,
            ),
        )

        logical_result = LogicalFallacyResult(fallacy_score=0.2, coherence_score=0.8)

        reality_result = RealityDistortionResult(distortion_score=0.25, factuality_score=0.75)

        processing_time = (time.time() - start_time) * 1000

        stub_report = CognitiveDefenseReport(
            analysis_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            version=settings.SERVICE_VERSION,
            text=request.text,
            source_url=request.source_url,
            credibility_result=credibility_result,
            emotional_result=emotional_result,
            logical_result=logical_result,
            reality_result=reality_result,
            threat_score=0.0,  # Will be computed by validator
            severity=ManipulationSeverity.LOW,
            recommended_action=CognitiveDefenseAction.ALLOW,
            confidence=0.5,
            reasoning="STUB: Full analysis not yet implemented (Phase 2+)",
            evidence=["Infrastructure initialized", "Awaiting ML models"],
            processing_time_ms=processing_time,
            models_used=[],
        )

        return AnalysisResponse(success=True, report=stub_report, error=None)

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return AnalysisResponse(success=False, report=None, error=str(e))


# ============================================================================
# LEGACY COMPATIBILITY ENDPOINT (TO BE DEPRECATED)
# ============================================================================


@app.post("/analyze_content")
async def legacy_analyze_content(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Legacy endpoint for backwards compatibility.

    DEPRECATED: Use /api/analyze instead.
    """
    logger.warning("⚠️  Legacy endpoint /analyze_content called - use /api/analyze instead")

    response = await analyze_content(request)

    if response.success:
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": response.report.model_dump() if response.report else {},
        }
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.error)


# ============================================================================
# STATISTICS & MONITORING ENDPOINTS
# ============================================================================


@app.get("/stats/cache")
async def cache_stats() -> Dict[str, Any]:
    """Get Redis cache statistics."""
    try:
        stats = await cache_manager.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/stats/database")
async def database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    from database import get_table_count

    try:
        tables = [
            "analysis_history",
            "source_reputation",
            "fact_check_cache",
            "entity_cache",
            "propaganda_patterns",
            "ml_model_metrics",
        ]

        counts = {}
        for table in tables:
            try:
                counts[table] = await get_table_count(table)
            except Exception as e:
                logger.warning(f"Could not get count for {table}: {e}")
                counts[table] = -1

        return {"success": True, "table_counts": counts}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/info")
async def service_info() -> Dict[str, Any]:
    """Get service configuration info."""
    return {
        "service": "Cognitive Defense System",
        "version": settings.SERVICE_VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "config": settings.get_info(),
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        workers=settings.WORKERS,
        log_level="debug" if settings.DEBUG else "info",
        reload=settings.DEBUG,
    )
