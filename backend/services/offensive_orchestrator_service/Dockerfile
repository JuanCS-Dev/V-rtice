# Offensive Orchestrator Service - Production Dockerfile
# Multi-stage build for optimized image size
# Python 3.11 slim base

FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Security: Run as non-root user
RUN useradd -m -u 1000 maximus && \
    mkdir -p /app /var/log/hotl && \
    chown -R maximus:maximus /app /var/log/hotl

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/maximus/.local

# Copy application code
COPY --chown=maximus:maximus . .

# Switch to non-root user
USER maximus

# Add local Python packages to PATH
ENV PATH=/home/maximus/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8090/health')"

# Expose port
EXPOSE 8090

# Constitutional v3.0 - Metrics port
EXPOSE 9090


# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "4"]
