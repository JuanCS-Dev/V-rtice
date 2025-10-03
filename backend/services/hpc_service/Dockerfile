# hPC Service Dockerfile
# Hierarchical Predictive Coding with PyMC3

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create model directory
RUN mkdir -p /app/models

# Copy application code
COPY bayesian_core.py /app/
COPY active_inference.py /app/
COPY main.py /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    HPC_HOST=0.0.0.0 \
    HPC_PORT=8006

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8006/health || exit 1

# Run service
CMD ["python", "main.py"]
