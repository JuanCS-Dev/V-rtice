FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Optional: Install Intel Hyperscan (if available)
# RUN apt-get update && apt-get install -y libhyperscan-dev

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for signatures and models
RUN mkdir -p /app/signatures /app/models

# Expose port
EXPOSE 8003

# Run FastAPI service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
