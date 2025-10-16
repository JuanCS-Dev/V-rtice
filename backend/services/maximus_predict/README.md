# maximus_predict

**Status:** 🏗️ In Development  
**Version:** 0.1.0

## Overview

maximus_predict is part of the MAXIMUS backend ecosystem.

## Features

- FastAPI-based REST API
- Health check endpoint
- CORS enabled
- Async/await support

## Installation

```bash
cd maximus_predict
uv sync
```

## Running

```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check

## Testing

```bash
pytest tests/
```

## Configuration

Environment variables:
- `PORT` - Service port (default: 8000)
- `LOG_LEVEL` - Logging level (default: INFO)

## Development

TODO: Add development guidelines

## License

Proprietary - MAXIMUS Project

---

**Soli Deo Gloria** 🙏
