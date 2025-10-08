# Active Immune Core Service - Production Dockerfile
# Multi-stage build for minimal image size

# ==================== BUILDER STAGE ====================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy lock file for deterministic builds
COPY requirements.txt.lock .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-deps -r requirements.txt.lock

# ==================== RUNTIME STAGE ====================
FROM python:3.11-slim

LABEL maintainer="Juan & Claude"
LABEL description="Active Immune Core Service - Autonomous threat detection"
LABEL version="1.0.0"

# Create app user (non-root)
RUN groupadd -r immunis && useradd -r -g immunis immunis

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app directory
WORKDIR /app

# Copy application code
COPY . /app/

# Change ownership to app user
RUN chown -R immunis:immunis /app

# Switch to app user
USER immunis

# Expose service port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Run service (production with 4 workers for better concurrency)
CMD ["python", "-m", "uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8200", \
     "--workers", "4", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
