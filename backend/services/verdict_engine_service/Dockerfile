FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy service files
COPY *.py ./
COPY pyproject.toml* ./
COPY tests/ ./tests/

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn prometheus-client structlog pydantic pydantic-settings asyncpg

# Expose port
EXPOSE 8093

# Constitutional v3.0 - Metrics port
EXPOSE 9090


# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8093/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8093"]
