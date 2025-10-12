"""
MAXIMUS Eureka - FastAPI Application.

Exposes REST API endpoints for:
- ML prediction metrics and analytics (Phase 5.5)
- Insight generation
- Pattern detection
- IoC extraction

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - Source of all wisdom
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ml_metrics import router as ml_metrics_router
from middleware.rate_limiter import (
    SlidingWindowRateLimiter,
    RateLimitMiddleware
)

# Import legacy API routes
from api import *

app = FastAPI(
    title="MAXIMUS Eureka Service",
    version="5.5.1",
    description="Adaptive Immune System - Remediation & ML Intelligence"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════
# RATE LIMITING (Sprint 6 - Issue #11)
# ═══════════════════════════════════════════════════════════════════════

# Create rate limiter instance
rate_limiter = SlidingWindowRateLimiter(
    default_limit=100,  # 100 req/min default
    window_seconds=60,
    burst_limit=200  # 200 req/sec burst
)

# Set endpoint-specific limits
rate_limiter.set_endpoint_limit("/api/v1/eureka/ml-metrics", limit=200, window_seconds=60)
rate_limiter.set_endpoint_limit("/api/v1/eureka/ml-metrics/recent-predictions", limit=50, window_seconds=60)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    limiter=rate_limiter,
    exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/"]
)

# Include ML metrics router (Phase 5.5)
app.include_router(ml_metrics_router)

# Include legacy routes from api.py
# These will be mounted at root level for backwards compatibility
from api import app as legacy_app
# Copy routes from legacy app
for route in legacy_app.routes:
    app.routes.append(route)


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Eureka Service."""
    print("🚀 Starting MAXIMUS Eureka API Service...")
    print("   Phase 5.5: ML Intelligence Monitoring ACTIVE")
    print("✅ API Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Eureka Service."""
    print("👋 Shutting down MAXIMUS Eureka API Service...")
    print("🛑 API Service stopped")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MAXIMUS Eureka",
        "version": "5.5.1",
        "phase": "5.5 - ML Intelligence Monitoring + Rate Limiting",
        "status": "operational",
        "endpoints": {
            "ml_metrics": "/api/v1/eureka/ml-metrics",
            "ml_health": "/api/v1/eureka/ml-metrics/health",
            "rate_limit_metrics": "/api/v1/eureka/rate-limit/metrics",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/api/v1/eureka/rate-limit/metrics")
async def rate_limit_metrics():
    """
    Get rate limiting metrics.
    
    Returns current rate limiter statistics:
    - Total hits
    - Total blocks  
    - Block rate
    - Active clients
    - Configuration
    
    Sprint 6 - Issue #11
    """
    return rate_limiter.get_metrics()


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8024,
        reload=True,
        log_level="info"
    )
