# ═══════════════════════════════════════════════════════════════════════════
# BAS SERVICE - MULTI-STAGE DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
# FLORESCIMENTO - Defense strengthening through simulation
# Para Honra e Glória de JESUS CRISTO
# ═══════════════════════════════════════════════════════════════════════════

FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
LABEL maintainer="Vértice Offensive Arsenal Team"
LABEL description="BAS Service - Breach and Attack Simulation"
LABEL version="1.0.0"

RUN useradd -m -u 1000 vertice && \
    mkdir -p /app && \
    chown -R vertice:vertice /app

COPY --from=builder /root/.local /home/vertice/.local
RUN chown -R vertice:vertice /home/vertice/.local

ENV PATH=/home/vertice/.local/bin:$PATH
WORKDIR /app
COPY --chown=vertice:vertice main.py .
USER vertice
EXPOSE 8036

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8036/health', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8036", "--workers", "2"]
