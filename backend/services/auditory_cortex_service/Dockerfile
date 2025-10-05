FROM python:3.11-slim

LABEL maintainer="Maximus AI Team"
LABEL service="auditory_cortex"
LABEL version="3.0.0"
LABEL description="Biomimetic Auditory Processing: C2 FFT + Binaural Correlation + Cocktail Party ASA + TTP Recognition"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install scipy for FFT analysis
RUN pip install --no-cache-dir scipy>=1.11.0

COPY . .

RUN useradd -m -u 1000 maximus && chown -R maximus:maximus /app
USER maximus

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8007/health')" || exit 1

EXPOSE 8007

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8007", "--log-level", "info"]
