FROM python:3.11-slim

LABEL maintainer="Maximus AI Team"
LABEL service="visual_cortex"
LABEL version="3.0.0"
LABEL description="Biomimetic Visual Processing: Malware Vision + Network Cartography + Event-Driven Sensing"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for visual processing
RUN pip install --no-cache-dir \
    pillow>=10.0.0 \
    scikit-image>=0.21.0

COPY . .

RUN useradd -m -u 1000 maximus && chown -R maximus:maximus /app
USER maximus

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8006/health')" || exit 1

EXPOSE 8006

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8006", "--log-level", "info"]
