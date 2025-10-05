# ============================================================================
# VULNERABILITY INTELLIGENCE SERVICE - Dockerfile
# Template-Driven Scanning with Nuclei
# ============================================================================

FROM golang:1.24-alpine AS nuclei-builder

# Install Nuclei from source
RUN apk add --no-cache git && \
    GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Nuclei binary from builder
COPY --from=nuclei-builder /go/bin/nuclei /usr/bin/nuclei

# Verify Nuclei installation
RUN nuclei -version

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/vuln_intel /app/nuclei-templates /app/data

# Expose ports
EXPOSE 8033 9033

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8033/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    SERVICE_NAME=vulnerability_intelligence \
    SERVICE_PORT=8033 \
    NUCLEI_TEMPLATES_DIR=/app/nuclei-templates

# Run the application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8033"]
