FROM python:3.11-slim

LABEL maintainer="Maximus AI Team"
LABEL service="immunis_macrophage"
LABEL version="3.0.0"
LABEL description="Macrophage - Threat Engulfment & Analysis"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 maximus && chown -R maximus:maximus /app
USER maximus

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8012/health')" || exit 1

EXPOSE 8012

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8012", "--log-level", "info"]
