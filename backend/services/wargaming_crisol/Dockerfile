# Wargaming Crisol Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including Docker CLI for Docker-in-Docker)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8026

# Health check (Sprint 6 - Issue #16)
# Checks /health endpoint + DB/Redis connectivity
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8026/health || exit 1

# Run application
CMD ["python", "main.py"]
