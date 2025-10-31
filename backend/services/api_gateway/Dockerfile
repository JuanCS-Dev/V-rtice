FROM python:3.11-slim AS builder
USER root
WORKDIR /build
RUN pip install --no-cache-dir uv
COPY pyproject.toml requirements.txt ./
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && uv pip sync requirements.txt

FROM python:3.11-slim
LABEL maintainer="Juan & Claude" version="2.0.1"
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN groupadd -r appuser && useradd -r -g appuser --uid 1000 appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000

# Constitutional v3.0 - Metrics port
EXPOSE 9090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
