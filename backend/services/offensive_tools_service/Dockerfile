FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/offensive_tools_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend security modules (parent context)
COPY security /app/security

# Copy service files
COPY services/offensive_tools_service/main.py .

# Environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8010

EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8010/health')"

CMD ["python", "main.py"]
