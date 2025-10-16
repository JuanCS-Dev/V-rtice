# Service Template - Clean Architecture

Production-ready template for Vértice MAXIMUS microservices following Clean Architecture principles.

## Architecture Layers

```
src/service_template/
├── domain/           # Business entities and rules (framework-independent)
├── application/      # Use cases and application logic
├── infrastructure/   # External integrations (DB, cache, APIs)
└── presentation/     # HTTP API (FastAPI)
```

## Features

- ✅ Clean Architecture (domain-centric)
- ✅ Type-safe (mypy strict)
- ✅ Async/await throughout
- ✅ SQLAlchemy 2.0 (async)
- ✅ Pydantic v2
- ✅ FastAPI with dependency injection
- ✅ Prometheus metrics
- ✅ Health checks
- ✅ CORS configured
- ✅ 95%+ test coverage

## Quick Start

```bash
# Install
cd /home/juan/vertice-dev/backend/service_template
pip install -e ".[dev]"

# Run
python -m service_template.main

# Or with uvicorn
uvicorn service_template.main:app --reload --port 8000
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /api/v1/entities` - Create entity
- `GET /api/v1/entities` - List entities (paginated)
- `GET /api/v1/entities/{id}` - Get entity by ID
- `PUT /api/v1/entities/{id}` - Update entity
- `DELETE /api/v1/entities/{id}` - Delete entity

## Testing

```bash
pytest
pytest --cov=service_template --cov-report=html
mypy src/
ruff check src/
```

## Environment Variables

See `.env` file for configuration options.

## Adapting for New Service

1. Replace `ExampleEntity` with your domain model
2. Update `ExampleRepository` interface
3. Implement repository in infrastructure layer
4. Create use cases in application layer
5. Add routes in presentation layer
6. Update tests

## Compliance

- Constituição Vértice Article II (Padrão Pagani): ✅ Zero mocks, 95%+ coverage
- Clean Architecture: ✅ Dependency inversion enforced
- Type Safety: ✅ mypy strict mode
- Testing: ✅ Unit + integration tests
