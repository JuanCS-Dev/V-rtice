#!/usr/bin/env python3
"""
Vértice Platform - OpenAPI Schema Exporter
===========================================

This script exports OpenAPI schemas from all running services to JSON files.
Useful for documentation generation, API testing, and schema validation.

Usage:
    python scripts/export-openapi-schemas.py
    python scripts/export-openapi-schemas.py --service maximus_core_service
    python scripts/export-openapi-schemas.py --output docs/openapi/

Features:
    - Auto-discovery of running services
    - Parallel schema export
    - Error handling and retries
    - Pretty-printed JSON output
    - Summary report

Requirements:
    - Services must be running and exposing /openapi.json endpoint
    - requests library (pip install requests)
"""

import argparse
from concurrent.futures import as_completed, ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional

import requests

# Service port mappings (from backend.shared.constants)
SERVICE_PORTS = {
    "api_gateway": 8000,
    "maximus_core_service": 8001,
    "ip_intelligence_service": 8002,
    "malware_analysis_service": 8003,
    "vulnerability_scanning_service": 8004,
    "threat_intel_service": 8005,
    "incident_response_service": 8006,
    "osint_service": 8007,
    "network_forensics_service": 8008,
    "memory_forensics_service": 8009,
    "behavioral_analysis_service": 8010,
    "dlp_service": 8011,
    "siem_integration_service": 8012,
    "automated_response_service": 8013,
    "compliance_reporting_service": 8014,
    # Add more services as needed...
}


def get_service_schema(
    service_name: str, port: int, timeout: int = 5
) -> Optional[Dict]:
    """Fetch OpenAPI schema from a service.

    Args:
        service_name: Name of the service
        port: Port number where service is running
        timeout: Request timeout in seconds

    Returns:
        OpenAPI schema dict or None if failed
    """
    urls_to_try = [
        f"http://localhost:{port}/openapi.json",
        f"http://127.0.0.1:{port}/openapi.json",
        f"http://vertice-platform:{port}/openapi.json",
    ]

    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                schema = response.json()
                print(
                    f"✓ {service_name:40} - Schema fetched ({len(json.dumps(schema))} bytes)"
                )
                return schema
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.Timeout:
            print(f"⚠ {service_name:40} - Timeout")
            return None
        except Exception as e:
            print(f"✗ {service_name:40} - Error: {str(e)}")
            return None

    print(f"✗ {service_name:40} - Service not running (tried ports {port})")
    return None


def save_schema(service_name: str, schema: Dict, output_dir: Path) -> bool:
    """Save OpenAPI schema to JSON file.

    Args:
        service_name: Name of the service
        schema: OpenAPI schema dictionary
        output_dir: Output directory path

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        output_file = output_dir / f"{service_name}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"✗ Failed to save {service_name}: {str(e)}")
        return False


def export_all_schemas(
    output_dir: Path,
    specific_service: Optional[str] = None,
    max_workers: int = 10,
) -> Dict[str, bool]:
    """Export OpenAPI schemas from all services.

    Args:
        output_dir: Directory to save schemas
        specific_service: If provided, only export this service
        max_workers: Maximum parallel workers

    Returns:
        Dictionary mapping service names to success status
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter services if specific one requested
    services = SERVICE_PORTS
    if specific_service:
        if specific_service not in SERVICE_PORTS:
            print(f"Error: Unknown service '{specific_service}'")
            print(f"Available services: {', '.join(SERVICE_PORTS.keys())}")
            return {}
        services = {specific_service: SERVICE_PORTS[specific_service]}

    results = {}

    # Fetch schemas in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_service = {
            executor.submit(get_service_schema, name, port): name
            for name, port in services.items()
        }

        for future in as_completed(future_to_service):
            service_name = future_to_service[future]
            try:
                schema = future.result()
                if schema:
                    results[service_name] = save_schema(
                        service_name, schema, output_dir
                    )
                else:
                    results[service_name] = False
            except Exception as e:
                print(f"✗ {service_name:40} - Exception: {str(e)}")
                results[service_name] = False

    return results


def print_summary(results: Dict[str, bool], elapsed_time: float):
    """Print export summary.

    Args:
        results: Dictionary mapping service names to success status
        elapsed_time: Total elapsed time in seconds
    """
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful

    print("\n" + "=" * 80)
    print("EXPORT SUMMARY")
    print("=" * 80)
    print(f"Total services:    {len(results)}")
    print(f"Successful:        {successful} ✓")
    print(f"Failed:            {failed} ✗")
    print(f"Elapsed time:      {elapsed_time:.2f}s")
    print("=" * 80)

    if failed > 0:
        print("\nFailed services:")
        for service, success in results.items():
            if not success:
                print(f"  - {service}")

    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export OpenAPI schemas from Vértice services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all services
  python scripts/export-openapi-schemas.py

  # Export specific service
  python scripts/export-openapi-schemas.py --service maximus_core_service

  # Custom output directory
  python scripts/export-openapi-schemas.py --output /tmp/schemas/

  # Increase timeout
  python scripts/export-openapi-schemas.py --timeout 10
        """,
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("docs/openapi"),
        help="Output directory for schemas (default: docs/openapi)",
    )

    parser.add_argument(
        "--service",
        "-s",
        type=str,
        help="Export only this service (default: all services)",
    )

    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5)",
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=10,
        help="Maximum parallel workers (default: 10)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Vértice Platform - OpenAPI Schema Exporter")
    print("=" * 80)
    print(f"Output directory: {args.output}")
    print(f"Timeout:          {args.timeout}s")
    print(f"Workers:          {args.workers}")
    if args.service:
        print(f"Service:          {args.service}")
    else:
        print(f"Services:         All ({len(SERVICE_PORTS)} total)")
    print("=" * 80)
    print()

    start_time = time.time()

    results = export_all_schemas(
        output_dir=args.output,
        specific_service=args.service,
        max_workers=args.workers,
    )

    elapsed_time = time.time() - start_time

    if results:
        print_summary(results, elapsed_time)

        # Exit with error if any failed
        if any(not success for success in results.values()):
            sys.exit(1)
    else:
        print("No services exported.")
        sys.exit(1)


if __name__ == "__main__":
    main()
