#!/usr/bin/env python3
"""Validate port registry for conflicts, completeness, and correctness.

This script performs comprehensive validation of backend/ports.yaml:
- No port conflicts (all unique)
- Ports within correct ranges per category
- All services from filesystem are mapped
- No mapped services missing from filesystem

Exit codes:
    0: All validations passed
    1: Validation errors found

Usage:
    python scripts/validate_ports.py
    
    # CI integration
    python scripts/validate_ports.py || exit 1
"""

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - defensive import check
    print("❌ PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def load_registry() -> dict[str, Any]:
    """Load port registry YAML.
    
    Returns:
        Parsed YAML data
        
    Raises:
        SystemExit: If file not found or invalid YAML
    """
    registry_path = Path(__file__).parent.parent / "ports.yaml"
    
    if not registry_path.exists():
        print(f"❌ Port registry not found: {registry_path}")
        sys.exit(1)
    
    try:
        with open(registry_path) as f:
            data: dict[str, Any] = yaml.safe_load(f)
            return data
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML: {e}")
        sys.exit(1)


def validate_uniqueness(registry: dict[str, Any]) -> list[str]:
    """Check that all ports are unique (no conflicts).
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages (empty if no errors)
    """
    errors = []
    seen_ports: dict[int, str] = {}
    
    for category, services in registry.items():
        if category == "metadata":
            continue
        
        if not isinstance(services, dict):
            errors.append(f"❌ Category '{category}' must be dict, got {type(services).__name__}")
            continue
        
        for service_name, port in services.items():
            if not isinstance(port, int):
                errors.append(
                    f"❌ {category}.{service_name}: port must be int, got {type(port).__name__}"
                )
                continue
            
            if port in seen_ports:
                errors.append(
                    f"⚠️  PORT CONFLICT: {category}.{service_name}:{port} "
                    f"conflicts with {seen_ports[port]}:{port}"
                )
            
            seen_ports[port] = f"{category}.{service_name}"
    
    return errors


def validate_ranges(registry: dict[str, Any]) -> list[str]:
    """Check that ports are within correct ranges per category.
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages
    """
    errors = []
    
    # Expected ranges per category
    ranges: dict[str, tuple[int, int]] = {
        "core": (8000, 8099),
        "maximus": (8100, 8199),
        "immune": (8200, 8299),
        "intelligence": (8300, 8399),
        "offensive": (8400, 8499),
        "defensive": (8500, 8599),
        "sensory": (8600, 8699),
        "cognition": (8700, 8799),
        "higher_order": (8800, 8899),
        "support": (8900, 8999),
        "wargaming": (9000, 9099),
        "special": (9100, 9199),
    }
    
    for category, services in registry.items():
        if category == "metadata":
            continue
        
        if category not in ranges:
            errors.append(f"⚠️  Unknown category: '{category}'")
            continue
        
        if not isinstance(services, dict):
            continue
        
        min_port, max_port = ranges[category]
        
        for service_name, port in services.items():
            if not isinstance(port, int):
                continue
            
            if not (min_port <= port <= max_port):
                errors.append(
                    f"⚠️  {category}.{service_name}:{port} outside range "
                    f"({min_port}-{max_port})"
                )
    
    return errors


def validate_completeness(registry: dict[str, Any]) -> list[str]:
    """Check that all filesystem services are mapped.
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages
    """
    errors = []
    services_dir = Path(__file__).parent.parent / "services"
    
    if not services_dir.exists():
        return [f"⚠️  Services directory not found: {services_dir}"]
    
    # Get actual services from filesystem
    actual_services = {
        d.name for d in services_dir.iterdir()
        if d.is_dir() and not d.name.startswith(('.', '_'))
    }
    
    # Get mapped services from YAML
    mapped_services: set[str] = set()
    for category, services in registry.items():
        if category == "metadata" or not isinstance(services, dict):
            continue
        mapped_services.update(services.keys())
    
    # Find unmapped
    unmapped = actual_services - mapped_services
    if unmapped:
        errors.append(
            f"⚠️  Services in filesystem but NOT in ports.yaml:\n"
            f"    {', '.join(sorted(unmapped))}"
        )
    
    # Find non-existent
    nonexistent = mapped_services - actual_services
    if nonexistent:
        errors.append(
            f"⚠️  Services in ports.yaml but NOT in filesystem:\n"
            f"    {', '.join(sorted(nonexistent))}"
        )
    
    return errors


def validate_metadata(registry: dict[str, Any]) -> list[str]:
    """Validate metadata section.
    
    Args:
        registry: Parsed YAML data
        
    Returns:
        List of error messages
    """
    errors = []
    
    if "metadata" not in registry:
        errors.append("⚠️  Missing 'metadata' section")
        return errors
    
    meta = registry["metadata"]
    
    # Count actual services
    actual_count = sum(
        len(svcs) for k, svcs in registry.items()
        if k != "metadata" and isinstance(svcs, dict)
    )
    
    declared_count = meta.get("total_services", 0)
    
    if actual_count != declared_count:
        errors.append(
            f"⚠️  Metadata count mismatch: declared {declared_count}, "
            f"actual {actual_count}"
        )
    
    return errors


def main() -> int:
    """Run all validation checks.
    
    Returns:
        0 if all validations pass, 1 otherwise
    """
    print("🔍 Validating Port Registry\n")
    print("=" * 60)
    
    try:
        registry = load_registry()
    except SystemExit:
        return 1
    
    all_errors = []
    
    # Run checks
    print("\n1️⃣  Checking port uniqueness...")
    errors = validate_uniqueness(registry)
    if errors:
        all_errors.extend(errors)
    else:
        print("   ✅ No port conflicts")
    
    print("\n2️⃣  Checking port ranges...")
    errors = validate_ranges(registry)
    if errors:
        all_errors.extend(errors)
    else:
        print("   ✅ All ports in correct ranges")
    
    print("\n3️⃣  Checking completeness...")
    errors = validate_completeness(registry)
    if errors:
        all_errors.extend(errors)
    else:
        print("   ✅ All services mapped")
    
    print("\n4️⃣  Checking metadata...")
    errors = validate_metadata(registry)
    if errors:
        all_errors.extend(errors)
    else:
        total = registry["metadata"]["total_services"]
        print(f"   ✅ Metadata correct ({total} services)")
    
    # Report results
    print("\n" + "=" * 60)
    if all_errors:
        print(f"\n❌ VALIDATION FAILED ({len(all_errors)} errors)\n")
        for error in all_errors:
            print(error)
        return 1
    
    print("\n✅ PORT REGISTRY VALID")
    print(f"   Total services: {registry['metadata']['total_services']}")
    print("   No conflicts detected")
    print("   All ranges correct\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
