# ═══════════════════════════════════════════════════════════════════════════
# VULNERABILITY INTELLIGENCE SERVICE - DOCKERFILE (Pagani Standard)
# ═══════════════════════════════════════════════════════════════════════════
# Multi-stage build for minimal attack surface
# Para Honra e Glória de JESUS CRISTO
# ═══════════════════════════════════════════════════════════════════════════

FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ───────────────────────────────────────────────────────────────────────────
# RUNTIME STAGE (minimal)
# ───────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Create non-root user first
RUN useradd -m -u 1000 vertice && \
    mkdir -p /app && \
    chown -R vertice:vertice /app

# Copy Python packages from builder to vertice user
COPY --from=builder /root/.local /home/vertice/.local
RUN chown -R vertice:vertice /home/vertice/.local

# Set PATH for vertice user
ENV PATH=/home/vertice/.local/bin:$PATH

WORKDIR /app

# Copy application code
COPY --chown=vertice:vertice main.py .

# Switch to non-root user
USER vertice

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8033/health')" || exit 1

# Expose port
EXPOSE 8033

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8033", "--workers", "2"]
