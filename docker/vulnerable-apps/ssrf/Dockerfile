FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask==3.0.0 requests==2.31.0

# Copy app
COPY app.py .

# Expose port
EXPOSE 5000

# Run
CMD ["python", "app.py"]
