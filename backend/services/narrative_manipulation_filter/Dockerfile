# ============================================================================
# NARRATIVE MANIPULATION FILTER - Docker Container
# Multi-layer detection and protection against narrative manipulation
# ============================================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Create log directory
RUN mkdir -p /var/log/narrative_filter

# Expose service port
EXPOSE 8013

# Expose Prometheus metrics port
EXPOSE 9013

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8013/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=narrative_manipulation_filter
ENV SERVICE_HOST=0.0.0.0
ENV SERVICE_PORT=8013

# Run the service
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8013"]
