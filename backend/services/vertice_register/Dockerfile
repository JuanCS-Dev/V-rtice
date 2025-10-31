# Vértice Service Registry - Optimized Multi-Stage Build
# Target: <2s startup time, <50MB image size

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="Vértice Team"
LABEL description="Service Registry (RSS) - Mission Critical"

# Create non-root user for security
RUN useradd -m -u 1000 registry && \
    mkdir -p /app && \
    chown -R registry:registry /app

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/registry/.local

# Copy application code (TITANIUM - all modules)
COPY --chown=registry:registry main.py redis_backend.py cache.py \
                                system_metrics.py validation.py \
                                rate_limiter.py audit_logger.py ./

# Set environment
ENV PATH=/home/registry/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REDIS_HOST=vertice-redis-master \
    REDIS_PORT=6379

# Switch to non-root user
USER registry

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8888/health')"

# Expose port
EXPOSE 8888

# Constitutional v3.0 - Metrics port
EXPOSE 9090


# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "1", "--log-level", "info"]
