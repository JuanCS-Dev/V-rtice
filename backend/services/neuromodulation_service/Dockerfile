FROM python:3.11-slim

LABEL maintainer="Maximus AI Team"
LABEL service="neuromodulation"
LABEL version="3.0.0"
LABEL description="Digital Neurotransmitters: Dopamine, Serotonin, Acetylcholine, Noradrenaline"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 maximus && chown -R maximus:maximus /app
USER maximus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8033/health')" || exit 1

# Expose port
EXPOSE 8033

# Run service
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8033", "--log-level", "info"]
