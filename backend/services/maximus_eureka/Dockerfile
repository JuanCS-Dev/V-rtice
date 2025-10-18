FROM vertice/python311-uv:latest AS builder
USER root
WORKDIR /build
COPY services/maximus_eureka/pyproject.toml services/maximus_eureka/requirements.txt ./
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && uv pip sync requirements.txt

FROM python:3.11-slim
LABEL maintainer="Juan & Claude" version="2.1.0"
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:${PYTHONPATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN groupadd -r appuser && useradd -r -g appuser --uid 1000 appuser

# Copy shared modules first
WORKDIR /app
COPY --chown=appuser:appuser shared ./backend/shared/

# Copy service code
COPY --chown=appuser:appuser services/maximus_eureka ./backend/services/maximus_eureka/

USER appuser
WORKDIR /app/backend/services/maximus_eureka
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8036/health || exit 1
EXPOSE 8036
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8036"]
