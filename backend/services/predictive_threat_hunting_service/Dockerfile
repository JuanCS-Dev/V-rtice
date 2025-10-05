# FASE 8: Predictive Threat Hunting Service
# Attack prediction and vulnerability forecasting for proactive defense

FROM python:3.11-slim

LABEL maintainer="VÉRTICE Team"
LABEL service="predictive_threat_hunting"
LABEL phase="FASE_8"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY predictive_core.py .
COPY api.py .
COPY __init__.py .

# Create non-root user for security
RUN useradd -m -u 1000 vertice && \
    chown -R vertice:vertice /app

USER vertice

# Expose service port
EXPOSE 8016

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8016/health')" || exit 1

# Run service
CMD ["python", "api.py"]
