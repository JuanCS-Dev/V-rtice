# Behavioral Analyzer Service

Analyzes behavioral patterns to detect anomalies and threats based on system and user behavior.

## Purpose

Behavioral analysis and anomaly detection

## Features

- FastAPI-based REST API
- Async/await support
- Health check endpoint
- Prometheus metrics
- Docker containerization

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `SERVICE_NAME`: Service identifier
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `PORT`: Service port

## Development

### Prerequisites

- Python 3.11+
- Docker (optional)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run service
python main.py
```

### Docker

```bash
# Build
docker build -t vertice-behavioral_analyzer_service .

# Run
docker run -p 8000:8000 --env-file .env vertice-behavioral_analyzer_service
```

## API

### Health Check

```bash
GET /health
```

Returns service health status.

### Metrics

```bash
GET /metrics
```

Prometheus metrics endpoint.

## Architecture

This service is part of the Vértice distributed intelligence platform.

For more information, see the [main documentation](../../../docs/).

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=behavioral_analyzer_service --cov-report=html
```

## License

See main repository LICENSE file.
