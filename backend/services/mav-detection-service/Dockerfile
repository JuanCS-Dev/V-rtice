FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
LABEL description="MAV Detection & Protection Service - Social Defense Arsenal"
LABEL version="1.0.0"

RUN useradd -m -u 1000 vertice && mkdir -p /app && chown -R vertice:vertice /app
COPY --from=builder /root/.local /home/vertice/.local
RUN chown -R vertice:vertice /home/vertice/.local

ENV PATH=/home/vertice/.local/bin:$PATH
WORKDIR /app
COPY --chown=vertice:vertice main.py neo4j_client.py docker-entrypoint.sh ./
COPY --chown=vertice:vertice migrations ./migrations/
COPY --chown=vertice:vertice shared ./shared/
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER vertice
EXPOSE 8039

# Constitutional v3.0 - Metrics port
EXPOSE 9090


HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8039/health', timeout=2)" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8039", "--workers", "2"]
