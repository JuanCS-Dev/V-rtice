#!/usr/bin/env python3
"""Export OpenAPI schema from API Gateway.

This script exports the complete OpenAPI specification from the Vértice
API Gateway to a JSON file, enabling:
- Contract testing (frontend ↔ backend)
- Type generation for frontend (TypeScript)
- API documentation versioning
- Breaking change detection in CI/CD

Usage:
    python export_openapi.py [--output FILE] [--format json|yaml]

Examples:
    # Export to default location (openapi.json in project root)
    python export_openapi.py

    # Export to custom location
    python export_openapi.py --output /path/to/schema.json

    # Export as YAML
    python export_openapi.py --format yaml

Following Boris Cherny's principle: "Schema is the source of truth"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

try:
    from api_gateway.main import app
except ImportError as e:
    print(f"❌ Error importing API Gateway: {e}")
    print("\nMake sure you're running this from the project root:")
    print("  cd /path/to/V-rtice")
    print("  python backend/scripts/export_openapi.py")
    sys.exit(1)


def export_schema(output_path: Path, format_type: str = "json") -> None:
    """Export OpenAPI schema to file.

    Args:
        output_path: Path to write the schema file
        format_type: Output format ('json' or 'yaml')

    Raises:
        ValueError: If format_type is not 'json' or 'yaml'
    """
    # Get the OpenAPI schema
    schema = app.openapi()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export based on format
    if format_type == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        print(f"✅ OpenAPI schema exported to: {output_path}")
        print(f"   Format: JSON")
        print(f"   Size: {output_path.stat().st_size:,} bytes")

    elif format_type == "yaml":
        try:
            import yaml
        except ImportError:
            print("❌ PyYAML not installed. Install with: pip install pyyaml")
            print("   Falling back to JSON export...")
            format_type = "json"
            export_schema(output_path.with_suffix(".json"), "json")
            return

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(schema, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ OpenAPI schema exported to: {output_path}")
        print(f"   Format: YAML")
        print(f"   Size: {output_path.stat().st_size:,} bytes")

    else:
        raise ValueError(f"Unsupported format: {format_type}. Use 'json' or 'yaml'")

    # Print schema statistics
    paths_count = len(schema.get("paths", {}))
    schemas_count = len(schema.get("components", {}).get("schemas", {}))
    tags_count = len(schema.get("tags", []))

    print(f"\n📊 Schema Statistics:")
    print(f"   API Version: {schema.get('info', {}).get('version', 'unknown')}")
    print(f"   Endpoints: {paths_count}")
    print(f"   Schemas: {schemas_count}")
    print(f"   Tags: {tags_count}")

    # Print security schemes
    security_schemes = schema.get("components", {}).get("securitySchemes", {})
    if security_schemes:
        print(f"\n🔐 Security Schemes:")
        for scheme_name, scheme in security_schemes.items():
            scheme_type = scheme.get("type", "unknown")
            print(f"   - {scheme_name}: {scheme_type}")


def validate_schema(schema: dict) -> tuple[bool, list[str]]:
    """Validate OpenAPI schema for common issues.

    Args:
        schema: The OpenAPI schema dict

    Returns:
        tuple: (is_valid, list of issues)
    """
    issues = []

    # Check required fields
    if "openapi" not in schema:
        issues.append("Missing 'openapi' version field")

    if "info" not in schema:
        issues.append("Missing 'info' section")
    elif "title" not in schema.get("info", {}):
        issues.append("Missing 'info.title'")

    if "paths" not in schema or not schema["paths"]:
        issues.append("No paths defined")

    # Check for security schemes
    security_schemes = schema.get("components", {}).get("securitySchemes", {})
    if not security_schemes:
        issues.append("⚠️  Warning: No security schemes defined")

    # Check for common response schemas
    common_schemas = schema.get("components", {}).get("schemas", {})
    if "ErrorResponse" not in common_schemas:
        issues.append("⚠️  Warning: Missing 'ErrorResponse' schema")

    return len(issues) == 0, issues


def main() -> None:
    """Main entry point for OpenAPI export script."""
    parser = argparse.ArgumentParser(
        description="Export OpenAPI schema from Vértice API Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export to default location
  python export_openapi.py

  # Export to custom location
  python export_openapi.py --output /path/to/schema.json

  # Export as YAML
  python export_openapi.py --format yaml --output openapi.yaml

  # Validate only (no export)
  python export_openapi.py --validate-only

Integration with CI/CD:
  # In GitHub Actions / GitLab CI
  - name: Export OpenAPI Schema
    run: python backend/scripts/export_openapi.py

  - name: Validate Schema
    run: |
      npm install -g @apidevtools/swagger-cli
      swagger-cli validate openapi.json

  - name: Check for Breaking Changes
    uses: oasdiff/oasdiff-action@v0.0.15
    with:
      base: main
      revision: HEAD
      fail-on-breaking: true
        """
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=PROJECT_ROOT / "openapi.json",
        help="Output file path (default: openapi.json in project root)"
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate schema without exporting"
    )

    args = parser.parse_args()

    # Get schema
    print("📋 Generating OpenAPI schema...")
    try:
        schema = app.openapi()
    except Exception as e:
        print(f"❌ Error generating schema: {e}")
        sys.exit(1)

    # Validate schema
    print("\n🔍 Validating schema...")
    is_valid, issues = validate_schema(schema)

    if issues:
        print("\n⚠️  Schema Validation Issues:")
        for issue in issues:
            print(f"   - {issue}")

    if not is_valid:
        print("\n❌ Schema validation failed")
        sys.exit(1)

    print("✅ Schema validation passed")

    # Export (unless validate-only)
    if not args.validate_only:
        print(f"\n📤 Exporting schema...")
        try:
            export_schema(args.output, args.format)
        except Exception as e:
            print(f"\n❌ Error exporting schema: {e}")
            sys.exit(1)

        # Print usage instructions
        print(f"\n📚 Next Steps:")
        print(f"\n1. View interactive docs:")
        print(f"   → Swagger UI: http://localhost:8000/docs")
        print(f"   → ReDoc: http://localhost:8000/redoc")
        print(f"\n2. Generate frontend types:")
        print(f"   cd frontend")
        print(f"   npx openapi-typescript {args.output} -o src/types/api.ts")
        print(f"\n3. Validate with external tools:")
        print(f"   npx @apidevtools/swagger-cli validate {args.output}")
        print(f"\n4. Compare with previous version:")
        print(f"   npx oasdiff diff {args.output} openapi-previous.json")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
