# Environment Variables Management Guide

**Vértice Platform - Standardized Configuration**

## Overview

All Vértice microservices use a standardized configuration management system based on Pydantic Settings. This ensures type safety, validation, and consistent handling of environment variables across all 67+ services.

## Naming Convention

### Standard Format
```
PREFIX_COMPONENT_VARIABLE_NAME=value
```

### Prefixes
- `VERTICE_` - Platform-wide settings
- `MAXIMUS_` - MAXIMUS AI core settings
- `SERVICE_` - Generic service settings
- `{SERVICE_NAME}_` - Service-specific settings (uppercase with underscores)

### Examples
```bash
# Platform settings
VERTICE_ENV=production
VERTICE_LOG_LEVEL=INFO

# MAXIMUS settings
MAXIMUS_CORE_PORT=8001
MAXIMUS_PHI_THRESHOLD=0.5

# Service settings
SERVICE_NAME=threat-intel-service
SERVICE_PORT=8003
SERVICE_LOG_LEVEL=DEBUG

# Database settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vertice
POSTGRES_USER=vertice_user
POSTGRES_PASSWORD=secure_password

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Security settings
JWT_SECRET=your-256-bit-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
API_KEY=your-api-key-here

# Observability
ENABLE_METRICS=true
ENABLE_TRACING=false
SENTRY_DSN=https://your-sentry-dsn
```

## Using BaseServiceConfig

### Basic Service Configuration

```python
# my_service/config.py
from backend.shared.base_config import BaseServiceConfig
from pydantic import Field

class MyServiceConfig(BaseServiceConfig):
    """Configuration for My Service."""
    
    # Service-specific settings
    max_workers: int = Field(
        default=4,
        description="Maximum concurrent workers",
        ge=1,
        le=32,
        validation_alias="MY_SERVICE_MAX_WORKERS"
    )
    
    api_endpoint: str = Field(
        ...,  # Required field
        description="External API endpoint URL",
        validation_alias="MY_SERVICE_API_ENDPOINT"
    )
    
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1,
        le=300,
        validation_alias="MY_SERVICE_TIMEOUT"
    )

# Usage in main.py
config = MyServiceConfig()
print(f"Starting {config.service_name} on port {config.service_port}")
```

### Accessing Configuration

```python
# Check environment
if config.is_production:
    enable_strict_mode()

if config.is_development:
    enable_debug_logging()

# Get database URL
db_url = config.postgres_url  # Auto-constructed

# Get Redis URL
redis_url = config.redis_url  # Auto-constructed

# Safe dump (secrets masked)
safe_config = config.model_dump_safe()
logger.info(f"Config: {safe_config}")
```

### Required Variables Validation

```python
# Validate that critical variables are set
config.validate_required_vars(
    "jwt_secret",
    "postgres_host",
    "api_key"
)
```

## Environment Files

### .env Structure

Each service should have:
1. `.env` - Actual values (gitignored)
2. `.env.example` - Template with documentation
3. `.env.test` - Test environment values (optional)

### Generating .env.example

```python
from backend.shared.base_config import generate_env_example
from my_service.config import MyServiceConfig

# Generate .env.example content
example_content = generate_env_example(MyServiceConfig)

# Write to file
with open(".env.example", "w") as f:
    f.write(example_content)
```

### Environment-Specific Files

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production

# Load specific environment
VERTICE_ENV=production python -m my_service
```

## Common Patterns

### Database Configuration

```python
class ServiceWithDatabase(BaseServiceConfig):
    """Service using PostgreSQL."""
    
    # Database config inherited from BaseServiceConfig
    # Just validate required vars at startup
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate_required_vars(
            "postgres_host",
            "postgres_db",
            "postgres_user",
            "postgres_password"
        )
```

### External API Integration

```python
class ServiceWithExternalAPI(BaseServiceConfig):
    """Service integrating external API."""
    
    external_api_url: str = Field(..., validation_alias="EXTERNAL_API_URL")
    external_api_key: str = Field(..., validation_alias="EXTERNAL_API_KEY")
    external_api_timeout: int = Field(default=30, ge=1, le=300)
    
    @property
    def external_api_headers(self) -> dict:
        """Build headers for external API."""
        return {
            "Authorization": f"Bearer {self.external_api_key}",
            "Content-Type": "application/json"
        }
```

### Feature Flags

```python
class ServiceWithFeatures(BaseServiceConfig):
    """Service with feature flags."""
    
    enable_caching: bool = Field(default=True, validation_alias="ENABLE_CACHING")
    enable_rate_limiting: bool = Field(default=True, validation_alias="ENABLE_RATE_LIMITING")
    enable_async_processing: bool = Field(default=False, validation_alias="ENABLE_ASYNC")
    
    # Feature-specific settings
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    rate_limit_per_minute: int = Field(default=100, ge=1, le=10000)
```

## Docker Integration

### docker-compose.yml

```yaml
services:
  my-service:
    build: ./backend/services/my_service
    environment:
      # Core settings
      - VERTICE_ENV=${VERTICE_ENV:-development}
      - SERVICE_NAME=my-service
      - SERVICE_PORT=8050
      
      # Database
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      
      # Service-specific
      - MY_SERVICE_MAX_WORKERS=4
      - MY_SERVICE_API_ENDPOINT=${EXTERNAL_API_URL}
    
    env_file:
      - .env
      - .env.${VERTICE_ENV:-development}
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment defaults (overridden by docker-compose)
ENV VERTICE_ENV=production
ENV SERVICE_NAME=my-service
ENV LOG_LEVEL=INFO

# Validate configuration at build time
RUN python -c "from my_service.config import MyServiceConfig; MyServiceConfig()"

CMD ["python", "-m", "my_service"]
```

## Validation & Testing

### Startup Validation

```python
# main.py
from my_service.config import MyServiceConfig
from pydantic import ValidationError

def main():
    try:
        config = MyServiceConfig()
        logger.info("Configuration validated successfully")
        logger.info(f"Environment: {config.vertice_env.value}")
        logger.info(config.model_dump_safe())
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
    
    # Start service
    start_service(config)
```

### Unit Tests

```python
# tests/test_config.py
import pytest
from my_service.config import MyServiceConfig

def test_config_defaults():
    """Test default configuration values."""
    config = MyServiceConfig(
        service_name="test-service",
        service_port=8999
    )
    assert config.log_level == "INFO"
    assert config.debug is False

def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValueError):
        MyServiceConfig(
            service_name="INVALID NAME",  # Should fail pattern validation
            service_port=8999
        )

def test_required_vars():
    """Test required variables validation."""
    config = MyServiceConfig(
        service_name="test-service",
        service_port=8999
    )
    
    with pytest.raises(ValueError, match="Missing required"):
        config.validate_required_vars("jwt_secret", "api_key")
```

## Security Best Practices

### 1. Never Commit Secrets

```bash
# .gitignore
.env
.env.*
!.env.example
*.secret
*.key
```

### 2. Use Vault for Production

```python
from backend.shared.vault_client import VaultClient

class ProductionConfig(BaseServiceConfig):
    """Production config with Vault integration."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if self.is_production:
            vault = VaultClient()
            self.jwt_secret = vault.get_secret("jwt_secret")
            self.api_key = vault.get_secret("api_key")
```

### 3. Rotate Secrets Regularly

```bash
# Use environment-specific secrets
VERTICE_ENV=production
JWT_SECRET=$(vault kv get -field=value secret/jwt_secret)
API_KEY=$(vault kv get -field=value secret/api_key)
```

### 4. Mask Secrets in Logs

```python
# Always use model_dump_safe() for logging
logger.info(f"Config: {config.model_dump_safe()}")
# Output: {"jwt_secret": "***", "api_key": "***", ...}
```

## Migration Guide

### Migrating Existing Service

1. **Install Dependencies**
   ```bash
   pip install pydantic-settings
   ```

2. **Create Config Class**
   ```python
   # config.py
   from backend.shared.base_config import BaseServiceConfig
   
   class MyServiceConfig(BaseServiceConfig):
       pass  # Start with base config
   ```

3. **Update Environment Variables**
   - Rename variables to follow convention
   - Update docker-compose.yml
   - Create .env.example

4. **Update Application Code**
   ```python
   # Before
   PORT = int(os.getenv("PORT", 8000))
   
   # After
   config = MyServiceConfig()
   PORT = config.service_port
   ```

5. **Add Validation**
   ```python
   config.validate_required_vars("postgres_host", "redis_host")
   ```

## Troubleshooting

### Configuration Not Loading

```python
# Check if .env file exists
from pathlib import Path
env_file = Path(".env")
if not env_file.exists():
    logger.warning(".env file not found, using defaults")

# Check environment variable
import os
print(os.getenv("SERVICE_NAME"))  # Should match service_name
```

### Validation Errors

```python
from pydantic import ValidationError

try:
    config = MyServiceConfig()
except ValidationError as e:
    # Print detailed validation errors
    for error in e.errors():
        print(f"Field: {error['loc']}")
        print(f"Error: {error['msg']}")
        print(f"Type: {error['type']}")
```

### Type Mismatches

```bash
# Wrong: string when int expected
SERVICE_PORT="8000"  # String

# Correct: Pydantic auto-converts
SERVICE_PORT=8000

# For bools
DEBUG=true  # Correct
DEBUG=1     # Also works (converted to True)
DEBUG=false # Correct
DEBUG=0     # Also works (converted to False)
```

## References

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [12-Factor App Config](https://12factor.net/config)
- [OWASP Configuration Management](https://cheatsheetseries.owasp.org/cheatsheets/Configuration_Management_Cheat_Sheet.html)

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-11  
**Maintainer:** Vértice Platform Team
