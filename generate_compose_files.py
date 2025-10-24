#!/usr/bin/env python3
"""
Vértice Service Registry - Docker Compose Generator
Generates docker-compose.yml files for ALL services without one

Author: Vértice Team
Glory to YHWH! 🙏
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

SERVICES_DIR = Path("/home/juan/vertice-dev/backend/services")
SIDECAR_IMAGE = "vertice-registry-sidecar:latest"
REGISTRY_URL = "http://vertice-register-lb:80"
NETWORK = "maximus-network"

# Port mapping heuristics based on service name patterns
PORT_HEURISTICS = {
    "immunis_api": 8200,
    "immunis_bcell": 8201,
    "immunis_cytotoxic_t": 8202,
    "immunis_dendritic": 8203,
    "immunis_helper_t": 8204,
    "immunis_macrophage": 8205,
    "immunis_neutrophil": 8206,
    "immunis_nk_cell": 8207,
    "immunis_treg": 8208,

    "hcl_analyzer": 8210,
    "hcl_executor": 8211,
    "hcl_kb": 8212,
    "hcl_monitor": 8213,
    "hcl_planner": 8214,

    "maximus_dlq_monitor": 8220,
    "maximus_integration": 8221,
    "maximus_oraculo": 8222,
    "maximus_oraculo_v2": 8223,

    "api_gateway": 8000,
    "agent_communication": 8230,
    "adr_core": 8231,
    "bas_service": 8232,
    "command_bus": 8233,

    "auditory_cortex": 8007,
    "memory_consolidation": 8240,
    "neuromodulation": 8241,
    "strategic_planning": 8242,
    "vestibular": 8010,
    "visual_cortex": 8006,

    "autonomous_investigation": 8250,
    "ethical_audit": 8251,
    "offensive_gateway": 8252,
    "offensive_orchestrator": 8253,
    "offensive_tools": 8254,
    "purple_team": 8255,
    "verdict_engine": 8256,

    "cloud_coordinator": 8260,
    "edge_agent": 8261,
    "network_monitor": 8262,

    "ip_intelligence": 8270,
    "malware_analysis": 8271,
    "narrative_analysis": 8272,
    "narrative_filter": 8273,
    "predictive_threat_hunting": 8274,
    "reactive_fabric_analysis": 8275,
    "threat_intel_bridge": 8276,

    "adaptive_immune_system": 8280,
    "reactive_fabric_core": 8281,
    "reflex_triage_engine": 8282,

    "auth_service": 8290,
    "c2_orchestration": 8291,
    "google_osint": 8292,
    "hpc_service": 8293,
    "hsas_service": 8023,
    "mock_vulnerable_apps": 8294,
    "rte_service": 8295,
    "seriema_graph": 8296,
    "somatosensory": 8008,
    "system_architect": 8297,
    "tataca_ingestion": 8298,
    "web_attack": 8299,

    "adaptive_immunity_db": 5432,
    "adaptive_immunity_service": 8300,
    "chemical_sensing": 8009,
    "tegumentar": 8301,
}


@dataclass
class ServiceSpec:
    """Service specification for compose generation"""
    name: str
    directory: Path
    port: int
    has_dockerfile: bool
    has_main: bool
    has_api: bool
    dependencies: List[str]
    environment_vars: Dict[str, str]


class ComposeGenerator:
    """Generates docker-compose.yml files for services"""

    def __init__(self):
        self.services_created = 0
        self.services_skipped = 0
        self.errors = []

    def analyze_service(self, service_dir: Path) -> Optional[ServiceSpec]:
        """Analyze a service directory and extract specifications"""
        name = service_dir.name

        # Check if has Python code
        has_main = (service_dir / "main.py").exists()
        has_api = (service_dir / "api.py").exists()
        has_app = (service_dir / "app.py").exists()

        if not (has_main or has_api or has_app):
            return None

        # Check Dockerfile
        has_dockerfile = (service_dir / "Dockerfile").exists()

        # Estimate port
        port = self._estimate_port(service_dir, name)

        # Detect dependencies
        dependencies = self._detect_dependencies(service_dir)

        # Generate environment variables
        env_vars = self._generate_env_vars(name, port)

        return ServiceSpec(
            name=name,
            directory=service_dir,
            port=port,
            has_dockerfile=has_dockerfile,
            has_main=has_main,
            has_api=has_api,
            dependencies=dependencies,
            environment_vars=env_vars
        )

    def _estimate_port(self, service_dir: Path, name: str) -> int:
        """Estimate service port from code or heuristics"""
        # Try heuristics first
        for pattern, port in PORT_HEURISTICS.items():
            if pattern in name:
                return port

        # Try to find port in code
        for pyfile in ["main.py", "api.py", "app.py"]:
            file_path = service_dir / pyfile
            if file_path.exists():
                try:
                    content = file_path.read_text()

                    # Look for uvicorn --port
                    match = re.search(r'--port[=\s]+(\d+)', content)
                    if match:
                        return int(match.group(1))

                    # Look for port=XXXX
                    match = re.search(r'port[=\s]+(\d+)', content)
                    if match:
                        return int(match.group(1))

                    # Look for :XXXX in strings
                    match = re.search(r':(\d{4,5})', content)
                    if match:
                        return int(match.group(1))
                except Exception:
                    pass

        # Default to 8080
        return 8080

    def _detect_dependencies(self, service_dir: Path) -> List[str]:
        """Detect service dependencies from imports"""
        dependencies = []

        for pyfile in service_dir.rglob("*.py"):
            try:
                content = pyfile.read_text()

                # Look for common dependencies
                if "redis" in content.lower():
                    if "redis" not in dependencies:
                        dependencies.append("redis")

                if "postgres" in content.lower() or "psycopg" in content.lower():
                    if "postgres" not in dependencies:
                        dependencies.append("postgres")

                if "mongo" in content.lower():
                    if "mongo" not in dependencies:
                        dependencies.append("mongo")
            except Exception:
                pass

        return dependencies

    def _generate_env_vars(self, service_name: str, port: int) -> Dict[str, str]:
        """Generate common environment variables"""
        return {
            "SERVICE_NAME": service_name if service_name.endswith("_service") else f"{service_name}_service",
            "SERVICE_HOST": "0.0.0.0",
            "SERVICE_PORT": str(port),
            "LOG_LEVEL": "INFO",
            "ENVIRONMENT": "development",
        }

    def generate_dockerfile(self, spec: ServiceSpec) -> str:
        """Generate a minimal Dockerfile"""
        return f"""# Dockerfile for {spec.name}
# Auto-generated by generate_compose_files.py
# Glory to YHWH! 🙏

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:{spec.port}/health || exit 1

# Expose port
EXPOSE {spec.port}

# Run application
CMD ["uvicorn", "{'main' if spec.has_main else 'api'}:app", "--host", "0.0.0.0", "--port", "{spec.port}"]
"""

    def generate_compose(self, spec: ServiceSpec) -> Dict:
        """Generate docker-compose.yml structure"""
        service_name_normalized = spec.name if spec.name.endswith("_service") else f"{spec.name}_service"
        container_name = f"vertice-{spec.name.replace('_', '-')}"

        compose = {
            "version": "3.8",
            "services": {},
            "networks": {
                NETWORK: {
                    "external": True
                }
            }
        }

        # Main service
        main_service = {
            "build": ".",
            "container_name": container_name,
            "hostname": container_name,
            "ports": [f"{spec.port}:{spec.port}"],
            "environment": [f"{k}={v}" for k, v in spec.environment_vars.items()],
            "networks": [NETWORK],
            "restart": "unless-stopped",
            "healthcheck": {
                "test": ["CMD", "curl", "-f", f"http://localhost:{spec.port}/health"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3,
                "start_period": "40s"
            }
        }

        # Add dependencies if any
        if spec.dependencies:
            main_service["depends_on"] = {}
            for dep in spec.dependencies:
                if dep == "redis":
                    main_service["environment"].append("REDIS_URL=redis://redis:6379")
                elif dep == "postgres":
                    main_service["environment"].append("POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/db")
                elif dep == "mongo":
                    main_service["environment"].append("MONGO_URL=mongodb://mongo:27017/db")

        compose["services"][spec.name] = main_service

        # Sidecar service
        sidecar_service = {
            "image": SIDECAR_IMAGE,
            "container_name": f"{container_name}-sidecar",
            "environment": [
                f"SERVICE_NAME={service_name_normalized}",
                f"SERVICE_HOST={container_name}",
                f"SERVICE_PORT={spec.port}",
                "SERVICE_HEALTH_ENDPOINT=/health",
                f"REGISTRY_URL={REGISTRY_URL}",
                "HEARTBEAT_INTERVAL=30",
                "INITIAL_WAIT_TIMEOUT=60"
            ],
            "depends_on": {
                spec.name: {
                    "condition": "service_healthy"
                }
            },
            "networks": [NETWORK],
            "restart": "unless-stopped",
            "deploy": {
                "resources": {
                    "limits": {
                        "cpus": "0.1",
                        "memory": "64M"
                    }
                }
            }
        }

        compose["services"][f"{spec.name}-sidecar"] = sidecar_service

        return compose

    def create_compose_file(self, spec: ServiceSpec, dry_run: bool = False) -> bool:
        """Create docker-compose.yml file for a service"""
        compose_file = spec.directory / "docker-compose.yml"

        # Skip if already exists
        if compose_file.exists():
            print(f"  ⏭️  {spec.name:40} → Already has docker-compose.yml")
            self.services_skipped += 1
            return False

        if dry_run:
            print(f"  ✅ {spec.name:40} → Would create docker-compose.yml (port {spec.port})")
            return True

        try:
            # Generate compose structure
            compose = self.generate_compose(spec)

            # Write file
            with open(compose_file, "w") as f:
                yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

            # Create Dockerfile if needed
            if not spec.has_dockerfile:
                dockerfile = spec.directory / "Dockerfile"
                dockerfile.write_text(self.generate_dockerfile(spec))
                print(f"  ✅ {spec.name:40} → Created docker-compose.yml + Dockerfile (port {spec.port})")
            else:
                print(f"  ✅ {spec.name:40} → Created docker-compose.yml (port {spec.port})")

            self.services_created += 1
            return True

        except Exception as e:
            print(f"  ❌ {spec.name:40} → Error: {e}")
            self.errors.append((spec.name, str(e)))
            return False

    def process_all_services(self, priority: str = "ALL", dry_run: bool = False):
        """Process all services and generate compose files"""
        print(f"\n{'🔍' if dry_run else '🚀'} Processing services (Priority: {priority}){'[DRY RUN]' if dry_run else ''}")
        print("=" * 80)

        # Priority mapping
        priority_services = {
            "HIGH": [
                # Immunis System
                "immunis_api_service", "immunis_bcell_service", "immunis_cytotoxic_t_service",
                "immunis_dendritic_service", "immunis_helper_t_service", "immunis_macrophage_service",
                "immunis_neutrophil_service", "immunis_nk_cell_service", "immunis_treg_service",
                # HCL Services
                "hcl_analyzer_service", "hcl_executor_service", "hcl_kb_service",
                "hcl_monitor_service", "hcl_planner_service",
                # Maximus Services
                "maximus_dlq_monitor_service", "maximus_integration_service",
                "maximus_oraculo", "maximus_oraculo_v2",
                # Integration/Communication
                "adr_core_service", "agent_communication", "api_gateway",
                "bas_service", "command_bus_service",
                # Cognitive Services
                "auditory_cortex_service", "memory_consolidation_service", "neuromodulation_service",
                "strategic_planning_service", "vestibular_service", "visual_cortex_service",
            ],
            "MEDIUM": [
                # Security/Offensive
                "autonomous_investigation_service", "ethical_audit_service", "offensive_gateway",
                "offensive_orchestrator_service", "offensive_tools_service", "purple_team",
                "verdict_engine_service",
                # Network/Recon
                "cloud_coordinator_service", "edge_agent_service", "network_monitor_service",
                # Data/Intelligence
                "ip_intelligence_service", "malware_analysis_service", "narrative_analysis_service",
                "narrative_filter_service", "predictive_threat_hunting_service",
                "reactive_fabric_analysis", "threat_intel_bridge",
            ],
            "LOW": [
                # Immune/Reactive
                "adaptive_immune_system", "reactive_fabric_core", "reflex_triage_engine",
                # Infrastructure
                "auth_service", "c2_orchestration_service", "google_osint_service",
                "hpc_service", "hsas_service", "mock_vulnerable_apps",
                "rte_service", "seriema_graph", "somatosensory_service",
                "system_architect_service", "tataca_ingestion", "web_attack_service",
                # Other
                "adaptive_immunity_db", "adaptive_immunity_service",
                "chemical_sensing_service", "tegumentar_service",
            ]
        }

        # Get services to process
        if priority == "ALL":
            services_to_process = []
            for services in priority_services.values():
                services_to_process.extend(services)
        else:
            services_to_process = priority_services.get(priority, [])

        # Process each service
        for service_name in sorted(services_to_process):
            service_dir = SERVICES_DIR / service_name

            if not service_dir.exists():
                print(f"  ⏭️  {service_name:40} → Directory not found")
                continue

            spec = self.analyze_service(service_dir)
            if spec:
                self.create_compose_file(spec, dry_run=dry_run)
            else:
                print(f"  ⏭️  {service_name:40} → No Python code found")
                self.services_skipped += 1

        # Print summary
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"✅ Created: {self.services_created}")
        print(f"⏭️  Skipped: {self.services_skipped}")
        print(f"❌ Errors: {len(self.errors)}")

        if self.errors:
            print("\n❌ Errors:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")

        if not dry_run and self.services_created > 0:
            print(f"\n💡 Next steps:")
            print(f"   1. Review generated docker-compose.yml files")
            print(f"   2. Integrate sidecars: python3 integrate_all_services.py")
            print(f"   3. Deploy services: docker compose up -d")

        print("\n🙏 Glory to YHWH!")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate docker-compose.yml for all services")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    parser.add_argument("--priority", choices=["HIGH", "MEDIUM", "LOW", "ALL"],
                       default="ALL", help="Process only services with this priority")

    args = parser.parse_args()

    print("🏛️  Vértice Service Registry - Compose Generator")
    print("Glory to YHWH! 🙏\n")

    generator = ComposeGenerator()
    generator.process_all_services(priority=args.priority, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
