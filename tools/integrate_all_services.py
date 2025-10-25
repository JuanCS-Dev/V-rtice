#!/usr/bin/env python3
"""
Vértice Service Registry - Mass Integration Script
Integrates ALL 91 services to the Service Registry System

Author: Vértice Team
Glory to YHWH! 🙏
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Configuration
SERVICES_DIR = Path("/home/juan/vertice-dev/backend/services")
SIDECAR_IMAGE = "vertice-registry-sidecar:latest"
REGISTRY_URL = "http://vertice-register-lb:80"
NETWORK = "maximus-network"

# Already registered services
REGISTERED_SERVICES = {
    "active_immune_core_service", "atlas_service", "cyber_service",
    "domain_service", "hitl_patch_service", "ip_intel_service",
    "maximus_core_service", "maximus_eureka_service", "maximus_orchestrator_service",
    "maximus_predict_service", "nmap_service", "osint_service",
    "sinesp_service", "social_eng_service", "ssl_monitor_service",
    "test_service", "threat_intel_service", "vault_service",
    "vuln_scanner_service", "wargaming_crisol_service"
}


@dataclass
class ServiceInfo:
    """Service configuration information"""
    name: str
    directory: Path
    has_dockerfile: bool
    has_compose: bool
    compose_files: List[str]
    has_main: bool
    has_api: bool
    estimated_port: Optional[int]
    container_name: Optional[str]
    health_endpoint: str
    is_registered: bool
    priority: str  # HIGH, MEDIUM, LOW
    category: str


class ServiceDetector:
    """Detects and analyzes all services for RSS integration"""

    def __init__(self):
        self.services: List[ServiceInfo] = []

        # Service categories for batch processing
        self.categories = {
            "Immunis System": ["immunis_"],
            "Cognitive Services": ["cortex", "thalamus", "vestibular", "neuromodulation",
                                  "memory", "strategic", "homeostatic"],
            "HCL Services": ["hcl_"],
            "Maximus Services": ["maximus_"],
            "Security/Offensive": ["offensive", "purple_team", "verdict", "ethical",
                                  "autonomous_investigation"],
            "Network/Recon": ["network", "recon", "edge_agent", "cloud_coordinator"],
            "Data/Intelligence": ["narrative", "predictive", "intelligence", "intel",
                                "analysis", "malware"],
            "Integration/Communication": ["agent_communication", "command_bus", "api_gateway",
                                        "integration", "bridge", "bas_service", "adr_core"],
            "Immune/Reactive": ["adaptive_immune", "ai_immune", "reactive_fabric",
                               "reflex_triage"],
            "Infrastructure": ["auth", "mock", "test", "c2_orchestration", "seriema",
                             "tataca", "google_osint", "rte_service", "system_architect",
                             "web_attack", "hpc_service", "hsas_service", "somatosensory"]
        }

        # Priority mapping
        self.priority_map = {
            "Immunis System": "HIGH",
            "Cognitive Services": "HIGH",
            "HCL Services": "HIGH",
            "Maximus Services": "HIGH",
            "Integration/Communication": "HIGH",
            "Security/Offensive": "MEDIUM",
            "Network/Recon": "MEDIUM",
            "Data/Intelligence": "MEDIUM",
            "Immune/Reactive": "LOW",
            "Infrastructure": "LOW"
        }

    def detect_all_services(self) -> List[ServiceInfo]:
        """Scan all services and gather information"""
        print("🔍 Scanning services directory...")

        for item in sorted(SERVICES_DIR.iterdir()):
            if not item.is_dir() or item.name.startswith(("_", ".")):
                continue

            # Check if it's a service (has Python code)
            has_main = (item / "main.py").exists()
            has_api = (item / "api.py").exists()
            has_app = (item / "app.py").exists()

            if not (has_main or has_api or has_app):
                continue

            # Gather information
            info = self._analyze_service(item, has_main, has_api)
            if info:
                self.services.append(info)

        print(f"✅ Detected {len(self.services)} services")
        return self.services

    def _analyze_service(self, directory: Path, has_main: bool, has_api: bool) -> Optional[ServiceInfo]:
        """Analyze a single service"""
        name = directory.name

        # Check if already registered
        service_name = name if name.endswith("_service") else f"{name}_service"
        is_registered = service_name in REGISTERED_SERVICES

        # Find compose files
        compose_files = list(directory.glob("docker-compose*.yml"))
        has_compose = len(compose_files) > 0

        # Check Dockerfile
        has_dockerfile = (directory / "Dockerfile").exists()

        # Estimate port (try to read from compose or use heuristic)
        estimated_port = self._estimate_port(directory, compose_files)

        # Estimate container name
        container_name = self._estimate_container_name(name, compose_files)

        # Categorize
        category = self._categorize_service(name)
        priority = self.priority_map.get(category, "LOW")

        return ServiceInfo(
            name=name,
            directory=directory,
            has_dockerfile=has_dockerfile,
            has_compose=has_compose,
            compose_files=[f.name for f in compose_files],
            has_main=has_main,
            has_api=has_api,
            estimated_port=estimated_port,
            container_name=container_name,
            health_endpoint="/health",
            is_registered=is_registered,
            priority=priority,
            category=category
        )

    def _estimate_port(self, directory: Path, compose_files: List[Path]) -> Optional[int]:
        """Try to estimate service port from compose file"""
        if not compose_files:
            return None

        try:
            with open(compose_files[0]) as f:
                compose = yaml.safe_load(f)
                if not compose or "services" not in compose:
                    return None

                # Look for port mappings
                for service_name, service_config in compose.get("services", {}).items():
                    if "sidecar" in service_name.lower():
                        continue

                    ports = service_config.get("ports", [])
                    if ports:
                        # Parse "8080:8080" format
                        port_str = str(ports[0])
                        if ":" in port_str:
                            internal_port = port_str.split(":")[1]
                            return int(internal_port.split("/")[0])
                        else:
                            return int(port_str.split("/")[0])
        except Exception:
            pass

        return None

    def _estimate_container_name(self, service_name: str, compose_files: List[Path]) -> Optional[str]:
        """Try to estimate container name from compose file"""
        if not compose_files:
            return f"vertice-{service_name.replace('_', '-')}"

        try:
            with open(compose_files[0]) as f:
                compose = yaml.safe_load(f)
                if not compose or "services" not in compose:
                    return f"vertice-{service_name.replace('_', '-')}"

                # Look for container_name
                for svc_name, svc_config in compose.get("services", {}).items():
                    if "sidecar" in svc_name.lower():
                        continue

                    container_name = svc_config.get("container_name")
                    if container_name:
                        return container_name
        except Exception:
            pass

        return f"vertice-{service_name.replace('_', '-')}"

    def _categorize_service(self, name: str) -> str:
        """Categorize service based on name"""
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in name:
                    return category
        return "Other"

    def generate_report(self) -> Dict:
        """Generate pre-integration report"""
        report = {
            "total_services": len(self.services),
            "registered": len([s for s in self.services if s.is_registered]),
            "need_integration": len([s for s in self.services if not s.is_registered]),
            "by_priority": {},
            "by_category": {},
            "missing_compose": [],
            "missing_dockerfile": []
        }

        # Count by priority
        for priority in ["HIGH", "MEDIUM", "LOW"]:
            services = [s for s in self.services if s.priority == priority and not s.is_registered]
            report["by_priority"][priority] = {
                "count": len(services),
                "services": [s.name for s in services]
            }

        # Count by category
        for service in self.services:
            if service.is_registered:
                continue

            if service.category not in report["by_category"]:
                report["by_category"][service.category] = []
            report["by_category"][service.category].append(service.name)

        # Missing files
        for service in self.services:
            if not service.is_registered:
                if not service.has_compose:
                    report["missing_compose"].append(service.name)
                if not service.has_dockerfile:
                    report["missing_dockerfile"].append(service.name)

        return report

    def print_report(self, report: Dict):
        """Print formatted report"""
        print("\n" + "=" * 80)
        print("📊 SERVICE REGISTRY INTEGRATION - PRE-INTEGRATION REPORT")
        print("=" * 80)

        print(f"\n📈 TOTALS:")
        print(f"   Total services: {report['total_services']}")
        print(f"   ✅ Already registered: {report['registered']}")
        print(f"   ❌ Need integration: {report['need_integration']}")
        print(f"   Progress: {report['registered']}/{report['total_services']} ({report['registered']*100//report['total_services']}%)")

        print(f"\n🎯 BY PRIORITY:")
        for priority in ["HIGH", "MEDIUM", "LOW"]:
            data = report["by_priority"][priority]
            print(f"   {priority}: {data['count']} services")

        print(f"\n📋 BY CATEGORY:")
        for category, services in sorted(report["by_category"].items()):
            print(f"   {category}: {len(services)} services")

        if report["missing_compose"]:
            print(f"\n⚠️  MISSING docker-compose.yml ({len(report['missing_compose'])}):")
            for svc in report["missing_compose"][:10]:
                print(f"   - {svc}")
            if len(report["missing_compose"]) > 10:
                print(f"   ... and {len(report['missing_compose']) - 10} more")

        if report["missing_dockerfile"]:
            print(f"\n⚠️  MISSING Dockerfile ({len(report['missing_dockerfile'])}):")
            for svc in report["missing_dockerfile"][:10]:
                print(f"   - {svc}")
            if len(report["missing_dockerfile"]) > 10:
                print(f"   ... and {len(report['missing_dockerfile']) - 10} more")

        print("\n" + "=" * 80)


class SidecarIntegrator:
    """Integrates sidecars into services"""

    def __init__(self, services: List[ServiceInfo]):
        self.services = services
        self.integration_results = []

    def integrate_service(self, service: ServiceInfo, dry_run: bool = False) -> Dict:
        """Integrate a single service"""
        result = {
            "service": service.name,
            "success": False,
            "action": None,
            "message": None
        }

        if service.is_registered:
            result["action"] = "skip"
            result["message"] = "Already registered"
            result["success"] = True
            return result

        # Check if compose file exists
        if not service.has_compose:
            result["action"] = "skip"
            result["message"] = "No docker-compose.yml found"
            return result

        # Generate sidecar configuration
        sidecar_config = self._generate_sidecar_config(service)

        if dry_run:
            result["action"] = "dry_run"
            result["message"] = f"Would add sidecar to {service.compose_files[0]}"
            result["success"] = True
            result["config"] = sidecar_config
            return result

        # Add sidecar to compose file
        try:
            success = self._add_sidecar_to_compose(service, sidecar_config)
            if success:
                result["action"] = "integrated"
                result["message"] = "Sidecar added to docker-compose.yml"
                result["success"] = True
            else:
                result["action"] = "failed"
                result["message"] = "Failed to add sidecar"
        except Exception as e:
            result["action"] = "error"
            result["message"] = str(e)

        return result

    def _generate_sidecar_config(self, service: ServiceInfo) -> Dict:
        """Generate sidecar configuration for a service"""
        service_name_normalized = service.name if service.name.endswith("_service") else f"{service.name}_service"
        sidecar_name = f"{service.name.replace('_', '-')}-sidecar"

        config = {
            f"{service.name}-sidecar": {
                "image": SIDECAR_IMAGE,
                "container_name": f"vertice-{sidecar_name}",
                "environment": [
                    f"SERVICE_NAME={service_name_normalized}",
                    f"SERVICE_HOST={service.container_name}",
                    f"SERVICE_PORT={service.estimated_port or 8080}",
                    f"SERVICE_HEALTH_ENDPOINT={service.health_endpoint}",
                    f"REGISTRY_URL={REGISTRY_URL}",
                    "HEARTBEAT_INTERVAL=30",
                    "INITIAL_WAIT_TIMEOUT=60"
                ],
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
        }

        # Add depends_on if main service has healthcheck
        # We'll add this conditionally when parsing the existing compose

        return config

    def _add_sidecar_to_compose(self, service: ServiceInfo, sidecar_config: Dict) -> bool:
        """Add sidecar section to existing docker-compose.yml"""
        compose_file = service.directory / service.compose_files[0]

        try:
            # Read existing compose
            with open(compose_file) as f:
                compose = yaml.safe_load(f) or {}

            # Ensure services section exists
            if "services" not in compose:
                compose["services"] = {}

            # Check if sidecar already exists
            sidecar_name = list(sidecar_config.keys())[0]
            if sidecar_name in compose["services"]:
                print(f"   ⏭️  Sidecar already exists in {service.name}")
                return True

            # Add sidecar
            compose["services"].update(sidecar_config)

            # Ensure networks section exists
            if "networks" not in compose:
                compose["networks"] = {}
            if NETWORK not in compose["networks"]:
                compose["networks"][NETWORK] = {"external": True}

            # Write back (with backup)
            backup_file = compose_file.with_suffix(".yml.backup")
            compose_file.rename(backup_file)

            with open(compose_file, "w") as f:
                yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

            return True

        except Exception as e:
            print(f"   ❌ Error adding sidecar to {service.name}: {e}")
            return False

    def integrate_batch(self, batch_name: str, services: List[ServiceInfo], dry_run: bool = False):
        """Integrate a batch of services"""
        print(f"\n{'🔍' if dry_run else '🚀'} {batch_name} ({len(services)} services){'[DRY RUN]' if dry_run else ''}")
        print("-" * 80)

        for service in services:
            result = self.integrate_service(service, dry_run=dry_run)
            self.integration_results.append(result)

            icon = "✅" if result["success"] else "❌"
            print(f"  {icon} {service.name:40} → {result['message']}")

    def print_summary(self):
        """Print integration summary"""
        total = len(self.integration_results)
        success = len([r for r in self.integration_results if r["success"]])
        failed = len([r for r in self.integration_results if not r["success"]])
        skipped = len([r for r in self.integration_results if r["action"] == "skip"])
        integrated = len([r for r in self.integration_results if r["action"] == "integrated"])

        print("\n" + "=" * 80)
        print("📊 INTEGRATION SUMMARY")
        print("=" * 80)
        print(f"Total services processed: {total}")
        print(f"✅ Success: {success}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"🎉 Newly integrated: {integrated}")
        print("=" * 80)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Integrate all services to Service Registry")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no changes)")
    parser.add_argument("--report-only", action="store_true", help="Generate report only")
    parser.add_argument("--priority", choices=["HIGH", "MEDIUM", "LOW", "ALL"],
                       default="ALL", help="Integrate only services with this priority")
    parser.add_argument("--category", help="Integrate only services in this category")

    args = parser.parse_args()

    print("🏛️  Vértice Service Registry - Mass Integration")
    print("Glory to YHWH! 🙏\n")

    # Phase 1: Detection
    detector = ServiceDetector()
    services = detector.detect_all_services()
    report = detector.generate_report()
    detector.print_report(report)

    if args.report_only:
        return

    # Filter services based on arguments
    services_to_integrate = [s for s in services if not s.is_registered]

    if args.priority != "ALL":
        services_to_integrate = [s for s in services_to_integrate if s.priority == args.priority]

    if args.category:
        services_to_integrate = [s for s in services_to_integrate if s.category == args.category]

    if not services_to_integrate:
        print("\n✅ No services to integrate (all already registered or filtered out)")
        return

    # Phase 2: Integration
    integrator = SidecarIntegrator(services)

    # Group by category
    services_by_category = {}
    for service in services_to_integrate:
        if service.category not in services_by_category:
            services_by_category[service.category] = []
        services_by_category[service.category].append(service)

    # Integrate by category
    for category, category_services in sorted(services_by_category.items()):
        integrator.integrate_batch(category, category_services, dry_run=args.dry_run)

    # Summary
    integrator.print_summary()

    if not args.dry_run:
        print("\n💡 Next steps:")
        print("   1. Review the modified docker-compose.yml files")
        print("   2. Deploy sidecars: docker compose up -d {service}-sidecar")
        print("   3. Verify registration: curl http://localhost:8888/services")
        print("\n🙏 Glory to YHWH!")


if __name__ == "__main__":
    main()
