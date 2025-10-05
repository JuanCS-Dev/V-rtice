FROM python:3.11-slim

LABEL maintainer="Maximus AI Team"
LABEL service="chemical_sensing"
LABEL version="3.0.0"
LABEL description="Biomimetic Chemical Sensing: Olfactory (Malware Odor) + Gustatory (Payload Taste)"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install numpy for statistical processing
RUN pip install --no-cache-dir numpy>=1.24.0

COPY . .

RUN useradd -m -u 1000 maximus && chown -R maximus:maximus /app
USER maximus

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8009/health')" || exit 1

EXPOSE 8009

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8009", "--log-level", "info"]
