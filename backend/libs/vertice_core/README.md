# vertice-core

Core utilities for Vértice services.

## Installation

```bash
pip install vertice-core
```

## Usage

### Structured Logging

```python
from vertice_core import get_logger

logger = get_logger("my_service")
logger.info("user_login", user_id=123, ip="192.168.1.1")
```

### Configuration

```python
from vertice_core import BaseServiceSettings

class MySettings(BaseServiceSettings):
    pass

settings = MySettings(service_name="my_service", port=8000)
```

### Exceptions

```python
from vertice_core import NotFoundError, ValidationError

raise NotFoundError("User", 123)
raise ValidationError("Invalid email", field="email")
```

### Metrics

```python
from vertice_core import create_service_metrics

metrics = create_service_metrics("my_service")
metrics["requests_total"].labels(method="GET", endpoint="/", status=200).inc()
```

### Tracing

```python
from vertice_core import setup_tracing

tracer = setup_tracing("my_service", "1.0.0")
```

## License

MIT
