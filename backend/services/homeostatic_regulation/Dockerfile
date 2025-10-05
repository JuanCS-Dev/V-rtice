# ============================================================================
# HOMEOSTATIC REGULATION - Dockerfile
# Global system health monitoring and safety boundaries
# ============================================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/homeostatic_regulation /app/data

# Expose ports
EXPOSE 8015 9015

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8015/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    SERVICE_NAME=homeostatic_regulation \
    SERVICE_PORT=8015

# Run the application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8015"]
