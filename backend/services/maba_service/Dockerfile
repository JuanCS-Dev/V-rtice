# MABA (MAXIMUS Browser Agent) - Production Dockerfile
#
# Version: 1.0
# Base: python:3.11-slim + Playwright
#
# Build: docker build -t maba:latest .
# Run: docker run -p 8152:8152 maba:latest

# ============================================================================
# BUILDER STAGE - Install dependencies
# ============================================================================
FROM python:3.11-slim AS builder

LABEL stage="builder"

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers in venv (deps installed separately in runtime)
RUN . /opt/venv/bin/activate && \
    playwright install chromium

# ============================================================================
# RUNTIME STAGE - Minimal production image
# ============================================================================
FROM python:3.11-slim AS runtime

LABEL maintainer="Juan & Claude <noreply@vertice.dev>"
LABEL version="1.0.0"
LABEL description="MABA - MAXIMUS Browser Agent for autonomous web automation"
LABEL service="maba"

# Install runtime dependencies (Playwright browser deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxshmfence1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Playwright browsers from builder
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Create non-root user
RUN groupadd -r maba && useradd -r -g maba --uid 1000 maba

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/screenshots /app/shared && \
    chown -R maba:maba /app

# Copy shared libraries FIRST (symlink in build context)
COPY --chown=maba:maba ./shared /app/shared

# Copy application code (AFTER deps for cache)
COPY --chown=maba:maba . .

# Add shared directory to Python path
ENV PYTHONPATH=/app

# Configure Python for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER maba

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8152/health || exit 1

# Expose ports
EXPOSE 8152 9090

# Metadata OCI
LABEL org.opencontainers.image.source="https://github.com/vertice-dev/vertice"
LABEL org.opencontainers.image.description="MABA - MAXIMUS Browser Agent"
LABEL org.opencontainers.image.licenses="Proprietary"

# Run application
CMD ["python", "main.py"]
