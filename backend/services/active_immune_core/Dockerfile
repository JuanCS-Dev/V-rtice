# 🐳 Active Immune Core Service - Production Dockerfile
#
# Version: 2.0 (uv + multi-stage)
# Base: vertice/python311-uv
# Performance: 5x faster build

# ============================================================================
# BUILDER STAGE
# ============================================================================
FROM vertice/python311-uv:latest AS builder

USER root
WORKDIR /build

COPY pyproject.toml requirements.txt ./

RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip sync requirements.txt

# ============================================================================
# RUNTIME STAGE
# ============================================================================
FROM python:3.11.14-slim

LABEL maintainer="Juan & Claude <noreply@vertice.dev>"
LABEL description="Active Immune Core - Autonomous threat detection"
LABEL version="2.0.0"
LABEL service="active-immune-core"

# Runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy venv
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user
RUN groupadd -r immunis && useradd -r -g immunis --uid 1000 immunis

WORKDIR /app

# Copy code
COPY --chown=immunis:immunis . .

# Python config
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

USER immunis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

EXPOSE 8200

# Metadata
LABEL org.opencontainers.image.source="https://github.com/vertice-dev/vertice"
LABEL org.opencontainers.image.description="Active Immune Core with uv"

CMD ["python", "-m", "uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8200", \
     "--workers", "4", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
