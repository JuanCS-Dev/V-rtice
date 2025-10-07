# Vértice Platform - OpenAPI Schemas

This directory contains exported OpenAPI 3.0 schemas for all Vértice platform microservices.

## Directory Structure

```
docs/openapi/
├── README.md                          # This file
├── maximus_core_service.json          # Maximus Core API schema
├── ip_intelligence_service.json       # IP Intelligence API schema
├── malware_analysis_service.json      # Malware Analysis API schema
└── ...                                 # Additional service schemas
```

## What is OpenAPI?

OpenAPI (formerly Swagger) is a specification for describing REST APIs. These JSON schemas can be used to:

- **Generate documentation** (Swagger UI, ReDoc)
- **Generate client libraries** (Python, JavaScript, Go, etc.)
- **Validate API requests/responses**
- **Test APIs** (Postman, Insomnia, etc.)
- **Mock APIs** for development

## Exporting Schemas

### Automatic Export (All Services)

```bash
# Export all running services
python scripts/export-openapi-schemas.py

# Export to custom directory
python scripts/export-openapi-schemas.py --output /tmp/schemas/
```

### Single Service Export

```bash
# Export specific service
python scripts/export-openapi-schemas.py --service maximus_core_service

# Or download directly
curl http://localhost:8001/openapi.json > maximus_core_service.json
```

### Scheduled Export (Cron)

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd /path/to/vertice && python scripts/export-openapi-schemas.py
```

## Viewing Schemas

### Option 1: Interactive Documentation (Swagger UI)

Navigate to the service's `/docs` endpoint:

```
http://localhost:8001/docs  # Maximus Core
http://localhost:8002/docs  # IP Intelligence
```

### Option 2: Alternative UI (ReDoc)

Navigate to the service's `/redoc` endpoint:

```
http://localhost:8001/redoc  # Maximus Core
http://localhost:8002/redoc  # IP Intelligence
```

### Option 3: Generate Static HTML

```bash
# Generate HTML documentation for all services
./scripts/generate-api-docs.sh

# View generated docs
open docs/api/index.html
```

## Using Schemas

### Generate Client Libraries

#### Python Client

```bash
# Install openapi-generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate \
  -i docs/openapi/maximus_core_service.json \
  -g python \
  -o clients/python/maximus-core/
```

#### JavaScript/TypeScript Client

```bash
# Generate TypeScript client
openapi-generator-cli generate \
  -i docs/openapi/maximus_core_service.json \
  -g typescript-axios \
  -o clients/typescript/maximus-core/
```

### Import into Postman

1. Open Postman
2. Click **Import**
3. Select OpenAPI schema file
4. Postman will create a collection with all endpoints

### Validate API Responses

```bash
# Install openapi-validator
npm install -g openapi-validator

# Validate schema
openapi-validator docs/openapi/maximus_core_service.json
```

## Schema Versioning

Schemas are versioned along with the service version:

- **Service**: Maximus Core Service
- **Version**: 3.0.0
- **Schema**: `maximus_core_service.json` (matches service version)

When a service version changes, the schema should be re-exported.

## CI/CD Integration

### GitHub Actions

```yaml
name: Export OpenAPI Schemas

on:
  push:
    branches: [main]

jobs:
  export-schemas:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Export schemas
        run: python scripts/export-openapi-schemas.py

      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/openapi/*.json
          git commit -m "Update OpenAPI schemas" || echo "No changes"
          git push
```

## Schema Format

All schemas follow the **OpenAPI 3.0** specification:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Service Name",
    "version": "1.0.0",
    "description": "Service description",
    "contact": {
      "name": "Vértice Platform Team",
      "email": "dev@vertice.security"
    }
  },
  "servers": [
    {"url": "http://localhost:8001"}
  ],
  "paths": {
    "/endpoint": {
      "post": {
        "summary": "Endpoint description",
        "requestBody": {...},
        "responses": {...}
      }
    }
  },
  "components": {
    "schemas": {...},
    "securitySchemes": {...}
  }
}
```

## Common Issues

### Issue: Schema export fails

**Cause**: Service not running or not exposing `/openapi.json`

**Solution**:
1. Start the service
2. Verify endpoint: `curl http://localhost:8001/openapi.json`
3. Check service configuration

### Issue: Schema is empty or incomplete

**Cause**: FastAPI app not properly configured

**Solution**:
1. Import `create_openapi_config` from `backend.shared.openapi_config`
2. Use it when creating FastAPI app
3. Add proper Pydantic models for requests/responses

### Issue: Schemas are outdated

**Cause**: Services updated but schemas not re-exported

**Solution**:
1. Re-run export script: `python scripts/export-openapi-schemas.py`
2. Set up automated export in CI/CD
3. Add pre-commit hook to export on changes

## Best Practices

✅ **DO:**
- Export schemas after every service update
- Version schemas with service versions
- Validate schemas before committing
- Use schemas to generate client libraries
- Keep schemas in version control

❌ **DON'T:**
- Manually edit exported schemas
- Commit schemas without testing
- Skip schema validation
- Ignore schema breaking changes
- Deploy without updating schemas

## Additional Resources

- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Swagger Editor](https://editor.swagger.io/)
- [OpenAPI Generator](https://openapi-generator.tech/)
- [Vértice API Documentation Guide](../API_DOCUMENTATION.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/features/#automatic-docs)

## Support

For issues with OpenAPI schemas:
- Email: dev@vertice.security
- Docs: https://docs.vertice.security
- GitHub: https://github.com/vertice-platform/vertice
