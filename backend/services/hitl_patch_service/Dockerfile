# HITL Patch Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY hitl_patch_service/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hitl_patch_service /app

# Expose port
EXPOSE 8027

# Run application
CMD ["python", "api/main.py"]
