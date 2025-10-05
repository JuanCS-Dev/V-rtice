# FASE 9: Adaptive Immunity Service
# Antibody diversification and affinity maturation

FROM python:3.11-slim

LABEL maintainer="VÉRTICE Team"
LABEL service="adaptive_immunity"
LABEL phase="FASE_9"

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
COPY adaptive_core.py .
COPY api.py .
COPY __init__.py .

# Create non-root user for security
RUN useradd -m -u 1000 vertice && \
    chown -R vertice:vertice /app

USER vertice

# Expose service port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8020/health')" || exit 1

# Run service
CMD ["python", "api.py"]
