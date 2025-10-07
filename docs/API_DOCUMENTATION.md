```markdown
# Vértice Platform - API Documentation Guide

Comprehensive guide for creating, maintaining, and publishing OpenAPI/Swagger documentation for all 67+ microservices in the Vértice platform.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [OpenAPI Configuration](#openapi-configuration)
3. [Creating New Services](#creating-new-services)
4. [Adding Documentation to Existing Services](#adding-documentation-to-existing-services)
5. [Best Practices](#best-practices)
6. [Accessing Documentation](#accessing-documentation)
7. [Generating Static Documentation](#generating-static-documentation)
8. [CI/CD Integration](#cicd-integration)

---

## Quick Start

### For New Services

```python
from fastapi import FastAPI
from backend.shared.openapi_config import create_openapi_config
from backend.shared.error_handlers import register_error_handlers

# Create app with OpenAPI config
app = FastAPI(**create_openapi_config(
    service_name="My New Service",
    service_description="Description of what this service does",
    version="1.0.0",
    service_port=8001,
))

# Register error handlers
register_error_handlers(app)
```

### For Existing Services

See the [template file](templates/fastapi_service_template.py) for a complete example with:
- Request/response models
- Endpoint documentation
- Tags and descriptions
- Response examples
- Error handling

---

## OpenAPI Configuration

### Shared Module: `backend/shared/openapi_config.py`

This module provides standardized OpenAPI configuration across all services.

#### Features

✅ **Standardized Metadata**
- Title, version, description
- Contact information
- License info

✅ **Server Configurations**
- Development (localhost)
- Docker Compose (internal network)
- Production (API Gateway)

✅ **Security Schemes**
- API Key authentication
- JWT Bearer tokens
- OAuth2 flows

✅ **Common Tags**
- Health
- Analysis
- Scan
- Investigation
- Intelligence
- Response
- Reporting
- Configuration

### Basic Configuration

```python
from backend.shared.openapi_config import create_openapi_config

config = create_openapi_config(
    service_name="IP Intelligence Service",
    service_description="IP reputation and geolocation analysis",
    version="2.0.0",
    service_port=8002,
)

app = FastAPI(**config)
```

### Custom Tags

```python
config = create_openapi_config(
    service_name="My Service",
    service_description="Service description",
    version="1.0.0",
    tags=[
        {
            "name": "Custom Tag",
            "description": "Description of this tag",
        },
        {
            "name": "Another Tag",
            "description": "Another tag description",
        },
    ],
)
```

### Pre-configured Services

Use pre-made configurations for common services:

```python
from backend.shared.openapi_config import (
    get_maximus_core_config,
    get_ip_intelligence_config,
    get_malware_analysis_config,
)

# Maximus Core
app = FastAPI(**get_maximus_core_config())

# IP Intelligence
app = FastAPI(**get_ip_intelligence_config())

# Malware Analysis
app = FastAPI(**get_malware_analysis_config())
```

---

## Creating New Services

### Step 1: Copy the Template

```bash
cp docs/templates/fastapi_service_template.py backend/services/my_service/api.py
```

### Step 2: Update Service Configuration

```python
SERVICE_NAME = "My Awesome Service"
SERVICE_DESCRIPTION = """
**My Awesome Service** - Brief description

Detailed description with:
- Feature 1
- Feature 2
- Feature 3
"""
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8XXX  # Get from ServicePorts constant
```

### Step 3: Define Request/Response Models

```python
from pydantic import BaseModel, Field

class MyRequest(BaseModel):
    """Request model with detailed documentation."""

    field1: str = Field(
        ...,
        description="Description of field1",
        examples=["example1", "example2"],
        min_length=1,
        max_length=100,
    )

    field2: int = Field(
        default=10,
        description="Description of field2",
        ge=1,
        le=100,
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "field1": "example value",
                    "field2": 42,
                }
            ]
        }
```

### Step 4: Document Endpoints

```python
@app.post(
    "/my-endpoint",
    response_model=MyResponse,
    status_code=status.HTTP_200_OK,
    tags=["My Tag"],
    summary="Short endpoint description",
    description="""
    Detailed endpoint description with Markdown support.

    **Features:**
    - Feature 1
    - Feature 2

    **Parameters:**
    - `field1`: Description
    - `field2`: Description
    """,
    responses={
        200: {
            "description": "Success response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {...},
                    }
                }
            },
        },
        400: {"description": "Bad request"},
        500: {"description": "Internal error"},
    },
)
async def my_endpoint(request: MyRequest):
    """Endpoint handler with detailed docstring."""
    # Implementation
    pass
```

---

## Adding Documentation to Existing Services

### Option 1: Minimal Integration (Quick)

Update only the FastAPI app initialization:

```python
# BEFORE
app = FastAPI(title="My Service", version="1.0.0")

# AFTER
from backend.shared.openapi_config import create_openapi_config
from backend.shared.error_handlers import register_error_handlers

app = FastAPI(**create_openapi_config(
    service_name="My Service",
    service_description="Brief description",
    version="1.0.0",
    service_port=8001,
))

register_error_handlers(app)
```

### Option 2: Full Integration (Recommended)

1. **Update app initialization** (as above)
2. **Add Pydantic models** with field descriptions
3. **Add endpoint tags and descriptions**
4. **Add response examples**
5. **Add request validation**

See the [template](templates/fastapi_service_template.py) for complete example.

---

## Best Practices

### 1. **Use Descriptive Names**

❌ **Bad:**
```python
@app.post("/do")
async def do(data: dict):
    pass
```

✅ **Good:**
```python
@app.post("/analyze-threat")
async def analyze_threat(request: ThreatAnalysisRequest):
    """Analyze a threat indicator and assess risk level."""
    pass
```

### 2. **Document All Fields**

❌ **Bad:**
```python
class Request(BaseModel):
    ip: str
    depth: int
```

✅ **Good:**
```python
class Request(BaseModel):
    """Threat analysis request."""

    ip: str = Field(
        ...,
        description="IPv4 or IPv6 address to analyze",
        examples=["192.168.1.1", "2001:0db8::1"],
    )

    depth: int = Field(
        default=3,
        description="Analysis depth (1=quick, 5=deep)",
        ge=1,
        le=5,
    )
```

### 3. **Use Tags for Organization**

```python
@app.post("/scan", tags=["Scanning"])
@app.get("/report", tags=["Reporting"])
@app.get("/health", tags=["Health"])
```

### 4. **Provide Response Examples**

```python
@app.post(
    "/analyze",
    responses={
        200: {
            "description": "Analysis complete",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "threat_level": "high",
                        "confidence": 0.92,
                    }
                }
            },
        },
    },
)
```

### 5. **Use Enums for Limited Values**

```python
from backend.shared.enums import ThreatLevel, ResponseStatus

class Response(BaseModel):
    status: ResponseStatus
    threat_level: ThreatLevel
```

### 6. **Validate Inputs**

```python
from pydantic import field_validator
from backend.shared.validators import validate_ipv4

class Request(BaseModel):
    ip: str

    @field_validator("ip")
    @classmethod
    def validate_ip_format(cls, v):
        return validate_ipv4(v)
```

### 7. **Add Markdown to Descriptions**

```python
description = """
**Comprehensive Threat Analysis**

This endpoint performs multi-source analysis including:
- Reputation checking (VirusTotal, AbuseIPDB)
- Historical behavior analysis
- IOC correlation

**Supported Indicators:**
- IPv4/IPv6 addresses
- Domain names
- File hashes (MD5, SHA1, SHA256)
"""
```

---

## Accessing Documentation

### Interactive Documentation (Swagger UI)

Each service exposes interactive API documentation:

```
http://localhost:{PORT}/docs
```

**Examples:**
- Maximus Core: http://localhost:8001/docs
- IP Intelligence: http://localhost:8002/docs
- Malware Analysis: http://localhost:8003/docs

### Alternative Documentation (ReDoc)

Cleaner, print-friendly documentation:

```
http://localhost:{PORT}/redoc
```

### OpenAPI JSON Schema

Raw OpenAPI schema (for tooling):

```
http://localhost:{PORT}/openapi.json
```

---

## Generating Static Documentation

### Option 1: Export OpenAPI JSON

```bash
# Export OpenAPI schema
curl http://localhost:8001/openapi.json > docs/openapi/maximus-core.json
```

### Option 2: Generate HTML Documentation

```bash
# Install Redoc CLI
npm install -g redoc-cli

# Generate static HTML
redoc-cli bundle http://localhost:8001/openapi.json \
  -o docs/html/maximus-core.html
```

### Option 3: Generate Markdown Documentation

```bash
# Install openapi-generator
npm install @openapitools/openapi-generator-cli -g

# Generate Markdown docs
openapi-generator-cli generate \
  -i http://localhost:8001/openapi.json \
  -g markdown \
  -o docs/markdown/maximus-core/
```

### Option 4: Use Provided Script

```bash
# Generate docs for all services
./scripts/generate-openapi-docs.sh --all

# Generate docs for specific service
./scripts/generate-openapi-docs.sh --service maximus_core_service
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Generate API Docs

on: [push, pull_request]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Generate OpenAPI schemas
        run: |
          python scripts/export-openapi-schemas.py

      - name: Upload docs
        uses: actions/upload-artifact@v3
        with:
          name: openapi-schemas
          path: docs/openapi/
```

### GitLab CI

```yaml
generate_docs:
  stage: docs
  script:
    - pip install -r requirements.txt
    - python scripts/export-openapi-schemas.py
  artifacts:
    paths:
      - docs/openapi/
```

### Docker Compose (Development)

```yaml
services:
  swagger-ui:
    image: swaggerapi/swagger-ui
    ports:
      - "8080:8080"
    environment:
      URLS: |
        [
          { name: "Maximus Core", url: "http://localhost:8001/openapi.json" },
          { name: "IP Intelligence", url: "http://localhost:8002/openapi.json" }
        ]
```

---

## Troubleshooting

### Issue: OpenAPI docs not showing

**Solution**: Check that you're importing and using `create_openapi_config()`:

```python
from backend.shared.openapi_config import create_openapi_config

app = FastAPI(**create_openapi_config(...))
```

### Issue: Error handlers not working

**Solution**: Make sure to register error handlers:

```python
from backend.shared.error_handlers import register_error_handlers

register_error_handlers(app)
```

### Issue: Missing fields in Swagger UI

**Solution**: Ensure Pydantic models have `Field()` with descriptions:

```python
field: str = Field(..., description="Field description")
```

### Issue: Examples not showing

**Solution**: Add `Config` class with `json_schema_extra`:

```python
class MyModel(BaseModel):
    class Config:
        json_schema_extra = {
            "examples": [{"field": "value"}]
        }
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redocly.com/redoc/)

---

## Examples by Service Type

### Analysis Service

See: `backend/services/malware_analysis_service/api.py`

### Intelligence Service

See: `backend/services/ip_intelligence_service/api.py`

### Scanning Service

See: `backend/services/vulnerability_scanning_service/api.py`

### Reporting Service

See: `backend/services/incident_reporting_service/api.py`

---

## Contact

For questions or issues with API documentation:
- Team: Vértice Platform Developers
- Email: dev@vertice.security
- Docs: https://docs.vertice.security
```
