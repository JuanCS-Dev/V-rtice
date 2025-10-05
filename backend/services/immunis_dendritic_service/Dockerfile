FROM python:3.11-slim

LABEL maintainer="Maximus AI Team"
LABEL service="immunis_dendritic"
LABEL version="3.0.0"
LABEL description="Dendritic Cell - Pattern Recognition & Presentation"

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
  CMD python -c "import httpx; httpx.get('http://localhost:8014/health')" || exit 1

EXPOSE 8014

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8014", "--log-level", "info"]
