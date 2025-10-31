# MVP (MAXIMUS Vision Protocol) - Production Dockerfile
#
# Version: 1.0
# Base: python:3.11-slim
#
# Build: docker build -t mvp:latest .
# Run: docker run -p 8153:8153 mvp:latest

# ============================================================================
# BUILDER STAGE - Install dependencies
# ============================================================================
FROM python:3.11-slim AS builder

LABEL stage="builder"

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# RUNTIME STAGE - Minimal production image
# ============================================================================
FROM python:3.11-slim AS runtime

LABEL maintainer="Juan & Claude <noreply@vertice.dev>"
LABEL version="1.0.0"
LABEL description="MVP - MAXIMUS Vision Protocol for system observability"
LABEL service="mvp"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r mvp && useradd -r -g mvp --uid 1001 mvp

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/narratives /app/shared && \
    chown -R mvp:mvp /app

# Copy shared libraries FIRST (symlink in build context)
COPY --chown=mvp:mvp ./shared /app/shared

# Copy application code (AFTER deps for cache)
COPY --chown=mvp:mvp . .

# Add shared directory to Python path
ENV PYTHONPATH=/app

# Configure Python for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER mvp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8153/health || exit 1

# Expose ports
EXPOSE 8153 9091

# Metadata OCI
LABEL org.opencontainers.image.source="https://github.com/vertice-dev/vertice"
LABEL org.opencontainers.image.description="MVP - MAXIMUS Vision Protocol"
LABEL org.opencontainers.image.licenses="Proprietary"

# Run application
CMD ["python", "main.py"]
