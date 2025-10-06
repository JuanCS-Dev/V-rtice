FROM python:3.11-slim

LABEL maintainer="Maximus AI Team"
LABEL service="cloud_coordinator"
LABEL version="1.0.0"
LABEL fase="10"

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 maximus && \
    chown -R maximus:maximus /app

USER maximus

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8051/health')" || exit 1

EXPOSE 8051

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8051", "--log-level", "info"]
