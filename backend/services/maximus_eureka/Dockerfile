FROM python:3.11-slim

LABEL maintainer="Vertice Team <dev@vertice.ai>"
LABEL description="MAXIMUS EUREKA - Deep Malware Analysis Orchestrator"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn[standard] python-multipart && \
    pip install --no-cache-dir pyyaml requests

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 vertice && chown -R vertice:vertice /app
USER vertice

# Expose port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8200/health')"

# Run application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8200", "--workers", "2"]
