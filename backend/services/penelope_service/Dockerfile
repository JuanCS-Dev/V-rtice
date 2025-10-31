# PENELOPE (Self-Healing Service) - Production Dockerfile
#
# Version: 1.0 - Biblical Governance Edition
# Base: python:3.11-slim
#
# Build: docker build -t penelope:latest .
# Run: docker run -p 8154:8154 penelope:latest

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

# ============================================================================
# RUNTIME STAGE - Minimal production image
# ============================================================================
FROM python:3.11-slim AS runtime

LABEL maintainer="Juan & Claude <noreply@vertice.dev>"
LABEL version="1.0.0"
LABEL description="PENELOPE - Self-Healing Service with Biblical Governance"
LABEL service="penelope"
LABEL governance="7_biblical_articles"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user (with humility - Tapeinophrosyne)
RUN groupadd -r penelope && useradd -r -g penelope --uid 1002 penelope

WORKDIR /app

# Create necessary directories (Stewardship - Article IV)
RUN mkdir -p /app/logs /app/patches /app/diagnoses /app/shared && \
    chown -R penelope:penelope /app

# Copy shared libraries FIRST (symlink in build context)
COPY --chown=penelope:penelope ./shared /app/shared

# Copy application code (AFTER deps for cache)
COPY --chown=penelope:penelope . .

# Add shared directory to Python path
ENV PYTHONPATH=/app

# Configure Python for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Sabbath configuration (Article VI)
ENV PENELOPE_SABBATH_ENABLED=true \
    PENELOPE_SABBATH_TIMEZONE=America/Sao_Paulo

# Switch to non-root user
USER penelope

# Health check (Praotes - gentle checks)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8154/health || exit 1

# Expose ports
EXPOSE 8154 9092

# Metadata OCI
LABEL org.opencontainers.image.source="https://github.com/vertice-dev/vertice"
LABEL org.opencontainers.image.description="PENELOPE - Self-Healing Service"
LABEL org.opencontainers.image.licenses="Proprietary"
LABEL biblical.article.i="Sophia - Wisdom"
LABEL biblical.article.ii="Praotes - Gentleness"
LABEL biblical.article.iii="Tapeinophrosyne - Humility"
LABEL biblical.article.iv="Stewardship"
LABEL biblical.article.v="Agape - Love"
LABEL biblical.article.vi="Sabbath - Rest"
LABEL biblical.article.vii="Aletheia - Truth"

# Run application (Soli Deo Gloria)
CMD ["python", "main.py"]
