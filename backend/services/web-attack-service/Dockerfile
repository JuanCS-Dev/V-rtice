# ═══════════════════════════════════════════════════════════════════════════
# WEB ATTACK SURFACE SERVICE - MULTI-STAGE DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
# FLORESCIMENTO - Organic growth through secure containerization
# Security-hardened, non-root, minimal attack surface
# Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
# ═══════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────
# STAGE 1: BUILDER - Install dependencies
# ───────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to user directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ───────────────────────────────────────────────────────────────────────────
# STAGE 2: RUNTIME - Minimal production image
# ───────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Vértice Offensive Arsenal Team"
LABEL description="Web Attack Surface Service - FLORESCIMENTO ✨"
LABEL version="1.0.0"

# Create non-root user FIRST
RUN useradd -m -u 1000 vertice && \
    mkdir -p /app && \
    chown -R vertice:vertice /app

# Copy installed packages from builder to vertice user home
COPY --from=builder /root/.local /home/vertice/.local
RUN chown -R vertice:vertice /home/vertice/.local

# Set PATH for vertice user
ENV PATH=/home/vertice/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=vertice:vertice main.py .

# Switch to non-root user
USER vertice

# Expose service port
EXPOSE 8034

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8034/health', timeout=2)" || exit 1

# Start application with 2 workers for concurrency
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8034", "--workers", "2"]
