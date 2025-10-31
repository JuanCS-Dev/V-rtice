FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY main.py .

# Copy security module from parent context (needs to be built from backend/ dir)
# This service imports: from security.offensive.api.offensive_tools

# Environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8010

EXPOSE 8010

# Constitutional v3.0 - Metrics port
EXPOSE 9090


# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8010/health')"

CMD ["python", "main.py"]
