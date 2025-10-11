FROM python:3.11-slim

WORKDIR /app

# Install ping utility
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

# Install Flask
RUN pip install --no-cache-dir flask==3.0.0

# Copy app
COPY app.py .

# Expose port
EXPOSE 5000

# Run
CMD ["python", "app.py"]
