FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MIP code
COPY . /app/mip/

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8100/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "mip.api:app", "--host", "0.0.0.0", "--port", "8100"]
