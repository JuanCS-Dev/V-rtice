# ============================================================================
# OFFENSIVE SECURITY GATEWAY - Dockerfile
# Unified Orchestration Layer
# ============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /var/log/offensive_gateway

# Expose ports
EXPOSE 8037 9037

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8037/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    SERVICE_NAME=offensive_gateway \
    SERVICE_PORT=8037

# Run the application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8037"]
