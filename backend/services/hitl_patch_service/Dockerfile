# HITL Patch Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt /app/requirements.txt

# Install dependencies + curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Expose port
EXPOSE 8027

# Constitutional v3.0 - Metrics port
EXPOSE 9090


# Health check (Sprint 6 - Issue #16)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8027/health || exit 1

# Run application
CMD ["python", "-m", "api.main"]
