# ============================================================================
# NETWORK RECONNAISSANCE SERVICE - Dockerfile
# Two-Stage Reconnaissance with Masscan + Nmap
# ============================================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including masscan and nmap
RUN apt-get update && apt-get install -y \
    curl \
    masscan \
    nmap \
    git \
    build-essential \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/network_recon /app/data

# Expose ports
EXPOSE 8032 9032

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8032/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    SERVICE_NAME=network_reconnaissance \
    SERVICE_PORT=8032

# Note: Masscan requires elevated privileges for SYN scanning
# Run with --cap-add=NET_ADMIN or --privileged if needed

# Run the application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8032"]
