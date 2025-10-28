# Narrative Filter Service

Filters and analyzes narrative manipulation attempts in data streams.

## Purpose

Narrative manipulation detection and filtering

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
docker build -t vertice-narrative_filter_service .

# Run
docker run -p 8000:8000 --env-file .env vertice-narrative_filter_service
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
pytest tests/ --cov=narrative_filter_service --cov-report=html
```

## License

See main repository LICENSE file.
