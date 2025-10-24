# Vértice Registry Sidecar Agent - ULTRA LIGHTWEIGHT
# Target: ~10MB final image size using Alpine Linux
# Strategy: Single-stage build with minimal Python

FROM python:3.11-alpine

LABEL maintainer="Vértice Team"
LABEL description="Registry Sidecar Agent - Auto-register services with TITANIUM resilience"

# Install dependencies (no build tools needed - pure Python)
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent.py .

# Run as non-root for security
RUN adduser -D -u 1000 sidecar && \
    chown -R sidecar:sidecar /app

USER sidecar

# Health check (agent itself)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ps aux | grep -q "[p]ython.*agent.py" || exit 1

# Run agent
CMD ["python", "-u", "agent.py"]
