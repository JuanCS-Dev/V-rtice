# ═══════════════════════════════════════════════════════════════════════════
# C2 ORCHESTRATION SERVICE - MULTI-STAGE DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
# FLORESCIMENTO - Ethical operations through secure containerization
# Para Honra e Glória de JESUS CRISTO
# ═══════════════════════════════════════════════════════════════════════════

FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ───────────────────────────────────────────────────────────────────────────
# STAGE 2: RUNTIME
# ───────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Vértice Offensive Arsenal Team"
LABEL description="C2 Orchestration Service - Ethical C2 Operations"
LABEL version="1.0.0"

# Create non-root user FIRST
RUN useradd -m -u 1000 vertice && \
    mkdir -p /app && \
    chown -R vertice:vertice /app

# Copy packages from builder
COPY --from=builder /root/.local /home/vertice/.local
RUN chown -R vertice:vertice /home/vertice/.local

ENV PATH=/home/vertice/.local/bin:$PATH

WORKDIR /app

COPY --chown=vertice:vertice main.py .

USER vertice

EXPOSE 8035

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8035/health', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8035", "--workers", "2"]
