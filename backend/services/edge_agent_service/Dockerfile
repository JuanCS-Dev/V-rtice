# FASE 10: Edge Agent Service
# Edge sensor for distributed organism deployment

FROM python:3.11-slim

LABEL maintainer="VÉRTICE Team"
LABEL service="edge_agent"
LABEL phase="FASE_10"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY edge_agent_core.py .
COPY api.py .
COPY __init__.py .

# Create non-root user for security
RUN useradd -m -u 1000 vertice && \
    chown -R vertice:vertice /app

USER vertice

# Expose service port
EXPOSE 8021

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8021/health')" || exit 1

# Run service
CMD ["python", "api.py"]
