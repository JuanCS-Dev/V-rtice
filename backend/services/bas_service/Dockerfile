# ============================================================================
# BREACH & ATTACK SIMULATION SERVICE - Dockerfile
# MITRE ATT&CK Purple Team Automation
# ============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /var/log/bas /app/data/reports /app/data/ssh /app/data/atomic-red-team

# Expose ports
EXPOSE 8036 9036

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8036/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    SERVICE_NAME=breach_attack_simulation \
    SERVICE_PORT=8036

# Run the application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8036"]
