#!/usr/bin/env python3
"""Generate docker-compose.yml from port registry.

This script reads backend/ports.yaml and generates a complete docker-compose.yml
with all services properly configured with their assigned ports.

Features:
- Automatic service discovery from ports.yaml
- Health checks for all services
- Proper network configuration
- Volume mounts for development
- Environment variable injection

Usage:
    python scripts/generate_docker_compose.py
    python scripts/generate_docker_compose.py --output docker-compose.generated.yml
"""

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def load_registry() -> dict[str, Any]:
    """Load port registry."""
    registry_path = Path(__file__).parent.parent / "ports.yaml"
    
    if not registry_path.exists():
        print(f"❌ Port registry not found: {registry_path}")
        sys.exit(1)
    
    with open(registry_path) as f:
        return yaml.safe_load(f)


def generate_service_config(service_name: str, port: int, category: str) -> dict[str, Any]:
    """Generate docker-compose configuration for a service.
    
    Args:
        service_name: Name of the service
        port: Assigned port number
        category: Service category (maximus, immune, etc)
        
    Returns:
        Service configuration dict
    """
    service_dir = f"./services/{service_name}"
    
    config = {
        "build": {
            "context": service_dir,
            "dockerfile": "Dockerfile"
        },
        "container_name": f"vertice-{service_name}",
        "ports": [f"{port}:{port}"],
        "environment": {
            "SERVICE_NAME": service_name,
            "SERVICE_PORT": port,
            "SERVICE_CATEGORY": category,
            "PYTHONUNBUFFERED": "1",
            "LOG_LEVEL": "${LOG_LEVEL:-INFO}"
        },
        "volumes": [
            f"{service_dir}:/app",
            "/app/.venv"
        ],
        "networks": ["vertice-network"],
        "restart": "unless-stopped",
        "healthcheck": {
            "test": [
                "CMD-SHELL",
                f"curl -f http://localhost:{port}/health || exit 1"
            ],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "40s"
        },
        "depends_on": {
            "postgres": {"condition": "service_healthy"},
            "redis": {"condition": "service_healthy"}
        },
        "labels": {
            "vertice.service": service_name,
            "vertice.category": category,
            "vertice.port": str(port)
        }
    }
    
    return config


def generate_infrastructure() -> dict[str, Any]:
    """Generate infrastructure services (postgres, redis, etc)."""
    return {
        "postgres": {
            "image": "postgres:16-alpine",
            "container_name": "vertice-postgres",
            "environment": {
                "POSTGRES_DB": "vertice",
                "POSTGRES_USER": "${POSTGRES_USER:-vertice}",
                "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-vertice_dev}"
            },
            "ports": ["5432:5432"],
            "volumes": [
                "postgres_data:/var/lib/postgresql/data"
            ],
            "networks": ["vertice-network"],
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U vertice"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        },
        "redis": {
            "image": "redis:7-alpine",
            "container_name": "vertice-redis",
            "ports": ["6379:6379"],
            "volumes": ["redis_data:/data"],
            "networks": ["vertice-network"],
            "healthcheck": {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        }
    }


def generate_compose(registry: dict[str, Any]) -> dict[str, Any]:
    """Generate complete docker-compose configuration.
    
    Args:
        registry: Port registry data
        
    Returns:
        Complete docker-compose dict
    """
    compose = {
        "version": "3.9",
        "services": generate_infrastructure(),
        "networks": {
            "vertice-network": {
                "driver": "bridge",
                "name": "vertice-network"
            }
        },
        "volumes": {
            "postgres_data": {},
            "redis_data": {}
        }
    }
    
    # Add all services from registry
    for category, services in registry.items():
        if category == "metadata" or not isinstance(services, dict):
            continue
        
        for service_name, port in services.items():
            compose["services"][service_name] = generate_service_config(
                service_name, port, category
            )
    
    return compose


def main() -> int:
    """Main execution."""
    parser = argparse.ArgumentParser(description="Generate docker-compose from port registry")
    parser.add_argument(
        "--output",
        "-o",
        default="docker-compose.generated.yml",
        help="Output file path"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print to stdout instead of writing file"
    )
    
    args = parser.parse_args()
    
    print("🔧 Generating docker-compose.yml from port registry...")
    
    registry = load_registry()
    compose = generate_compose(registry)
    
    # Convert to YAML
    output = yaml.dump(
        compose,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True
    )
    
    if args.dry_run:
        print(output)
    else:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            f.write("# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY\n")
            f.write("# Generated from backend/ports.yaml\n")
            f.write(f"# Total services: {registry['metadata']['total_services']}\n\n")
            f.write(output)
        
        print(f"✅ Generated: {output_path}")
        print(f"   Services: {registry['metadata']['total_services']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
